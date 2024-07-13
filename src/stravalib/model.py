"""
==============================
Model Functions and Classes
==============================
This module contains entity classes that represent the various Strava
datatypes, such as `Activity`, `Gear`, and more. These entities inherit
fields from superclasses in `strava_model.py`, which is generated from
the official Strava API specification. The classes in this module add
behavior such as type enrichment, unit conversion, and lazy loading
related entities from the API.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    ClassVar,
    Generic,
    Literal,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
)

import pytz
from dateutil import parser
from dateutil.parser import ParserError
from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    field_validator,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from pytz import UnknownTimeZoneError

from stravalib import exc, strava_model
from stravalib.strava_model import (
    ActivityType,
    BaseStream,
    Comment,
    ExplorerSegment,
    LatLng,
    PolylineMap,
    SportType,
    SummaryGear,
)
from stravalib.unit_helper import _Quantity

if TYPE_CHECKING:
    from stravalib.client import BatchedResultsIterator

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U", bound="BoundClientEntity")


# Create alias for this type so docs are more readable
AllDateTypes = Union[
    datetime,
    str,
    bytes,
    int,
    float,
]


# Could naive_datetime also be run in a validator?
def naive_datetime(value: Optional[AllDateTypes]) -> Optional[datetime]:
    """Utility helper that parses a datetime value provided in
    JSON, string, int or other formats and returns a datetime.datetime
    object.

    Parameters
    ----------
    value : str, int
        A value representing a date/time that may be presented in string,
        int, deserialized or other format.

    Returns
    -------
    datetime.datetime
        A datetime object representing the datetime input value.

    Notes
    -----
    Valid str, following formats work (from pydantic docs):

    YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        # If epoch is given, we have to assume it's UTC. When using the
        # regular fromtimestamp(), epoch will be interpreted as in the
        # _local_ timezone.
        dt = datetime.utcfromtimestamp(value)
        return dt.replace(tzinfo=None)
    elif isinstance(value, str):
        try:
            dt = parser.parse(value)
            return dt.replace(tzinfo=None)
        except ParserError:
            # Maybe timestamp was passed as string, e.g '1714305600'?
            try:
                dt = datetime.utcfromtimestamp(float(value))
                return dt.replace(tzinfo=None)
            except ValueError:
                LOGGER.error(f"Invalid datetime value: {value}")
                raise
    elif isinstance(value, datetime):
        return value.replace(tzinfo=None)
    else:
        raise ValueError(f"Unsupported value type: {type(value)}")


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


# This method checks a list of floats - ie a stream not just a single lat/lon
def check_valid_location(
    location: Optional[Union[Sequence[float], str]]
) -> Optional[list[float]]:
    """
    Validate a list of location xy values.

    Converts a list of floating point values stored as strings to floats and
    returns either a list of floats or None if no location data is found.
    This function is used to validate LatLon object inputs

    Parameters
    ----------
    location : List of floats
        Either a List of x,y floating point values or strings or None
        (The legacy serialized format is str)

    Returns
    --------
    List or None
        Either returns a List of floating point values representing location
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
            # Location for activities without GPS may be returned as empty list
            return None
    # Because this could be any Sequence type, explicitly return list
    elif location:
        return list(location)
    else:
        return None


# Custom types:

BaseType = TypeVar("BaseType")
CustomType = TypeVar("CustomType")


class _CustomTypeAnnotation(Generic[BaseType, CustomType], ABC):
    _type: Type[CustomType]

    @classmethod
    @abstractmethod
    def validate(cls, value: BaseType) -> CustomType: ...

    @classmethod
    @abstractmethod
    def get_core_schema(cls) -> Mapping[str, Any]: ...

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: BaseType,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        from_schema = core_schema.chain_schema(
            [
                cls.get_core_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(cls._type), from_schema]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: v
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return handler(cls.get_core_schema())


class _CustomIntAnnotation(_CustomTypeAnnotation[int, Any], ABC):
    @classmethod
    def get_core_schema(cls) -> Mapping[str, Any]:
        return core_schema.int_schema()


class _CustomFloatAnnotation(_CustomTypeAnnotation[float, Any], ABC):
    @classmethod
    def get_core_schema(cls) -> Mapping[str, Any]:
        return core_schema.float_schema()


class _CustomStrAnnotation(_CustomTypeAnnotation[str, Any], ABC):
    @classmethod
    def get_core_schema(cls) -> Mapping[str, Any]:
        return core_schema.str_schema()


class Duration(int):
    """
    A class that calculates the duration or time elapsed for an activity,
    activity segment, or activity lap.

    This class extends the built-in `int` class to represent durations in
    seconds and provides a method to convert this duration to a
    `datetime.timedelta` object.

    Methods
    -------
    timedelta() -> timedelta
        Converts the duration to a `datetime.timedelta` object.

    Examples
    --------

    >>> activity = client.get_activity(11416949675)
    >>> activity.elapsed_time
    3214
    >>> activity.elapsed_time.timedelta()
    datetime.timedelta(seconds=3214)
    """

    def timedelta(self) -> timedelta:
        """
        Converts the duration to a `datetime.timedelta` object.

        Returns
        -------
        timedelta
            A `datetime.timedelta` object representing the duration in
            seconds.
        """

        return timedelta(seconds=float(self))


class _DurationAnnotation(_CustomIntAnnotation):
    _type = Duration

    @classmethod
    def validate(cls, value: int) -> Duration:
        return Duration(value)


class Timezone(str):
    """A class to represent and manipulate time zone information.

    This class extends the built-in `str` class to include a method
    for converting the time zone string to a pytz time zone object.

    Methods
    -------
    timezone() -> pytz._UTCclass | pytz.tzinfo.StaticTzInfo | pytz.tzinfo.DstTzInfo | None
        Converts the time zone string to a pytz time zone object.

    Examples
    --------

    >>> activity = client.get_activity(11416949675)
    >>> activity.timezone
    '(GMT+01:00) Europe/Amsterdam'
    >>> activity.timezone.timezone()
    <DstTzInfo 'Europe/Amsterdam' LMT+0:18:00 STD>
    """

    def timezone(
        self,
    ) -> (
        pytz._UTCclass
        | pytz.tzinfo.StaticTzInfo
        | pytz.tzinfo.DstTzInfo
        | None
    ):
        """
        Converts the time zone string to a pytz time zone object.

        This method attempts to convert the time zone string, which can
        either be in the format "(GMT-08:00) America/Los_Angeles" or
        "America/Los_Angeles", to a corresponding pytz time zone object.

        Returns
        -------
        pytz._UTCclass, pytz.tzinfo.StaticTzInfo, `pytz.tzinfo.DstTzInfo`, or
        `None`The corresponding `pytz` time zone object if the time zone string is
        recognized, otherwise `None`.

        Raises
        ------
        `UnknownTimeZoneError`
            If the time zone string is not recognized.
        """
        if " " in self:
            # (GMT-08:00) America/Los_Angeles
            tzname = self.split(" ", 1)[1]
        else:
            # America/Los_Angeles
            tzname = self
        try:
            return pytz.timezone(tzname)
        except UnknownTimeZoneError as e:
            LOGGER.warning(
                f"Encountered unknown time zone {tzname}, returning None"
            )
            return None


class _TimezoneAnnotation(_CustomStrAnnotation):
    _type = Timezone

    @classmethod
    def validate(cls, value: str) -> Timezone:
        return Timezone(value)


class Distance(_Quantity):
    """A class for representing distances as quantities (using meter as unit, which is the implicit default of Strava). These quantities can then
    be converted to other units such as feet or meters using the
    `stravalib.unit_helper` module.

    Examples
    ----------
    Once you have distance in meters, you can then use the unit_helper
    module to convert to other units such as feet

    >>> from stravalib import unit_helper
    >>> activity = client.get_activity(11416949675)
    >>> activity.distance
    8055.9
    >>> activity.distance.quantity()
    <Quantity(8055.9, 'meter')>
    >>>  unit_helper.feet(activity.distance)
    <Quantity(26430.1181, 'foot')>
    >>> unit_helper.miles(activity.distance)
    <Quantity(5.00570419, 'mile')>
    >>> unit_helper.miles(activity.distance).magnitude
    5.00570419
    """

    unit = "meters"


class _DistanceAnnotation(_CustomFloatAnnotation):
    _type = Distance

    @classmethod
    def validate(cls, value: float) -> Distance:
        return Distance(value)


class Velocity(_Quantity):
    """
    A class for representing velocities as quantities (using meters per second as unit, which is the implicit default of Strava). These quantities can then
        be converted to other units such as km/h or mph using the
        `stravalib.unit_helper` module.

    Examples
    --------

    >>> from stravalib import unit_helper
    >>> activity = client.get_activity(11854593990)
    >>> activity.average_speed
    3.53
    >>> activity.average_speed.quantity()
    <Quantity(3.53, 'meter / second')>
    >>> unit_helper.miles_per_hour(activity.average_speed)
    <Quantity(7.89638511, 'mile / hour')>
    >>> unit_helper.miles_per_hour(activity.average_speed).magnitude
    7.896385110952039
    """

    unit = "meters/second"


class _VelocityAnnotation(_CustomFloatAnnotation):
    _type = Velocity

    @classmethod
    def validate(cls, value: float) -> Velocity:
        return Velocity(value)


DurationType = Annotated[Duration, _DurationAnnotation]
DistanceType = Annotated[Distance, _DistanceAnnotation]
VelocityType = Annotated[Velocity, _VelocityAnnotation]
TimezoneType = Annotated[Timezone, _TimezoneAnnotation]


class BoundClientEntity(BaseModel):
    """A class that bounds the Client object to the model."""

    # Using Any as type here to prevent catch-22 between circular import and
    # Pydantic forward-referencing issues "resolved" by PEP-8 violations.
    # See e.g. https://github.com/pydantic/pydantic/issues/1873
    bound_client: Optional[Any] = Field(None, exclude=True)


class RelaxedActivityType(ActivityType):
    """This object supports allowing an array of Literal values to be used for
    Activity Type. by default, the generated `strava_model` module only allows
    a Literal that includes types: `Ride` and `Run`.
    """

    @model_validator(mode="before")
    def check_activity_type(cls, values: str) -> str:
        """Pydantic validator that checks whether an activity type value is
        valid prior to populating the model. If the available activity type
        is not valid, it assigns the value to be "Workout".

        Parameters
        ----------
        values : str
            A dictionary containing an activity type key value pair.

        Returns
        -------
        str
            A dictionary with a validated activity type value assigned.
        """

        if values not in get_args(
            ActivityType.model_fields["root"].annotation
        ):
            LOGGER.warning(
                f'Unexpected activity type. Given={values}, replacing by "Workout"'
            )
            values = "Workout"
        return values


class RelaxedSportType(SportType):
    """A class that extends the list of Literal values allowed for Sport Types
    that are defined in the generated `strava_model` module.
    """

    @model_validator(mode="before")
    def check_sport_type(cls, values: str) -> str:
        """Pydantic validator that checks whether a sport type value is
        valid prior to populating the model. If the existing sport type
        is not valid, it assigns the value to be "Workout".

        Parameters
        ----------
        values : str
            A dictionary containing an sport type key value pair.

        Returns
        -------
        str
            A str containing the validated sport type.
        """

        if values not in SportType.__annotations__["root"]:
            LOGGER.warning(
                f'Unexpected sport type. Given={values}, replacing by "Workout"'
            )
            values = "Workout"
        return values


class LatLon(LatLng):
    """Stores lat / lon values or None."""

    @model_validator(mode="before")
    def check_valid_latlng(cls, values: Sequence[float]) -> list[float] | None:
        """Validate that Strava returned an actual lat/lon rather than an empty
        list. If list is empty, return None

        Parameters
        ----------
        values: List
            The list of lat/lon values returned by Strava. This list will be
            empty if there was no GPS associated with the activity.

        Returns
        -------
        List or None
            list of lat/lon values or None

        """

        # Strava sometimes returns empty list in case of activities without GPS
        # Explicitly return a list to make mypy happy
        if values:
            return list(values)
        else:
            return None

    @property
    def lat(self) -> float:
        """The latitude value of an x,y coordinate.

        Returns
        -------
        float
            The latitude value.
        """
        return self.root[0]

    @property
    def lon(self) -> float:
        """
        The longitude value of an x,y coordinate.

        Returns
        -------
        float
            The longitude value.
        """
        return self.root[1]


class MetaClub(strava_model.MetaClub, BoundClientEntity):
    """
    Represents an identifiable club with lazily loaded properties to obtain
    this club's members and activities.
    """

    @lazy_property
    def members(self) -> BatchedResultsIterator[strava_model.ClubAthlete]:
        """
        Lazy property to retrieve club members stored as Athlete objects.

        Returns
        -------
        List
            A list of club members stored as Athlete objects.
        """
        assert self.bound_client is not None, "Bound client is not set."
        return self.bound_client.get_club_members(self.id)

    @lazy_property
    def activities(self) -> BatchedResultsIterator[ClubActivity]:
        """
        Lazy property to retrieve club activities.

        Returns
        -------
        Iterator
            An iterator of Activity objects representing club activities.
        """
        assert self.bound_client is not None, "Bound client is not set."
        return self.bound_client.get_club_activities(self.id)


class SummaryClub(MetaClub, strava_model.SummaryClub):
    """
    Represents a single club with detailed information about the club including
    the club's location, activity types, etc.

    See Also
    --------
    DetailedClub : A class representing a club's detailed information.

    Notes
    -----
    Clubs are the only object that can have multiple valid
    `activity_types`. Activities only have one.

    Endpoint docs are found here:
    https://developers.strava.com/docs/reference/#api-models-SummaryClub


    """

    # Undocumented attributes:
    profile: Optional[str] = None
    description: Optional[str] = None
    club_type: Optional[str] = None


class DetailedClub(SummaryClub, strava_model.DetailedClub):
    """The detailed club object contains all of the club data available to
    the authenticated Athlete."""

    ...


class ActivityTotals(strava_model.ActivityTotal):
    """Contains a set of total values for an activity including
    elapsed time, moving time, distance and elevation gain.
    """

    # Attribute overrides for custom types:
    distance: Optional[DistanceType] = None
    elevation_gain: Optional[DistanceType] = None
    elapsed_time: Optional[DurationType] = None
    moving_time: Optional[DurationType] = None


class AthleteStats(strava_model.ActivityStats):
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
    biggest_ride_distance: Optional[DistanceType] = None
    biggest_climb_elevation_gain: Optional[DistanceType] = None


class MetaAthlete(strava_model.MetaAthlete, BoundClientEntity):
    """
    Represents an identifiable athlete with lazily loaded property to obtain
    this athlete's summary stats.
    """

    # Undocumented
    resource_state: Optional[int] = None

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

        assert self.bound_client is not None, "Bound client is not set."
        return self.bound_client.get_athlete_stats(self.id)


class SummaryAthlete(MetaAthlete, strava_model.SummaryAthlete):
    """The Summary Athlete object. This is redefined here to inherit the
    `BoundClient` which allows API access for lazy methods."""

    ...


class DetailedAthlete(SummaryAthlete, strava_model.DetailedAthlete):
    """Represents high level athlete information including
    their name, email, clubs they belong to, bikes, shoes, etc.

    Notes
    ------
    Also provides access to detailed athlete stats upon request.
    Many attributes in this object are undocumented by Strava and could be
    modified at any time.
    """

    # Field overrides from superclass for type extensions:
    clubs: Optional[Sequence[SummaryClub]] = None

    # Undocumented attributes:
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
    """Indicates if the athlete has admin privileges."""
    owner: Optional[bool] = None
    subscription_permissions: Optional[Sequence[bool]] = None

    @field_validator("athlete_type", mode="before")
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


class ActivityPhotoPrimary(strava_model.Primary):
    """
    Represents the primary photo for an activity.

    Attributes
    ----------
    use_primary_photo : bool, optional
        Indicates whether the photo is used as the primary photo.

    Notes
    -----
    https://developers.strava.com/docs/reference/#api-models-PhotosSummary_primary
    This object is not returned in strava_model, but it is documented in the
    Strava API V3 spec. The Spec documentation deviates from what is actually
    returned. This model represents what is actually returned.
    """

    # Strava_model has this defined as id but unique_id is the correct attr name
    # it's also defined as an int but should be a string
    unique_id: str | None
    media_type: int | None = None


class PhotosSummary(strava_model.PhotosSummary):
    """
    Represents the metadata of photos returned with the activity.

    Not to be confused with the fully loaded photos for an activity.

    Attributes
    ----------

    primary : ActivityPhoto_primary, optional
        The primary photo for the activity.
    use_primary_photo : bool, optional
        Indicates whether the primary photo is used. Not currently documented
        by Strava.

    Notes
    -----
    Undocumented attributes could be changed by Strava at any time.
    THe API spec specifies that this object returns count and
    ActivityPhoto_primary

    https://developers.strava.com/docs/reference/#api-models-PhotosSummary
    """

    primary: Optional[ActivityPhotoPrimary] = None

    # Undocumented by strava
    use_primary_photo: Optional[bool] = None


class ActivityPhoto(BaseModel):
    """A full photo record attached to an activity.

    Notes
    -----
    Warning: this entity is undocumented by Strava and there is no official
    endpoint to retrieve it
    """

    activity_id: Optional[int] = None
    activity_name: Optional[str] = None
    athlete_id: Optional[int] = None
    caption: Optional[str] = None
    created_at: Optional[datetime] = None
    created_at_local: Optional[datetime] = None
    default_photo: Optional[bool] = None
    location: Optional[LatLon] = None
    post_id: Optional[int] = None
    sizes: Optional[dict[str, Sequence[int]]] = None
    source: Optional[int] = None
    type: Optional[int] = None
    unique_id: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    urls: Optional[dict[str, str]] = None

    # TODO: i don't see these in the actual returns but they are used below
    ref: Optional[str] = None
    uid: Optional[str] = None

    _naive_local = field_validator("created_at_local")(naive_datetime)
    _check_latlng = field_validator("location", mode="before")(
        check_valid_location
    )

    def __repr__(self) -> str:
        """Return a string representation of the instance.

        This representation varies according to the source of the photo (native,
        from Instagram, or an unknown source. This representation includes the
        class name, photo type, and a key identifier."""
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
            idval = self.uid

        return "<{clz} {type} {idfield}={id}>".format(
            clz=self.__class__.__name__,
            type=photo_type,
            idfield=idfield,
            id=idval,
        )


class Lap(
    strava_model.Lap,
    BoundClientEntity,
):
    """An object that represents an Activity lap.

    This object inherits the BoundClient to support API access through lazy
    methods.

    """

    # Field overrides from superclass for type extensions:
    activity: Optional[MetaActivity] = None
    athlete: Optional[MetaAthlete] = None
    distance: Optional[DistanceType] = None
    total_elevation_gain: Optional[DistanceType] = None
    elapsed_time: Optional[DurationType] = None
    moving_time: Optional[DurationType] = None
    average_speed: Optional[VelocityType] = None
    max_speed: Optional[VelocityType] = None

    # Undocumented attributes:
    average_watts: Optional[float] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    device_watts: Optional[bool] = None

    _naive_local = field_validator("start_date_local")(naive_datetime)


class Map(PolylineMap):
    """Pass through object. Inherits from PolyLineMap"""

    pass


class Split(
    strava_model.Split,
):
    """
    A split -- may be metric or standard units (which has no bearing
    on the units used in this object, just the binning of values).
    """

    # Attribute overrides for type extensions:
    distance: Optional[DistanceType] = None
    elevation_difference: Optional[DistanceType] = None
    elapsed_time: Optional[DurationType] = None
    moving_time: Optional[DurationType] = None
    average_speed: Optional[VelocityType] = None

    # Undocumented attributes:
    average_heartrate: Optional[float] = None
    average_grade_adjusted_speed: Optional[VelocityType] = None


class SegmentExplorerResult(
    ExplorerSegment,
    BoundClientEntity,
):
    """Represents a segment result from the segment explorer feature.

    Notes
    -----
    These do not represent full segment objects. The segment object can be
    fetched using the 'segment' property of this object.
    """

    # Field overrides from superclass for type extensions:
    elev_difference: Optional[DistanceType] = None
    distance: Optional[DistanceType] = None
    start_latlng: Optional[LatLon] = None
    end_latlng: Optional[LatLon] = None

    # Undocumented attributes:
    starred: Optional[bool] = None

    _check_latlng = field_validator(
        "start_latlng", "end_latlng", mode="before"
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


class AthletePrEffort(
    strava_model.SummaryPRSegmentEffort,
):
    """An object that holds athlete PR effort attributes."""

    # Override fields from superclass to match actual responses by Strava API:
    activity_id: Optional[int] = Field(
        validation_alias=AliasChoices("pr_activity_id", "activity_id"),
        default=None,
    )
    elapsed_time: Optional[int] = Field(
        validation_alias=AliasChoices("pr_elapsed_time", "elapsed_time"),
        default=None,
    )

    # Attribute overrides for type extensions:
    pr_elapsed_time: Optional[DurationType] = None

    # Undocumented attributes:
    distance: Optional[DistanceType] = None
    start_date: Optional[datetime] = None
    start_date_local: Optional[datetime] = None
    is_kom: Optional[bool] = None

    _naive_local = field_validator("start_date_local")(naive_datetime)


class SummarySegment(strava_model.SummarySegment, BoundClientEntity):
    """Contains summary information for a specific segment

    Notes
    -----
    Several attributes represent overrides from the superclass to support
    accurate typing.
    """

    # Field overrides from superclass for type extensions:
    start_latlng: Optional[LatLon] = None
    end_latlng: Optional[LatLon] = None
    athlete_pr_effort: Optional[AthletePrEffort] = None
    # Ignore because the spec is incorrectly typed - Optional[Literal["Ride", "Run"]]
    activity_type: Optional[RelaxedActivityType] = None  # type: ignore[assignment]
    athlete_segment_stats: Optional[AthleteSegmentStats] = (
        None  # Actually, this is only part of a (detailed) segment response
    )

    _latlng_check = field_validator(
        "start_latlng", "end_latlng", mode="before"
    )(check_valid_location)


class Segment(SummarySegment, strava_model.DetailedSegment):
    """
    Represents a single Strava segment.
    """

    # Field overrides from superclass for type extensions:
    map: Optional[Map] = None
    distance: Optional[DistanceType] = None
    elevation_high: Optional[DistanceType] = None
    elevation_low: Optional[DistanceType] = None
    total_elevation_gain: Optional[DistanceType] = None

    # Undocumented attributes:
    start_latitude: Optional[float] = None
    end_latitude: Optional[float] = None
    start_longitude: Optional[float] = None
    end_longitude: Optional[float] = None
    starred: Optional[bool] = None
    pr_time: Optional[timedelta] = None
    starred_date: Optional[datetime] = None
    elevation_profile: Optional[str] = None


class SegmentEffortAchievement(BaseModel):
    """
    An undocumented structure being returned for segment efforts.

    Notes
    -----
    Undocumented Strava elements can change at any time without notice.
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


class SummarySegmentEffort(strava_model.SummarySegmentEffort):
    """Returns summary information for a segment in an activity."""

    # Override superclass fields to match actual Strava API responses
    activity_id: Optional[int] = Field(
        validation_alias=AliasChoices("pr_activity_id", "activity_id"),
        default=None,
    )
    elapsed_time: Optional[int] = Field(
        validation_alias=AliasChoices("pr_elapsed_time", "elapsed_time"),
        default=None,
    )

    _naive_local = field_validator("start_date_local")(naive_datetime)


class BaseEffort(
    SummarySegmentEffort,
    strava_model.DetailedSegmentEffort,
):
    """Base class for a best effort or segment effort."""

    # Field overrides from superclass for type extensions:
    segment: Optional[SummarySegment] = None
    activity: Optional[MetaActivity] = None
    athlete: Optional[MetaAthlete] = None
    elapsed_time: Optional[DurationType] = None
    moving_time: Optional[DurationType] = None
    distance: Optional[DistanceType] = None


class BestEffort(BaseEffort):
    """Class representing a best effort (e.g. best time for 5k)"""

    pass


class SegmentEffort(BaseEffort):
    """Class representing a best effort on a particular segment."""

    achievements: Optional[Sequence[SegmentEffortAchievement]] = None


class AthleteSegmentStats(
    SummarySegmentEffort,
):
    """
    A structure being returned for segment stats for current athlete.
    """

    # Attribute overrides for type extensions:
    distance: Optional[DistanceType] = None
    elapsed_time: Optional[DurationType] = None

    # Undocumented attributes:
    effort_count: Optional[int] = None
    pr_date: Optional[date] = None


class MetaActivity(strava_model.MetaActivity, BoundClientEntity):
    """
    Represents an identifiable activity with lazily loaded properties to
    collect this activity's comments, zones, kudos and photos.
    """

    @lazy_property
    def comments(self) -> BatchedResultsIterator[Comment]:
        """Retrieves comments for a specific activity id."""
        assert self.bound_client is not None
        return self.bound_client.get_activity_comments(self.id)

    @lazy_property
    def zones(self) -> list[ActivityZone]:
        """Retrieve a list of zones for an activity.

        Returns
        -------
        list
            A list of :class:`stravalib.model.ActivityZone` objects.
        """

        assert self.bound_client is not None
        return self.bound_client.get_activity_zones(self.id)

    @lazy_property
    def kudos(self) -> BatchedResultsIterator[SummaryAthlete]:
        """Retrieves the kudos provided for a specific activity."""
        assert self.bound_client is not None
        return self.bound_client.get_activity_kudos(self.id)

    @lazy_property
    def full_photos(self) -> BatchedResultsIterator[ActivityPhoto]:
        """Retrieves activity photos for a specific activity by id."""
        assert self.bound_client is not None
        return self.bound_client.get_activity_photos(
            self.id, only_instagram=False
        )


class SummaryActivity(MetaActivity, strava_model.SummaryActivity):
    """The Activity object that contains high level summary activity for an
    activity.

    Notes
    -----
    In the case that the Strava spec is misaligned with the data actually
    returned, we override attributes as needed.

    """

    # field overrides from superclass for type extensions:
    athlete: Optional[MetaAthlete] = None
    # These force validator to run on lat/lon
    start_latlng: Optional[LatLon] = None
    end_latlng: Optional[LatLon] = None
    map: Optional[Map] = None
    type: Optional[RelaxedActivityType] = None
    sport_type: Optional[RelaxedSportType] = None

    _latlng_check = field_validator(
        "start_latlng", "end_latlng", mode="before"
    )(check_valid_location)


class DetailedActivity(
    SummaryActivity,
    strava_model.DetailedActivity,
):
    """
    Represents an activity (ride, run, etc.).
    """

    # Field overrides from superclass for type extensions:
    distance: Optional[DistanceType] = None
    total_elevation_gain: Optional[DistanceType] = None
    gear: Optional[SummaryGear] = None
    best_efforts: Optional[Sequence[BestEffort]] = None
    # TODO: returning empty Sequence should be  DetailedSegmentEffort object
    # TODO: test on activity with actual segments
    segment_efforts: Optional[Sequence[SegmentEffort]] = None
    # TODO: Returns Split object - check returns for that object
    splits_metric: Optional[Sequence[Split]] = None
    splits_standard: Optional[Sequence[Split]] = None
    photos: Optional[PhotosSummary] = None
    laps: Optional[Sequence[Lap]] = None
    elapsed_time: Optional[DurationType] = None
    moving_time: Optional[DurationType] = None
    average_speed: Optional[VelocityType] = None
    max_speed: Optional[VelocityType] = None
    timezone: Optional[TimezoneType] = None

    # Added for backward compatibility
    # TODO maybe deprecate?
    TYPES: ClassVar[tuple[Any, ...]] = get_args(
        ActivityType.model_fields["root"].annotation
    )

    SPORT_TYPES: ClassVar[tuple[Any, ...]] = get_args(
        SportType.model_fields["root"].annotation
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
    prefer_perceived_exertion: Optional[bool] = None
    visibility: Optional[str] = None
    private_note: Optional[str] = None

    _naive_local = field_validator("start_date_local")(naive_datetime)


class ClubActivity(strava_model.ClubActivity):
    """Represents an activity returned from a club.

    Notes
    -----
    The Strava API specification suggests that this should
    return a `MetaAthlete` Object for the athlete associated with this activity.
    However, the object spec is missing what is actually returned,
    i.e., resource_state, first name, and last initial.
    This object matches the actual return data, not the spec.
    """

    # Intentional class override as spec returns metaAthlete object
    # (which only contains id)
    athlete: Optional[strava_model.ClubAthlete] = None  # type: ignore[assignment]


class TimedZoneDistribution(strava_model.TimedZoneRange):
    """
    A single distribution bucket object, used for activity zones.

    Notes
    -----
    Min/max value types are overridden. The
    Strava API incorrectly types zones as being `int`. However it can
    return `int` or `float` (floats are returned for pace, ints for heartrate
    and power).
    """

    # Type overrides to support pace values returned as ints
    min: float | None = None  # type: ignore[assignment]
    max: float | None = None  # type: ignore[assignment]


class ActivityZone(
    strava_model.ActivityZone,
    BoundClientEntity,
):
    """
    Base class for activity zones.

    A collection of :class:`stravalib.strava_model.TimedZoneDistribution` objects.
    """

    # Field overrides from superclass for type extensions:
    distribution_buckets: Optional[Sequence[TimedZoneDistribution]] = None  # type: ignore[assignment]

    # strava_model only contains heartrate and power (ints), but also returns pace (float)
    type: Optional[Literal["heartrate", "power", "pace"]] = None  # type: ignore[assignment]


class Stream(BaseStream):
    """Stream of readings from the activity, effort or segment."""

    type: Optional[str] = None

    # Not using the typed subclasses from the generated model
    # for backward compatibility:
    data: Optional[Sequence[Any]] = None


class Route(
    strava_model.Route,
    BoundClientEntity,
):
    """Represents a spatial route created by an athlete."""

    # Superclass field overrides for using extended types
    distance: Optional[DistanceType] = None
    elevation_gain: Optional[DistanceType] = None
    athlete: Optional[SummaryAthlete] = None
    map: Optional[Map] = None
    segments: Optional[Sequence[SummarySegment]] = None


class Subscription(BaseModel):
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


class SubscriptionCallback(BaseModel):
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


class SubscriptionUpdate(BaseModel):
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
