"""
Helpers for converting Strava's units to something more practical.

These are really just thin wrappers to the brilliant 'units' python library. 
"""
from units import unit
import units.predefined


METRIC = 'metric'
IMPERIAL = 'imperial'

# Setup the units we will use in this module.
units.predefined.define_units()

meter = unit('m')
second = unit('s')
hour = unit('s')
foot = unit('ft')
mile = unit('mi')
kilometer = unit('km')

meters_per_second = meter / second
mph = mile / hour
kph = kilometer / hour

def meters_to_miles(value):
    """
    Convert meters to miles.
    
    :param value: Distance in meters. 
    :type value: float
    
    :return: Equivalent number of miles.
    :rtype: float
    """
    return mile(meter(value)).get_num()

def meters_to_feet(value):
    """
    Convert meters to feet.
    
    :param value: Distance in meters
    :type value: float
    
    :return: Equivalent number of feet.
    :rtype: float
    """
    return foot(meter(value)).get_num()

def metersps_to_mph(value):
    """
    Convert meters-per-second to miles-per-hour.
    
    :param value: The meters per second value.
    :type value: float
    :rtype: float
    """
    return mph(meters_per_second(value)).get_num()

def kph_to_mph(value):
    """
    Convert kilometers-per-hour to miles-per-hour.
    
    :param value: The speed in kilometers per hour.
    :type value: float
    :rtype: float
    """
    return mph(kph(value)).get_num()
    