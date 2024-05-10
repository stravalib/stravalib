import pytest
import pytz

from stravalib.field_conversions import (
    optional_input,
    timezone,
)


def test_optional_input():
    @optional_input
    def foo(x):
        return x + 1

    assert foo(1) == 2
    assert foo(None) is None


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
