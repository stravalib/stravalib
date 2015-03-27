"""
Entity classes for representing the various Strava datatypes.
"""
import abc
import logging
from collections import Sequence

from stravalib import exc
from stravalib import unithelper as uh

from stravalib.attributes import (META, SUMMARY, DETAILED, Attribute,
                                  TimestampAttribute, LocationAttribute,
                                  EntityCollection, EntityAttribute,
                                  TimeIntervalAttribute, TimezoneAttribute,
                                  DateAttribute)


class BaseEntity(object):
    """
    A base class for all entities in the system, including objects that may not
    be first-class entities in Strava.
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
        for (k, v) in d.items():
            # Only set defined attributes.
            if hasattr(self.__class__, k):
                self.log.debug("Setting attribute `{0}` [{1}] on entity {2} with value {3!r}".format(k, getattr(self.__class__, k).__class__.__name__, self, v))
                try:
                    setattr(self, k, v)
                except AttributeError as x:
                    raise AttributeError("Could not find attribute `{0}` on entity {1}, value: {2!r}.  (Original: {3!r})".format(k, self, v, x))
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
    Mixin for entities that include the resource_state attribute.
    """
    resource_state = Attribute(int, (META, SUMMARY, DETAILED))  #: The detail-level for this entity.


class IdentifiableEntity(ResourceStateEntity):
    """
    Mixin for entities that include an ID attribute.
    """
    id = Attribute(int, (META, SUMMARY, DETAILED))  #: The numeric ID for this entity.


class BoundEntity(BaseEntity):
    """
    Base class for entities that support lazy loading additional data using a bound client.
    """

    bind_client = None  #: The :class:`stravalib.client.Client` that can be used to load related resources.

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
    """
    Base class for entities that are bound and have an ID associated with them.

    In theory these entities can be "expaned" by additional Client queries.  In practice this is not
    implemented, since usefulness is limited due to resource-state limitations, etc.
    """
    def expand(self):
        """
        Expand this object with data from the bound client.

        (THIS IS NOT IMPLEMENTED CURRENTLY.)
        """
        raise NotImplementedError()  # This is a little harder now due to resource states, etc.


class Club(LoadableEntity):
    """
    Class to represent a club.

    Currently summary and detail resource states have the same attributes.
    """
    name = Attribute(unicode, (SUMMARY, DETAILED))  #: Name of the club.
    profile_medium = Attribute(unicode, (SUMMARY, DETAILED))  #: URL to a 62x62 pixel club picture
    profile = Attribute(unicode, (SUMMARY, DETAILED))  #: URL to a 124x124 pixel club picture

    @property
    def members(self):
        """ An iterator of :class:`stravalib.model.Athlete` members of this club. """
        if self._members is None:
            self.assert_bind_client()
            self._members = self.bind_client.get_club_members(self.id)
        return self._members

    @property
    def activities(self):
        """ An iterator of reverse-chronological :class:`stravalib.model.Activity` activities for this club. """
        if self._activities is None:
            self.assert_bind_client()
            self._activities = self.bind_client.get_club_activities(self.id)
        return self._activities


class Gear(IdentifiableEntity):
    """
    Information about Gear (bike or shoes) used during activity.
    """
    id = Attribute(unicode, (META, SUMMARY, DETAILED))  #: Alpha-numeric gear ID.
    name = Attribute(unicode, (SUMMARY, DETAILED))  #: Name athlete entered for bike (does not apply to shoes)
    distance = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: Distance for this bike/shoes.
    primary = Attribute(bool, (SUMMARY, DETAILED))  #: athlete's default bike/shoes
    brand_name = Attribute(unicode, (DETAILED,))  #: Brand name of bike/shoes.
    model_name = Attribute(unicode, (DETAILED,))  #: Modelname of bike/shoes.
    description = Attribute(unicode, (DETAILED,))  #: Description of bike/shoe item.

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
    Represents an athlete's bike.
    """
    frame_type = Attribute(int, (DETAILED,))  #: (detailed-only) Type of bike frame.


class Shoe(Gear):
    """
    Represent's an athlete's pair of shoes.
    """


class ActivityTotals(BaseEntity):
    """
    Represent ytd/recent/all run/ride totals.
    """
    achievement_count = Attribute(int)  #: How many achievements
    count = Attribute(int)  #: How many activities
    distance = Attribute(float, units=uh.meters)  #: Total distance travelled
    elapsed_time = TimeIntervalAttribute()  #: :class:`datetime.timedelta` of total elapsed time
    elevation_gain = Attribute(float, units=uh.meters)  #: Total elevation gain
    moving_time = TimeIntervalAttribute()  #: :class:`datetime.timedelta` of total moving time


class Athlete(LoadableEntity):
    """
    Represents a Strava athlete.
    """
    firstname = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's first name.
    lastname = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's last name.
    profile_medium = Attribute(unicode, (SUMMARY, DETAILED))  #: URL to a 62x62 pixel profile picture
    profile = Attribute(unicode, (SUMMARY, DETAILED))  #: URL to a 124x124 pixel profile picture
    city = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's home city
    state = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's home state
    country = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's home country
    sex = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's sex ('M', 'F' or null)
    friend = Attribute(unicode, (SUMMARY, DETAILED))  #: 'pending', 'accepted', 'blocked' or 'null' the authenticated athlete's following status of this athlete
    follower = Attribute(unicode, (SUMMARY, DETAILED))  #: 'pending', 'accepted', 'blocked' or 'null' this athlete's following status of the authenticated athlete
    premium = Attribute(bool, (SUMMARY, DETAILED))  #: Whether athlete is a premium member (true/false)

    created_at = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when athlete record was created.
    updated_at = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when athlete record was last updated.

    approve_followers = Attribute(bool, (SUMMARY, DETAILED))  #: Whether athlete has elected to approve followers

    badge_type_id = Attribute(int, (SUMMARY, DETAILED))  #: (undocumented)

    follower_count = Attribute(int, (DETAILED,))  #: (detailed-only) How many people are following this athlete
    friend_count = Attribute(int, (DETAILED,))  #: (detailed-only) How many people is this athlete following
    mutual_friend_count = Attribute(int, (DETAILED,))  #: (detailed-only) How many people are both following and being followed by this athlete
    date_preference = Attribute(unicode, (DETAILED,))  #: (detailed-only) Athlete's preferred date representation (e.g. "%m/%d/%Y")
    measurement_preference = Attribute(unicode, (DETAILED,))  #: (detailed-only) How athlete prefers to see measurements (i.e. "feet" (or what "meters"?))
    email = Attribute(unicode, (DETAILED,))  #: (detailed-only)  Athlete's email address

    clubs = EntityCollection(Club, (DETAILED,))  #: (detailed-only) Which clubs athlete belongs to. (:class:`list` of :class:`stravalib.model.Club`)
    bikes = EntityCollection(Bike, (DETAILED,))  #: (detailed-only) Which bikes this athlete owns. (:class:`list` of :class:`stravalib.model.Bike`)
    shoes = EntityCollection(Shoe, (DETAILED,))  #: (detailed-only) Which shoes this athlete owns. (:class:`list` of :class:`stravalib.model.Shoe`)

    # Some undocumented summary & detailed  attributes
    ytd_run_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))  #: (undocumented) Year-to-date totals for runs. (:class:`stravalib.model.ActivityTotals`)
    recent_run_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))  #: (undocumented) Recent totals for runs. (:class:`stravalib.model.ActivityTotals`)
    all_run_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))  #: (undocumented) All-time totals for runs. (:class:`stravalib.model.ActivityTotals`)

    ytd_ride_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))  #: (undocumented) Year-to-date totals for rides. (:class:`stravalib.model.ActivityTotals`)
    recent_ride_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))  #: (undocumented) Recent totals for rides. (:class:`stravalib.model.ActivityTotals`)
    all_ride_totals = EntityAttribute(ActivityTotals, (SUMMARY, DETAILED))  #: (undocumented) All-time totals for rides. (:class:`stravalib.model.ActivityTotals`)

    super_user = Attribute(bool, (SUMMARY, DETAILED))  #: (undocumented) Whether athlete is a super user (not
    biggest_ride_distance = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: (undocumented) Longest ride for athlete.
    biggest_climb_elevation_gain = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: (undocumented) Greatest single elevation gain for athlete.

    email_language = Attribute(unicode, (SUMMARY, DETAILED))  #: The user's preferred lang/locale (e.g. en-US)

    # A bunch more undocumented detailed-resolution attribs
    weight = Attribute(float, (DETAILED,), units=uh.kg)  #: (undocumented, detailed-only)  Athlete's configured weight.
    max_heartrate = Attribute(float, (DETAILED,))  #: (undocumented, detailed-only) Athlete's configured max HR

    username = Attribute(unicode, (DETAILED))  #: (undocumented, detailed-only) Athlete's username.
    description = Attribute(unicode, (DETAILED,))  #: (undocumented, detailed-only) Athlete's personal description
    instagram_username = Attribute(unicode, (DETAILED,))  #: (undocumented, detailed-only) Associated instagram username

    offer_in_app_payment = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only)
    global_privacy = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only) Whether athlete has global privacy enabled.
    receive_newsletter = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only) Whether athlete has elected to receive newsletter
    email_kom_lost = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only) Whether athlete has elected to receive emails when KOMs are lost.
    dateofbirth = DateAttribute((DETAILED,))  #: (undocumented, detailed-only) Athlete's date of birth
    facebook_sharing_enabled = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only) Whether Athlete has enabled sharing on Facebook
    ftp = Attribute(unicode, (DETAILED,))   #: (undocumented, detailed-only)
    profile_original = Attribute(unicode, (DETAILED,))  #: (undocumented, detailed-only)
    premium_expiration_date = Attribute(int, (DETAILED,))  #: (undocumented, detailed-only) When does premium membership expire (:class:`int` unix epoch)
    email_send_follower_notices = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only)
    plan = Attribute(unicode, (DETAILED,))  #: (undocumented, detailed-only)
    agreed_to_terms = Attribute(unicode, (DETAILED,))  #: (undocumented, detailed-only) Whether athlete has agreed to terms
    follower_request_count = Attribute(int, (DETAILED,))  #: (undocumented, detailed-only) How many people have requested to follow this athlete
    email_facebook_twitter_friend_joins = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only) Whether athlete has elected to receve emails when a twitter or facebook friend joins Strava
    receive_kudos_emails = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only) Whether athlete has elected to receive emails on kudos
    receive_follower_feed_emails = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only) Whether athlete has elected to receive emails on new followers
    receive_comment_emails = Attribute(bool, (DETAILED,))  #: (undocumented, detailed-only) Whether athlete has elected to receive emails on activity comments

    sample_race_distance = Attribute(int, (DETAILED,))  # (undocumented, detailed-only)
    sample_race_time = Attribute(int, (DETAILED,))  # (undocumented, detailed-only)

    _friends = None
    _followers = None

    def __repr__(self):
        fname = self.firstname and self.firstname.encode('utf-8')
        lname = self.lastname and self.lastname.encode('utf-8')
        return '<Athlete id={id} firstname={fname} lastname={lname}>'.format(id=self.id,
                                                                             fname=fname,
                                                                             lname=lname)

    @property
    def friends(self):
        """
        :return: Iterator of :class:`stravalib.model.Athlete` friend objects for this athlete.
        """
        if self._friends is None:
            self.assert_bind_client()
            if self.friend_count > 0:
                self._friends = self.bind_client.get_athlete_friends(self.id)
            else:
                # Shortcut if we know there aren't any
                self._friends = []
        return self._friends

    @property
    def followers(self):
        """
        :return: Iterator of :class:`stravalib.model.Athlete` followers objects for this athlete.
        """
        if self._followers is None:
            self.assert_bind_client()
            if self.follower_count > 0:
                self._followers = self.bind_client.get_athlete_followers(self.id)
            else:
                # Shortcut if we know there aren't any
                self._followers = []
        return self._followers


class ActivityComment(LoadableEntity):
    """
    Comments attached to an activity.
    """
    activity_id = Attribute(int, (META, SUMMARY, DETAILED))  #: ID of activity
    text = Attribute(unicode, (META, SUMMARY, DETAILED))  #: Text of comment
    created_at = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when was coment created
    athlete = EntityAttribute(Athlete, (SUMMARY, DETAILED))  #: Associated :class:`stravalib.model.Athlete` (summary-level representation)


class ActivityPhotoMeta(BaseEntity):
    """
    The photos structure returned with the activity, not to be confused with the full loaded photos for an activity.
    """
    count = Attribute(int)
    primary = Attribute(unicode)

    def __repr__(self):
        return '<{0} count={1}>'.format(self.__class__.__name__, self.count)


class ActivityPhoto(LoadableEntity):
    """
    Information about photos attached to an activity.
    """
    activity_id = Attribute(int, (META, SUMMARY, DETAILED))  #: ID of activity
    ref = Attribute(unicode, (META, SUMMARY, DETAILED))  #: ref eg. "http://instagram.com/p/eAvA-tir85/"
    uid = Attribute(unicode, (META, SUMMARY, DETAILED))  #: unique id
    caption = Attribute(unicode, (META, SUMMARY, DETAILED))  #: caption on photo
    type = Attribute(unicode, (META, SUMMARY, DETAILED))  #: type of photo (currently only InstagramPhoto)
    uploaded_at = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when was photo uploaded
    created_at = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when was photo created
    location = LocationAttribute()  #: Start lat/lon of photo


class ActivityKudos(LoadableEntity):
    """
    Activity kudos are a subset of athlete properties.
    """
    firstname = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's first name.
    lastname = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's last name.
    profile_medium = Attribute(unicode, (SUMMARY, DETAILED))  #: URL to a 62x62 pixel profile picture
    profile = Attribute(unicode, (SUMMARY, DETAILED))  #: URL to a 124x124 pixel profile picture
    city = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's home city
    state = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's home state
    country = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's home country
    sex = Attribute(unicode, (SUMMARY, DETAILED))  #: Athlete's sex ('M', 'F' or null)
    friend = Attribute(unicode, (SUMMARY, DETAILED))  #: 'pending', 'accepted', 'blocked' or 'null' the authenticated athlete's following status of this athlete
    follower = Attribute(unicode, (SUMMARY, DETAILED))  #: 'pending', 'accepted', 'blocked' or 'null' this athlete's following status of the authenticated athlete
    premium = Attribute(bool, (SUMMARY, DETAILED))  #: Whether athlete is a premium member (true/false)

    created_at = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when athlete record was created.
    updated_at = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when athlete record was last updated.

    approve_followers = Attribute(bool, (SUMMARY, DETAILED))  #: Whether athlete has elected to approve followers


class ActivityLap(LoadableEntity):

    name = Attribute(unicode, (SUMMARY, DETAILED))  #: Name of lap
    activity = EntityAttribute("Activity", (SUMMARY, DETAILED))  #: The associated :class:`stravalib.model.Activity`
    athlete = EntityAttribute(Athlete, (SUMMARY, DETAILED))  #: The associated :class:`stravalib.model.Athlete`

    elapsed_time = TimeIntervalAttribute((SUMMARY, DETAILED))  #: :class:`datetime.timedelta` of elapsed time for lap
    moving_time = TimeIntervalAttribute((SUMMARY, DETAILED))  #: :class:`datetime.timedelta` of moving time for lap
    start_date = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when lap was started in GMT
    start_date_local = TimestampAttribute((SUMMARY, DETAILED), tzinfo=None)  #: :class:`datetime.datetime` when lap was started local
    distance = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: The distance for this lap.
    start_index = Attribute(int, (SUMMARY, DETAILED))  #:
    end_index = Attribute(int, (SUMMARY, DETAILED))  #:
    total_elevation_gain = Attribute(float, (SUMMARY, DETAILED,), units=uh.meters)  #: What is total elevation gain for lap
    average_speed = Attribute(float, (SUMMARY, DETAILED,), units=uh.meters_per_second)  #: Average speed for lap
    max_speed = Attribute(float, (SUMMARY, DETAILED,), units=uh.meters_per_second)  #: Max speed for lap
    average_cadence = Attribute(float, (SUMMARY, DETAILED,))  #: Average cadence for lap
    average_watts = Attribute(float, (SUMMARY, DETAILED,))  #: Average watts for lap
    average_heartrate = Attribute(float, (SUMMARY, DETAILED,))  #: Average heartrate for lap
    max_heartrate = Attribute(float, (SUMMARY, DETAILED,))  #: Max heartrate for lap
    lap_index = Attribute(int, (SUMMARY, DETAILED))  #: Index of lap
    device_watts = Attribute(bool, (SUMMARY, DETAILED))  # true if the watts are from a power meter, false if estimated


class Map(IdentifiableEntity):
    id = Attribute(unicode, (SUMMARY, DETAILED))  #: Alpha-numeric identifier
    polyline = Attribute(str, (SUMMARY, DETAILED))  #: Google polyline encoding
    summary_polyline = Attribute(str, (SUMMARY, DETAILED))  #: Google polyline encoding for summary shape


class Split(BaseEntity):
    """
    A split -- may be metric or standard units (which has no bearing
    on the units used in this object, just the binning of values).
    """
    distance = Attribute(float, units=uh.meters)  #: Distance for this split
    elapsed_time = TimeIntervalAttribute()  #: :class:`datetime.timedelta` of elapsed time for split
    elevation_difference = Attribute(float, units=uh.meters)   #: Elevation difference for split
    moving_time = TimeIntervalAttribute()  #: :class:`datetime.timedelta` of moving time for split
    average_heartrate = Attribute(float)   #: Average HR for split
    split = Attribute(int)  #: Which split number


class SegmentExplorerResult(LoadableEntity):
    """
    Represents a segment result from the segment explorer feature.

    (These are not full segment objects, but the segment object can be fetched
    via the 'segment' property of this object.)
    """
    _segment = None
    id = Attribute(int)  #: ID of the segment.
    name = Attribute(unicode)  #: Name of the segment
    climb_category = Attribute(int)  #: Climb category for the segment (0 is higher)
    climb_category_desc = Attribute(unicode)  #: Climb category text
    avg_grade = Attribute(float)  #: Average grade for segment.
    start_latlng = LocationAttribute()  #: Start lat/lon for segment
    end_latlng = LocationAttribute()  #: End lat/lon for segment
    elev_difference = Attribute(float, units=uh.meters)  #: Total elevation difference over segment.
    distance = Attribute(float, units=uh.meters)  #: Distance of segment.
    points = Attribute(str)  #: Encoded Google polyline of points in segment

    @property
    def segment(self):
        """ Associated (full) :class:`stravalib.model.Segment` object. """
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

    name = Attribute(unicode, (SUMMARY, DETAILED))  #: Name of the segment.
    activity_type = Attribute(unicode, (SUMMARY, DETAILED))  #: Activity type of segment ('Ride' or 'Run')
    distance = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: Distance of segment
    average_grade = Attribute(float, (SUMMARY, DETAILED))  #: Average grade (%) for segment
    maximum_grade = Attribute(float, (SUMMARY, DETAILED))  #: Maximum grade (%) for segment
    elevation_high = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: The highest point of the segment.
    elevation_low = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: The lowest point of the segment.
    start_latlng = LocationAttribute((SUMMARY, DETAILED))  #: The start lat/lon (:class:`tuple`)
    end_latlng = LocationAttribute((SUMMARY, DETAILED))  #: The end lat/lon (:class:`tuple`)
    start_latitude = Attribute(float, (SUMMARY, DETAILED))  #: The start latitude (:class:`float`)
    end_latitude = Attribute(float, (SUMMARY, DETAILED))  #: The end latitude (:class:`float`)
    start_longitude = Attribute(float, (SUMMARY, DETAILED))  #: The start longitude (:class:`float`)
    end_longitude = Attribute(float, (SUMMARY, DETAILED))  #: The end longitude (:class:`float`)
    climb_category = Attribute(int, (SUMMARY, DETAILED))  # 0-5, lower is harder
    city = Attribute(unicode, (SUMMARY, DETAILED))  #: The city this segment is in.
    state = Attribute(unicode, (SUMMARY, DETAILED))  #: The state this segment is in.
    country = Attribute(unicode, (SUMMARY, DETAILED))  #: The country this segment is in.
    private = Attribute(bool, (SUMMARY, DETAILED))  #: Whether this is a private segment.
    starred = Attribute(bool, (SUMMARY, DETAILED))  #: Whether this segment is starred by authenticated athlete

    # detailed attribs
    created_at = TimestampAttribute((DETAILED,))  #: :class:`datetime.datetime` when was segment created.
    updated_at = TimestampAttribute((DETAILED,))  #: :class:`datetime.datetime` when was segment last updated.
    total_elevation_gain = Attribute(float, (DETAILED,), units=uh.meters)  #: What is total elevation gain for segment.
    map = EntityAttribute(Map, (DETAILED,))  #: :class:`stravalib.model.Map` object for segment.
    effort_count = Attribute(int, (DETAILED,))  #: How many times has this segment been ridden.
    athlete_count = Attribute(int, (DETAILED,))  #: How many athletes have ridden this segment
    hazardous = Attribute(bool, (DETAILED,))  #: Whether this segment has been flagged as hazardous
    star_count = Attribute(int, (DETAILED,))  #: number of stars on this segment.

    @property
    def leaderboard(self):
        """
        The :class:`stravalib.model.SegmentLeaderboard` object for this segment.
        """
        if self._leaderboard is None:
            self.assert_bind_client()
            if self.id is not None:
                self._leaderboard = self.bind_client.get_segment_leaderboard(self.id)
        return self._leaderboard


class SegmentEfforAchievement(BaseEntity):
    """
    An undocumented structure being returned for segment efforts.
    """
    rank = Attribute(int) #: Rank in segment (either overall leaderboard, or pr rank)
    type = Attribute(unicode) #: The type of achievement -- e.g. 'year_pr' or 'overall'
    type_id = Attribute(int) #: Numeric ID for type of achievement?  (6 = year_pr, 2 = overall ??? other?)


class BaseEffort(LoadableEntity):
    """
    Base class for a best effort or segment effort.
    """
    name = Attribute(unicode, (SUMMARY, DETAILED))  #: The name of the segment
    segment = EntityAttribute(Segment, (SUMMARY, DETAILED))  #: The associated :class:`stravalib.model.Segment` for this effort
    activity = EntityAttribute("Activity", (SUMMARY, DETAILED))  #: The associated :class:`stravalib.model.Activity`
    athlete = EntityAttribute(Athlete, (SUMMARY, DETAILED))  #: The associated :class:`stravalib.model.Athlete`
    kom_rank = Attribute(int, (SUMMARY, DETAILED))  #: 1-10 segment KOM ranking for athlete at time of upload
    pr_rank = Attribute(int, (SUMMARY, DETAILED))  #: 1-3 personal record ranking for athlete at time of upload
    moving_time = TimeIntervalAttribute((SUMMARY, DETAILED))  #: :class:`datetime.timedelta`
    elapsed_time = TimeIntervalAttribute((SUMMARY, DETAILED))  #: :class:`datetime.timedelta`
    start_date = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when effort was started in GMT
    start_date_local = TimestampAttribute((SUMMARY, DETAILED), tzinfo=None)  #: :class:`datetime.datetime` when effort was started in activity timezone for this effort
    distance = Attribute(int, (SUMMARY, DETAILED), units=uh.meters)  #: The distance for this effort.
    average_watts = Attribute(float, (SUMMARY, DETAILED))  #: Average power during effort
    average_heartrate = Attribute(float, (SUMMARY, DETAILED))   #: Average HR during effort
    max_heartrate = Attribute(float, (SUMMARY, DETAILED))   #: Max HR during effort
    average_cadence = Attribute(float, (SUMMARY, DETAILED))   #: Average cadence during effort
    start_index = Attribute(int, (SUMMARY, DETAILED))  #: The activity stream index of the start of this effort
    end_index = Attribute(int, (SUMMARY, DETAILED))  #: The activity stream index of the end of this effort

    achievements = EntityCollection(SegmentEfforAchievement, (SUMMARY, DETAILED)) #: Undocumented attribute includes list of achievements for this effort.

class BestEffort(BaseEffort):
    """
    Class representing a best effort (e.g. best time for 5k)
    """


class SegmentEffort(BaseEffort):
    """
    Class representing a best effort on a particular segment.
    """
    hidden = Attribute(bool, (SUMMARY, DETAILED,))  # indicates a hidden/non-important effort when returned as part of an activity, value may change over time.


class Activity(LoadableEntity):
    """
    Represents an activity (ride, run, etc.).
    """
    # "Constants" for types of activities
    RIDE = "Ride"
    RUN = "Run"
    SWIM = "Swim"
    WALK = "Walk"

    ALPINESKI = "AlpineSki"
    BACKCOUNTRYSKI = "BackcountrySki"
    CANOEING = "Canoeing"
    CROSSCOUNTRYSKIING = "CrossCountrySkiing"
    CROSSFIT = "Crossfit"
    ELLIPTICAL = "Elliptical"
    HIKE = "Hike"
    ICESKATE = "IceSkate"
    INLINESKATE = "InlineSkate"
    KAYAKING = "Kayaking"
    KITESURF = "Kitesurf"
    NORDICSKI = "NordicSki"
    ROCKCLIMBING = "RockClimbing"
    ROLLERSKI = "RollerSki"
    ROWING = "Rowing"
    SNOWBOARD = "Snowboard"
    SNOWSHOE = "Snowshoe"
    STAIRSTEPPER = "StairStepper"
    STANDUPPADDLING = "StandUpPaddling"
    SURFING = "Surfing"
    WEIGHTTRAINING = "WeightTraining"
    WINDSURF = "Windsurf"
    WORKOUT = "Workout"
    YOGA = "Yoga"

    _comments = None
    _zones = None
    _kudos = None
    _photos = None
    #_gear = None
    _laps = None
    _related = None

    TYPES = (RIDE, RUN, SWIM, WALK, ALPINESKI, BACKCOUNTRYSKI, CANOEING,
             CROSSCOUNTRYSKIING, CROSSFIT, ELLIPTICAL, HIKE, ICESKATE,
             INLINESKATE, KAYAKING, KITESURF, NORDICSKI, ROCKCLIMBING,
             ROLLERSKI, ROWING, SNOWBOARD, SNOWSHOE, STAIRSTEPPER,
             STANDUPPADDLING, SURFING, WEIGHTTRAINING, WINDSURF, WORKOUT, YOGA)

    guid = Attribute(unicode, (SUMMARY, DETAILED))  #: (undocumented)

    external_id = Attribute(unicode, (SUMMARY, DETAILED))  #: An external ID for the activity (relevant when specified during upload).
    upload_id = Attribute(unicode, (SUMMARY, DETAILED))  #: The upload ID for an activit.
    athlete = EntityAttribute(Athlete, (SUMMARY, DETAILED))  #: The associated :class:`stravalib.model.Athlete` that performed this activity.
    name = Attribute(unicode, (SUMMARY, DETAILED))  #: The name of the activity.
    distance = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: The distance for the activity.
    moving_time = TimeIntervalAttribute((SUMMARY, DETAILED))  #: The moving time duration for this activity.
    elapsed_time = TimeIntervalAttribute((SUMMARY, DETAILED))  #: The total elapsed time (including stopped time) for this activity.
    total_elevation_gain = Attribute(float, (SUMMARY, DETAILED), units=uh.meters)  #: Total elevation gain for activity.
    type = Attribute(unicode, (SUMMARY, DETAILED))  #: The activity type.
    start_date = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when activity was started in GMT
    start_date_local = TimestampAttribute((SUMMARY, DETAILED), tzinfo=None)  #: :class:`datetime.datetime` when activity was started in activity timezone
    timezone = TimezoneAttribute((SUMMARY, DETAILED))  #: The timezone for activity.
    start_latlng = LocationAttribute((SUMMARY, DETAILED))  #: The start location (lat/lon :class:`tuple`)
    end_latlng = LocationAttribute((SUMMARY, DETAILED))  #: The end location (lat/lon :class:`tuple`)

    location_city = Attribute(unicode, (SUMMARY, DETAILED))  #: The activity location city
    location_state = Attribute(unicode, (SUMMARY, DETAILED))  #: The activity location state
    location_country = Attribute(unicode, (SUMMARY, DETAILED))  #: The activity location state
    start_latitude = Attribute(float, (SUMMARY, DETAILED))  #: The start latitude
    start_longitude = Attribute(float, (SUMMARY, DETAILED))  #: The start longitude

    achievement_count = Attribute(int, (SUMMARY, DETAILED))  #: How many achievements earned for the activity
    kudos_count = Attribute(int, (SUMMARY, DETAILED))  #: How many kudos received for activity
    comment_count = Attribute(int, (SUMMARY, DETAILED))  #: How many comments  for activity.
    athlete_count = Attribute(int, (SUMMARY, DETAILED))  #: How many other athlete's participated in activity
    photo_count = Attribute(int, (SUMMARY, DETAILED))  #: How many photos linked to activity
    map = EntityAttribute(Map, (SUMMARY, DETAILED))  #: :class:`stravavlib.model.Map` of activity.

    trainer = Attribute(bool, (SUMMARY, DETAILED))  #: Whether activity was performed on a stationary trainer.
    commute = Attribute(bool, (SUMMARY, DETAILED))  #: Whether activity is a commute.
    manual = Attribute(bool, (SUMMARY, DETAILED))  #: Whether activity was manually entered.
    private = Attribute(bool, (SUMMARY, DETAILED))  #: Whether activity is private
    flagged = Attribute(bool, (SUMMARY, DETAILED))   #: Whether activity was flagged.

    gear_id = Attribute(unicode, (SUMMARY, DETAILED))  #: Which bike/shoes were used on activity.
    gear = EntityAttribute(Gear, (DETAILED,))

    average_speed = Attribute(float, (SUMMARY, DETAILED), units=uh.meters_per_second)  #: Average speed for activity.
    max_speed = Attribute(float, (SUMMARY, DETAILED), units=uh.meters_per_second)  #: Max speed for activity

    device_watts = Attribute(bool, (SUMMARY, DETAILED))  #: True if the watts are from a power meter, false if estimated

    truncated = Attribute(int, (SUMMARY, DETAILED))  #: Only present if activity is owned by authenticated athlete, set to 0 if not truncated by privacy zones
    has_kudoed = Attribute(bool, (SUMMARY, DETAILED))  #: If authenticated user has kudoed this activity

    best_efforts = EntityCollection(BestEffort, (DETAILED,))  #: :class:`list` of metric :class:`stravalib.model.BestEffort` summaries
    segment_efforts = EntityCollection(SegmentEffort, (DETAILED,))  #: :class:`list` of :class:`stravalib.model.SegmentEffort` efforts for activity.
    splits_metric = EntityCollection(Split, (DETAILED,))  #: :class:`list` of metric :class:`stravalib.model.Split` summaries (running activities only)
    splits_standard = EntityCollection(Split, (DETAILED,))  #: :class:`list` of standard/imperial :class:`stravalib.model.Split` summaries (running activities only)

    # Undocumented attributes
    average_watts = Attribute(float, (SUMMARY, DETAILED))  #: (undocumented) Average power during activity
    weighted_average_watts = Attribute(int, (SUMMARY, DETAILED))  # rides with power meter data only similar to xPower or Normalized Power
    average_heartrate = Attribute(float, (SUMMARY, DETAILED))  #: (undocumented) Average HR during activity
    max_heartrate = Attribute(int, (SUMMARY, DETAILED))  #: (undocumented) Max HR during activity
    average_cadence = Attribute(float, (SUMMARY, DETAILED))  #: (undocumented) Average cadence during activity
    kilojoules = Attribute(float, (SUMMARY, DETAILED))  #: (undocumented) Kilojoules of energy used during activity
    device_watts = Attribute(bool, (SUMMARY, DETAILED))  # true if the watts are from a power meter, false if estimated
    average_temp = Attribute(int, (SUMMARY, DETAILED))  #: (undocumented) Average temperature (when available from device) during activity.

    calories = Attribute(float, (DETAILED,))  #: Calculation of how many calories burned on activity
    description = Attribute(unicode, (DETAILED,))  #: (undocumented) Description of activity.
    workout_type = Attribute(unicode, (DETAILED,))  #: (undocumented)

    photos = EntityAttribute(ActivityPhotoMeta, (DETAILED,)) #: (undocumented) A new photo metadata structure.
    instagram_primary_photo = Attribute(unicode, (DETAILED,)) #: (undocumented) Appears to be the ref to first associated instagram photo

    @property
    def comments(self):
        """
        Iterator of :class:`stravalib.model.ActivityComment` objects for this activity.
        """
        if self._comments is None:
            self.assert_bind_client()
            if self.comment_count > 0:
                self._comments = self.bind_client.get_activity_comments(self.id)
            else:
                # Shortcut if we know there aren't any
                self._comments = []
        return self._comments

    @property
    def laps(self):
        """
        Iterator of :class:`stravalib.model.ActivityLap` objects for this activity.
        """
        if self._laps is None:
            self.assert_bind_client()
            self._laps = self.bind_client.get_activity_laps(self.id)
        return self._laps

    @property
    def zones(self):
        """
        :class:`list` of :class:`stravalib.model.ActivityZone` objects for this activity.
        """
        if self._zones is None:
            self.assert_bind_client()
            self._zones = self.bind_client.get_activity_zones(self.id)
        return self._zones

    @property
    def kudos(self):
        """
        :class:`list` of :class:`stravalib.model.ActivityKudos` objects for this activity.
        """
        if self._kudos is None:
            self.assert_bind_client()
            self._kudos = self.bind_client.get_activity_kudos(self.id)
        return self._kudos

    @property
    def full_photos(self):
        """
        :class:`list` of :class:`stravalib.model.ActivityPhoto` objects for this activity.
        """
        if self._photos is None:
            if self.photo_count > 0:
                self.assert_bind_client()
                self._photos = self.bind_client.get_activity_photos(self.id)
            else:
                self._photos = []
        return self._photos

    @property
    def related(self):
        """
        Iterator of :class:`stravalib.model.Activty` objects for activities matched as
        with this activity.
        """
        if self._related is None:
            if self.athlete_count - 1 > 0:
                self.assert_bind_client()
                self._related = self.bind_client.get_related_activities(self.id)
            else:
                self._related = []
        return self._related


class SegmentLeaderboardEntry(BoundEntity):
    """
    Represents a single entry on a segment leaderboard.

    The :class:`stravalib.model.SegmentLeaderboard` object is essentially a collection
    of instances of this class.
    """
    _athlete = None
    _activity = None
    _effort = None

    effort_id = Attribute(int)  #: The numeric ID for the segment effort.
    athlete_id = Attribute(int)  #: The numeric ID for the athlete.
    athlete_name = Attribute(unicode)  #: The athlete's name.
    athlete_gender = Attribute(unicode)  #: The athlete's sex (M/F)
    athlete_profile = Attribute(unicode)  #: Link to athlete profile photo
    average_hr = Attribute(float)  #: The athlete's average HR for this effort
    average_watts = Attribute(float)  #: The athlete's average power for this effort
    distance = Attribute(float, units=uh.meters)  #: The distance for this effort.
    elapsed_time = TimeIntervalAttribute()  #: The elapsed time for this effort
    moving_time = TimeIntervalAttribute()  #: The moving time for this effort
    start_date = TimestampAttribute((SUMMARY, DETAILED))  #: :class:`datetime.datetime` when this effot was started in GMT
    start_date_local = TimestampAttribute((SUMMARY, DETAILED), tzinfo=None)  #: :class:`datetime.datetime` when this effort was started in activity timezone
    activity_id = Attribute(int)  #: The numeric ID of the associated activity for this effort.
    rank = Attribute(int)  #: The rank on the leaderboard.

    def __repr__(self):
        return '<SegmentLeaderboardEntry rank={0} athlete_name={1!r}>'.format(self.rank, self.athlete_name)

    @property
    def athlete(self):
        """ The related :class:`stravalib.model.Athlete` (performs additional server fetch). """
        if self._athlete is None:
            self.assert_bind_client()
            if self.athlete_id is not None:
                self._athlete = self.bind_client.get_athlete(self.athlete_id)
        return self._athlete

    @property
    def activity(self):
        """ The related :class:`stravalib.model.Activity` (performs additional server fetch). """
        if self._activity is None:
            self.assert_bind_client()
            if self.activity_id is not None:
                self._activity = self.bind_client.get_activity(self.activity_id)
        return self._activity

    @property
    def effort(self):
        """ The related :class:`stravalib.model.SegmentEffort` (performs additional server fetch). """
        if self._effort is None:
            self.assert_bind_client()
            if self.effort_id is not None:
                self._effort = self.bind_client.get_segment_effort(self.effort_id)
        return self._effort


class SegmentLeaderboard(Sequence, BoundEntity):
    """
    The ranked leaderboard for a segment.

    This class is effectively a collection of :class:`stravalib.model.SegmentLeaderboardEntry` objects.
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
    """
    A single distribution bucket object, used for activity zones.
    """
    max = Attribute(int)  #: Max datatpoint
    min = Attribute(int)  #: Min datapoint
    time = Attribute(int, units=uh.seconds)  #: Time in seconds (*not* a :class:`datetime.timedelta`)


class BaseActivityZone(LoadableEntity):
    """
    Base class for activity zones.

    A collection of :class:`stravalib.model.DistributionBucket` objects.
    """
    distribution_buckets = EntityCollection(DistributionBucket, (SUMMARY, DETAILED))  #: The collection of :class:`stravalib.model.DistributionBucket` objects
    type = Attribute(unicode, (SUMMARY, DETAILED))  #: Type of activity zone (heartrate, power, pace).
    sensor_based = Attribute(bool, (SUMMARY, DETAILED))  #: Whether zone data is sensor-based (as opposed to calculated)

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
    """
    Activity zone for heart rate.
    """
    score = Attribute(int, (SUMMARY, DETAILED))  #: The score (suffer score) for this HR zone.
    points = Attribute(int, (SUMMARY, DETAILED))  #: The points for this HR zone.
    custom_zones = Attribute(bool, (SUMMARY, DETAILED))  #: Whether athlete has setup custom zones.
    max = Attribute(int, (SUMMARY, DETAILED))  #: The max heartrate


class PaceActivityZone(BaseActivityZone):
    """
    Activity zone for pace.
    """
    score = Attribute(int, (SUMMARY, DETAILED))  #: The score for this zone.
    sample_race_distance = Attribute(int, (SUMMARY, DETAILED), units=uh.meters)  #: (Not sure?)
    sample_race_time = TimeIntervalAttribute((SUMMARY, DETAILED))  #: (Not sure?)


class PowerActivityZone(BaseActivityZone):
    """
    Activity zone for power.
    """
    # these 2 below were removed according to June 3, 2014 update @
    #    http://strava.github.io/api/v3/changelog/
    bike_weight = Attribute(float, (SUMMARY, DETAILED), units=uh.kgs)  #: Weight of bike being used (factored into power calculations)
    athlete_weight = Attribute(float, (SUMMARY, DETAILED), units=uh.kgs)  #: Weight of athlete (factored into power calculations)


class Stream(LoadableEntity):
    """
    Stream of readings from the activity, effort or segment.
    """
    type = Attribute(unicode)
    data = Attribute(list,)  #: array of values
    series_type = Attribute(unicode, )  #: type of stream: time, latlng, distance, altitude, velocity_smooth, heartrate, cadence, watts, temp, moving, grade_smooth
    original_size = Attribute(int, )  #: the size of the complete stream (when not reduced with resolution)
    resolution = Attribute(unicode, )  #: (optional, default is 'all') the desired number of data points. 'low' (100), 'medium' (1000), 'high' (10000) or 'all'

    def __repr__(self):
        return '<Stream type={} resolution={} original_size={}>'.format(self.type,
                                                                        self.resolution,
                                                                        self.original_size,)
