"""
Model
==============
Entity classes for representing the various Strava datatypes.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from functools import wraps
from typing import Any, ClassVar, Dict, List, Literal, Optional, Tuple, Type, Union

from pydantic import BaseModel, root_validator, validator
from pydantic.datetime_parse import parse_datetime

from stravalib import exc
from stravalib import unithelper as uh
from stravalib.exc import warn_method_deprecation
from stravalib.field_conversions import enum_values, time_interval, timezone
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
                LOGGER.warning(f'Cannot retrieve {obj.__class__}.{fn.__name__}, self.id is None')
                return None
            return fn(obj)
        except AttributeError as e:
            raise exc.UnboundEntity(
                f"Unable to fetch objects for unbound {obj.__class__} entity: {e}"
            )

    return property(wrapper)


def extend_types(
        *args,
        model_class: Union[Type[BaseModel], str]=None,
        as_collection: bool=False,
        **kwargs
):
    """
    Returns a reusable pydantic validator for parsing optional nested
    structures into a desired destination class `model_class`.
    """

    if model_class is None:
        raise ValueError('This validator should be provided with a destination class')

    def extender(serialized_value: Optional[Any]):
        if isinstance(model_class, str):
            klass = getattr(sys.modules[__name__], model_class)
        else:
            klass = model_class
        if serialized_value is not None:
            if as_collection:
                return [klass.parse_obj(v) for v in serialized_value]
            else:
                return klass.parse_obj(serialized_value)
        else:
            return None
    return validator(*args, **kwargs, allow_reuse=True, pre=True)(extender)


# Custom validators for some edge cases:

def check_valid_location(location: Optional[List[float]]) -> Optional[List[float]]:
    # location for activities without GPS may be returned as empty list
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
    * _deprecated_fields (TODO)
    * _unsupported_fields (TODO)
    * _field_conversions
    """

    def __getattribute__(self, attr):
        value = object.__getattribute__(self, attr)
        if attr in ["_field_conversions", "bound_client"] or attr.startswith('_'):
            return value
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
        try:
            if attr in self._field_conversions:
                return self._field_conversions[attr](value)
        except AttributeError:
            # Current model class has no field conversions defined
            pass
        return value


class BoundClientEntity(BaseModel):
    # Using Any as type here to prevent catch-22 between circular import and
    # pydantic forward-referencing issues "resolved" by PEP-8 violations.
    # See e.g. https://github.com/pydantic/pydantic/issues/1873
    bound_client: Optional[Any] = None


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
    pass


class ActivityTotals(
    ActivityTotal, DeprecatedSerializableMixin, BackwardCompatibilityMixin
):
    _field_conversions = {
        "elapsed_time": time_interval,
        "moving_time": time_interval,
        "distance": uh.meters,
        "elevation_gain": uh.meters
    }


class AthleteStats(
    ActivityStats, DeprecatedSerializableMixin, BackwardCompatibilityMixin
):
    """
    Rolled-up totals for rides, runs and swims, as shown in an athlete's public
    profile. Non-public activities are not counted for these totals.
    """

    _field_conversions = {
        "biggest_ride_distance": uh.meters,
        "biggest_climb_elevation_gain": uh.meters,
    }

    _activity_total_extensions = extend_types(
        "recent_ride_totals",
        "recent_run_totals",
        "recent_swim_totals",
        "ytd_ride_totals",
        "ytd_run_totals",
        "ytd_swim_totals",
        "all_ride_totals",
        "all_run_totals",
        "all_swim_totals",
        model_class=ActivityTotals
    )


class Athlete(
    DetailedAthlete, DeprecatedSerializableMixin, BackwardCompatibilityMixin, BoundClientEntity
):
    is_authenticated: Optional[bool] = None
    athlete_type: Optional[int] = None

    _clubs_extension = extend_types('clubs', model_class=Club, as_collection=True)
    _gear_extension = extend_types('bikes', 'shoes', model_class=Gear, as_collection=True)

    @validator('athlete_type')
    def to_str_representation(cls, raw_type):
        # Replaces legacy "ChoicesAttribute" class
        return {0: "cyclist", 1: "runner"}.get(raw_type)

    @lazy_property
    def authenticated_athlete(self):
        return self.bound_client.get_athlete()

    @lazy_property
    def stats(self):
        """
        :return: Associated :class:`stravalib.model.AthleteStats`
        """
        if not self.is_authenticated_athlete():
            raise exc.NotAuthenticatedAthlete("Statistics are only available for the authenticated athlete")
        return self.bound_client.get_athlete_stats(self.id)


    def is_authenticated_athlete(self):
        """
        :return: Boolean as to whether the athlete is the authenticated athlete.
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
    _athlete_extension = extend_types('athlete', model_class=Athlete)


class ActivityPhotoPrimary(Primary):
    pass


class ActivityPhotoMeta(PhotosSummary):
    """
    The photos structure returned with the activity, not to be confused with the full loaded photos for an activity.
    """

    _primary_extension = extend_types('primary', model_class=ActivityPhotoPrimary)


class ActivityPhoto(BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    A full photo record attached to an activity.
    Warning: this entity is undocumented by Strava and there is no official endpoint to retrieve it
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

    _naive_local = validator('created_at_local', allow_reuse=True)(naive_datetime)

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


class ActivityLap(Lap, BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    _field_conversions = {
        'elapsed_time': time_interval,
        'moving_time': time_interval,
        'distance': uh.meters,
        'total_elevation_gain': uh.meters,
        'average_speed': uh.meters_per_second,
        'max_speed': uh.meters_per_second
    }

    _naive_local = validator('start_date_local', allow_reuse=True)(naive_datetime)

    _activity_extension = extend_types('activity', model_class='Activity')
    _athlete_extension = extend_types('athlete', model_class=Athlete)


class Map(PolylineMap):
    pass


class Split(Split, BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    A split -- may be metric or standard units (which has no bearing
    on the units used in this object, just the binning of values).
    """

    _field_conversions = {
        'elapsed_time': time_interval,
        'moving_time': time_interval,
        'distance': uh.meters,
        'elevation_difference': uh.meters,
        'average_speed': uh.meters_per_second
    }


class SegmentExplorerResult(
    ExplorerSegment, BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity
):
    """
    Represents a segment result from the segment explorer feature.

    (These are not full segment objects, but the segment object can be fetched
    via the 'segment' property of this object.)
    """

    _field_conversions = {
        'elev_difference', uh.meters,
        'distance', uh.meters
    }

    _latlng_extensions = extend_types('start_latlng', 'end_latlng', model_class='LatLon')

    @lazy_property
    def segment(self):
        """Associated (full) :class:`stravalib.model.Segment` object."""
        return self.bound_client.get_segment(self.id)


class AthleteSegmentStats(SummarySegmentEffort, BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    A structure being returned for segment stats for current athlete.
    """

    _field_conversions = {'pr_elapsed_time': time_interval}


class AthletePrEffort(SummaryPRSegmentEffort, BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    _field_conversions = {'pr_elapsed_time': time_interval}

    @property
    def elapsed_time(self):
        # for backward compatibility
        return self.pr_elapsed_time


class Segment(DetailedSegment, BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity):
    """
    Represents a single Strava segment.
    """

    _field_conversions = {
        'distance': uh.meters,
        'elevation_high': uh.meters,
        'elevation_low': uh.meters,
        'total_elevation_gain': uh.meters
    }

    _latlng_check = validator('start_latlng', 'end_latlng', allow_reuse=True, pre=True)(check_valid_location)

    _latlng_extensions = extend_types('start_latlng', 'end_latlng', model_class=LatLon)
    _map_extensions = extend_types('map', model_class=Map)
    _segment_stat_extension = extend_types('athlete_segment_stats', model_class=AthleteSegmentStats)
    _pr_effort_extension = extend_types('athlete_pr_effort', model_class=AthletePrEffort)


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


class BaseEffort(DetailedSegmentEffort, BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity):
    """
    Base class for a best effort or segment effort.
    """

    _field_conversions = {
        'moving_time': time_interval,
        'elapsed_time': time_interval,
        'distance': uh.meters
    }

    _naive_local = validator('start_date_local', allow_reuse=True)(naive_datetime)

    _segment_extension = extend_types('segment', model_class=Segment)
    _activity_extension = extend_types('activity', model_class='Activity')  # Prevents unresolved reference
    _athlete_extension = extend_types('athlete', model_class=Athlete)


class BestEffort(BaseEffort):
    """
    Class representing a best effort (e.g. best time for 5k)
    """


class SegmentEffort(BaseEffort):
    """
    Class representing a best effort on a particular segment.
    """

    achievements: Optional[List[SegmentEffortAchievement]] = None


class Activity(DetailedActivity, BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity):
    """
    Represents an activity (ride, run, etc.).
    """

    _field_conversions = {
        'moving_time': time_interval,
        'elapsed_time': time_interval,
        'timezone': timezone,
        'distance': uh.meters,
        'total_elevation_gain': uh.meters,
        'average_speed': uh.meters_per_second,
        'max_speed': uh.meters_per_second

    }

    _latlng_check = validator('start_latlng', 'end_latlng', allow_reuse=True, pre=True)(check_valid_location)
    _naive_local = validator('start_date_local', allow_reuse=True)(naive_datetime)

    _athlete_extension = extend_types('athlete', model_class=Athlete)
    _latlng_extension = extend_types('start_latlng', 'end_latlng', model_class=LatLon)
    _map_extension = extend_types('map', model_class=Map)
    _gear_extension = extend_types('gear', model_class=Gear)
    _best_effort_extension = extend_types('best_efforts', model_class=BestEffort, as_collection=True)
    _segment_effort_extension = extend_types('segment_efforts', model_class=SegmentEffort, as_collection=True)
    _splits_extension = extend_types('splits_metric', 'splits_standard', model_class=Split, as_collection=True)
    _photos_extension = extend_types('photos', model_class=ActivityPhotoMeta)
    _laps_extension = extend_types('laps', model_class=ActivityLap, as_collection=True)

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

    # Added for backward compatibility
    # TODO maybe deprecate?
    TYPES: ClassVar[Tuple] = tuple(t.value for t in ActivityType)


class DistributionBucket(TimedZoneRange):
    """
    A single distribution bucket object, used for activity zones.
    """

    _field_conversions = {'time': uh.seconds}


class BaseActivityZone(ActivityZone, BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity):
    """
    Base class for activity zones.

    A collection of :class:`stravalib.model.DistributionBucket` objects.
    """

    # overriding the superclass type: it should also support pace as value
    type: Optional[Literal["heartrate", "power", "pace"]] = None

    _distribution_extension = extend_types(
        'distribution_buckets', model_class=DistributionBucket, as_collection=True
    )


class Stream(BaseStream, BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    Stream of readings from the activity, effort or segment.
    """

    type: Optional[str] = None

    # Not using the typed subclasses from the generated model
    # for backward compatibility:
    data: Optional[List[Any]] = None


class Route(Route, BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity):
    """
    Represents a Route.
    """

    # Superclass field overrides for using extended types
    athlete: Optional[Athlete] = None
    map: Optional[Map] = None
    segments: Optional[List[Segment]]

    _field_conversions = {
        'distance': uh.meters,
        'elevation_gain': uh.meters
    }


class Subscription(BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity):
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


class SubscriptionCallback(BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    Represents a Webhook Event Subscription Callback.
    """

    hub_mode: Optional[str] = None
    hub_verify_token: Optional[str] = None
    hub_challenge: Optional[str] = None

    class Config:
        alias_generator = lambda field_name: field_name.replace('hub_', 'hub.')

    def validate(self, verify_token=Subscription.VERIFY_TOKEN_DEFAULT):
        assert self.hub_verify_token == verify_token


class SubscriptionUpdate(BackwardCompatibilityMixin, DeprecatedSerializableMixin, BoundClientEntity):
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
