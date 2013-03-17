"""
Entity classes for representing the various Strava datatypes. 
"""
from stravalib import exc

class StravaEntity(object):
    """
    Base class holds properties/functionality that Strava entities have in common.
    """
    id = None
    name = None
    
    def __init__(self, entity_pouplator=None):
        """
        Base entity initializer, which can take an entity_populator callable
        that will set the values of this entity.
        """
        self._entity_pouplator = entity_pouplator
        
    def hydrate(self):
        """
        Fill this object with data from the specified entity filler. 
        """
        if not self._entity_pouplator:
            raise exc.UnboundEntity("Cannot set entity attributes for unbound entity.")
        self._entity_pouplator(self)
    
    def __repr__(self):
        return '<{0} id={id} name={name!r}>'.format(self.__class__.__name__, id=self.id, name=self.name)
     
class Club(StravaEntity):
    """
    Class to represent Strava clubs/teams.
    """
    description = None
    location = None
    
    def __init__(self, members_fetcher=None, **kwargs):
        super(Club, self).__init__(**kwargs)
        self._members_fetcher = members_fetcher
        self._members = None
    
    @property
    def members(self):
        if self._members is None:
            if self._members_fetcher is None:
                raise exc.UnboundEntity("Unable to retrieve members for unbound {0} entity.".format(self.__class__))
            else:
                self._members = self._members_fetcher()  
        return self._members
    
class Athlete(StravaEntity):
    """
    Represents a Strava athlete.
    """
    username = None
        
class Ride(StravaEntity):
    """
    Represents a Strava activity.
    """
            
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
    
# The Strava API is somewhat tailored to cycling, but we will 
# alias Activity in the expectation that the v3 API will provide a more
# generic interface.
Activity = Ride

class Effort(StravaEntity):
    pass


class Segment(StravaEntity):
    pass
