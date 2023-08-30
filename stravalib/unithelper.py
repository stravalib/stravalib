"""
Unit Helper
==============
Helpers for converting Strava's units to something more practical.
"""
from numbers import Number
from typing import Any, Protocol, Union, cast, runtime_checkable

import pint

from stravalib.exc import warn_units_deprecated
from stravalib.unit_registry import Q_


@runtime_checkable
class UnitsQuantity(Protocol):
    """
    A type that represents the (deprecated) `units` Quantity. The `unit`
    attribute in the units library consists of other classes, so this
    representation may not be 100% backward compatible!
    """

    num: float
    unit: str


class Quantity(Q_):  # type: ignore[valid-type, misc]
    """
    Extension of `pint.Quantity` for temporary backward compatibility with
    the legacy `units` package.
    """

    @property
    def num(self) -> pint._typing.Magnitude:
        warn_units_deprecated()
        return self.magnitude

    @property
    def unit(self) -> str:
        warn_units_deprecated()
        return str(self.units)

    def __int__(self) -> int:
        return int(self.magnitude)

    def __float__(self) -> float:
        return float(self.magnitude)


class UnitConverter:
    def __init__(self, unit: str) -> None:
        self.unit = unit

    def __call__(
        self, q: Union[Number, pint.Quantity, UnitsQuantity]
    ) -> Quantity:
        if isinstance(q, Number):
            # provided quantity is unitless, so mimic legacy `units` behavior:
            converted_q = Quantity(q, self.unit)
        else:
            try:
                converted_q = Quantity(
                    cast(pint.Quantity, q).to(self.unit).magnitude, self.unit
                )
            except AttributeError:
                # unexpected type of quantity, maybe it's a legacy `units` Quantity
                warn_units_deprecated()
                computed_q = Quantity(q.num, q.unit)
                converted_q = Quantity(
                    computed_q.to(self.unit).magnitude, self.unit
                )

        return converted_q


def is_quantity_type(obj: Any) -> bool:
    if isinstance(obj, (pint.Quantity, Quantity)):
        return True
    elif isinstance(obj, UnitsQuantity):  # check using Duck Typing
        warn_units_deprecated()
        return True
    else:
        return False


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
