"""
Providing a simplified, protocol-version-abstracting interface to Strava web services. 
"""
import functools

from stravalib import model
from stravalib.protocol import v1, v2, scrape
from stravalib.measurement import IMPERIAL, METRIC

class Client(object):
    """
    Main client class for interacting with the Strava backends.
    
    This class abstracts interactions with Strava's various protocols (REST v1 & v2,
    the main website) to provide a simple and full-featured API.
    """
    
    def __init__(self, units=IMPERIAL):
        """
        
        :param units: Whether to use imperial or metric units (value must be 'imperial' or 'metric', 
                      also provided by module-level constants)
        :type units: str
        """
        self.v1mapper = v1.V1ModelMapper(units=units)
        self.v1client = v1.V1ServerProxy()
        
        self.v2mapper = v2.V2ModelMapper(units=units)
        self.v2client = v2.V2ServerProxy()
        
        
    def get_ride(self, ride_id):
        """
        :rtype: :class:`stravalib.model.Ride`
        """
        v1ride = self.v1client.get_ride(ride_id)
        v2ride = self.v2client.get_ride(ride_id)
        
        ride = model.Ride()
        self.v1mapper.populate_ride(ride, v1ride)
        self.v2mapper.populate_ride(ride, v2ride)
        return ride
        
    # Alias with assumption that one of these will be deprecated in the future.
    get_activity = get_ride 
    
    def get_club(self, club_id):
        """
        :rtype: :class:`stravalib.model.Club`
        """
        v1club = self.v1client.get_club(club_id)
        
        get_members = functools.partial(self.get_club_members, club_id)
        
        club = model.Club(get_members=get_members)
        
        self.v1mapper.populate_ride(ride, v1ride)
        self.v2mapper.populate_ride(ride, v2ride)
        return ride
    
    def get_club_members(self, club_id):
        pass