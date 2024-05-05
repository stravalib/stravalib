from __future__ import annotations

import logging
from functools import wraps
from typing import Callable, TypeVar

import pytz
from pytz.exceptions import UnknownTimeZoneError

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
