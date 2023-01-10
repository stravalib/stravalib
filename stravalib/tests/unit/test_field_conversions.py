from enum import Enum

import pytest

from stravalib.field_conversions import enum_value, enum_values, optional_input


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
