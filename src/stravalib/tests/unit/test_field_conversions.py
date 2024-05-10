import pytest
import pytz

from stravalib.field_conversions import (
    optional_input,
    timezone,
)

# from stravalib.strava_model import ActivityType, SportType


def test_optional_input():
    @optional_input
    def foo(x):
        return x + 1

    assert foo(1) == 2
    assert foo(None) is None


# def test_enum_value():
#     """Test that when there is one specific Sport or other type,
#     that enum_value returns that value only.

#     TODO: Question - do we need enum_value method with pydantic 2.x?
#     """

#     a = ActivityType("Run")
#     assert enum_value(a) == "Run"


# def test_enum_values():
#     """Club objects may have one or more ActivityTypes associated with them.

#     This tests that when provided with a list of types, enum values
#     parses multiple types and returns a list.
#     """



@pytest.mark.parametrize(
    "arg,expected_value",
    (
        ("Factory", None),
        ("(GMT+00:00) Factory", None),
        ("Europe/Amsterdam", pytz.timezone("Europe/Amsterdam")),
        ("(GMT+01:00) Europe/Amsterdam", pytz.timezone("Europe/Amsterdam")),
    ),
)
def test_timezone(arg, expected_value):
    assert timezone(arg) == expected_value
