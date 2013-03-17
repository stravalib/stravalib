import functools
import logging
import collections
from datetime import datetime, timedelta

from stravalib.protocol import BaseServerProxy, BaseModelMapper
from stravalib.model import Ride, Athlete, Club
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
    
    def populate_athlete(self, athlete_model, athlete_struct):
        """
        Populates a :class:`stravalib.model.Athlete` model object with data from the V1 struct
        that is returned with ride details.
        
        :param athlete_model: The athlete model to fill.
        :type athlete_model: :class:`stravalib.model.Athlete`
        :param athlete_struct: The athlete struct from V1 ride response object.
        :type athlete_struct: dict
        """
        athlete_model.id = athlete_struct['id']
        athlete_model.name = athlete_struct['name']
        # Often we only have partial athlete structure (e.g. when returning club members, etc.)
        athlete_model.username = athlete_struct.get('username')
    
    def populate_ride_minimal(self, ride_model, ride_struct):
        """
        Populates a :class:`stravalib.model.Ride` model object with data from minimal structures returned 
        from (e.g.) ride index method.
        
        :param ride_model: The model object to fill.
        :type ride_model: :class:`stravalib.model.Ride`
        :param ride_struct: The raw ride V1 response structure.
        :type ride_struct: dict
        """
        ride_model.id = ride_struct['id']
        ride_model.name = ride_struct['name']
        
    def populate_ride(self, ride_model, ride_struct):
        """
        Populates a :class:`stravalib.model.Ride` model object with data from the V1 structure.
        
        Note that not all of the model properties will have been set by this method (some are
        only available from V2 structure).
        
        :param ride_model: The model object to fill.
        :type ride_model: :class:`stravalib.model.Ride`
        :param ride_struct: The raw ride V1 response structure.
        :type ride_struct: dict
        """
        self.populate_ride_minimal(ride_model, ride_struct)
        
        athlete_struct = ride_struct['athlete']
        athlete = Athlete()
        self.populate_athlete(athlete_model=athlete, athlete_struct=athlete_struct)
        ride_model.athlete = athlete
        
        ride_model.average_speed = self._convert_speed(ride_struct['averageSpeed'])
        ride_model.average_watts = ride_struct['averageWatts']
        ride_model.maximum_speed = self._convert_speed(measurement.kph(ride_struct['maximumSpeed'] / 1000.0)) # Not sure why this is in meters per *hour* ... !?
        ride_model.elevation_gain = self._convert_elevation(ride_struct['elevationGain'])
        ride_model.commute = ride_struct['commute']
        ride_model.trainer = ride_struct['trainer']
        ride_model.distance = self._convert_distance(ride_struct['distance'])
        ride_model.elapsed_time = timedelta(seconds=ride_struct['elapsedTime'])
        ride_model.moving_time = timedelta(seconds=ride_struct['movingTime'])
        ride_model.location = ride_struct['location']
        ride_model.start_date = self._parse_datetime(ride_struct['startDateLocal'], ride_struct['timeZoneOffset'])
        
    
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
        
        
class V1ServerProxy(BaseServerProxy):
    """
    A client library implement V1 of the Strava API.
    """
    
    # http://www.strava.com/api/v1/athletes/:athlete_id/bikes/:id
    # {"bike": {"name":"Surly Crosscheck","default_bike":false,"athlete_id":21,"notes":"Single speed commuter bike","weight":12.7006,"id":1371,"frame_type":2,"retired":0}}
    # {"bike": {"name":"Storck Absolutist","default_bike":false,"athlete_id":21,"notes":"","weight":7.71107,"id":21,"frame_type":3,"retired":0}},{"bike": {"name":"Turner Flux","default_bike":false,"athlete_id":21,"notes":"","weight":12.7006,"id":22,"frame_type":1,"retired":0}},{"bike": {"name":"Rock Lobster","default_bike":false,"athlete_id":21,"notes":"","weight":8.61825,"id":41,"frame_type":2,"retired":0}},{"bike": {"name":"Surly Crosscheck","default_bike":false,"athlete_id":21,"notes":"Single speed commuter bike","weight":12.7006,"id":1371,"frame_type":2,"retired":0}}
    
    
    def get_club(self, club_id):
        """
        Return V1 object structure for club
        
        {"club":{"description":"Mission Cycling is devoted to the enjoyment of one of the world's purest, most classic sporting endeavors: Cycling. Our aim is simple: to enjoy the unique challenges and rewards offered by experiencing our unique countryside from the saddle of a bike.",
          "name":"Mission Cycling",
          "location":"San Francisco, CA",
          "club_id":15}
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
    
    def get_ride_efforts(self, ride_id):
        """
        Return V1 object structure for ride efforts.
        
        :param ride_id: The id of associated ride to fetch.
        """
        url = "http://{0}/api/v1/rides/{1}/efforts".format(self.server, ride_id)
        return self._get(url)['efforts']
        
    def list_rides(self, **kwargs):
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
    

class RideIterator(object):
    """
    Iterates over rides for specified criteria, fetching in 50-ride chunks from the 
    server.
    
    Strava API only returns 50 rides at a time, so this is a mechanism to abstract over
    that limitation. 
    """
    def __init__(self, v1client, limit=None, **kwargs):
        """
        :param v1client: The V1 API client.
        :type v1client: :class:`stravalib.protocol.v1.V1ServerProxy`
        
        :param limit: The maximum number of rides to return.
        :type limit: int
        
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
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.limit = limit
        
        self.apifunc = functools.partial(v1client.list_rides, **kwargs)
        
        self._counter = 0
        self._ride_buffer = None
        self._offset = 0
        self._all_rides_fetched = False
    
    def _fill_buffer(self):
        """
        Fills the internal size-50 buffer from Strava API.
        """
        # If we cannot fetch anymore from the server then we're done here.
        if self._all_rides_fetched:
            raise StopIteration
        
        self._ride_buffer = collections.deque(self.apifunc(offset=self._offset))
        self.log.debug("Requested rides {0} - {1} (got: {2})".format(self._offset,
                                                                     self._offset + 50,
                                                                     len(self._ride_buffer)))
        if len(self._ride_buffer) < 50:
            self._all_rides_fetched = True
            
        self._offset += 50

    def __iter__(self):
        return self
    
    def next(self):
        if self.limit and self._counter >= self.limit:
            raise StopIteration
        if not self._ride_buffer:
            self._fill_buffer()
        try:
            result = self._ride_buffer.popleft()
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
        