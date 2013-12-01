"""
Entity classes for representing the various Strava datatypes. 
"""
import abc
import logging
from datetime import datetime
from collections import namedtuple

from stravalib import exc
from stravalib import measurement
from stravalib.attributes import EntityCollection, META, SUMMARY, DETAILED, IntAttribute, \
                                 TextAttribute, BoolAttribute, FloatAttribute, EntityAttribute, \
                                 TimestampAttribute, LocationAttribute

class Entity(object):
    pass

class BaseEntity(object):
    """
    A base class for all entities in the system.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, **kwargs):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.from_dict(kwargs)
        
    def from_dict(self, d):
        """
        Populates this object from specified dict.
        
        Only defined attributes will be set; warnings will be logged for invalid attributes.
        """
        for (k,v) in d.items():
            # Only set defined attributes.
            if hasattr(self.__class__, k):
                self.log.debug("Setting attribute {0} on entity {1} with value {2}".format(k, self, v))
                setattr(self, k, v)
            else:
                self.log.warning("No such attribute {0} on entity {1}".format(k, self))
    
    @classmethod
    def deserialize(cls, v):
        """
        Creates a new object based on serialized (dict) struct. 
        """
        o = cls()
        o.from_dict(v)
        return o
    
    #def __repr__(self):
    #    return '<{0} id={id} name={name!r}>'.format(self.__class__.__name__, id=self.id, name=self.name)


class ResourceStateEntity(BaseEntity):
    """
    A base class for all entities in the system.
    """
    resource_state = IntAttribute((META,SUMMARY,DETAILED))

class IdentifiableEntity(ResourceStateEntity):
    """
    A base class for all entities in the system.
    """
    id = IntAttribute((META,SUMMARY,DETAILED))
    
class BoundEntity(IdentifiableEntity):
    """
    The base class for entities that support lazy loading additional data using a bound client.
    """
    __metaclass__ = abc.ABCMeta
            
    def __init__(self, bind_client=None, **kwargs):
        """
        Base entity initializer, which accepts a client parameter that creates a "bound" entity
        which can perform additional lazy loading of content.
        
        :param resource_state: The detail level for this entity.
        :type resource_state: int
        
        :param bind_client: The client instance to bind to this entity.
        :type bind_client: :class:`stravalib.simple.Client`
        """
        self.bind_client = bind_client
        super(BoundEntity, self).__init__(**kwargs)

    @classmethod
    def deserialize(cls, v, bind_client=None):
        """
        Creates a new object based on serialized (dict) struct. 
        """
        o = cls(bind_client=bind_client)
        o.from_dict(v)
        return o
    
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
    
    
class Club(BoundEntity):
    """
    Class to represent a club.
    
    Currently summary and detail resource states have the same attributes.
    {
      "id": 1,
      "resource_state": 2,
      "name": "Team Strava Cycling"
    }
    """

    @property
    def members(self):
        if self._members is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve members for unbound {0} entity.".format(self.__class__))
            else:
                self._members = self.bind_client.get_club_members(self.id)  
        return self._members

    @property
    def activities(self):
        if self._activities is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve activities for unbound {0} entity.".format(self.__class__))
            else:
                self._activities = self.bind_client.get_club_activities(self.id)  
        return self._activities
    
class Bike(IdentifiableEntity):
    """
    
    """
    id = TextAttribute((META,SUMMARY,DETAILED))
    name = TextAttribute((SUMMARY,DETAILED))
    distance = FloatAttribute((SUMMARY,DETAILED))
    primary = BoolAttribute((SUMMARY,DETAILED))
    
class Shoe(IdentifiableEntity):
    """
    
    """
    id = TextAttribute((META,SUMMARY,DETAILED))
    name = TextAttribute((SUMMARY,DETAILED))
    distance = FloatAttribute((SUMMARY,DETAILED))
    primary = BoolAttribute((SUMMARY,DETAILED))
    
class Athlete(BoundEntity):
    """
    Represents a Strava athlete.
    """
    firstname = TextAttribute((SUMMARY,DETAILED))
    lastname = TextAttribute((SUMMARY,DETAILED))
    profile_medium = TextAttribute((SUMMARY,DETAILED)) # URL to a 62x62 pixel profile picture
    profile = TextAttribute((SUMMARY,DETAILED)) # URL to a 124x124 pixel profile picture
    city = TextAttribute((SUMMARY,DETAILED))
    state = TextAttribute((SUMMARY,DETAILED))
    sex = TextAttribute((SUMMARY,DETAILED)) # 'M', 'F' or null
    friend = TextAttribute((SUMMARY,DETAILED)) # 'pending', 'accepted', 'blocked' or 'null' the authenticated athlete's following status of this athlete
    follower = TextAttribute((SUMMARY,DETAILED)) # 'pending', 'accepted', 'blocked' or 'null' this athlete's following status of the authenticated athlete
    preimum = BoolAttribute((SUMMARY,DETAILED)) # true/false
    
    created_at = TimestampAttribute((SUMMARY,DETAILED)) # time string
    updated_at = TimestampAttribute((SUMMARY,DETAILED)) # time string
    
    follower_count = IntAttribute((DETAILED,))
    friend_count = IntAttribute((DETAILED,))
    mutual_friend_count = IntAttribute((DETAILED,))
    date_preference = TextAttribute((DETAILED,)) # "%m/%d/%Y"
    measurement_preference = TextAttribute((DETAILED,)) # "feet" (or what "meters"?)
    
    clubs = None # Club[]
    bikes = None # Bike[]
    shoes = None # Shoe[]

    
class ActivityComment(BoundEntity):
    activity_id = IntAttribute((META,SUMMARY,DETAILED))
    text = TextAttribute((META,SUMMARY,DETAILED))
    created_at = TimestampAttribute((SUMMARY,DETAILED))
    
    athlete = None
    # 'athlete' is a summary-level representation of commenter

class Map(IdentifiableEntity):
    id = TextAttribute((SUMMARY,DETAILED))
    polyline = TextAttribute((SUMMARY,DETAILED))
    summary_polyline = TextAttribute((SUMMARY,DETAILED))

class BaseSplit(BaseEntity):
    pass
    # Consider pushing up attribs from MetricSplit and StandardSplit (challenge is in class-level specification of units)

class MetricSplit(BaseSplit):  # This is not a BaseEntity, since there is no id or resource_state ... maybe we need a simpler Base?
    """
    A metric-unit split.
    """
    
    distance = FloatAttribute(units=measurement.meters)
    elapsed_time = IntAttribute(units=measurement.seconds)
    elevation_difference = FloatAttribute(units=measurement.meters) 
    moving_time = IntAttribute(units=measurement.seconds)
    split = IntAttribute()

class StandardSplit(BaseSplit):  # This is not a BaseEntity, since there is no id or resource_state ... maybe we need a simpler Base?
    """
    A standard-unit (not metric) split.
    """
    distance = FloatAttribute(units=measurement.feet)
    elapsed_time = IntAttribute(units=measurement.seconds)
    elevation_difference = FloatAttribute(units=measurement.feet) 
    moving_time = IntAttribute(units=measurement.seconds)
    split = IntAttribute()

class Segment(BoundEntity):
    """
    """
    name = TextAttribute((SUMMARY,DETAILED))
    activity_type = TextAttribute((SUMMARY,DETAILED))
    distance = FloatAttribute((SUMMARY,DETAILED), units=measurement.meters)
    average_grade = FloatAttribute((SUMMARY,DETAILED)) # percent
    maximum_grade = FloatAttribute((SUMMARY,DETAILED)) # percent
    elevation_high = FloatAttribute((SUMMARY,DETAILED), units=measurement.meters)
    elevation_low = FloatAttribute((SUMMARY,DETAILED), units=measurement.meters)
    start_latlng = LocationAttribute((SUMMARY,DETAILED))
    end_latlng = LocationAttribute((SUMMARY,DETAILED))
    start_latitude = FloatAttribute((SUMMARY,DETAILED))
    end_latitude = FloatAttribute((SUMMARY,DETAILED))
    start_longitude = FloatAttribute((SUMMARY,DETAILED))
    end_longitude = FloatAttribute((SUMMARY,DETAILED))
    climb_category = IntAttribute((SUMMARY,DETAILED)) # 0-5, lower is harder
    city = TextAttribute((SUMMARY,DETAILED))
    state = TextAttribute((SUMMARY,DETAILED))
    private = BoolAttribute((SUMMARY,DETAILED))
    
    # detailed attribs
    created_at = TimestampAttribute((DETAILED,))
    updated_at = TimestampAttribute((DETAILED,))
    total_elevation_gain = FloatAttribute((DETAILED,), units=measurement.meters)
    map = EntityAttribute(Map, (DETAILED,))
    effort_count = IntAttribute((DETAILED,))
    athlete_count = IntAttribute((DETAILED,))
    hazardous = BoolAttribute((DETAILED,))
    pr_time = IntAttribute((DETAILED,), units=measurement.seconds)
    pr_distance = FloatAttribute((DETAILED,), units=measurement.meters)
    starred = BoolAttribute((DETAILED,))
    
    
class BaseEffort(BoundEntity):
    pass

class BestEffort(BaseEffort):
    name = TextAttribute((SUMMARY,DETAILED))
    segment = EntityAttribute(Segment, (SUMMARY,DETAILED))
    activity = EntityAttribute("Activity", (SUMMARY,DETAILED)) # How to use actual classes?
    athlete = EntityAttribute(Athlete, (SUMMARY,DETAILED))
    kom_rank = IntAttribute((SUMMARY,DETAILED))
    pr_rank = IntAttribute((SUMMARY,DETAILED))
    moving_time = IntAttribute((SUMMARY,DETAILED))
    elapsed_time = IntAttribute((SUMMARY,DETAILED))
    start_date = TimestampAttribute((SUMMARY,DETAILED))
    start_date_local = TimestampAttribute((SUMMARY,DETAILED))
    distance = IntAttribute((SUMMARY,DETAILED), units=measurement.meters)
      
class SegmentEffort(BaseEffort):
    """
    A class that can represent an effort for a segment.
    """
    start_index = IntAttribute((SUMMARY,DETAILED)) # the activity stream index of the start of this effort
    end_index = IntAttribute((SUMMARY,DETAILED)) # the activity stream index of the end of this effort
    
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
              
class Activity(BoundEntity):
    """
    
    """
    external_id = TextAttribute((SUMMARY,DETAILED))
    upload_id = TextAttribute((SUMMARY,DETAILED))
    athlete = None # META-level
    name = TextAttribute((SUMMARY,DETAILED))
    moving_time = IntAttribute((SUMMARY,DETAILED)) # seconds
    elapsed_time = IntAttribute((SUMMARY,DETAILED)) # seconds
    total_elevation_gain = FloatAttribute((SUMMARY,DETAILED)) # meters
    type = TextAttribute((SUMMARY,DETAILED))
    start_date = TimestampAttribute((SUMMARY,DETAILED))
    start_date_local = TimestampAttribute((SUMMARY,DETAILED))
    timezone = TextAttribute((SUMMARY,DETAILED))
    start_latlng = LocationAttribute((SUMMARY,DETAILED))
    end_latlng = LocationAttribute((SUMMARY,DETAILED))

    location_city = TextAttribute((SUMMARY,DETAILED)),
    location_state = TextAttribute((SUMMARY,DETAILED)),
    start_latitude = FloatAttribute((SUMMARY,DETAILED)),
    start_longitude = FloatAttribute((SUMMARY,DETAILED)),
    achievement_count = IntAttribute((SUMMARY,DETAILED)),
    kudos_count = IntAttribute((SUMMARY,DETAILED)),
    comment_count = IntAttribute((SUMMARY,DETAILED)),
    athlete_count = IntAttribute((SUMMARY,DETAILED)),
    photo_count = IntAttribute((SUMMARY,DETAILED)),
    map = EntityAttribute(Map, (SUMMARY,DETAILED))
    
    trainer = BoolAttribute((SUMMARY,DETAILED))
    commute = BoolAttribute((SUMMARY,DETAILED))
    manual = BoolAttribute((SUMMARY,DETAILED))
    flagged = BoolAttribute((SUMMARY,DETAILED))
    
    # TODO: gear?  (LazyAttribute)
    gear_id = TextAttribute((SUMMARY,DETAILED))
    
    
    average_speed = FloatAttribute((SUMMARY,DETAILED)) # meters/sec
    max_speed = FloatAttribute((SUMMARY,DETAILED)) # meters/sec
    calories = FloatAttribute((SUMMARY,DETAILED)) 
    truncated = IntAttribute((SUMMARY,DETAILED))
    has_kudoed = BoolAttribute((SUMMARY,DETAILED))
  
    segment_efforts = EntityCollection(SegmentEffort, (DETAILED,))
    splits_metric = EntityCollection(MetricSplit, (DETAILED,))
    splits_standard = EntityCollection(StandardSplit, (DETAILED,))
    best_efforts = EntityCollection(BestEffort, (DETAILED,))
    
    """
    @property
    def efforts(self):
        if self._efforts is None:
            if self.bind_client is None:
                raise exc.UnboundEntity("Unable to retrieve efforts for unbound {0} entity.".format(self.__class__))
            else:
                self._efforts = self.bind_client.get_ride_efforts(self.id)  
        return self._efforts
    """



class SegmentLeaderboard(object):
    """
    {
  "effort_count": 7037,
  "entry_count": 7037,
  "entries": [
    {
      "athlete_name": "Jim Whimpey",
      "athlete_id": 123529,
      "athlete_gender": "M",
      "average_hr": 190.519,
      "average_watts": 460.805,
      "distance": 2659.89,
      "elapsed_time": 360,
      "moving_time": 360,
      "start_date": "2013-03-29T13:49:35Z",
      "start_date_local": "2013-03-29T06:49:35Z",
      "activity_id": 46320211,
      "effort_id": 801006623,
      "rank": 1,
      "athlete_profile": "http://pics.com/227615/large.jpg"
    },
    {
      "athlete_name": "Chris Zappala",
      "athlete_id": 11673,
      "athlete_gender": "M",
      "average_hr": null,
      "average_watts": 368.288,
      "distance": 2705.77,
      "elapsed_time": 374,
      "moving_time": 374,
      "start_date": "2012-02-23T14:50:16Z",
      "start_date_local": "2012-02-23T06:50:16Z",
      "activity_id": 4431903,
      "effort_id": 83383918,
      "rank": 2,
      "athlete_profile": "http://pics.com/227615/large.jpg"
    }
  ]
}
    """
    
    
class ActivityZone(object):
    """
    {
    "score": 215,
    "distribution_buckets": [
      { "max": 115, "min": 0,   "time": 1735 },
      { "max": 152, "min": 115, "time": 5966 },
      { "max": 171, "min": 152, "time": 4077 },
      { "max": 190, "min": 171, "time": 4238 },
      { "max": -1,  "min": 190, "time": 36 }
    ],
    "type": "heartrate",
    "resource_state": 3,
    "sensor_based": true,
    "points": 119,
    "custom_zones": false,
    "max": 196
  },
  {
    "distribution_buckets": [
      { "max": 0,   "min": 0,   "time": 3043 },
      { "max": 50,  "min": 0,   "time": 999 },
      { "max": 100, "min": 50,  "time": 489 },
      { "max": 150, "min": 100, "time": 737 },
      { "max": 200, "min": 150, "time": 1299 },
      { "max": 250, "min": 200, "time": 1478 },
      { "max": 300, "min": 250, "time": 1523 },
      { "max": 350, "min": 300, "time": 2154 },
      { "max": 400, "min": 350, "time": 2226 },
      { "max": 450, "min": 400, "time": 1181 },
      { "max": -1,  "min": 450, "time": 923 }
    ],
    "type": "power",
    "resource_state": 3,
    "sensor_based": true,
    "bike_weight": 8.16466,
    "athlete_weight": 68.0389
  }
    """