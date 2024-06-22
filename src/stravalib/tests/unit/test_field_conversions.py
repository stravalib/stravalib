from stravalib.field_conversions import (
    optional_input,
)


def test_optional_input():
    @optional_input
    def foo(x):
        return x + 1

    assert foo(1) == 2
    assert foo(None) is None
