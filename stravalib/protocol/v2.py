import requests

from stravalib.protocol import BaseServerProxy, BaseModelMapper

class V2ModelMapper(BaseModelMapper):
    
    def __init__(self, units=pass):
        pass
    
    
    
class V2ServerProxy(BaseServerProxy):
    """
    
    """
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