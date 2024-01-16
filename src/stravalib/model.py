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
from datetime import date, datetime, timedelta
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Literal,
    Optional,
    TypeVar,
    Union,
    get_args,
)

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.datetime_parse import parse_datetime
from typing_extensions import Self

from stravalib import exc, strava_model
from stravalib import unithelper as uh
from stravalib.field_conversions import (
    enum_value,
    enum_values,
    timezone,
)
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
    SportType,
    SummaryClub,
    SummaryGear,
    SummaryPRSegmentEffort,
    SummarySegmentEffort,
    TimedZoneRange,
)
from stravalib.strava_model import Route as RouteStrava

if TYPE_CHECKING:
    from stravalib.client import BatchedResultsIterator

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U", bound="BoundClientEntity")


def lazy_property(fn: Callable[[U], T]) -> Optional[T]:
    """
    Should be used to decorate the functions that return a lazily loaded
    entity (collection), e.g., the members of a club.

    Parameters
    ----------
    fn : Callable
        The input function that returns the lazily loaded entity (collection).

    Returns
    -------
    property
        A lazily loaded property.

    Raises
    ------
    exc.UnboundEntity
        If the object is unbound (self.bound_client is None) or has a None ID (self.id is None).

    Notes
    -----
    Assumes that fn (like a regular getter property) has as single
    argument a reference to self, and uses one of the (bound) client
    methods to retrieve an entity (collection) by self.id.

    """

    @wraps(fn)
    def wrapper(obj: U) -> Optional[T]:
        try:
            if obj.bound_client is None:
                raise exc.UnboundEntity(
                    f"Unable to fetch objects for unbound {obj.__class__} entity."
                )
            if obj.id is None:  # type: ignore[attr-defined]
                LOGGER.warning(
                    f"Cannot retrieve {obj.__class__}.{fn.__name__}, self.id is None"
                )
                return None
            return fn(obj)
        except AttributeError as e:
            raise exc.UnboundEntity(
                f"Unable to fetch objects for unbound {obj.__class__} entity: {e}"
            )

    return property(wrapper)  # type: ignore[return-value]


# Custom validators for some edge cases:


def check_valid_location(
    location: Optional[Union[list[float], str]]
) -> Optional[list[float]]:
    """
    Parameters
    ----------
    location : list of floats
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
    if isinstance(location, str):
        try:
            return [float(l) for l in location.split(",")]
        except AttributeError:
            # Location for activities without GPS may be returned as empty list by
            # Strava
            return None
    else:
        return location if location else None


# Create alias for this type so docs are more readable
AllDateTypes = Union[datetime, str, bytes, int, float]


def naive_datetime(value: Optional[AllDateTypes]) -> Optional[datetime]:
    """Utility helper that parses a datetime value provided in
    JSON, string, int or other formats and returns a datetime.datetime
    object

    Parameters
    ----------
    value : str, int
        A value representing a date/time that may be presented in string,
        int, deserialized or other format.

    Returns
    -------
    datetime.datetime
        A datetime object representing the datetime input value.
    """
    if value:
        dt = parse_datetime(value)
        return dt.replace(tzinfo=None)
    else:
        return None


class DeprecatedSerializableMixin(BaseModel):
    """
    Provides backward compatibility with legacy BaseEntity

    Inherits from the `pydantic.BaseModel` class.
    """

    @classmethod
    def deserialize(cls, attribute_value_mapping: dict[str, Any]) -> Self:
        """
        Creates and returns a new object based on serialized (dict) struct.

        Parameters
        ----------
        attribute_value_mapping : dict
            A dictionary representing the serialized data.

        Returns
        -------
        DeprecatedSerializableMixin
            A new instance of the class created from the serialized data.

        Deprecated
        ----------
        1.0.0
            The `deserialize()` method is deprecated in favor of `parse_obj()` method.
            For more details, refer to the Pydantic documentation:
            https://docs.pydantic.dev/usage/models/#helper-functions


        """
        exc.warn_method_deprecation(
            cls,
            "deserialize()",
            "parse_obj()",
            "https://docs.pydantic.dev/usage/models/#helper-functions",
        )
        return cls.parse_obj(attribute_value_mapping)

    def from_dict(self, attribute_value_mapping: dict[str, Any]) -> None:
        """
        Deserializes v into self, resetting and/or overwriting existing
        fields.

        Parameters
        ----------
        attribute_value_mapping : dict
            A dictionary that will be deserialized into the parent object.

        Deprecated
        ----------
        1.0.0
            The `from_dict()` method is deprecated in favor of `parse_obj()` method.
            For more details, refer to the Pydantic documentation:
            https://docs.pydantic.dev/usage/models/#helper-functions
        """

        exc.warn_method_deprecation(
            self.__class__,
            "from_dict()",
            "parse_obj()",
            "https://docs.pydantic.dev/usage/models/#helper-functions",
        )
        # Ugly hack is necessary because parse_obj does not behave in-place but
        # returns a new object
        self.__init__(**self.parse_obj(attribute_value_mapping).dict())  # type: ignore[misc]

    def to_dict(self) -> dict[str, Any]:
        """
        Returns a dict representation of self

        Returns
        -------
        dict
            A dictionary containing the data from the instance.

        Deprecated
        ----------
            The `to_dict()` method is deprecated in favor of `dict()` method.
            For more details, refer to the Pydantic documentation:
            https://docs.pydantic.dev/1.10/usage/exporting_models/
        """
        exc.warn_method_deprecation(
            self.__class__,
            "to_dict()",
            "dict()",
            "https://docs.pydantic.dev/1.10/usage/exporting_models/",
        )
        return self.dict()


class BackwardCompatibilityMixin:
    """
    Mixin that intercepts attribute lookup and raises warnings or modifies
    return values based on what is defined in the following class attributes:

    * _field_conversions
    * _deprecated_fields (TODO)
    * _unsupported_fields (TODO)
    """

    pass

    def __getattribute__(self, attr: str) -> Any:
        """A method to retrieve attributes from the object.

        Parameters
        ----------
        attr : str
            The name of the attribute to retrieve.

        Returns
        -------
        Any
            The value of the requested attribute.

        Notes
        -----
        This method is called whenever an attribute is accessed on the object.
        It is used to control attribute retrieval and perform additional
        actions.

        """
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
    """A class that bounds the Client object to the model."""

    # Using Any as type here to prevent catch-22 between circular import and
    # Pydantic forward-referencing issues "resolved" by PEP-8 violations.
    # See e.g. https://github.com/pydantic/pydantic/issues/1873
    bound_client: Optional[Any] = Field(None, exclude=True)


class RelaxedActivityType(ActivityType):
    @root_validator(pre=True)
    def check_activity_type(cls, values: dict[str, Any]) -> dict[str, Any]:
        v = values["__root__"]
        if v not in get_args(ActivityType.__fields__["__root__"].type_):
            LOGGER.warning(
                f'Unexpected activity type. Given={v}, replacing by "Workout"'
            )
            values["__root__"] = "Workout"
        return values


class RelaxedSportType(SportType):
    @root_validator(pre=True)
    def check_sport_type(cls, values: dict[str, Any]) -> dict[str, Any]:
        v = values["__root__"]
        if v not in get_args(SportType.__fields__["__root__"].type_):
            LOGGER.warning(
                f'Unexpected sport type. Given={v}, replacing by "Workout"'
            )
            values["__root__"] = "Workout"
        return values


class LatLon(LatLng, BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """
    Enables backward compatibility for legacy namedtuple
    """

    # TODO: stravalib/model.py:377: error: Incompatible return value type (got "Optional[List[Optional[float]]]", expected "Optional[List[float]]")  [return-value]
    # this error doesn't make sense as the types are correct based on what the
    # error says it wants to see. so why is it throwing the error?
    @root_validator
    def check_valid_latlng(cls, values: list[float]) -> Optional[list[float]]:
        """Validate that Strava returned an actual lat/lon rather than an empty
        list. If list is empty, return None

        Parameters
        ----------
        values: list
            The list of lat/lon values returned by Strava. This list will be
            empty if there was no GPS associated with the activity.

        Returns
        -------
        list or None
            list of lat/lon values or None

        """
        # Strava sometimes returns empty list in case of activities without GPS
        return values if values else None

    @property
    def lat(self) -> float:
        """
        The latitude value of an x,y coordinate.

        Returns
        -------
        float
            The latitude value.
        """
        return self.__root__[0]

    @property
    def lon(self) -> float:
        """
        The longitude value of an x,y coordinate.

        Returns
        -------
        float
            The longitude value.
        """
        return self.__root__[1]


class Club(
    DetailedClub,
    DeprecatedSerializableMixin,
    BackwardCompatibilityMixin,
    BoundClientEntity,
):
    """
    Represents a single club with detailed information about the club including
    club name, id, location, activity types, etc.

    See Also
    --------
    DetailedClub : A class representing a club's detailed information.
    DeprecatedSerializableMixin : A mixin to provide backward compatibility
        with legacy BaseEntity.
    BackwardCompatibilityMixin : A mixin to provide backward compatibility with
        legacy BaseDetailedEntity.
    BoundClientEntity : A mixin to bind the club with a Strava API client.

    """

    # Undocumented attributes:
    profile: Optional[str] = None
    description: Optional[str] = None
    club_type: Optional[str] = None

    _field_conversions = {"activity_types": enum_values}

    @lazy_property
    def members(self) -> BatchedResultsIterator[Athlete]:
        """
        Lazy property to retrieve club members stored as Athlete objects.

        Returns
        -------
        list
            A list of club members stored as Athlete objects.
        """
        assert self.bound_client is not None, "Bound client is not set."
        return self.bound_client.get_club_members(self.id)

    @lazy_property
    def activities(self) -> BatchedResultsIterator[Activity]:
        """
        Lazy property to retrieve club activities.

        Returns
        -------
        Iterator
            An iterator of Activity objects representing club activities.
        """
        assert self.bound_client is not None, "Bound client is not set."
        return self.bound_client.get_club_activities(self.id)


class Gear(
    DetailedGear, DeprecatedSerializableMixin, BackwardCompatibilityMixin
):
    """
    Represents a piece of gear (equipment) used in physical activities.
    """

    _field_conversions = {"distance": uh.meters}


class Bike(Gear):
    """
    Represents a bike as a "type" / using the structure of
    `stravalib.model.Gear`.
    """

    pass


class Shoe(Gear):
    """
    Represents a Shoes as a "type" / using the structure of
    `stravalib.model.Gear`.
    """

    pass


class ActivityTotals(
    ActivityTotal, DeprecatedSerializableMixin, BackwardCompatibilityMixin
):
    """An objecting containing a set of total values for an activity including
    elapsed time, moving time, distance and elevation gain."""

    _field_conversions = {
        "distance": uh.meters,
        "elevation_gain": uh.meters,
    }
    elapsed_time: Optional[timedelta] = None  # type: ignore[assignment]
    moving_time: Optional[timedelta] = None  # type: ignore[assignment]


class AthleteStats(
    ActivityStats, DeprecatedSerializableMixin, BackwardCompatibilityMixin
):
    """
    Summary totals for rides, runs and swims, as shown in an athlete's public
    profile. Non-public activities are not counted for these totals.
    """

    # Field overrides from superclass for type extensions:
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
    """Represents high level athlete information including
    their name, email, clubs they belong to, bikes, shoes, etc.

    Notes
    ------
    Also provides access to detailed athlete stats upon request.
    """

    # Field overrides from superclass for type extensions:
    clubs: Optional[list[SummaryClub]] = None
    bikes: Optional[list[SummaryGear]] = None
    shoes: Optional[list[SummaryGear]] = None

    # Undocumented attributes:
    is_authenticated: Optional[bool] = None
    athlete_type: Optional[Literal["cyclist", "runner"]] = None
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
    subscription_permissions: Optional[list[bool]] = None

    @validator("athlete_type", pre=True)
    def to_str_representation(
        cls, raw_type: int
    ) -> Optional[Literal["cyclist", "runner"]]:
        """Replaces legacy 'ChoicesAttribute' class.

        Parameters
        ----------
        raw_type : int
            The raw integer representing the athlete type.

        Returns
        -------
        str
            The string representation of the athlete type.
        """

        if raw_type == 0:
            return "cyclist"
        elif raw_type == 1:
            return "runner"
        else:
            LOGGER.warning(f"Unknown athlete type value: {raw_type}")
            return None

    @lazy_property
    def authenticated_athlete(self) -> Athlete:
        """
        Returns an `Athlete` object containing Strava account data
        for the (authenticated) athlete.

        Returns
        -------
        Athlete
            The detailed information of the authenticated athlete.
        """
        assert self.bound_client is not None, "Bound client is not set."
        return self.bound_client.get_athlete()

    @lazy_property
    def stats(self) -> AthleteStats:
        """
        Grabs statistics for an (authenticated) athlete.

        Returns
        -------
        Associated :class:`stravalib.model.AthleteStats`

        Raises
        ------
        `stravalib.exc.NotAuthenticatedAthlete` exception if authentication is
        missing.
        """
        if not self.is_authenticated_athlete():
            raise exc.NotAuthenticatedAthlete(
                "Statistics are only available for the authenticated athlete"
            )
        assert self.bound_client is not None, "Bound client is not set."

        return self.bound_client.get_athlete_stats(self.id)

    def is_authenticated_athlete(self) -> bool:
        """Check if the athlete is authenticated

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
                if authenticated_athlete is None:
                    return False

                self.is_authenticated = authenticated_athlete.id == self.id

        return self.is_authenticated


# TODO: better description
class ActivityComment(Comment):
    """Field overrides the athlete attribute to be of type :class:`Athlete`
    rather than :class:`SummaryAthlete`
    """

    athlete: Optional[Athlete] = None


class ActivityPhotoPrimary(Primary):
    """Represents the primary photo for an activity.

    Notes
    -----
    Attributes for activity photos are undocumented
    """

    use_primary_photo: Optional[bool] = None


class ActivityPhotoMeta(PhotosSummary):
    """The photos structure returned with the activity. Not to be confused with
    the full loaded photos for an activity.
    """

    # Field overrides from superclass for type extensions:
    primary: Optional[ActivityPhotoPrimary] = None

    # Undocumented attributes:
    use_primary_photo: Optional[bool] = None


class ActivityPhoto(BackwardCompatibilityMixin, DeprecatedSerializableMixin):
    """A full photo record attached to an activity.

    Notes
    -----
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
    urls: Optional[dict[str, str]] = None
    sizes: Optional[dict[str, list[int]]] = None
    post_id: Optional[int] = None
    default_photo: Optional[bool] = None
    source: Optional[int] = None

    _naive_local = validator("created_at_local", allow_reuse=True)(
        naive_datetime
    )
    _check_latlng = validator("location", allow_reuse=True, pre=True)(
        check_valid_location
    )

    def __repr__(self) -> str:
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
    Represents kudos an athlete received on an activity.

    Notes
    -----
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
        "distance": uh.meters,
        "total_elevation_gain": uh.meters,
        "average_speed": uh.meters_per_second,
        "max_speed": uh.meters_per_second,
    }
    elapsed_time: Optional[timedelta] = None  # type: ignore[assignment]
    moving_time: Optional[timedelta] = None  # type: ignore[assignment]

    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )


class Map(PolylineMap):
    """Pass through object. Inherits from PolyLineMap"""

    pass


class Split(
    strava_model.Split,
    BackwardCompatibilityMixin,
    DeprecatedSerializableMixin,
):
    """
    A split -- may be metric or standard units (which has no bearing
    on the units used in this object, just the binning of values).
    """

    # Undocumented attributes:
    average_heartrate: Optional[float] = None
    average_grade_adjusted_speed: Optional[float] = None

    _field_conversions = {
        "distance": uh.meters,
        "elevation_difference": uh.meters,
        "average_speed": uh.meters_per_second,
        "average_grade_adjusted_speed": uh.meters_per_second,
    }
    elapsed_time: Optional[timedelta] = None  # type: ignore[assignment]
    moving_time: Optional[timedelta] = None  # type: ignore[assignment]


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
    def segment(self) -> Segment:
        """Returns the associated (full) :class:`Segment` object.

        This property is lazy-loaded. Segment objects will be fetched from
        the bound client only when explicitly accessed for the first time.

        Returns
        -------
        Segment object or None
            The associated Segment object, if available; otherwise, returns None.

        """
        assert self.bound_client is not None
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
    pr_elapsed_time: Optional[timedelta] = None
    pr_date: Optional[date] = None

    _field_conversions = {
        "distance": uh.meters,
    }
    elapsed_time: Optional[timedelta] = None  # type: ignore[assignment]

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
        "distance": uh.meters,
    }
    pr_elapsed_time: Optional[timedelta] = None  # type: ignore[assignment]

    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )

    @property
    def elapsed_time(self) -> Optional[timedelta]:
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

    # Field overrides from superclass for type extensions:
    start_latlng: Optional[LatLon] = None
    end_latlng: Optional[LatLon] = None
    map: Optional[Map] = None
    athlete_segment_stats: Optional[AthleteSegmentStats] = None
    athlete_pr_effort: Optional[AthletePrEffort] = None
    activity_type: Optional[RelaxedActivityType] = None  # type: ignore[assignment]

    # Undocumented attributes:
    start_latitude: Optional[float] = None
    end_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_longitude: Optional[float] = None
    starred: Optional[bool] = None
    pr_time: Optional[timedelta] = None
    starred_date: Optional[datetime] = None
    elevation_profile: Optional[str] = None

    _field_conversions = {
        "distance": uh.meters,
        "elevation_high": uh.meters,
        "elevation_low": uh.meters,
        "total_elevation_gain": uh.meters,
        "activity_type": enum_value,
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
    Rank in segment (either overall leader board, or pr rank)
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

    # Field overrides from superclass for type extensions:
    segment: Optional[Segment] = None
    activity: Optional[Activity] = None
    athlete: Optional[Athlete] = None

    _field_conversions = {
        "distance": uh.meters,
    }
    moving_time: Optional[timedelta] = None  # type: ignore[assignment]
    elapsed_time: Optional[timedelta] = None  # type: ignore[assignment]

    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )


class BestEffort(BaseEffort):
    """
    Class representing a best effort (e.g. best time for 5k)
    """

    pass


class SegmentEffort(BaseEffort):
    """
    Class representing a best effort on a particular segment.
    """

    achievements: Optional[list[SegmentEffortAchievement]] = None


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
    type: Optional[RelaxedActivityType] = None
    sport_type: Optional[RelaxedSportType] = None
    # Ignoring types here given there are overrides
    best_efforts: Optional[list[BestEffort]] = None  # type: ignore[assignment]
    segment_efforts: Optional[list[SegmentEffort]] = None  # type: ignore[assignment]
    splits_metric: Optional[list[Split]] = None  # type: ignore[assignment]
    splits_standard: Optional[list[Split]] = None  # type: ignore[assignment]
    photos: Optional[ActivityPhotoMeta] = None
    laps: Optional[list[Lap]] = None

    # Added for backward compatibility
    # TODO maybe deprecate?
    TYPES: ClassVar[tuple[Any, ...]] = get_args(
        ActivityType.__fields__["__root__"].type_
    )

    # TODO this and line 1055 above changed from str to Any
    SPORT_TYPES: ClassVar[tuple[Any, ...]] = get_args(
        SportType.__fields__["__root__"].type_
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
        "timezone": timezone,
        "distance": uh.meters,
        "total_elevation_gain": uh.meters,
        "average_speed": uh.meters_per_second,
        "max_speed": uh.meters_per_second,
        "type": enum_value,
        "sport_type": enum_value,
    }
    moving_time: Optional[timedelta] = None  # type: ignore[assignment]
    elapsed_time: Optional[timedelta] = None  # type: ignore[assignment]

    _latlng_check = validator(
        "start_latlng", "end_latlng", allow_reuse=True, pre=True
    )(check_valid_location)
    _naive_local = validator("start_date_local", allow_reuse=True)(
        naive_datetime
    )

    @lazy_property
    def comments(self) -> BatchedResultsIterator[ActivityComment]:
        assert self.bound_client is not None
        return self.bound_client.get_activity_comments(self.id)

    @lazy_property
    def zones(self) -> list[BaseActivityZone]:
        """Retrieve a list of zones for an activity.

        Returns
        -------
        py:class:`list`
            A list of :class:`stravalib.model.BaseActivityZone` objects.
        """

        assert self.bound_client is not None
        return self.bound_client.get_activity_zones(self.id)

    @lazy_property
    def kudos(self) -> BatchedResultsIterator[ActivityKudos]:
        assert self.bound_client is not None
        return self.bound_client.get_activity_kudos(self.id)

    @lazy_property
    def full_photos(self) -> BatchedResultsIterator[ActivityPhoto]:
        assert self.bound_client is not None
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

    # Field overrides from superclass for type extensions:
    # Using type that is currently mimicking legacy behavior...
    distribution_buckets: Optional[list[DistributionBucket]] = None  # type: ignore[assignment]

    # TODO: ignoring type given legacy support will be deprecated
    type: Optional[Literal["heartrate", "power", "pace"]] = None  # type: ignore[assignment]


class Stream(
    BaseStream, BackwardCompatibilityMixin, DeprecatedSerializableMixin
):
    """
    Stream of readings from the activity, effort or segment.
    """

    type: Optional[str] = None

    # Not using the typed subclasses from the generated model
    # for backward compatibility:
    data: Optional[list[Any]] = None


class Route(
    RouteStrava,
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
    segments: Optional[list[Segment]]  # type: ignore[assignment]

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

    hub_mode: Optional[str] = Field(None, alias="hub.mode")
    hub_verify_token: Optional[str] = Field(None, alias="hub.verify_token")
    hub_challenge: Optional[str] = Field(None, alias="hub.challenge")

    def validate_token(
        self, verify_token: str = Subscription.VERIFY_TOKEN_DEFAULT
    ) -> None:
        """
        Validate the subscription's hub_verify_token against the provided
        token.

        Parameters
        ----------
        verify_token : str
            The token to verify subscription
            If not provided, it uses the default `VERIFY_TOKEN_DEFAULT`.

        Returns
        -------
        None
            None if an assertion error is not raised

        Raises
        ------
        AssertionError
            If the hub_verify_token does not match the provided verify_token.
        """
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
    updates: Optional[dict[str, Any]] = None


SegmentEffort.update_forward_refs()
ActivityLap.update_forward_refs()
BestEffort.update_forward_refs()
