import pytest

from stravalib import unit_helper as uh
from stravalib.unit_helper import _Quantity


class DistanceQuantity(_Quantity):
    unit = "feet"


@pytest.mark.parametrize(
    "expression,expected_unitless_result",
    ((uh.ureg("feet") * 6, 1.83), (DistanceQuantity(6), 1.83), (2.0, 2.0)),
)
def test_unit_converter(expression, expected_unitless_result):
    converter = uh.UnitConverter("meters")
    assert converter(expression).magnitude == pytest.approx(
        expected_unitless_result, abs=0.01
    )


def test_arithmetic_comparison_support():
    assert uh.meters(2) == uh.meters(2)
    assert uh.meters(2) > uh.meters(1)
    assert uh.meters(2) + uh.meters(1) == uh.meters(3)
