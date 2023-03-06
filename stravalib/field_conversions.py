import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, List, Optional, Sequence, Union

import pytz
from pytz.exceptions import UnknownTimeZoneError

from stravalib.strava_model import ActivityType, SportType

LOGGER = logging.getLogger(__name__)


def optional_input(field_conversion_fn: Callable) -> Callable:
    @wraps(field_conversion_fn)
    def fn_wrapper(field_value: Any):
        if field_value is not None:
            return field_conversion_fn(field_value)
        else:
            return None

    return fn_wrapper


@optional_input
def enum_value(v: Union[ActivityType, SportType]) -> str:
    try:
        return v.__root__
    except AttributeError:
        LOGGER.warning(
            f"{v} is not an enum, returning itself instead of its value"
        )
        return v


@optional_input
def enum_values(enums: Sequence[Union[ActivityType, SportType]]) -> List:
    # Pydantic (1.x) has config for using enum values, but unfortunately
    # it doesn't work for lists of enums.
    # See https://github.com/pydantic/pydantic/issues/5005
    return [enum_value(e) for e in enums]


@optional_input
def time_interval(seconds: int) -> timedelta:
    """
    Replaces legacy TimeIntervalAttribute
    """
    return timedelta(seconds=seconds)


@optional_input
def timezone(tz: str) -> Optional[pytz.timezone]:
    if " " in tz:
        # (GMT-08:00) America/Los_Angeles
        tzname = tz.split(" ", 1)[1]
    else:
        # America/Los_Angeles
        tzname = tz
    try:
        tz = pytz.timezone(tzname)
    except UnknownTimeZoneError as e:
        LOGGER.warning(
            f"Encountered unknown time zone {tzname}, returning None"
        )
        tz = None
    return tz
