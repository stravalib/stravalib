from enum import Enum

import pytest
import pytz

from stravalib.field_conversions import (
    enum_value,
    enum_values,
    optional_input,
    timezone,
)


def test_optional_input():
    @optional_input
    def foo(x):
        return x + 1

    assert foo(1) == 2
    assert foo(None) is None


class Foo(Enum):
    FOO = "foo"
    BAR = "bar"


@pytest.mark.parametrize("arg,expected_value", ((Foo.FOO, "foo"), (42, 42)))
def test_enum_value(arg, expected_value):
    assert enum_value(arg) == expected_value


def test_enum_values():
    assert enum_values([Foo.FOO, 42, Foo.BAR]) == ["foo", 42, "bar"]


@pytest.mark.parametrize(
    'arg,expected_value',
    (
        ('Factory', None),
        ('(GMT+00:00) Factory', None),
        ('Europe/Amsterdam', pytz.timezone('Europe/Amsterdam')),
        ('(GMT+01:00) Europe/Amsterdam', pytz.timezone('Europe/Amsterdam'))
    )
)
def test_timezone(arg, expected_value):
    assert timezone(arg) == expected_value
