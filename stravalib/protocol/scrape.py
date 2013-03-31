# -*- coding: utf-8 -*-
import re
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

class WebsiteClient(object):

    default_user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.52 Safari/537.17'
    headers = None
    cookies = None
    creds = None
    
    def __init__(self, username, password, user_agent=None):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        if user_agent is None:
            user_agent = self.default_user_agent
        self.rsession = requests.Session()
        self.rsession.headers.update({'User-Agent': user_agent})
        if username and password:
            self.creds = Credentials(username, password)
        
    @property
    def authenticated(self):
        # XXX: This is not really sufficient
        return self.cookies is not None
    
    def login(self):
        if not self.creds:
            raise ValueError("No credentials were specified.")
        
        r = self.rsession.get('https://www.strava.com/login')
        soup = BeautifulSoup(r.text)
        
        token_name = soup.find('meta', attrs=dict(name="csrf-param"))['content']
        token_value = soup.find('meta', attrs=dict(name="csrf-token"))['content']
        
        r = self.rsession.post('https://www.strava.com/session',
                               data={'email': self.creds.username,
                                     'password': self.creds.password,
                                     'plan': '',
                                     'utf8': u'✓',
                                     token_name: token_value},
                               cookies=r.cookies)
        
        soup = BeautifulSoup(r.text)
        #print r.text
        #print "Page title: %s" % soup.title.string
        if soup.title.string.startswith('Log In'):
            raise exc.LoginFailed("Login failed.")
        
        self.cookies = r.cookies
    
    @auth_required
    def export_gpx(self, activity_id):
        """
        Export an activity as GPX. 
        
        (requires authentication -- and premium acct.)
        """
        r = self.rsession.get('http://app.strava.com/activities/{id}/export_gpx'.format(id=activity_id),
                           cookies=self.cookies)
        
        return r.content
    
    @auth_required
    def check_upload_status(self, upload_id):
        """
        Checks the status of a single uploaded file.
        
        Here is an example of in-progress response:
          {"id":51490096,"name":"01/26/2012 04:02:23 AM","progress":65,"workflow":"Analyzing"}
        
        Here is an example of completed response:
          {"id":51490096,"name":"01/26/2012 04:02:23 AM","progress":100,"workflow":"Uploaded",
            "activity":{"id":46504896,"name":"01/26/2012 Arlington, VA","type":"Ride","workout_type":null,"display_type":
            "Ride","private":false,"bike_id":null,"athlete_gear_id":null,"start_date":"01/26/2012","start_day":"Thu",
            "distance":"15.5","long_unit":"miles","short_unit":"mi","moving_time":"00:58:27","moving_time_raw":3507,"elapsed_time":"01:01:40","trainer":false,"commute":false,"elevation_gain":"712",
            "description":null,"activity_url":"http://app.strava.com/activities/46504896",
            "activity_url_for_twitter":"http://app.strava.com/activities/46504896?ref=1MT1yaWRlX3NoYXJlOzI9dHdpdHRlcjs0PTE4OTQ0MTE%253D",
            "twitter_msg":"went for a 15.5 mile ride.","static_map_url":"http://maps.google.com/maps/api/staticmap?maptype=terrain\u0026size=220x130\u0026sensor=false\u0026path=color:0xFF0000BF|weight:2|38.8828,-77.1436|38.8823,-77.1447|38.884,-77.1489|38.884,-77.1496|38.8833,-77.1501|38.8845,-77.1538|38.8829,-77.156|38.8824,-77.1591|38.8858,-77.1596|38.8869,-77.1606|38.89,-77.1733|38.8917,-77.1843|38.8919,-77.1887|38.8911,-77.2013|38.8898,-77.2064|38.8903,-77.2094|38.8914,-77.2114|38.8904,-77.2123|38.8896,-77.2144|38.8963,-77.2398|38.8971,-77.2419|38.9002,-77.2462|38.9009,-77.2478|38.9014,-77.2514|38.9009,-77.2575|38.9009,-77.2596|38.9013,-77.2611|38.9045,-77.2673|38.9154,-77.2797|38.9181,-77.2837|38.9202,-77.2854|38.9249,-77.2877|38.9273,-77.2904|38.9316,-77.2997|38.9328,-77.3055|38.9336,-77.3075|38.9369,-77.3134|38.9409,-77.3183|38.9419,-77.3215|38.9431,-77.3239|38.9471,-77.3276|38.9488,-77.3303|38.9535,-77.3463|38.9545,-77.3493|38.9567,-77.3536|38.9571,-77.3569|38.9564,-77.3611|38.9573,-77.357|38.9571,-77.3552|38.9486,-77.3578|38.944,-77.3609|38.9445,-77.3615|38.9441,-77.3618"}},
                  
        :param upload_id: A single upload ID to check.
        :type upload_id: int
        :return: Progress dict for specified file.
        :rtype: dict
        """
        r = self.rsession.get('http://app.strava.com/upload/progress.json',
                              params={'ids[]': upload_id},
                              cookies=self.cookies)
        progress = r.json()
        if not len(progress):
            raise exc.Fault("No matches for upload id: {0}".format(upload_id))
        else:
            for p in progress:
                if p['id'] == upload_id:
                    return p
            else:
                self.log.debug("upload status reponse: {0!r}".format(progress))
                raise exc.Fault("Statuses returned, but no matches for upload id: {0}".format(upload_id))
        
    @auth_required
    def upload(self, activity_file):
        """
        Upload using the website instead of the V2 uploader.  
        
        The V2 uploader, while simpler, has some quirks -- such as reporting the device
        as an iPhone -- that make it not an ideal way to upload ride data.
        
        :param activity_file: A file path or file-like object to use for uploading.
        :type activity_file: str or file-like object.
        :return: The ids of the uploaded files.  Note that list may include other recently uploaded IDs too.
        :rtype: list
        """
        
        """
        For reference here is the upload form:
        
        <form action="/upload/files" enctype="multipart/form-data" method="POST" novalidate="novalidate">
        <input name="_method" type="hidden" value="post">
        <input name="authenticity_token" type="hidden" value="VRxU+PlDIKEctpxvZkrqcHN5oq7QavspWaWwL18vZzQ=">
        <input id="files" multiple="multiple" name="files[]" type="file">
        </form>
        """
        if hasattr(activity_file, 'read'):
            fileobj = activity_file
        else:
            fileobj = open(activity_file)
        
        r = self.rsession.get('http://app.strava.com/upload/select_new',
                              cookies=self.cookies)
        
        soup = BeautifulSoup(r.text)
        
        authenticity_token = soup.find('input', attrs=dict(name="authenticity_token"))['value']
        
        params = {'_method': 'post',
                  'authenticity_token': authenticity_token}
        
        files = {'files[]': fileobj}
        r = self.rsession.post('http://app.strava.com/upload/files', data=params, files=files, cookies=self.cookies)
        r.raise_for_status()
        
        matches = re.search(r'var uploadingIds\s*=\s*\[([\d,]+)\];', r.text)
        if not matches:
            self.log.debug(r.text)
            raise exc.Fault("Unable to locate upload IDs in reponse (enable debug logging to see response html page)")
        
        upload_ids = [int(u_id.strip()) for u_id in matches.group(1).split(',')] 
        
        return upload_ids