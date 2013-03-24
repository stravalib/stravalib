import collections

import requests

from stravalib.protocol import BaseServerProxy, BaseModelMapper

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

LatLon = collections.namedtuple('LatLon', ['lat', 'lon'])

class V2ModelMapper(BaseModelMapper):
    
    def populate_ride(self, ride_model, ride_struct):
        """
        Populates the lat/lon attributes on the ride model from the V2 ride struct.
        """
        ride_model.start_latlon = LatLon(ride_struct['start_latlon'])
        ride_model.end_latlon = LatLon(ride_struct['end_latlon'])
    
    def populate_segment(self, segment_model, segment_struct):
        """
        Populates the lat/lon attributes on the model from the V2 segment struct (obtained from getting v2 ride efforts).
        
            "segment": {
                "avg_grade": 3.70959, 
                "climb_category": 0, 
                "elev_difference": 2.8000000000000114, 
                "end_latlng": [
                    38.88408467173576, 
                    -77.15276716277003
                ], 
                "id": 1030752, 
                "name": "Brandymore Castle Hill Climb East Ascent", 
                "start_latlng": [
                    38.88401275500655, 
                    -77.15194523334503
                ]
            }
        """
        segment_model.start_latlon = LatLon(segment_struct['start_latlon'])
        segment_model.end_latlon = LatLon(segment_struct['end_latlon'])
        
#    def populate_athlete(self, athlete_model, athlete_struct):
#        pass
    
class V2ServerProxy(BaseServerProxy):
    """
    A client library implementing V2 of the Strava API.
    """
    mapper_class = V2ModelMapper
    auth_token = None
    
    @property
    def authenticated(self):
        return self.token is not None
    
    def authenticate(self, email, password):
        """
        """
        url = 'https://{server}/api/v2/authentication/login'.format(server=self.server)
        rawresp = requests.post(url, params=dict(email=email, password=password))
        resp = self._parse_response(rawresp)
        self.auth_token = resp['token']
        
    def get_ride(self, ride_id):
        """
        Gets the V2 structure for a ride.
        
             {
                "id": "34813017", 
                "ride": {
                    "average_speed": 7.692614601018676, 
                    "distance": 36247.6, 
                    "elapsed_time": 4753, 
                    "elevation_gain": 770.982, 
                    "end_latlng": [
                        38.88380078, 
                        -77.14209122
                    ], 
                    "id": 34813017, 
                    "location": "Arlington, VA", 
                    "moving_time": 4712, 
                    "name": "Arlington Big Loop - Windy", 
                    "start_date_local": "2012-12-30T13:50:31Z", 
                    "start_latlng": [
                        38.88286368, 
                        -77.14193397
                    ]
                }, 
                "version": "1356898729"
            }
            
        :param id: The id of the ride.
        """
        url = "http://{server}/api/v2/rides/{id}".format(server=self.server, id=int(ride_id))
        return self._get(url)['ride']
    
    
    def get_ride_efforts(self, ride_id):
        """
        Return V2 object structure for ride efforts.
        
        Each effort:
        {
            "effort": {
                "average_speed": 3.8800000000000003, 
                "distance": 69.84, 
                "elapsed_time": 18, 
                "id": 571734780, 
                "moving_time": 18, 
                "start_date_local": "2012-12-30T13:53:36Z"
            }, 
            "segment": {
                "avg_grade": 3.70959, 
                "climb_category": 0, 
                "elev_difference": 2.8000000000000114, 
                "end_latlng": [
                    38.88408467173576, 
                    -77.15276716277003
                ], 
                "id": 1030752, 
                "name": "Brandymore Castle Hill Climb East Ascent", 
                "start_latlng": [
                    38.88401275500655, 
                    -77.15194523334503
                ]
            }
        }
            
        :param ride_id: The id of associated ride to fetch.
        """
        url = "http://{0}/api/v1/rides/{1}/efforts".format(self.server, ride_id)
        return self._get(url)['efforts']
    
    
    def upload(self):
        raise NotImplementedError()