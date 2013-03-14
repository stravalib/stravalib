
class StravaEntity(object):
    id = None
    name = None

class Athlete(StravaEntity):
    username = None
        
class Ride(StravaEntity):
    
    athlete = None # V1
    average_speed = None # V1,V2
    average_watts = None # V1
    maximum_speed = None # V1, V2
    elevation_gain = None # V1 
    
    commute = None # V1
    trainer = None # V1
    distance = None # V1, V2
    elapsed_time = None # V1, V2
    moving_time = None # V1, V2
    
    location = None # V1, V2
    start_latlon = None # V2
    end_latlon = None # V2
    start_date = None # V1, V2

    def from_v1_result(self, obj):
        r = Ride()
        r.athlete = Athlete.from_v1_ride(self, obj['athlete'])
        
        
        return r

{
    "ride": {
        "athlete": {
            "id": 182475, 
            "name": "Hans Lellelid", 
            "username": "hozn"
        }, 
        "averageSpeed": 7.692614601018676, 
        "averageWatts": 248.872, 
        "bike": {
            "id": 67822, 
            "name": "Road"
        }, 
        "commute": false, 
        "description": "", 
        "distance": 36247.6, 
        "elapsedTime": 4753, 
        "elevationGain": 770.982, 
        "id": 34813017, 
        "location": "Arlington, VA", 
        "maximumSpeed": 65232.0, 
        "movingTime": 4712, 
        "name": "Arlington Big Loop - Windy", 
        "startDate": "2012-12-30T18:50:31Z", 
        "startDateLocal": "2012-12-30T13:50:31Z", 
        "timeZoneOffset": -18000, 
        "trainer": false
    }
}
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