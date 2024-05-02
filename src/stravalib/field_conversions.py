from __future__ import annotations

import logging
from collections.abc import Sequence
from functools import wraps
from typing import Callable, TypeVar

import pytz
from pytz.exceptions import UnknownTimeZoneError

from stravalib.strava_model import ActivityType, SportType

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


def optional_input(
    field_conversion_fn: Callable[[T], U]
) -> Callable[[T | None], U | None]:
    """
    Transform a one argument function to make the input optional.

    When None is passed as argument the wrapped function return None.
    """

    @wraps(field_conversion_fn)
    def fn_wrapper(field_value: T | None) -> U | None:
        if field_value is not None:
            return field_conversion_fn(field_value)
        else:
            return None

    return fn_wrapper


@optional_input
def enum_value(v: ActivityType | SportType) -> str:
    """A method that collects the root value of a Activity or
    SportType object.

    We may not need this method if pydantic 2.x supports lists

    Parameters
    ----------
    v : ActivityType | SportType
        An object of type ActivityType or SportType that contains a single
        sport or activity type value.

    Returns
    -------
    str
        The type value associated with the activity.
    """
    try:
        return v.root
    except AttributeError:
        LOGGER.warning(
            f"{v} is not an enum, returning itself instead of its value"
        )
        return v  # type: ignore[return-value]


@optional_input
def enum_values(enums: Sequence[ActivityType | SportType]) -> list[str | None]:
    """A function that processes multiple enums and returns a list.

    Parameters
    ----------
    enums : Sequence[ActivityType | SportType]
        A sport or activity type object (RootModel base).

    Returns
    -------
    list[str | None]
        A list of valid sport or activity types

    Notes
    -----
    # Pydantic (1.x) has config for using enum values, but unfortunately
    # it doesn't work for lists of enums.
    # See https://github.com/pydantic/pydantic/issues/5005

    TODO - look up pydantic 2.0 handling lists of enums
    """
    return [enum_value(e) for e in enums]


@optional_input
def timezone(
    tz: str,
) -> pytz._UTCclass | pytz.tzinfo.StaticTzInfo | pytz.tzinfo.DstTzInfo | None:
    if " " in tz:
        # (GMT-08:00) America/Los_Angeles
        tzname = tz.split(" ", 1)[1]
    else:
        # America/Los_Angeles
        tzname = tz
    try:
        return pytz.timezone(tzname)
    except UnknownTimeZoneError as e:
        LOGGER.warning(
            f"Encountered unknown time zone {tzname}, returning None"
        )
        return None
