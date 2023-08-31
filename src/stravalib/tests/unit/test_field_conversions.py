import pytest
import pytz

from stravalib.field_conversions import (
    enum_value,
    enum_values,
    optional_input,
    timezone,
)
from stravalib.strava_model import ActivityType, SportType


def test_optional_input():
    @optional_input
    def foo(x):
        return x + 1

    assert foo(1) == 2
    assert foo(None) is None


def test_enum_value():
    assert enum_value(ActivityType(__root__="Run")) == "Run"


def test_enum_values():
    assert enum_values(
        [ActivityType(__root__="Run"), SportType(__root__="Ride")]
    ) == ["Run", "Ride"]


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
