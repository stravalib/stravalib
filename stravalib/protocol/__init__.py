from __future__ import division, absolute_import, print_function
import abc
import json
import logging
import collections

import requests
from pytz import FixedOffset
from dateutil import parser as date_parser
from units.abstract import AbstractUnit

from stravalib import exc
from stravalib.measurement import IMPERIAL, METRIC
from stravalib import measurement

Credentials = collections.namedtuple('Credentials', ('username', 'password'))

class BaseModelMapper(object):
    """
    Base class for the mappers that populate model objects from V1/V2 results.
    """
    __metaclass__ = abc.ABCMeta
    
    _units = METRIC
    
    def __init__(self, client, units):
        """
        Initialize model mapper with reference to server proxy and desired units ('imperial' or 'metric').
        
        :param client: The master client instance that is using this mapper.  This is currently needed since the mapper
                            may need to instantiate "bound" model objects.
        :type client: :class:`stravalib.simple.Client`
        """
        self.client = client
        self.units = units

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, v):
        valid_units = (IMPERIAL, METRIC)
        if not v in valid_units:
            raise ValueError("units param must be one of: {0}".format(valid_units))
        self._units = v
    
    def populate_minimal(self, entity_model, entity_struct):
        """
        Populates a :class:`stravalib.model.StravaEntity` model object with minimal (id and name) attributes.
        
        :param entity_model: The model object to fill.
        :type entity_model: :class:`stravalib.model.Ride`
        :param entity_struct: The raw ride V1 response structure.
        :type entity_struct: dict
        """
        entity_model.id = entity_struct['id']
        entity_model.name = entity_struct['name']
    
    def _convert_distance(self, v):
        """
        Converts distance to configured imperial/metric units.
        :param v: The distance.  If this is not a units object, assumed to be meters.
        :type v: :class:`units.abstract.AbstractUnit` or float
        """
        if not isinstance(v, AbstractUnit):
            v = measurement.meter(v)
            
        if self.units == IMPERIAL:
            result = measurement.mile(v)
        else:
            result = measurement.kilometer(v)
            
        return result.get_num()
    
    def _convert_speed(self, v):
        """
        Converts speed (must have units) to configured imperial/metric units.
        :param v: The speed.  If this is not a units object, assumed to be meters per second.
        :type v: :class:`units.abstract.AbstractUnit` or float
        """
        #print("Got raw value %r" % (v,))
        if not isinstance(v, AbstractUnit):
            v = measurement.meters_per_second(v)
        
        #print("Normalized: %r" % (v,))
        
        if self.units == IMPERIAL:
            result = measurement.mph(v)
        else:
            result = measurement.kph(v)
            
        return result.get_num()
    
    def _convert_elevation(self, v):
        """
        Converts elevation (must have units) to configured imperial/metric units.
        :param v: The elevation.  If this is not a units object, assumed to be meters.
        :type v: :class:`units.abstract.AbstractUnit` or float
        """
        if not isinstance(v, AbstractUnit):
            v = measurement.meter(v)
            
        if self.units == IMPERIAL:
            result = measurement.foot(v)
        else:
            result = measurement.meter(v)
        
        return result.get_num()
        
    # TODO: Give some thought to how we can ensure that all of our dates have the TZ
    # associated with them.  It looks like only certain strava methods will return the tz offset,
    # so we may end up w/ extraneous calls just to get this info ... ?
    def _parse_datetime(self, datestr, utcoffset=None):
        """
        Parses a Strava datetime; if offset is provided, this will be added to the date as a fixed-offset timezone.
        
        There are some quirks to Strava dates; namely they look like they are UTC but they are actually local to the
        rider's TZ. (It's OK, we just replace the tz.)
        
        :param utcoffset: The offset east of UTC, specified in seconds (for some bizarre reason).
        :type utcoffset: int
        """
        if utcoffset:
            tz = FixedOffset(utcoffset / 60)
        else:
            tz = None
        return date_parser.parse(datestr).replace(tzinfo=tz)
        
class BaseApiClient(object):
    """
    The common functionality for Strava REST API client implementations.
    """
    __metaclass__ = abc.ABCMeta
    
    server = 'www.strava.com'
    mapper = None
    
    @abc.abstractproperty
    def mapper_class(self):
        """ The class to instantiate for mapping results to model entities. """
        
    def __init__(self, units, requests_session=None):
        """
        Initialize this protocol client, optionally providing a (shared) :class:`requests.Session`
        object.
        
        :param units: 'imperial' or 'metric'
        :param requests_session: An existing :class:`requests.Session` object to use.
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        if requests_session:
            self.rsession = requests_session
        else:
            self.rsession = requests.Session()
        self.mapper = self.mapper_class(client=self, units=units)
    
    def _get(self, url, params=None):
        self.log.debug("GET {0!r} with params {1!r}".format(url, params))
        raw = self.rsession.get(url, params=params)
        raw.raise_for_status()
        resp = self._handle_protocol_error(raw.json())
        return resp
    
    def _handle_protocol_error(self, response):
        """
        Parses the JSON response from the server, raising a :class:`stravalib.exc.Fault` if the
        server returned an error.
        
        :param response: The response JSON
        :raises Fault: If the response contains an error. 
        """
        if 'error' in response:
            raise exc.Fault(response['error'])
        return response
    