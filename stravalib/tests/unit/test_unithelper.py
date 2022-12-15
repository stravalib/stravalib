from dataclasses import dataclass

import pint
import pytest
from pint import Unit

from stravalib import unithelper as uh
from stravalib.unithelper import UnitsQuantity


@dataclass
class UnitsLikeQuantity(UnitsQuantity):
    num: float
    unit: str


@pytest.mark.parametrize(
    'from_unit,to_unit,expected_magnitude,expected_unit',
    (
        (None, 'meter', 1, 'meter'),
        ('meter', 'meter', 1, 'meter'),
        ('km', 'meter', 1000, 'meter'),
        ('m/s', 'kph', 3.6, 'kilometer / hour')
    )
)
class TestUnitConversion:
    def test_conversion_legacy(self, from_unit, to_unit, expected_magnitude, expected_unit):
        quantity = UnitsLikeQuantity(1, from_unit) if from_unit else 1
        with pytest.warns(DeprecationWarning):
            converted_quantity = getattr(uh, to_unit)(quantity)
            assert converted_quantity.num == pytest.approx(expected_magnitude, .01)
            assert str(converted_quantity.unit) == expected_unit

    def test_conversion(self, from_unit, to_unit, expected_magnitude, expected_unit):
        quantity = 1 * Unit(from_unit) if from_unit else 1
        converted_quantity = getattr(uh, to_unit)(quantity)
        assert converted_quantity.magnitude == pytest.approx(expected_magnitude, .01)
        assert str(converted_quantity.units) == expected_unit


@pytest.mark.parametrize(
    'obj,expected_result,expected_warning',
    (
        (pint.Quantity('m'), True, None),
        (uh.Quantity(pint.Quantity('m')), True, None),
        (uh.meters(1), True, None),
        (UnitsLikeQuantity(1, 'meter'), True, DeprecationWarning),
        (42, False, None)
    )
)
def test_is_quantity_type(obj, expected_result, expected_warning):
    if expected_warning:
        with pytest.warns(expected_warning):
            assert uh.is_quantity_type(obj) == expected_result
    else:
        assert uh.is_quantity_type(obj) == expected_result
