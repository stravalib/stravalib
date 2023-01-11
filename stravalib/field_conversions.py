import logging
from datetime import timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, List, Sequence

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
def enum_value(v: Enum) -> Any:
    try:
        return v.value
    except AttributeError:
        LOGGER.warning(
            f"{v} is not an enum, returning itself instead of its value"
        )
        return v


@optional_input
def enum_values(enums: Sequence[Enum]) -> List:
    return [enum_value(e) for e in enums]


@optional_input
def time_interval(seconds: int):
    """
    Replaces legacy TimeIntervalAttribute
    """
    return timedelta(seconds=seconds)
