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

def auth_required(method):
    def wrapper(self,*args,**kwargs):
        if not self.authenticated:
            if self.creds:
                self.login()
            else:
                raise exc.LoginRequired("This method requires authentication.")
        return method(self, *args, **kwargs)
    return wrapper

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
    
    @auth_required
    def export_gpx(self, activity_id):
        """
        Export an activity as GPX. 
        
        (requires authentication -- and premium acct.)
        """
        r = self.rsess.get('http://app.strava.com/activities/{id}/export_gpx'.format(id=activity_id),
                           cookies=self.cookies)
        
        return r.content
    
    @auth_required
    def upload(self, fileobj):
        """
        Upload using the browser API instead of the V2 uploader.  
        
        The V2 uploader, while simpler, has some quirks -- such as reporting the device
        as an iPhone -- that make it not an ideal way to upload ride data. 
        """
        
        """
        <form action="/upload/files" enctype="multipart/form-data" method="POST" novalidate="novalidate">
        <input name="_method" type="hidden" value="post">
        <input name="authenticity_token" type="hidden" value="VRxU+PlDIKEctpxvZkrqcHN5oq7QavspWaWwL18vZzQ=">
        <input id="files" multiple="multiple" name="files[]" type="file">
        <div class="loader">
        <div class="graphic spinner"><img alt="Anim-spinner-20x20" src="http://d26ifou2tyrp3u.cloudfront.net/assets/common/anim-spinner-20x20-65cdce3c15857b19c06268245df96465.gif"><span class="status">Uploading Files...</span></div>
        </div>
        </form>
        """
        raise NotImplementedError()