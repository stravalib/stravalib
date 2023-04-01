"""
==============================
Model Functions and Classes
==============================
This module contains entity classes for representing the various Strava
datatypes, such as Activity, Gear, and more. These entities inherit
fields from superclasses in `strava_model.py`, which is generated from
the official Strava API specification. The classes in this module add
behavior such as type enrichment, unit conversion, and lazy loading
related entities from the API.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from functools import wraps
from typing import Any, ClassVar, Dict, List, Literal, Optional, Tuple, Union, get_args

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.datetime_parse import parse_datetime

from stravalib import exc
from stravalib import unithelper as uh
from stravalib.exc import warn_method_deprecation
from stravalib.field_conversions import enum_value, enum_values, time_interval, timezone
from stravalib.strava_model import (
    ActivityStats,
    ActivityTotal,
    ActivityType,
    ActivityZone,
    BaseStream,
    Comment,
    DetailedActivity,
    DetailedAthlete,
    DetailedClub,
    DetailedGear,
    DetailedSegment,
    DetailedSegmentEffort,
    ExplorerSegment,
    Lap,
    LatLng,
    PhotosSummary,
    PolylineMap,
    Primary,
    Route,
    Split,
    SummaryPRSegmentEffort,
    SummarySegmentEffort,
    TimedZoneRange,
)

LOGGER = logging.getLogger(__name__)


def lazy_property(fn):
    """
    Should be used to decorate the functions that return a lazily loaded
    entity (collection), e.g., the members of a club.

    Assumes that fn (like a regular getter property) has as single
    argument a reference to self, and uses one of the (bound) client
    methods to retrieve an entity (collection) by self.id.
    """

    @wraps(fn)
    def wrapper(obj):
        try:
            if obj.bound_client is None:
                raise exc.UnboundEntity(
                    f"Unable to fetch objects for unbound {obj.__class__} entity."
                )
            if obj.id is None:
                LOGGER.warning(
                    f"Cannot retrieve {obj.__class__}.{fn.__name__}, self.id is None"
                )
                return None
            return fn(obj)
        except AttributeError as e:
            raise exc.UnboundEntity(
                f"Unable to fetch objects for unbound {obj.__class__} entity: {e}"
            )

    return property(wrapper)


# Custom validators for some edge cases:


def check_valid_location(
    location: Optional[Union[List[float], str]]
) -> Optional[List[float]]:
    """
    Parameters
    ----------
    location : list of float
        Either a list of x,y floating point values or strings or None
        (The legacy serialized format is str)

    Returns
    --------
    list or None
        Either returns a list of floating point values representing location
        x,y data or None if empty list is returned from the API.

    Raises
    ------
    AttributeError
        If empty list is returned, raises AttributeError

    """

    # Legacy serialized form is str, so in case of attempting to de-serialize
    # from local storage:
    try:
        return [float(l) for l in location.split(",")]
    except AttributeError:
        # Location for activities without GPS may be returned as empty list by
        # Strava
        return location if location else None


def naive_datetime(value: Optional[Any]) -> Optional[datetime]:
    if value:
        dt = parse_datetime(value)
        return dt.replace(tzinfo=None)
    else:
        return None


class DeprecatedSerializableMixin(BaseModel):
    """
    Provides backward compatibility with legacy BaseEntity
    """

    @classmethod
    def deserialize(cls, attribute_value_mapping: Dict):
        """
        Creates and returns a new object based on serialized (dict) struct.
        """
        warn_method_deprecation(
            cls,
            "deserialize()",
            "parse_obj()",
            "https://docs.pydantic.dev/usage/models/#helper-functions",
        )
        return cls.parse_obj(attribute_value_mapping)

    def from_dict(self, attribute_value_mapping: Dict):
        """
        Deserializes v into self, resetting and ond/or overwriting existing fields
        """
        warn_method_deprecation(
            self.__class__.__name__,
            "from_dict()",
            "parse_obj()",
            "https://docs.pydantic.dev/usage/models/#helper-functions",
        )
        # Ugly hack is necessary because parse_obj does not behave in-place but returns a new object
        self.__init__(**self.parse_obj(attribute_value_mapping).dict())

    def to_dict(self):
        """
        Returns a dict representation of self
        """
        warn_method_deprecation(
            self.__class__.__name__,
            "to_dict()",
            "dict()",
            "https://docs.pydantic.dev/usage/exporting_models/",
        )
        return self.dict()


class BackwardCompatibilityMixin:
    """
    Mixin that intercepts attribute lookup and raises warnings or modifies return values
    based on what is defined in the following class attributes:

    * _field_conversions
    * _deprecated_fields (TODO)
    * _unsupported_fields (TODO)
    """

    def __getattribute__(self, attr):
        value = object.__getattribute__(self, attr)
        if attr in ["_field_conversions", "bound_client"] or attr.startswith(
            "_"
        ):
            return value
        try:
            if attr in self._field_conversions:
                return self._field_conversions[attr](value)
        except AttributeError:
            # Current model class has no field conversions defined
            pass
        try:
            value.bound_client = self.bound_client
            return value
        except (AttributeError, ValueError):
            pass
        try:
            for v in value:
                v.bound_client = self.bound_client
            return value
        except (AttributeError, ValueError, TypeError):
            # TypeError if v is not iterable
            pass
        return value


class BoundClientEntity(BaseModel):
    # Using Any as type here to prevent catch-22 between circular import and
    # pydantic forward-referencing issues "resolved" by PEP-8 violations.
    # See e.g. https://github.com/pydantic/pydantic/issues/1873
    bound_client: Optional[Any] = Field(None, exclude=True)


class LatLon(LatLng, BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    Enables backward compatibility for legacy namedtuple
    """

    @root_validator
    def check_valid_latlng(cls, values):
        # Strava sometimes returns an empty list in case of activities without GPS
        return values if values else None

    @property
    def lat(self):
        return self.__root__[0]

    @property
    def lon(self):
        return self.__root__[1]


class Club(
    DetailedClub,
    DeprecatedSerializableMixin,
    BackwardCompatibilityMixin,
    BoundClientEntity,
):
    # Undocumented attributes:
    profile: Optional[str] = None
    description: Optional[str] = None
    club_type: Optional[str] = None

    _field_conversions = {"activity_types": enum_values}

    @lazy_property
    def members(self):
        return self.bound_client.get_club_members(self.id)

    @lazy_property
    def activities(self):
        return self.bound_client.get_club_activities(self.id)


class Gear(
    DetailedGear, DeprecatedSerializableMixin, BackwardCompatibilityMixin
):
    _field_conversions = {"distance": uh.meters}


class Bike(Gear):
    pass


class Shoe(Gear):
    pass


class ActivityTotals(
    ActivityTotal, DeprecatedSerializableMixin, BackwardCompatibilityMixin
):
    _field_conversions = {
        "elapsed_time": time_interval,
        "moving_time": time_interval,
        "distance": uh.meters,
        "elevation_gain": uh.meters,
    }


class AthleteStats(
    ActivityStats, DeprecatedSerializableMixin, BackwardCompatibilityMixin
):
    """
    Rolled-up totals for rides, runs and swims, as shown in an athlete's public
    profile. Non-public activities are not counted for these totals.
    """

    # field overrides from superclass for type extensions:
    recent_ride_totals: Optional[ActivityTotals] = None
    recent_run_totals: Optional[ActivityTotals] = None
    recent_swim_totals: Optional[ActivityTotals] = None
    ytd_ride_totals: Optional[ActivityTotals] = None
    ytd_run_totals: Optional[ActivityTotals] = None
    ytd_swim_totals: Optional[ActivityTotals] = None
    all_ride_totals: Optional[ActivityTotals] = None
    all_run_totals: Optional[ActivityTotals] = None
    all_swim_totals: Optional[ActivityTotals] = None

    _field_conversions = {
        "biggest_ride_distance": uh.meters,
        "biggest_climb_elevation_gain": uh.meters,
    }


class Athlete(
    DetailedAthlete,
    DeprecatedSerializableMixin,
    BackwardCompatibilityMixin,
    BoundClientEntity,
):
    # field overrides from superclass for type extensions:
    clubs: Optional[List[Club]] = None
    bikes: Optional[List[Bike]] = None
    shoes: Optional[List[Shoe]] = None

    # Undocumented attributes:
    is_authenticated: Optional[bool] = None
    athlete_type: Optional[int] = None
    friend: Optional[str] = None
    follower: Optional[str] = None
    approve_followers: Optional[bool] = None
    badge_type_id: Optional[int] = None
    mutual_friend_count: Optional[int] = None
    date_preference: Optional[str] = None
    email: Optional[str] = None
    super_user: Optional[bool] = None
    email_language: Optional[str] = None
    max_heartrate: Optional[float] = None
    username: Optional[str] = None
    description: Optional[str] = None
    instagram_username: Optional[str] = None
    offer_in_app_payment: Optional[bool] = None
    global_privacy: Optional[bool] = None
    receive_newsletter: Optional[bool] = None
    email_kom_lost: Optional[bool] = None
    dateofbirth: Optional[date] = None
    facebook_sharing_enabled: Optional[bool] = None
    profile_original: Optional[str] = None
    premium_expiration_date: Optional[int] = None
    email_send_follower_notices: Optional[bool] = None
    plan: Optional[str] = None
    agreed_to_terms: Optional[str] = None
    follower_request_count: Optional[int] = None
    email_facebook_twitter_friend_joins: Optional[bool] = None
    receive_kudos_emails: Optional[bool] = None
    receive_follower_feed_emails: Optional[bool] = None
    receive_comment_emails: Optional[bool] = None
    sample_race_distance: Optional[int] = None
    sample_race_time: Optional[int] = None
    membership: Optional[str] = None
    admin: Optional[bool] = None
    owner: Optional[bool] = None
    subscription_permissions: Optional[list] = None

    @validator("athlete_type")
    def to_str_representation(cls, raw_type):
        # Replaces legacy "ChoicesAttribute" class
        return {0: "cyclist", 1: "runner"}.get(raw_type)

    @lazy_property
    def authenticated_athlete(self):
        return self.bound_client.get_athlete()

    @lazy_property
    def stats(self):
        """
        Returns
        -------
        Associated :class:`stravalib.model.AthleteStats`
        """
        if not self.is_authenticated_athlete():
            raise exc.NotAuthenticatedAthlete(
                "Statistics are only available for the authenticated athlete"
            )
        return self.bound_client.get_athlete_stats(self.id)

    def is_authenticated_athlete(self):
        """
        Returns
        -------
        bool
            Whether the athlete is the authenticated athlete (or not).
        """

        if self.is_authenticated is None:
            if self.resource_state == 3:
                # If the athlete is in detailed state it must be the authenticated athlete
                self.is_authenticated = True
            else:
                # We need to check this athlete's id matches the authenticated athlete's id
                authenticated_athlete = self.authenticated_athlete
                self.is_authenticated = authenticated_athlete.id == self.id

        return self.is_authenticated


class ActivityComment(Comment):
    # Field overrides from superclass for type extensions:
    athlete: Optional[Athlete] = None


class ActivityPhotoPrimary(Primary):
    # Undocumented attributes:
    use_primary_photo: Optional[bool] = None


class ActivityPhotoMeta(PhotosSummary):
    """
    The photos structure returned with the activity, not to be confused with
    the full loaded photos for an activity.
    """

    # field overrides from superclass for type extensions:
    primary: Optional[ActivityPhotoPrimary] = None

    # Undocumented attributes:
    use_primary_photo: Optional[bool] = None


class ActivityPhoto(BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    A full photo record attached to an activity.
    Warning: this entity is undocumented by Strava and there is no official
    endpoint to retrieve it
    """

    athlete_id: Optional[int] = None
    activity_id: Optional[int] = None
    activity_name: Optional[str] = None
    ref: Optional[str] = None
    uid: Optional[str] = None
    unique_id: Optional[str] = None
    caption: Optional[str] = None
    type: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    created_at_local: Optional[datetime] = None
    location: Optional[LatLon] = None
    urls: Optional[Dict] = None
    sizes: Optional[Dict] = None
    post_id: Optional[int] = None
    default_photo: Optional[bool] = None
    source: Optional[int] = None

    _naive_local = validator("created_at_local", allow_reuse=True)(
        naive_datetime
    )
    _check_latlng = validator("location", allow_reuse=True, pre=True)(
        check_valid_location
    )

    def __repr__(self):
        if self.source == 1:
            photo_type = "native"
            idfield = "unique_id"
            idval = self.unique_id
        elif self.source == 2:
            photo_type = "instagram"
            idfield = "uid"
            idval = self.uid
        else:
            photo_type = "(no type)"
            idfield = "id"
            idval = self.id

        return "<{clz} {type} {idfield}={id}>".format(
            clz=self.__class__.__name__,
            type=photo_type,
            idfield=idfield,
            id=idval,
        )


class ActivityKudos(Athlete):
    """
    Activity kudos are a subset of athlete properties.
    """

    pass


class ActivityLap(
    Lap,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
    BoundClientEntity,
):
    # Field overrides from superclass for type extensions:
    activity: Optional[Activity] = None
    athlete: Optional[Athlete] = None

    # Undocumented attributes:
    average_watts: Optional[float] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    device_watts: Optional[bool] = None

    _field_conversions = {
        "elapsed_time": time_interval,
        "moving_time": time_interval,
        "distance": uh.meters,
        "total_elevation_gain": uh.meters,
        "average_speed": uh.meters_per_second,
        "max_speed": uh.meters_per_second,
    }

    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )


class Map(PolylineMap):
    pass


class Split(Split, BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    A split -- may be metric or standard units (which has no bearing
    on the units used in this object, just the binning of values).
    """

    # Undocumented attributes:
    average_heartrate: Optional[float] = None
    average_grade_adjusted_speed: Optional[float] = None

    _field_conversions = {
        "elapsed_time": time_interval,
        "moving_time": time_interval,
        "distance": uh.meters,
        "elevation_difference": uh.meters,
        "average_speed": uh.meters_per_second,
        "average_grade_adjusted_speed": uh.meters_per_second,
    }


class SegmentExplorerResult(
    ExplorerSegment,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
    BoundClientEntity,
):
    """
    Represents a segment result from the segment explorer feature.

    (These are not full segment objects, but the segment object can be fetched
    via the 'segment' property of this object.)
    """

    # Field overrides from superclass for type extensions:
    start_latlng: Optional[LatLon] = None
    end_latlng: Optional[LatLon] = None

    # Undocumented attributes:
    starred: Optional[bool] = None

    _field_conversions = {"elev_difference", uh.meters, "distance", uh.meters}

    _check_latlng = validator(
        "start_latlng", "end_latlng", allow_reuse=True, pre=True
    )(check_valid_location)

    @lazy_property
    def segment(self):
        """Associated (full) :class:`stravalib.model.Segment` object."""
        return self.bound_client.get_segment(self.id)


class AthleteSegmentStats(
    SummarySegmentEffort,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
):
    """
    A structure being returned for segment stats for current athlete.
    """

    # Undocumented attributes:
    effort_count: Optional[int] = None
    pr_elapsed_time: Optional[int] = None
    pr_date: Optional[date] = None

    _field_conversions = {
        "elapsed_time": time_interval,
        "pr_elapsed_time": time_interval,
        "distance": uh.meters,
    }

    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )


class AthletePrEffort(
    SummaryPRSegmentEffort,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
):
    # Undocumented attributes:
    distance: Optional[float] = None
    start_date: Optional[datetime] = None
    start_date_local: Optional[datetime] = None
    is_kom: Optional[bool] = None

    _field_conversions = {
        "pr_elapsed_time": time_interval,
        "distance": uh.meters,
    }

    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )

    @property
    def elapsed_time(self):
        # For backward compatibility
        return self.pr_elapsed_time


class Segment(
    DetailedSegment,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
    BoundClientEntity,
):
    """
    Represents a single Strava segment.
    """

    # field overrides from superclass for type extensions:
    start_latlng: Optional[LatLon] = None
    end_latlng: Optional[LatLon] = None
    map: Optional[Map] = None
    athlete_segment_stats: Optional[AthleteSegmentStats] = None
    athlete_pr_effort: Optional[AthletePrEffort] = None

    # Undocumented attributes:
    start_latitude: Optional[float] = None
    end_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_longitude: Optional[float] = None
    starred: Optional[bool] = None
    pr_time: Optional[int] = None
    starred_date: Optional[datetime] = None
    elevation_profile: Optional[str] = None

    _field_conversions = {
        "distance": uh.meters,
        "elevation_high": uh.meters,
        "elevation_low": uh.meters,
        "total_elevation_gain": uh.meters,
        "pr_time": time_interval,
    }

    _latlng_check = validator(
        "start_latlng", "end_latlng", allow_reuse=True, pre=True
    )(check_valid_location)


class SegmentEffortAchievement(BaseModel):
    """
    An undocumented structure being returned for segment efforts.
    """

    rank: Optional[int] = None
    """
    Rank in segment (either overall leaderboard, or pr rank)
    """

    type: Optional[str] = None
    """
    The type of achievement -- e.g. 'year_pr' or 'overall'
    """

    type_id: Optional[int] = None
    """
    Numeric ID for type of achievement?  (6 = year_pr, 2 = overall ??? other?)
    """

    effort_count: Optional[int] = None


class BaseEffort(
    DetailedSegmentEffort,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
    BoundClientEntity,
):
    """
    Base class for a best effort or segment effort.
    """

    # field overrides from superclass for type extensions:
    segment: Optional[Segment] = None
    activity: Optional[Activity] = None
    athlete: Optional[Athlete] = None

    _field_conversions = {
        "moving_time": time_interval,
        "elapsed_time": time_interval,
        "distance": uh.meters,
    }

    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )


class BestEffort(BaseEffort):
    """
    Class representing a best effort (e.g. best time for 5k)
    """


class SegmentEffort(BaseEffort):
    """
    Class representing a best effort on a particular segment.
    """

    achievements: Optional[List[SegmentEffortAchievement]] = None


class Activity(
    DetailedActivity,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
    BoundClientEntity,
):
    """
    Represents an activity (ride, run, etc.).
    """

    # field overrides from superclass for type extensions:
    athlete: Optional[Athlete] = None
    start_latlng: Optional[LatLon] = None
    end_latlng: Optional[LatLon] = None
    map: Optional[Map] = None
    gear: Optional[Gear] = None
    best_efforts: Optional[List[BestEffort]] = None
    segment_efforts: Optional[List[SegmentEffort]] = None
    splits_metric: Optional[List[Split]] = None
    splits_standard: Optional[List[Split]] = None
    photos: Optional[ActivityPhotoMeta] = None
    laps: Optional[List[ActivityLap]] = None

    # Added for backward compatibility
    # TODO maybe deprecate?
    TYPES: ClassVar[Tuple] = get_args(
        ActivityType.__fields__["__root__"].type_
    )

    # Undocumented attributes:
    guid: Optional[str] = None
    utc_offset: Optional[float] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    start_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    pr_count: Optional[int] = None
    suffer_score: Optional[int] = None
    has_heartrate: Optional[bool] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[int] = None
    average_cadence: Optional[float] = None
    average_temp: Optional[int] = None
    instagram_primary_photo: Optional[str] = None
    partner_logo_url: Optional[str] = None
    partner_brand_tag: Optional[str] = None
    from_accepted_tag: Optional[bool] = None
    segment_leaderboard_opt_out: Optional[bool] = None
    perceived_exertion: Optional[int] = None

    _field_conversions = {
        "moving_time": time_interval,
        "elapsed_time": time_interval,
        "timezone": timezone,
        "distance": uh.meters,
        "total_elevation_gain": uh.meters,
        "average_speed": uh.meters_per_second,
        "max_speed": uh.meters_per_second,
        "type": enum_value,
        "sport_type": enum_value,
    }

    _latlng_check = validator(
        "start_latlng", "end_latlng", allow_reuse=True, pre=True
    )(check_valid_location)
    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )

    @lazy_property
    def comments(self):
        return self.bound_client.get_activity_comments(self.id)

    @lazy_property
    def zones(self):
        return self.bound_client.get_activity_zones(self.id)

    @lazy_property
    def kudos(self):
        return self.bound_client.get_activity_kudos(self.id)

    @lazy_property
    def full_photos(self):
        return self.bound_client.get_activity_photos(
            self.id, only_instagram=False
        )


class DistributionBucket(TimedZoneRange):
    """
    A single distribution bucket object, used for activity zones.
    """

    _field_conversions = {"time": uh.seconds}


class BaseActivityZone(
    ActivityZone,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
    BoundClientEntity,
):
    """
    Base class for activity zones.

    A collection of :class:`stravalib.model.DistributionBucket` objects.
    """

    # field overrides from superclass for type extensions:
    distribution_buckets: Optional[List[DistributionBucket]] = None

    # overriding the superclass type: it should also support pace as value
    type: Optional[Literal["heartrate", "power", "pace"]] = None


class Stream(
    BaseStream, BackwardCompatibilityMixin, DeprecatedSerializableMixin
):
    """
    Stream of readings from the activity, effort or segment.
    """

    type: Optional[str] = None

    # Not using the typed subclasses from the generated model
    # for backward compatibility:
    data: Optional[List[Any]] = None


class Route(
    Route,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
    BoundClientEntity,
):
    """
    Represents a Route.
    """

    # Superclass field overrides for using extended types
    athlete: Optional[Athlete] = None
    map: Optional[Map] = None
    segments: Optional[List[Segment]]

    _field_conversions = {"distance": uh.meters, "elevation_gain": uh.meters}


class Subscription(
    BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity
):
    """
    Represents a Webhook Event Subscription.
    """

    OBJECT_TYPE_ACTIVITY: ClassVar[str] = "activity"
    ASPECT_TYPE_CREATE: ClassVar[str] = "create"
    VERIFY_TOKEN_DEFAULT: ClassVar[str] = "STRAVA"

    id: Optional[int] = None
    application_id: Optional[int] = None
    object_type: Optional[str] = None
    aspect_type: Optional[str] = None
    callback_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SubscriptionCallback(
    BackwardCompatibilityMixin, DeprecatedSerializableMixin
):
    """
    Represents a Webhook Event Subscription Callback.
    """

    hub_mode: Optional[str] = None
    hub_verify_token: Optional[str] = None
    hub_challenge: Optional[str] = None

    class Config:
        alias_generator = lambda field_name: field_name.replace("hub_", "hub.")

    def validate(self, verify_token=Subscription.VERIFY_TOKEN_DEFAULT):
        assert self.hub_verify_token == verify_token


class SubscriptionUpdate(
    BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity
):
    """
    Represents a Webhook Event Subscription Update.
    """

    subscription_id: Optional[int] = None
    owner_id: Optional[int] = None
    object_id: Optional[int] = None
    object_type: Optional[str] = None
    aspect_type: Optional[str] = None
    event_time: Optional[datetime] = None
    updates: Optional[Dict] = None


SegmentEffort.update_forward_refs()
ActivityLap.update_forward_refs()
BestEffort.update_forward_refs()
