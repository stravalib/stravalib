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
    start_latlng = None # V2
    end_latlng = None # V2
    
    _efforts = None
    
    @property
    def efforts(self):
        if self._efforts is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve efforts for unbound {0} entity.".format(self.__class__))
            else:
                self._efforts = self.bind_client.get_ride_efforts(self.id)  
        return self._efforts
    
    
class Segment(StravaEntity):
    distance = None
    elevation_gain = None
    elevation_high = None
    elevation_low = None
    average_grade = None
    climb_category = None
    
    # API V2 provides latlng info, but apparently must get to it via effort 
    start_latlng = None
    end_latlng = None
    
    _best_efforts = None
    
    @property
    def leaderboard(self):
        """
        Returns the segment leaderboard.
        """
        # (there is no paging in the leaderboard, so exposing as a property seems reasonable)
        if self._best_efforts is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve efforts for unbound {0} entity.".format(self.__class__))
            else:
                self._best_efforts = self.bind_client.get_segment_efforts(self.id, best=True)  
        return self._best_efforts

class Effort(RideEffortBase):
    """
    A generic class that can represent an effort for a ride or a segment.
    """
    _segment_id = None
    _activity_id = None
    _segment = None
    _ride = None
    
    @property
    def segment_id(self):
        if self._segment_id is not None:
            return self._segment_id
        elif self._segment is not None:
            return self._segment.id
        else:
            return None
        
    @segment_id.setter
    def segment_id(self, v):
        self._segment_id = v
        
    @property
    def segment(self):
        if self._segment is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve segment for unbound {0} entity.".format(self.__class__))
            elif self.segment_id is None:
                raise RuntimeError("Cannot lookup segment; no segment_id has been set for this effort.")
            else:
                self._segment = self.bind_client.get_segment(self.segment_id)  
        return self._segment
    
    @segment.setter
    def segment(self, value):
        self._segment = value

    @property
    def activity_id(self):
        if self._activity_id is not None:
            return self._activity_id
        elif self._ride is not None:
            return self._ride.id
        else:
            return None
        
    @activity_id.setter
    def activity_id(self, v):
        self._activity_id = v
        
    @property
    def activity(self):
        if self._ride is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve activity for unbound {0} entity.".format(self.__class__))
            elif self.activity_id is None:
                raise RuntimeError("Cannot lookup activity; no activity_id has been set for this effort.")
            else:
                self._ride = self.bind_client.get_ride(self.activity_id)
        return self._ride
    
    @activity.setter
    def activity(self, v):
        self._ride = v