"""
Entity classes for representing the various Strava datatypes. 
"""
import abc
import logging
from collections import Sequence

from stravalib import exc
from stravalib import unithelper as uh

from stravalib.attributes import (META, SUMMARY, DETAILED, Attribute, 
                                  TimestampAttribute, LocationAttribute, EntityCollection, 
                                  EntityAttribute, TimeIntervalAttribute, TimezoneAttribute,
                                  DateAttribute)

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
                #self.log.debug("Setting attribute `{0}` [{1}] on entity {2} with value {3!r}".format(k, getattr(self.__class__, k).__class__.__name__, self, v))
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
        attrs = []
        if hasattr(self.__class__, 'id'):
            attrs.append('id={0}'.format(self.id))
        if hasattr(self.__class__, 'name'):
            attrs.append('name={0!r}'.format(self.name))
        if hasattr(self.__class__, 'resource_state'):
            attrs.append('resource_state={0}'.format(self.resource_state))
            
        return '<{0} {1}>'.format(self.__class__.__name__, ' '.join(attrs))

class ResourceStateEntity(BaseEntity):
    """
    A base class for all entities in the system.
    """
    resource_state = Attribute(int, (META,SUMMARY,DETAILED))
    
class IdentifiableEntity(ResourceStateEntity):
    """
    A base class for all entities in the system.
    """
    id = Attribute(int, (META,SUMMARY,DETAILED))
    
class BoundEntity(BaseEntity):
    """
    The base class for entities that support lazy loading additional data using a bound client.
    """
    
    bind_client = None
    
    def __init__(self, bind_client=None, **kwargs):
        """
        Base entity initializer, which accepts a client parameter that creates a "bound" entity
        which can perform additional lazy loading of content.
        
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
        if v is None:
            return None
        o = cls(bind_client=bind_client)
        o.from_dict(v)
        return o

    
    def assert_bind_client(self):
        if self.bind_client is None:
            raise exc.UnboundEntity("Unable to fetch objects for unbound {0} entity.".format(self.__class__))

class LoadableEntity(BoundEntity, IdentifiableEntity):
        
    def expand(self):
        """
        Expand this object with data from the bound client.
        
        This default implementation assumes things about the names of methods in the client, so
        may need to be overridden by subclasses.
        """
        raise NotImplementedError() # This is a little harder now that we don't have _populate_* methods.
        
        if not self.bind_client:
            raise exc.UnboundEntity("Cannot set entity attributes for unbound entity.")
        raise NotImplementedError()
        # TODO: Decided whether we want to keep this
        assumed_method_name = '_populate_{0}'.format(self.__class__.__name__.lower())
        method = getattr(self.bind_client, assumed_method_name)
        method(self.id, self)

class Club(LoadableEntity):
    """
    Class to represent a club.
    
    Currently summary and detail resource states have the same attributes.
    """
    name = Attribute(unicode, (SUMMARY,DETAILED))
    
    @property
    def members(self):
        if self._members is None:
            self.assert_bind_client()
            self._members = self.bind_client.get_club_members(self.id)  
        return self._members

    @property
    def activities(self):
        if self._activities is None:
            self.assert_bind_client()
            self._activities = self.bind_client.get_club_activities(self.id)  
        return self._activities

class Gear(IdentifiableEntity):
    """
    """
    id = Attribute(unicode, (META,SUMMARY,DETAILED))
    name = Attribute(unicode, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    primary = Attribute(bool, (SUMMARY,DETAILED))
    brand_name = Attribute(unicode, (DETAILED,))
    model_name = Attribute(unicode, (DETAILED,))
    description = Attribute(unicode, (DETAILED,))
    
    @classmethod
    def deserialize(cls, v):
        """
        Creates a new object based on serialized (dict) struct. 
        """
        if v is None:
            return None
        if cls == Gear and v.get('resource_state') == 3:            
            if 'frame_type' in v:
                o = Bike()
            else:
                o = Shoe()
        else:
            o = cls()
        o.from_dict(v)
        return o
    
class Bike(Gear):
    """    
    """
    frame_type = Attribute(int, (DETAILED,))
    
class Shoe(Gear):
    """
    """
    
class ActivityTotals(BaseEntity):
    """
    Represent ytd/recent/all run/ride totals. 
    """
    achievement_count = Attribute(int)
    count = Attribute(int)
    distance = Attribute(float, units=uh.meters)
    elapsed_time = TimeIntervalAttribute()
    elevation_gain = Attribute(float, units=uh.meters)
    moving_time = TimeIntervalAttribute()
    
class Athlete(LoadableEntity):
    """
    Represents a Strava athlete.
    """
    firstname = Attribute(unicode, (SUMMARY,DETAILED))
    lastname = Attribute(unicode, (SUMMARY,DETAILED))
    profile_medium = Attribute(unicode, (SUMMARY,DETAILED)) # URL to a 62x62 pixel profile picture
    profile = Attribute(unicode, (SUMMARY,DETAILED)) # URL to a 124x124 pixel profile picture
    city = Attribute(unicode, (SUMMARY,DETAILED))
    state = Attribute(unicode, (SUMMARY,DETAILED))
    sex = Attribute(unicode, (SUMMARY,DETAILED)) # 'M', 'F' or null
    friend = Attribute(unicode, (SUMMARY,DETAILED)) # 'pending', 'accepted', 'blocked' or 'null' the authenticated athlete's following status of this athlete
    follower = Attribute(unicode, (SUMMARY,DETAILED)) # 'pending', 'accepted', 'blocked' or 'null' this athlete's following status of the authenticated athlete
    preimum = Attribute(bool, (SUMMARY,DETAILED)) # true/false
    
    created_at = TimestampAttribute((SUMMARY,DETAILED)) # time string
    updated_at = TimestampAttribute((SUMMARY,DETAILED)) # time string
    
    approve_followers = Attribute(bool, (SUMMARY,DETAILED))
    
    follower_count = Attribute(int, (DETAILED,))
    friend_count = Attribute(int, (DETAILED,))
    mutual_friend_count = Attribute(int, (DETAILED,))
    date_preference = Attribute(unicode, (DETAILED,)) # "%m/%d/%Y"
    measurement_preference = Attribute(unicode, (DETAILED,)) # "feet" (or what "meters"?)
    premium = Attribute(bool, (DETAILED,))
    email = Attribute(unicode, (DETAILED,))
    
    clubs = EntityCollection(Club, (DETAILED,))
    bikes = EntityCollection(Bike, (DETAILED,))
    shoes = EntityCollection(Shoe, (DETAILED,))

    # Some undocumented summary & detailed  attributes
    ytd_run_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))
    recent_run_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))
    all_run_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))
    
    ytd_ride_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))
    recent_ride_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))
    all_ride_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))
    
    super_user = Attribute(bool, (SUMMARY,DETAILED))
    biggest_ride_distance = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    biggest_climb_elevation_gain = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    
    email_language = Attribute(unicode, (SUMMARY,DETAILED)) #: The user's preferred lang/locale (e.g. en-US)     
    
    # A bunch more undocumented detailed-resolution attribs
    weight = Attribute(float, (DETAILED,), units=uh.kg)
    max_heartrate = Attribute(float, (DETAILED,))
    
    username = Attribute(unicode, (DETAILED,))
    description = Attribute(unicode, (DETAILED,))
    instagram_username = Attribute(unicode, (DETAILED,))
    
    offer_in_app_payment = Attribute(bool, (DETAILED,))
    global_privacy = Attribute(bool, (DETAILED,))
    receive_newsletter = Attribute(bool, (DETAILED,))
    email_kom_lost = Attribute(bool, (DETAILED,))
    dateofbirth = DateAttribute((DETAILED,))
    facebook_sharing_enabled = Attribute(bool, (DETAILED,))
    ftp = Attribute(unicode, (DETAILED,))  # What is this?
    profile_original = Attribute(unicode, (DETAILED,))
    premium_expiration_date = Attribute(int, (DETAILED,)) #: Unix epoch
    email_send_follower_notices = Attribute(bool, (DETAILED,))
    plan = Attribute(unicode, (DETAILED,))
    agreed_to_terms = Attribute(unicode, (DETAILED,))
    follower_request_count = Attribute(int, (DETAILED,))
    email_facebook_twitter_friend_joins = Attribute(bool, (DETAILED,))
    receive_kudos_emails = Attribute(bool, (DETAILED,))
    receive_follower_feed_emails = Attribute(bool, (DETAILED,))
    receive_comment_emails = Attribute(bool, (DETAILED,))
    
    sample_race_distance = Attribute(int, (DETAILED,)) # What is this?
    sample_race_time = Attribute(int, (DETAILED,)) # What is this?
    
    def __repr__(self):
        return '<Athlete id={id} firstname={fname} lastname={lname}>'.format(id=self.id,
                                                                             fname=self.firstname,
                                                                             lname=self.lastname)
    
class ActivityComment(LoadableEntity):
    activity_id = Attribute(int, (META,SUMMARY,DETAILED))
    text = Attribute(unicode, (META,SUMMARY,DETAILED))
    created_at = TimestampAttribute((SUMMARY,DETAILED))
    
    athlete = EntityAttribute(Athlete, (SUMMARY,DETAILED))
    # 'athlete' is a summary-level representation of commenter

class Map(IdentifiableEntity):
    id = Attribute(unicode, (SUMMARY,DETAILED))
    polyline = Attribute(str, (SUMMARY,DETAILED))
    summary_polyline = Attribute(str, (SUMMARY,DETAILED))

class Split(BaseEntity):
    """
    A split -- may be metric or standard units (which has no bearing
    on the units used in this object, just the binning of values).
    """
    distance = Attribute(float, units=uh.meters)
    elapsed_time = TimeIntervalAttribute()
    elevation_difference = Attribute(float, units=uh.meters) 
    moving_time = TimeIntervalAttribute()
    split = Attribute(int)

class SegmentExplorerResult(LoadableEntity):
    """
    Represents a segment result from the segment explorer feature.
    
    (These are not full segment objects, but the segment object can be fetched
    via the 'segment' property of this object.)
    """
    _segment = None
    id = Attribute(int)
    name = Attribute(unicode)
    climb_category = Attribute(int)
    climb_category_desc = Attribute(unicode)
    avg_grade = Attribute(float)
    start_latlng = LocationAttribute()
    end_latlng = LocationAttribute()
    elev_difference = Attribute(float, units=uh.meters)
    distance = Attribute(float, units=uh.meters)
    points = Attribute(str) #: Encoded polyline 
    
    @property
    def segment(self):
        if self._segment is None:
            self.assert_bind_client()
            if self.id is not None:
                self._segment = self.bind_client.get_segment(self.id)
        return self._segment
    
class Segment(LoadableEntity):
    """
    Represents a single Strava segment.
    """
    _leaderboard = None
    
    name = Attribute(unicode, (SUMMARY,DETAILED))
    activity_type = Attribute(unicode, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    average_grade = Attribute(float, (SUMMARY,DETAILED)) # percent
    maximum_grade = Attribute(float, (SUMMARY,DETAILED)) # percent
    elevation_high = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    elevation_low = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    start_latlng = LocationAttribute((SUMMARY,DETAILED))
    end_latlng = LocationAttribute((SUMMARY,DETAILED))
    start_latitude = Attribute(float, (SUMMARY,DETAILED))
    end_latitude = Attribute(float, (SUMMARY,DETAILED))
    start_longitude = Attribute(float, (SUMMARY,DETAILED))
    end_longitude = Attribute(float, (SUMMARY,DETAILED))
    climb_category = Attribute(int, (SUMMARY,DETAILED)) # 0-5, lower is harder
    city = Attribute(unicode, (SUMMARY,DETAILED))
    state = Attribute(unicode, (SUMMARY,DETAILED))
    private = Attribute(bool, (SUMMARY,DETAILED))
    
    # detailed attribs
    created_at = TimestampAttribute((DETAILED,))
    updated_at = TimestampAttribute((DETAILED,))
    total_elevation_gain = Attribute(float, (DETAILED,), units=uh.meters)
    map = EntityAttribute(Map, (DETAILED,))
    effort_count = Attribute(int, (DETAILED,))
    athlete_count = Attribute(int, (DETAILED,))
    hazardous = Attribute(bool, (DETAILED,))
    pr_time = TimeIntervalAttribute((DETAILED,))
    pr_distance = Attribute(float, (DETAILED,), units=uh.meters)
    starred = Attribute(bool, (DETAILED,))
    
    @property
    def leaderboard(self):
        if self._leaderboard is None:
            self.assert_bind_client()
            if self.id is not None:
                self._leaderboard = self.bind_client.get_segment_leaderboard(self.id)
        return self._leaderboard
    
class BaseEffort(LoadableEntity):
    name = Attribute(unicode, (SUMMARY,DETAILED))
    segment = EntityAttribute(Segment, (SUMMARY,DETAILED))
    activity = EntityAttribute("Activity", (SUMMARY,DETAILED))
    athlete = EntityAttribute(Athlete, (SUMMARY,DETAILED))
    kom_rank = Attribute(int, (SUMMARY,DETAILED))
    pr_rank = Attribute(int, (SUMMARY,DETAILED))
    moving_time = TimeIntervalAttribute((SUMMARY,DETAILED))
    elapsed_time = TimeIntervalAttribute((SUMMARY,DETAILED))
    start_date = TimestampAttribute((SUMMARY,DETAILED))
    start_date_local = TimestampAttribute((SUMMARY,DETAILED), tzinfo=None)
    distance = Attribute(int, (SUMMARY,DETAILED), units=uh.meters)

class BestEffort(BaseEffort):
    pass

class SegmentEffort(BaseEffort):
    start_index = Attribute(int, (SUMMARY,DETAILED)) # the activity stream index of the start of this effort
    end_index = Attribute(int, (SUMMARY,DETAILED)) # the activity stream index of the end of this effort
                    
class Activity(LoadableEntity):
    """
    Represents an activity (ride, run, etc.).
    """
    # "Constants" for types of activities
    RIDE = "Ride"
    RUN = "Run"
    SWIM = "Swim" 
    HIKE = "Hike"
    WALK = "Walk"
    NORDICSKI = "NordicSki"
    ALPINESKI = "AlpineSki"
    BACKCOUNTRYSKI = "BackcountrySki"
    ICESKATE = "IceSkate"
    INLINESKATE = "InlineSkate"
    KITESURF = "Kitesurf"
    ROLLERSKI = "RollerSki"
    WINDSURF = "Windsurf"
    WORKOUT = "Workout"
    SNOWBOARD = "Snowboard"
    SNOWSHOE = "Snowshoe"
    
    _comments = None
    _zones = None
    _gear = None
    
    TYPES = (RIDE, RUN, SWIM, HIKE, WALK, NORDICSKI, ALPINESKI, BACKCOUNTRYSKI,
             ICESKATE, INLINESKATE, KITESURF, ROLLERSKI, WINDSURF, WORKOUT, 
             SNOWBOARD, SNOWSHOE)
    
    guid = Attribute(unicode, (SUMMARY,DETAILED)) # An undocumented attribute
    
    external_id = Attribute(unicode, (SUMMARY,DETAILED))
    upload_id = Attribute(unicode, (SUMMARY,DETAILED))
    athlete = EntityAttribute(Athlete, (SUMMARY,DETAILED))
    name = Attribute(unicode, (SUMMARY,DETAILED))
    distance = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    moving_time = TimeIntervalAttribute((SUMMARY,DETAILED))
    elapsed_time = TimeIntervalAttribute((SUMMARY,DETAILED))
    total_elevation_gain = Attribute(float, (SUMMARY,DETAILED), units=uh.meters)
    type = Attribute(unicode, (SUMMARY,DETAILED))
    start_date = TimestampAttribute((SUMMARY,DETAILED))
    start_date_local = TimestampAttribute((SUMMARY,DETAILED), tzinfo=None)
    timezone = TimezoneAttribute((SUMMARY,DETAILED))
    start_latlng = LocationAttribute((SUMMARY,DETAILED))
    end_latlng = LocationAttribute((SUMMARY,DETAILED))
    
    location_city = Attribute(unicode, (SUMMARY,DETAILED)),
    location_state = Attribute(unicode, (SUMMARY,DETAILED)),
    start_latitude = Attribute(float, (SUMMARY,DETAILED)),
    start_longitude = Attribute(float, (SUMMARY,DETAILED)),
    
    achievement_count = Attribute(int, (SUMMARY,DETAILED)),
    kudos_count = Attribute(int, (SUMMARY,DETAILED)),
    comment_count = Attribute(int, (SUMMARY,DETAILED)),
    athlete_count = Attribute(int, (SUMMARY,DETAILED)),
    photo_count = Attribute(int, (SUMMARY,DETAILED)),
    map = EntityAttribute(Map, (SUMMARY,DETAILED))
    
    trainer = Attribute(bool, (SUMMARY,DETAILED))
    commute = Attribute(bool, (SUMMARY,DETAILED))
    manual = Attribute(bool, (SUMMARY,DETAILED))
    private = Attribute(bool, (SUMMARY,DETAILED))
    flagged = Attribute(bool, (SUMMARY,DETAILED))
    
    gear_id = Attribute(unicode, (SUMMARY,DETAILED))
    
    average_speed = Attribute(float, (SUMMARY,DETAILED), units=uh.meters_per_second)
    max_speed = Attribute(float, (SUMMARY,DETAILED), units=uh.meters_per_second)
    calories = Attribute(float, (SUMMARY,DETAILED)) 
    truncated = Attribute(int, (SUMMARY,DETAILED))
    has_kudoed = Attribute(bool, (SUMMARY,DETAILED))
  
    segment_efforts = EntityCollection(SegmentEffort, (DETAILED,))
    splits_metric = EntityCollection(Split, (DETAILED,))
    splits_standard = EntityCollection(Split, (DETAILED,))
    best_efforts = EntityCollection(BestEffort, (DETAILED,))
    
    # Undocumented attributes
    average_watts = Attribute(float, (SUMMARY,DETAILED))
    average_heartrate = Attribute(float, (SUMMARY,DETAILED))
    max_heartrate = Attribute(int, (SUMMARY,DETAILED))
    average_cadence = Attribute(float, (SUMMARY,DETAILED))
    kilojoules = Attribute(float, (SUMMARY,DETAILED))
    
    average_temp = Attribute(int, (SUMMARY,DETAILED))
    
    description = Attribute(unicode, (DETAILED,))  # Is this also in summary?
    workout_type = Attribute(unicode, (DETAILED,))  # Is this also in summary?
    
    @property
    def gear(self):
        if self._gear is None:
            self.assert_bind_client()
            if self.gear_id is not None:
                self._gear = self.bind_client.get_gear(self.gear_id)
        return self._gear
        

    @property
    def comments(self):
        if self._comments is None:
            self.assert_bind_client()
            if self.comment_count > 0:
                self._comments = self.bind_client.get_activity_comments(self.id)
            else:
                # Shortcut if we know there aren't any
                self._comments = []
        return self._comments

    @property
    def zones(self):
        if self._zones is None:
            self.assert_bind_client()
            self._zones = self.bind_client.get_activity_zones(self.id)
        return self._zones

class SegmentLeaderboardEntry(BoundEntity):
    """
    Represents a single entry on a segment leaderboard.
    """
    _athlete = None
    _activity = None
    _effort = None
    
    effort_id = Attribute(int)
    athlete_id = Attribute(int)
    athlete_name = Attribute(unicode)
    athlete_gender = Attribute(unicode)
    average_hr = Attribute(float)
    average_watts = Attribute(float)
    distance = Attribute(float, units=uh.meters)
    elapsed_time = TimeIntervalAttribute()
    moving_time = TimeIntervalAttribute()
    start_date = TimestampAttribute((SUMMARY,DETAILED))
    start_date_local = TimestampAttribute((SUMMARY,DETAILED), tzinfo=None)
    activity_id = Attribute(int)
    rank = Attribute(int)
    athlete_profile = Attribute(unicode)
    
    def __repr__(self):
        return '<SegmentLeaderboardEntry rank={0} athlete_name={1!r}>'.format(self.rank, self.athlete_name)
    
    @property
    def athlete(self):
        """ The related athlete (performs additional server fetch). """
        if self._athlete is None:
            self.assert_bind_client()
            if self.athlete_id is not None:
                self._athlete = self.bind_client.get_athlete(self.athlete_id)
        return self._athlete

    @property
    def activity(self):
        """ The related activity (performs additional server fetch). """
        if self._activity is None:
            self.assert_bind_client()
            if self.activity_id is not None:
                self._activity = self.bind_client.get_activity(self.activity_id)
        return self._activity
    
    @property
    def effort(self):
        """ The related effort (performs additional server fetch). """
        if self._effort is None:
            self.assert_bind_client()
            if self.effort_id is not None:
                self._effort = self.bind_client.get_segment_effort(self.effort_id)
        return self._effort
    
class SegmentLeaderboard(Sequence, BoundEntity):
    """
    The ranked leaderboard for a segment.
    """
    effort_count = Attribute(int)
    entry_count = Attribute(int)
    entries = EntityCollection(SegmentLeaderboardEntry)
    
    def __iter__(self):
        return iter(self.entries)
    
    def __len__(self):
        return len(self.entries)
    
    def __contains__(self, k):
        return k in self.entries
    
    def __getitem__(self, k):
        return self.entries[k]
    
class DistributionBucket(BaseEntity):
    max = Attribute(int)
    min = Attribute(int)
    time = Attribute(int, units=uh.seconds)

class BaseActivityZone(LoadableEntity):
    """
    Base class for activity zones.
    """
    distribution_buckets = EntityCollection(DistributionBucket, (SUMMARY, DETAILED))
    type = Attribute(unicode, (SUMMARY, DETAILED))
    sensor_based = Attribute(bool, (SUMMARY, DETAILED))
    
    @classmethod
    def deserialize(cls, v, bind_client=None):
        """
        Creates a new object based on serialized (dict) struct. 
        """
        if v is None:
            return None
        az_classes = {'heartrate': HeartrateActivityZone,
                      'power': PowerActivityZone,
                      'pace': PaceActivityZone} 
        try:
            clazz = az_classes[v['type']]
        except KeyError:
            raise ValueError("Unsupported activity zone type: {0}".format(v['type']))
        else:
            o = clazz(bind_client=bind_client)
            o.from_dict(v)
            return o
    
    
class HeartrateActivityZone(BaseActivityZone):
    score = Attribute(int, (SUMMARY, DETAILED))
    points = Attribute(int, (SUMMARY, DETAILED))
    custom_zones = Attribute(bool, (SUMMARY, DETAILED))
    max = Attribute(int, (SUMMARY, DETAILED))

class PaceActivityZone(BaseActivityZone):
    score = Attribute(int, (SUMMARY, DETAILED))
    sample_race_distance = Attribute(int, (SUMMARY, DETAILED), units=uh.meters)
    sample_race_time = TimeIntervalAttribute((SUMMARY, DETAILED))
        
class PowerActivityZone(BaseActivityZone):
    bike_weight = Attribute(float, (SUMMARY, DETAILED), units=uh.kgs)
    athlete_weight = Attribute(float, (SUMMARY, DETAILED), units=uh.kgs)