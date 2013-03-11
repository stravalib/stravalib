import logging
import requests
from bs4 import BeautifulSoup

from stravalib.protocol import Credentials
from stravalib import exc

__authors__ = ['"Hans Lellelid" <hans@xmpl.org>']
__copyright__ = "Copyright 2013 Hans Lellelid"
__license__ = """Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
 
  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""

class WebSession(object):

    server = 'www.strava.com'
    default_user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.52 Safari/537.17'
    headers = None
    cookies = None
    creds = None
    
    def __init__(self, username, password, user_agent=None):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        if user_agent is None:
            user_agent = self.default_user_agent
        self.rsess = requests.Session()
        self.rsess.headers.update({'User-Agent': user_agent})
        if username and password:
            self.creds = Credentials(username, password)
        
    @property
    def authenticated(self):
        # XXX: This is not really sufficient
        return self.cookies is not None
    
    def login(self):
        if not self.creds:
            raise ValueError("No credentials were specified.")
        
        r = self.rsess.get('https://{server}/login'.format(server=self.server))
        soup = BeautifulSoup(r.text)
        
        token_name = soup.find('meta', attrs=dict(name="csrf-param"))['content']
        token_value = soup.find('meta', attrs=dict(name="csrf-token"))['content']
        
        r = self.rsess.post('https://{server}/session'.format(server=self.server),
                            params={'email': self.creds.username,
                                    'password': self.creds.password,
                                    'plan': '',
                                    token_name: token_value},
                            cookies=r.cookies)
        
        soup = BeautifulSoup(r.text)
        if not soup.title.string.startswith('Strava | Home'):
            raise exc.LoginFailed("Login failed.")
        
        self.cookies = r.cookies
    

    def export_gpx(self, activity_id):
        """
        Export an activity as GPX. 
        
        (requires authentication -- and premium acct.)
        """
        if not self.authenticated:
            if self.creds:
                self.login()
            else:
                raise exc.LoginRequired("GPX export requires authentication")
        
        r = self.rsess.get('http://app.strava.com/activities/{id}/export_gpx'.format(id=activity_id),
                           cookies=self.cookies)
        
        return r.content