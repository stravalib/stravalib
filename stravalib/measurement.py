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
hour = unit('h')
foot = unit('ft')
mile = unit('mi')
kilometer = unit('km')

meters_per_second = meter / second
mph = mile / hour
kph = kilometer / hour
    