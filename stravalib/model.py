"""
Entity classes for representing the various Strava datatypes. 
"""
import abc

from stravalib import exc

class StravaEntity(object):
    """
    Base class holds properties/functionality that Strava entities have in common.
    """
    __metaclass__ = abc.ABCMeta
    
    id = None
    name = None
            
    def __init__(self, bind_client=None):
        """
        Base entity initializer, which accepts a client parameter that creates a "bound" entity
        which can perform additional lazy loading of content.
        
        :param bind_client: The client instance to bind to this entity.
        :type bind_client: :class:`stravalib.simple.Client`
        """
        self.bind_client = bind_client
    
    def hydrate(self):
        """
        Fill this object with data from the bound client.
        
        This default implementation assumes things about the names of methods in the client, so
        may need to be overridden by subclasses.
        """
        if not self.bind_client:
            raise exc.UnboundEntity("Cannot set entity attributes for unbound entity.")
        assumed_method_name = '_populate_{0}'.format(self.__class__.__name__.lower())
        method = getattr(self.bind_client, assumed_method_name)
        method(self.id, self)
    
    def __repr__(self):
        return '<{0} id={id} name={name!r}>'.format(self.__class__.__name__, id=self.id, name=self.name)
     
class Club(StravaEntity):
    """
    Class to represent Strava clubs/teams.
    """
    description = None
    location = None
    _members = None
    
    @property
    def members(self):
        if self._members is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve members for unbound {0} entity.".format(self.__class__))
            else:
                self._members = self.bind_client.get_club_members(self.id)  
        return self._members
    
class Athlete(StravaEntity):
    """
    Represents a Strava athlete.
    """
    username = None

class RideEffortBase(StravaEntity):
    """
    Abstract class that holds the attributes that Rides and Efforts share in common.
    """
    athlete = None
    start_date = None
    
    average_speed = None
    maximum_speed = None
    average_watts = None
    
    distance = None
    elevation_gain = None 
    
    elapsed_time = None
    moving_time = None
    
class Ride(RideEffortBase):
    """
    Represents a Strava activity.
    """
    commute = None # V1
    trainer = None # V1
    
    location = None # V1, V2
    start_latlon = None # V2
    end_latlon = None # V2
    
    _efforts = None
    
    @property
    def efforts(self):
        if self._efforts is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve efforts for unbound {0} entity.".format(self.__class__))
            else:
                self._efforts = self.bind_client.get_ride_efforts(self.id)  
        return self._efforts
    

class RideEffort(RideEffortBase):
    """
    Represents an effort on a ride.
    """
    _segment = None

    @property
    def segment(self):
        if self._segment is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve segment for unbound {0} entity.".format(self.__class__))
            else:
                self._segment = self.bind_client.get_segment(self.segment_id)  
        return self._segment
    
    @segment.setter
    def segment(self, value):
        self._segment = value
    
class Segment(StravaEntity):
    distance = None
    elevation_gain = None
    elevation_high = None
    elevation_low = None
    average_grade = None
    climb_category = None
    
    # API V2 provides latlon info, but apparently must get to it via effort 
    start_latlon = None
    end_latlon = None
    
    _best_efforts = None
    
    @property
    def leaderboard(self):
        if self._best_efforts is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve efforts for unbound {0} entity.".format(self.__class__))
            else:
                self._best_efforts = self.bind_client.get_segment_efforts(self.id, best=True)  
        return self._best_efforts

class SegmentEffort(StravaEntity):
    """
    Represents a specific effort on a segment.  This is different from a RideEffort in that
    it includes info about the ride and athlete.
    
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
    """
    _effort = None
    _ride = None