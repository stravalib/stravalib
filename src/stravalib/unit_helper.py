"""
Unit Helper
==============
Helpers for converting Strava's units to something more practical.
"""

from typing import Any

import pint
from pint.facets.plain import PlainQuantity

from stravalib.unit_registry import ureg


class _Quantity(float):
    """
    Subtype of float that can represent quantities by adding a unit
    """

    unit: str
    """
    The quantity's unit
    """

    def quantity(self) -> pint.Quantity:
        """
        Returns the base type (e.g., float) as a pint.Quantity by attaching
        the unit to it.
        """
        return ureg.Quantity(self, self.unit)


class UnitConverter:
    """
    Callable that converts quantities or unitless numbers to quantities of its unit
    """

    def __init__(self, unit: str) -> None:
        self.unit = unit

    def __call__(
        self, q: _Quantity | pint.Quantity | float
    ) -> PlainQuantity[Any]:
        if isinstance(q, pint.Quantity):
            return q.to(self.unit)
        elif isinstance(q, _Quantity):
            return q.quantity().to(self.unit)
        else:
            # unitless number: simply return a Quantity
            return ureg.Quantity(q, self.unit)


meter = meters = UnitConverter("m")
second = seconds = UnitConverter("s")
hour = hours = UnitConverter("hour")
foot = feet = UnitConverter("ft")
mile = miles = UnitConverter("mi")
kilometer = kilometers = UnitConverter("km")

meters_per_second = UnitConverter("m/s")
miles_per_hour = mph = UnitConverter("mi/hour")
kilometers_per_hour = kph = UnitConverter("km/hour")
kilogram = kilograms = kg = kgs = UnitConverter("kg")
pound = pounds = lb = lbs = UnitConverter("lb")


def c2f(celsius: float) -> float:
    """
    Convert Celsius to Fahrenheit.

    Parameters
    ----------
    celsius :
        Temperature in Celsius.

    Returns
    -------
    float
        Temperature in Fahrenheit.

    """
    return (9.0 / 5.0) * celsius + 32
