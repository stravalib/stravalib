import functools
import logging
import collections
from datetime import datetime, timedelta

from stravalib.protocol import BaseApiClient, BaseModelMapper
from stravalib.model import Ride, Athlete, Club, Segment
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

class V1ModelMapper(BaseModelMapper):
    
    def populate_athlete(self, entity_model, entity_struct):
        """
        Populates a :class:`stravalib.model.Athlete` model object with data from the V1 struct
        that is returned with ride details.
        
        :param entity_model: The athlete model to fill.
        :type entity_model: :class:`stravalib.model.Athlete`
        :param entity_struct: The athlete struct from V1 ride response object.
        :type entity_struct: dict
        """
        entity_model.id = entity_struct['id']
        entity_model.name = entity_struct['name']
        # Often we only have partial athlete structure (e.g. when returning club members, etc.)
        entity_model.username = entity_struct.get('username')
        
    def populate_minimal_ride_effort(self, effort_model, effort_struct):
        """
        Populates some minimal ride effort data, as returned by the get_ride_efforts call.
        
        Effort struct example:
            {
             "elapsed_time": 18, 
             "id": 571734780, 
             "segment": {
                  "id": 1030752, 
                  "name": "Brandymore Castle Hill Climb East Ascent"
            }
            
        :param effort_model:
        :type effort_model: :class:`stravalib.model.SegmentEffort`
        """
        effort_model.id = effort_struct['id']
        effort_model.elapsed_time = timedelta(seconds=effort_struct['elapsed_time'])
        effort_model.segment = Segment(self.client)
        self.populate_minimal(effort_model.segment, effort_struct['segment'])
    
    def populate_minimal_segment_effort(self, effort_model, effort_struct):
        """
        Populates some minimal segment effort data, as returned by the get_segment_efforts call.
        
        Segment effort struct example:
             {
                "activityId": 886543, 
                "athlete": {
                    "id": 13669, 
                    "name": "Jeff Dickey", 
                    "username": "jdickey"
                }, 
                "elapsedTime": 103, 
                "id": 13149960, 
                "startDate": "2011-07-06T21:32:21Z", 
                "startDateLocal": "2011-07-06T17:32:21Z", 
                "timeZoneOffset": -18000
            }
        :param effort_model:
        :type effort_model: :class:`stravalib.model.SegmentEffort`
        """
        effort_model.id = effort_struct['id']
        effort_model.activity_id = effort_struct['activityId']
        effort_model.elapsed_time = timedelta(seconds=effort_struct['elapsedTime'])
        effort_model.start_date = self._parse_datetime(effort_struct['startDateLocal'], effort_struct['timeZoneOffset'])
        effort_model.athlete = Athlete(self.client)
        self.populate_athlete(effort_model.athlete, effort_struct['athlete'])
           
    def populate_ride_effort_base(self, entity_model, entity_struct):
        """
        Populates the attributes shared by rides and efforts.
        """
        self.populate_minimal(entity_model, entity_struct)
        
        athlete_struct = entity_struct['athlete']
        athlete = Athlete(bind_client=entity_model.bind_client)
        self.populate_athlete(athlete, athlete_struct)
        entity_model.athlete = athlete
        
        entity_model.average_speed = self._convert_speed(entity_struct['averageSpeed'])
        entity_model.average_watts = entity_struct['averageWatts']
        entity_model.maximum_speed = self._convert_speed(measurement.kph(entity_struct['maximumSpeed'] / 1000.0)) # Not sure why this is in meters per *hour* ... !?
        entity_model.elevation_gain = self._convert_elevation(entity_struct['elevationGain'])
        entity_model.distance = self._convert_distance(entity_struct['distance'])
        entity_model.elapsed_time = timedelta(seconds=entity_struct['elapsedTime'])
        entity_model.moving_time = timedelta(seconds=entity_struct['movingTime'])
        entity_model.start_date = self._parse_datetime(entity_struct['startDateLocal'], entity_struct['timeZoneOffset'])
    
        
    def populate_ride(self, entity_model, entity_struct):
        """
        Populates a :class:`stravalib.model.Ride` model object with data from the V1 structure.
        
        Note that not all of the model properties will have been set by this method (some are
        only available from V2 structure).
        
        :param entity_model: The model object to fill.
        :type entity_model: :class:`stravalib.model.Ride`
        :param entity_struct: The raw ride V1 response structure.
        :type entity_struct: dict
        """
        self.populate_ride_effort_base(entity_model, entity_struct)
        entity_model.commute = entity_struct['commute']
        entity_model.trainer = entity_struct['trainer']
        entity_model.location = entity_struct['location']
    
    def populate_effort(self, effort_model, effort_struct):
        """
        Populates a :class:`stravalib.model.Effort` model object with data from the V1 structure.
        
        :param effort_model: The model object to fill.
        :type effort_model: :class:`stravalib.model.Effort`
        :param effort_struct: The raw effort V1 response structure.
        :type effort_struct: dict
        """
        self.populate_ride_effort_base(effort_model, effort_struct)
        
        athlete_struct = effort_struct['athlete']
        athlete = Athlete(bind_client=effort_model.bind_client)
        self.populate_athlete(athlete, entity_struct=athlete_struct)
        
        minimal_ride_struct = effort_struct['ride']
        ride = Ride(bind_client=effort_model.bind_client)
        self.populate_minimal(ride, minimal_ride_struct)
        
        minimal_segment_struct = effort_struct['segment']
        segment = Segment(bind_client=effort_model.bind_client)
        self.populate_minimal(segment, minimal_segment_struct)
        
        effort_model.athlete = athlete
        
    def populate_segment(self, segment_model, segment_struct):
        """
        Populates a :class:`stravalib.model.Effort` model object with data from the V1 structure.
        
        :param segment_model: The model object to fill.
        :type segment_model: :class:`stravalib.model.Effort`
        :param segment_struct: The raw effort V1 response structure.
        :type segment_struct: dict
        """
        self.populate_minimal(segment_model, segment_struct)
        segment_model.average_grade = segment_struct['averageGrade']
        segment_model.climb_category = segment_struct['climbCategory']
        segment_model.distance = segment_struct['distance']
        segment_model.elevation_gain = segment_struct['elevationGain']
        segment_model.elevation_high = segment_struct['elevationHigh']
        segment_model.elevation_low = segment_struct['elevationLow']
        
    def populate_club(self, club_model, club_struct):
        """
        Populates a :class:`stravalib.model.Club` model object with data from the V1 structure.
        
        :param club_model: The model object to fill.
        :type club_model: :class:`stravalib.model.Club`
        :param club_struct: The raw club V1 response structure.
        :type club_struct: dict
        """
        club_model.id = club_struct['id']
        club_model.name = club_struct['name']
        club_model.location = club_struct['location']
        club_model.description = club_struct['description']
        
        
class ApiV1Client(BaseApiClient):
    """
    A client library implementing V1 of the Strava API.
    """
    mapper_class = V1ModelMapper
    
    # http://www.strava.com/api/v1/athletes/:athlete_id/bikes/:id
    # {"bike": {"name":"Surly Crosscheck","default_bike":false,"athlete_id":21,"notes":"Single speed commuter bike","weight":12.7006,"id":1371,"frame_type":2,"retired":0}}
    # {"bike": {"name":"Storck Absolutist","default_bike":false,"athlete_id":21,"notes":"","weight":7.71107,"id":21,"frame_type":3,"retired":0}},{"bike": {"name":"Turner Flux","default_bike":false,"athlete_id":21,"notes":"","weight":12.7006,"id":22,"frame_type":1,"retired":0}},{"bike": {"name":"Rock Lobster","default_bike":false,"athlete_id":21,"notes":"","weight":8.61825,"id":41,"frame_type":2,"retired":0}},{"bike": {"name":"Surly Crosscheck","default_bike":false,"athlete_id":21,"notes":"Single speed commuter bike","weight":12.7006,"id":1371,"frame_type":2,"retired":0}}
    
    
    def get_clubs(self, name):
        """
        Return V1 results of search for club by name.
        
        Response example:
            [{"name":"Mission Cycling","id":15}]
        
        :param name: The club name (substring) to match on.
        :rtype: list
        """
        response = self._get("http://{0}/api/v1/clubs".format(self.server), params={'name': name})
        return response['clubs']
    
    def get_club(self, club_id):
        """
        Return V1 object structure for club
        
        Response example:
            {"description":"Mission Cycling is devoted to the enjoyment of one of the world's purest, most classic sporting endeavors: Cycling. Our aim is simple: to enjoy the unique challenges and rewards offered by experiencing our unique countryside from the saddle of a bike.",
              "name":"Mission Cycling",
              "location":"San Francisco, CA",
              "club_id":15
            }
        
        :param club_id: The ID of the club to fetch.
        """
        response = self._get("http://{0}/api/v1/clubs/{1}".format(self.server, club_id))
        return response['club']
    
    def get_club_members(self, club_id):
        """
        Gets the member objects for specified club ID.
        
        :param club_id:
        """
        response = self._get("http://{0}/api/v1/clubs/{1}/members".format(self.server, club_id))
        return response['members']
        
    def get_ride(self, ride_id):
        """
        Return V1 object structure for ride.
        
        {"ride":{"id":11280631,
                 "startDate":"2012-06-20T11:10:00Z",
                 "startDateLocal":"2012-06-20T07:10:00Z",
                 "timeZoneOffset":-18000,
                 "elapsedTime":3000,
                 "movingTime":3000,
                 "distance":25588.6,
                 "averageSpeed":8.529533333333333,
                 "averageWatts":null,
                 "maximumSpeed":0.0,
                 "elevationGain":0,
                 "location":"Arlington, VA",
                 "name":"Morning Commute - computer malfunction?",
                 "bike":{"id":67845,"name":"Commuter/Cross"},
                 "athlete":{"id":182475,"name":"Hans Lellelid","username":"hozn"},
                 "description":"",
                 "commute":true,
                 "trainer":false}}
        
        :param ride_id: The ride_id of ride to fetch.
        """
        url = "http://{0}/api/v1/rides/{1}".format(self.server, ride_id)
        return self._get(url)['ride']
            
    def get_rides(self, **kwargs):
        """
        Enumerate rides for specified attribute/value.
        
        :keyword club_id: Optional. Id of the Club for which to search for member's Rides.
        :type club_id: int
        :keyword athlete_id: Optional. Id of the Athlete for which to search for Rides.
        :type athlete_id: int
        :keyword athlete_name: Optional. Username of the Athlete for which to search for Rides.
        :type athlete_name: str
        :keyword start_date: Optional. Day on which to start search for Rides.  The date is the local time of when the ride started.
        :type start_date: :class:`datetime.datetime`
        :keyword end_date: Optional. Day on which to end search for Rides. The date is the local time of when the ride ended.
        :type end_date: :class:`datetime.datetime`
        :keyword start_id: Optional. Only return Rides with an Id greater than or equal to the startId.
        :type start_id: int
        :keyword offset: The offset at which to return rides (only 50 rides are returned, so must use offset to get more)
        :type offset: int
        :rtype: list
        """
        # Dates should be formatted YYYY-MM-DD.  They are in local time of ride, so we are ignoring tz here.
        for datefield in ('start_date', 'end_date'):
            if datefield in kwargs and isinstance(kwargs[datefield], datetime):
                kwargs[datefield] = kwargs[datefield].strftime('%Y-%m-%d')
        
        params = dict([(_v1_attrib_name(k), v) for (k,v) in kwargs.items()])
            
        url = "http://{0}/api/v1/rides".format(self.server)
        response = self._get(url, params=params)
        return response['rides']
    
    def get_ride_efforts(self, ride_id):
        """
        Return V1 object structure for ride efforts.
        
        :param ride_id: The id of associated ride to fetch.
        """
        url = "http://{0}/api/v1/rides/{1}/efforts".format(self.server, ride_id)
        return self._get(url)['efforts']

    def get_effort(self, effort_id):
        """
        Returns V1 structure for an effort.
        
            {
                "effort": {
                    "athlete": {
                        "id": 174046, 
                        "name": "Jonathan C.", 
                        "username": "jcochrane"
                    }, 
                    "averageSpeed": 30605.56097560976, 
                    "averageWatts": 345.356, 
                    "distance": 1031.75, 
                    "elapsedTime": 123, 
                    "elevationGain": 23.4197, 
                    "id": 100336780, 
                    "maximumSpeed": 35697.888, 
                    "movingTime": 123, 
                    "ride": {
                        "id": 5266484, 
                        "name": "03/15/2012"
                    }, 
                    "segment": {
                        "id": 646144, 
                        "name": "Mount Rosslyn"
                    }, 
                    "startDate": "2012-03-16T00:23:38Z", 
                    "startDateLocal": "2012-03-15T20:23:38Z", 
                    "timeZoneOffset": -18000
                }
            }
        """
        url = "http://{0}/api/v1/efforts/{1}".format(self.server, effort_id)
        return self._get(url)['effort']

    def get_segment(self, segment_id):
        """
        Return V1 object structure for a segment.
        
        {"segment":{"climbCategory":"4",
                    "elevationGain":151.728,
                    "elevationHigh":458.206,
                    "elevationLow":304.395,
                    "distance":2378.34,
                    "name":"Panoramic to Pan Toll",
                    "id":156,"averageGrade":6.50757}
        } 
        """
        url = "http://{0}/api/v1/segments/{1}".format(self.server, segment_id)
        return self._get(url)['segment']
    
    def get_segment_efforts(self, segment_id, **kwargs):
        """
        Returns a list of matching Efforts on a Segment.
        
        :param segment_id: Required. The Id of the Segment for which to fetch efforts.
        :keyword club_id: Optional. Id of the Club for which to search for member's Efforts.
        :keyword athlete_id: Optional. Id of the Athlete for which to search for Efforts.
        :keyword athlete_name: Optional. Username of the Athlete for which to search for Rides.
        :keyword start_date: Optional. Day on which to start search for Efforts. The date should be formatted YYYY-MM-DD. The date is the local time of when the effort started.
        :type start_date: :class:`datetime.date`
        
        :keyword end_date: Optional. Day on which to end search for Efforts. The date should be formatted YYYY-MM-DD. The date is the local time of when the effort started.
        :type end_date: :class:`datetime.date`
        
        :param start_id: Optional. Only return Effforts with an Id greater than or equal to the startId.
        
        :param best:  Optional. Shows an best efforts per athlete sorted by elapsed time ascending (segment leaderboard).
        :type best: bool
        """
        # Dates should be formatted YYYY-MM-DD.  They are in local time of ride, so we are ignoring tz here.
        for datefield in ('start_date', 'end_date'):
            if datefield in kwargs and isinstance(kwargs[datefield], datetime):
                kwargs[datefield] = kwargs[datefield].strftime('%Y-%m-%d')
        
        params = dict([(_v1_attrib_name(k), v) for (k,v) in kwargs.items()])
            
        url = "http://{0}/api/v1/segments/{1}/efforts".format(self.server, segment_id)
        response = self._get(url, params=params)
        return response['efforts']
    
    
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
        