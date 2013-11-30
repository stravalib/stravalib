"""
Entity classes for representing the various Strava datatypes. 
"""
import abc
import logging
from datetime import datetime
from collections import namedtuple

from stravalib import exc
from stravalib import measurement
from stravalib.attributes import Attribute, Collection, META, SUMMARY, DETAILED

class Entity(object):
    pass

class BaseEntity(object):
    """
    A base class for all entities in the system.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, **kwargs):
        self.log = logging.getLogger('{0.__module__}.{1.__name__}'.format(self.__class__))
        self.from_dict(kwargs)
        
    def from_dict(self, d):
        """
        Populates this object from specified dict.
        
        Only defined attributes will be set; warnings will be logged for invalid attributes.
        """
        for (k,v) in d.items():
            # Only set defined attributes.
            if hasattr(self.__class__, k):
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
    
    def __repr__(self):
        return '<{0} id={id} name={name!r}>'.format(self.__class__.__name__, id=self.id, name=self.name)


class ResourceStateEntity(object):
    """
    A base class for all entities in the system.
    """
    resource_state = Attribute(int, (META,SUMMARY,DETAILED))

    def __init__(self, resource_state, **kwargs):
        super(ResourceStateEntity, self).__init__(**kwargs)
        self.resource_state = resource_state

class IdentifiableEntity(ResourceStateEntity):
    """
    A base class for all entities in the system.
    """
    id = Attribute(int, (META,SUMMARY,DETAILED))
    
class BoundEntity(IdentifiableEntity):
    """
    The base class for entities that support lazy loading additional data using a bound client.
    """
    __metaclass__ = abc.ABCMeta
            
    def __init__(self, resource_state, bind_client=None, **kwargs):
        """
        Base entity initializer, which accepts a client parameter that creates a "bound" entity
        which can perform additional lazy loading of content.
        
        :param resource_state: The detail level for this entity.
        :type resource_state: int
        
        :param bind_client: The client instance to bind to this entity.
        :type bind_client: :class:`stravalib.simple.Client`
        """
        self.bind_client = bind_client
        super(BoundEntity, self).__init__(resource_state=resource_state, **kwargs)
    
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
    id = Attribute(str, (META,SUMMARY,DETAILED))
    name = Attribute(str, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED))
    primary = Attribute(bool, (SUMMARY,DETAILED))
    
class Shoe(IdentifiableEntity):
    """
    
    """
    id = Attribute(str, (META,SUMMARY,DETAILED))
    name = Attribute(str, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED))
    primary = Attribute(bool, (SUMMARY,DETAILED))
    
class Athlete(BoundEntity):
    """
    Represents a Strava athlete.
    """
    firstname = Attribute(str, (SUMMARY,DETAILED))
    lastname = Attribute(str, (SUMMARY,DETAILED))
    profile_medium = Attribute(str, (SUMMARY,DETAILED)) # URL to a 62x62 pixel profile picture
    profile = Attribute(str, (SUMMARY,DETAILED)) # URL to a 124x124 pixel profile picture
    city = Attribute(str, (SUMMARY,DETAILED))
    state = Attribute(str, (SUMMARY,DETAILED))
    sex = Attribute(str, (SUMMARY,DETAILED)) # 'M', 'F' or null
    friend = Attribute(str, (SUMMARY,DETAILED)) # 'pending', 'accepted', 'blocked' or 'null' the authenticated athlete's following status of this athlete
    follower = Attribute(str, (SUMMARY,DETAILED)) # 'pending', 'accepted', 'blocked' or 'null' this athlete's following status of the authenticated athlete
    preimum = Attribute(bool, (SUMMARY,DETAILED)) # true/false
    
    created_at = Attribute(datetime, (SUMMARY,DETAILED)) # time string
    updated_at = Attribute(datetime, (SUMMARY,DETAILED)) # time string
    
    follower_count = Attribute(int, (DETAILED,))
    friend_count = Attribute(int, (DETAILED,))
    mutual_friend_count = Attribute(int, (DETAILED,))
    date_preference = Attribute(str, (DETAILED,)) # "%m/%d/%Y"
    measurement_preference = Attribute(str, (DETAILED,)) # "feet" (or what "meters"?)
    
    clubs = None # Club[]
    bikes = None # Bike[]
    shoes = None # Shoe[]

    
class ActivityComment(BoundEntity):
    activity_id = Attribute(int, (META,SUMMARY,DETAILED))
    text = Attribute(str, (META,SUMMARY,DETAILED))
    created_at = Attribute(datetime, (SUMMARY,DETAILED))
    
    athlete = None
    # 'athlete' is a summary-level representation of commenter

LatLon = namedtuple('LatLon', ['lat', 'lon'])

class Map(IdentifiableEntity):
    id = Attribute(str, (SUMMARY,DETAILED))
    polyline = Attribute(str, (SUMMARY,DETAILED))
    summary_polyline = Attribute(str, (SUMMARY,DETAILED))

class BaseSplit(BaseEntity):
    pass
    # Consider pushing up attribs from MetricSplit and StandardSplit (challenge is in class-level specification of units)

class MetricSplit(BaseSplit):  # This is not a BaseEntity, since there is no id or resource_state ... maybe we need a simpler Base?
    """
    A metric-unit split.
    """
    
    distance = Attribute(float, units=measurement.meters)
    elapsed_time = Attribute(int, unilts=measurement.seconds)
    elevation_difference = Attribute(float, units=measurement.meters) 
    moving_time = Attribute(int, units=measurement.seconds)
    split = Attribute(int)

class StandardSplit(BaseSplit):  # This is not a BaseEntity, since there is no id or resource_state ... maybe we need a simpler Base?
    """
    A standard-unit (not metric) split.
    """
    distance = Attribute(float, units=measurement.feet)
    elapsed_time = Attribute(int, unilts=measurement.seconds)
    elevation_difference = Attribute(float, units=measurement.feet) 
    moving_time = Attribute(int, units=measurement.seconds)
    split = Attribute(int)

class Segment(BoundEntity):
    """
    """
    name = Attribute(str, (SUMMARY,DETAILED))
    activity_type = Attribute(str, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED), units=measurement.meters)
    average_grade = Attribute(float, (SUMMARY,DETAILED)) # percent
    maximum_grade = Attribute(float, (SUMMARY,DETAILED)) # percent
    elevation_high = Attribute(float, (SUMMARY,DETAILED), units=measurement.meters)
    elevation_low = Attribute(float, (SUMMARY,DETAILED), units=measurement.meters)
    start_latlng = Attribute(LatLon, (SUMMARY,DETAILED))
    end_latlng = Attribute(LatLon, (SUMMARY,DETAILED))
    start_latitude = Attribute(float, (SUMMARY,DETAILED))
    end_latitude = Attribute(float, (SUMMARY,DETAILED))
    start_longitude = Attribute(float, (SUMMARY,DETAILED))
    end_longitude = Attribute(float, (SUMMARY,DETAILED))
    climb_category = Attribute(int, (SUMMARY,DETAILED)) # 0-5, lower is harder
    city = Attribute(str, (SUMMARY,DETAILED))
    state = Attribute(str, (SUMMARY,DETAILED))
    private = Attribute(bool, (SUMMARY,DETAILED))
    
    # detailed attribs
    created_at = Attribute(datetime, (DETAILED,))
    updated_at = Attribute(datetime, (DETAILED,))
    total_elevation_gain = Attribute(float, (DETAILED,), units=measurement.meters)
    map = Attribute(Map, (DETAILED,))
    effort_count = Attribute(int, (DETAILED,))
    athlete_count = Attribute(int, (DETAILED,))
    hazardous = Attribute(bool, (DETAILED,))
    pr_time = Attribute(int, (DETAILED,), units=measurement.seconds)
    pr_distance = Attribute(float, (DETAILED,), units=measurement.meters)
    starred = Attribute(bool, (DETAILED,))
    
    
class BaseEffort(BoundEntity):
    pass

class BestEffort(BaseEffort):
    name = Attribute(str, (SUMMARY,DETAILED))
    segment = Attribute(Segment, (SUMMARY,DETAILED))
    activity = Attribute("Activity", (SUMMARY,DETAILED)) # How to use actual classes?
    athlete = Attribute(Athlete, (SUMMARY,DETAILED))
    kom_rank = Attribute(int, (SUMMARY,DETAILED))
    pr_rank = Attribute(int, (SUMMARY,DETAILED))
    moving_time = Attribute(int, (SUMMARY,DETAILED))
    elapsed_time = Attribute(int, (SUMMARY,DETAILED))
    start_date = Attribute(datetime, (SUMMARY,DETAILED))
    start_date_local = Attribute(datetime, (SUMMARY,DETAILED))
    distance = Attribute(int, (SUMMARY,DETAILED), units=measurement.meters)
      
class SegmentEffort(BaseEffort):
    """
    A class that can represent an effort for a segment.
    """
    start_index = Attribute(int, (SUMMARY,DETAILED)) # the activity stream index of the start of this effort
    end_index = Attribute(int, (SUMMARY,DETAILED)) # the activity stream index of the end of this effort
    
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
    external_id = Attribute(str, (SUMMARY,DETAILED))
    upload_id = Attribute(str, (SUMMARY,DETAILED))
    athlete = None # META-level
    name = Attribute(str, (SUMMARY,DETAILED))
    moving_time = Attribute(int, (SUMMARY,DETAILED)) # seconds
    elapsed_time = Attribute(int, (SUMMARY,DETAILED)) # seconds
    total_elevation_gain = Attribute(float, (SUMMARY,DETAILED)) # meters
    type = Attribute(str, (SUMMARY,DETAILED))
    start_date = Attribute(datetime, (SUMMARY,DETAILED))
    start_date_local = Attribute(datetime, (SUMMARY,DETAILED))
    timezone = Attribute(str, (SUMMARY,DETAILED))
    start_latlng = Attribute(LatLon, (SUMMARY,DETAILED))
    end_latlng = Attribute(LatLon, (SUMMARY,DETAILED))

    location_city = Attribute(str, (SUMMARY,DETAILED)),
    location_state = Attribute(str, (SUMMARY,DETAILED)),
    start_latitude = Attribute(float, (SUMMARY,DETAILED)),
    start_longitude = Attribute(float, (SUMMARY,DETAILED)),
    achievement_count = Attribute(int, (SUMMARY,DETAILED)),
    kudos_count = Attribute(int, (SUMMARY,DETAILED)),
    comment_count = Attribute(int, (SUMMARY,DETAILED)),
    athlete_count = Attribute(int, (SUMMARY,DETAILED)),
    photo_count = Attribute(int, (SUMMARY,DETAILED)),
    map = Attribute(Map, (SUMMARY,DETAILED))
    
    trainer = Attribute(bool, (SUMMARY,DETAILED))
    commute = Attribute(bool, (SUMMARY,DETAILED))
    manual = Attribute(bool, (SUMMARY,DETAILED))
    flagged = Attribute(bool, (SUMMARY,DETAILED))
    
    # TODO: gear?  (LazyAttribute)
    gear_id = Attribute(str, (SUMMARY,DETAILED))
    
    
    average_speed = Attribute(float, (SUMMARY,DETAILED)) # meters/sec
    max_speed = Attribute(float, (SUMMARY,DETAILED)) # meters/sec
    calories = Attribute(float, (SUMMARY,DETAILED)) 
    truncated = Attribute(int, (SUMMARY,DETAILED))
    has_kudoed = Attribute(bool, (SUMMARY,DETAILED))
  
    segment_efforts = Collection(SegmentEffort, (DETAILED,))
    splits_metric = Collection(MetricSplit, (DETAILED,))
    splits_standard = Collection(StandardSplit, (DETAILED,))
    best_efforts = Collection(BestEffort, (DETAILED,))
    
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