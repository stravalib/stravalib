import functools
import logging
import collections
from datetime import datetime, timedelta
from urlparse import urlunsplit
from urllib import urlencode

from stravalib.protocol import BaseApiClient, BaseModelMapper
from stravalib.model import Activity, Athlete, Club, Segment
from stravalib import measurement

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

class ApiV3Client(BaseApiClient):
    """
    A client library implementing V3 of the Strava API.
    """
    base_url = 'https://www.strava.com/api/v3'
    
    # http://www.strava.com/api/v1/athletes/:athlete_id/bikes/:id
    # {"bike": {"name":"Surly Crosscheck","default_bike":false,"athlete_id":21,"notes":"Single speed commuter bike","weight":12.7006,"id":1371,"frame_type":2,"retired":0}}
    # {"bike": {"name":"Storck Absolutist","default_bike":false,"athlete_id":21,"notes":"","weight":7.71107,"id":21,"frame_type":3,"retired":0}},{"bike": {"name":"Turner Flux","default_bike":false,"athlete_id":21,"notes":"","weight":12.7006,"id":22,"frame_type":1,"retired":0}},{"bike": {"name":"Rock Lobster","default_bike":false,"athlete_id":21,"notes":"","weight":8.61825,"id":41,"frame_type":2,"retired":0}},{"bike": {"name":"Surly Crosscheck","default_bike":false,"athlete_id":21,"notes":"Single speed commuter bike","weight":12.7006,"id":1371,"frame_type":2,"retired":0}}
    
    def authorization_url(self, client_id, redirect_uri, approval_prompt='auto', scope=None, state=None):
        """
        Get the URL needed to authorize your application to access a Strava user's information.
        
        :param client_id: The numeric developer client id.
        :type client_id: int
        
        :param redirect_uri: The URL that Strava will redirect to after successful (or failed) authorization.
        :type redirect_uri: str
        
        :param approval_prompt: Whether to prompt for approval even if approval already granted to app.
                                Choices are 'auto' or 'force'.  (Default is 'auto')
        :type approval_prompt: str
        
        :param scope: The access scope required.  Omit to imply "public".  Valid values are 'public', 'write', 'view_private', 'view_private,write'
        :type scope: str
        
        :param state: An arbitrary variable that will be returned to your application in the redirect URI.
        :type state: str
        
        :return: The URL to use for authorization link.
        :rtype: str
        """
        if isinstance(scope, (list, tuple)):
            scope = ','.join(scope)
        params = {'client_id': client_id,
                  'redirect_uri': redirect_uri,
                  'approval_prompt': approval_prompt}
        if scope is not None:
            params['scope'] = scope
        if state is not None:
            params['state'] = state
            
        return urlunsplit(('https', self.server, '/oauth/authorize', urlencode(params), ''))
    
    def exchange_code_for_token(self, client_id, client_secret, code):
        """
        Exchange the temporary authorization code (returned with redirect from strava authorization URL)
        for a permanent access token.
        
        :param client_id: The numeric developer client id.
        :type client_id: int
        
        :param client_secret: The developer client secret
        :type client_secret: str
        
        :param code: The temporary authorization code
        :type code: str
        
        :return: The access token.
        :rtype: str
        """
        response = self._get('https://{0}/oath/token'.format(self.server),
                             params={'client_id': client_id, 'client_secret': client_secret, 'code': code})
        return response['access_token']

    def _extract_referenced_vars(self, s):
        """
        """
        d = {}
        while True:
            try:
                s.format(**d)
            except KeyError as exc:
                # exc.args[0] contains the name of the key that was not found;
                # 0 is used because it appears to work with all types of placeholders.
                d[exc.args[0]] = 0
            else:
                break
        return d.keys()

    def get(self, url, **params):
        """
        Performs a generic GET request for specified params, returning the response.
        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**params)
        for k,v in params.items():
            if k in referenced:
                del params[k]
        return self._get(url, params=params)
    
    def get_athlete(self, athlete_id=None):
        """
        Gets the specified athlete; if athlete_id is None then retrieves a detail-
        level representation of currently authenticated athlete; otherwise 
        summary-level representation returned of athlete.
        
        http://strava.github.io/api/v3/athlete/#get-details
        http://strava.github.io/api/v3/athlete/#get-another-details
        
        :param: athlete_id: The numeric ID of the athlete to fetch.
        :rtype: dict
        """
        if athlete_id is None:
            response = self._get('/athlete')
        else:
            response = self._get('/athletes/{0}'.format(athlete_id))
        return response
    
    def get_athlete_friends(self, athlete_id=None, **kwargs):
        """
        http://strava.github.io/api/v3/follow/#friends
        
        :param athlete_id
        :keyword page: The page number to fetch.
        :keyword per_page: Number of rows to return per page.
        """
        if athlete_id is None:
            response = self._get('/athlete/friends', params=kwargs)
        else:
            response = self._get('/athletes/{0}/friends', params=kwargs)
        return response
    
    def get_athlete_followers(self, athlete_id=None, **kwargs):
        """
        http://strava.github.io/api/v3/follow/#followers
        
        :param athlete_id
        :keyword page: The page number to fetch.
        :keyword per_page: Number of rows to return per page.
        """
        if athlete_id is None:
            response = self._get('/athlete/followers', params=kwargs)
        else:
            response = self._get('/athletes/{0}/followers', params=kwargs)
        return response
        
    def get_both_following(self, athlete_id, **kwargs):
        """
        Retrieve the athletes who both the authenticated user and the indicated athlete are following.
        
        http://strava.github.io/api/v3/follow/#both
        
        :param athlete_id
        :keyword page: The page number to fetch.
        :keyword per_page: Number of rows to return per page.
        """
        return self._get('/athletes/{0}/both-following'.format(athlete_id), params=kwargs)
        
    def update_athlete(self, **kwargs):
        """
        http://strava.github.io/api/v3/athlete/#get-details
        """
        raise NotImplementedError()
    
    def get_athlete_clubs(self):
        """
        List the clubs for the currently authenticated athlete.
        http://strava.github.io/api/v3/clubs/#get-athletes
        :rtype: list
        """
        response = self._get("/athlete/clubs")
        return response
    
    def get_club(self, club_id):
        """
        Return V3 object structure for club
        http://strava.github.io/api/v3/clubs/#get-details
        
        :param club_id: The ID of the club to fetch.
        """
        response = self._get("/clubs/{0}".format(club_id))
        return response['club']
    
    def get_club_members(self, club_id, **kwargs):
        """
        Gets the member objects for specified club ID.
        http://strava.github.io/api/v3/clubs/#get-members
        
        :param club_id: The numeric ID for a club.
        :keyword page: The page number to fetch.
        :keyword per_page: Number of rows to return per page.
        """
        response = self._get("/clubs/{0}/members".format(club_id), params=kwargs)
        return response['members']

    def get_club_activities(self, club_id, **kwargs):
        """
        Gets the activities associated with specified club.
        http://strava.github.io/api/v3/clubs/#get-activities
        
        :param club_id: The numeric ID for a club.
        :keyword page: The page number to fetch.
        :keyword per_page: Number of rows to return per page.
        """
        # TODO: Pager
        response = self._get("/clubs/{0}/activities".format(club_id), params=kwargs)
        return response
    
    def get_activity(self, activity_id):
        """
        Return V3 object structure for an activity.
        
        http://strava.github.io/api/v3/activities/#get-details
        
        :param activity_id: The activity_id of ride to fetch.
        """
        url = "http://{0}/api/v1/rides/{1}".format(self.server, activity_id)
        return self._get(url)['ride']
            
    def get_athlete_activities(self, **kwargs):
        """
        Enumerate rides for current athlete.
        :keyword before:
        :keyword after:
        :keyword page: The page number to fetch.
        :keyword per_page: Number of rows to return per page.
        """
        response = self._get("/athlete/activities", params=kwargs)
        return response
    
    def get_friend_activities(self):
        """
        http://strava.github.io/api/v3/activities/#get-feed
        """
        
    def update_activity(self, **kwargs):
        """
        http://strava.github.io/api/v3/activities/#put-updates
        """
        raise NotImplementedError()
    
    def get_activity_zones(self, activity_id):
        """
        http://strava.github.io/api/v3/activities/#zones
        """
        return self._get('/activities/{0}/zones'.format(activity_id))
    
    def get_gear(self, gear_id):
        """
        Get details for an item of gear.
        http://strava.github.io/api/v3/gear/#show
        
        :param gear_id: The gear id.
        :type gear_id: str
        """
    
    
    def get_ride_efforts(self, ride_id):
        """
        Return V1 object structure for ride efforts.
        
        :param ride_id: The id of associated ride to fetch.
        """
        url = "http://{0}/api/v1/rides/{1}/efforts".format(self.server, ride_id)
        return self._get(url)['efforts']

    def get_segment(self, segment_id):
        """
        http://strava.github.io/api/v3/segments/#retrieve 
        """
        url = "/segments/{0}".format(segment_id)
        return self._get(url)['segment']
    
    def get_segment_leaderboard(self, segment_id):
        """
        http://strava.github.io/api/v3/segments/#leaderboard
        """
    def explore_segments(self, bounds, activity_type, min_cat, max_cat):
        """
        Returns an array of up to 10 segments.
        http://strava.github.io/api/v3/segments/#explore
        """
        assert activity_type in ('riding', 'running')
        raise NotImplementedError()
    
    def get_segment_effort(self, effort_id):
        """
        http://strava.github.io/api/v3/efforts/#retrieve
        """
        return self._get('/segment_efforts/{0}'.format(effort_id))         
    
    # TODO: Streams
    # TODO: Uploads
    
class BatchedResultsIterator(object):
    """
    Iterates over requests that return a batch of (typically 50) results and support an offset parameter.
    
    For example, Strava API only returns 50 rides at a time, so this provides a mechanism to abstract over
    that limitation. 
    """
    
    batch_size = 50 #: How many results returned in a batch.
     
    def __init__(self, result_fetcher, limit=None):
        """
        :param result_fetcher: The callable that will return another batch of results.
        :type result_fetcher: callable
        
        :param limit: The maximum number of rides to return.
        :type limit: int
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.limit = limit
        self.result_fetcher = result_fetcher
        
        self._counter = 0
        self._buffer = None
        self._offset = 0
        self._all_results_fetched = False
    
    def _fill_buffer(self):
        """
        Fills the internal size-50 buffer from Strava API.
        """
        # If we cannot fetch anymore from the server then we're done here.
        if self._all_results_fetched:
            raise StopIteration
        
        self._buffer = collections.deque(self.result_fetcher(offset=self._offset))
        self.log.debug("Requested rides {0} - {1} (got: {2})".format(self._offset,
                                                                     self._offset + self.batch_size,
                                                                     len(self._buffer)))
        if len(self._buffer) < self.batch_size:
            self._all_results_fetched = True
            
        self._offset += self.batch_size

    def __iter__(self):
        return self
    
    def next(self):
        if self.limit and self._counter >= self.limit:
            raise StopIteration
        if not self._buffer:
            self._fill_buffer()
        try:
            result = self._buffer.popleft()
        except IndexError:
            raise StopIteration
        else:
            self._counter += 1
            return result
        
    
def _v1_attrib_name(attrib_name):
    """
    Converts a joined_lower attribute name to camelCase which is preferred by the V1 API.
    """
    parts = attrib_name.split('_')
    if len(parts) == 1: # single words don't need to be transformed
        return attrib_name
    else:
        return ''.join([parts[0]] + [p[0].upper() + p[1:] for p in parts[1:]])
        