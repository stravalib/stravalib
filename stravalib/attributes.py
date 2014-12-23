"""
Attribute types used for the model.

The types system provides a mechanism for serializing/un the data to/from JSON
structures and for capturing additional information about the model attributes.
"""
import logging
from datetime import datetime, timedelta, tzinfo, date
from collections import namedtuple
from weakref import WeakKeyDictionary, WeakValueDictionary

import pytz
from units.quantity import Quantity

import stravalib.model

META = 1
SUMMARY = 2
DETAILED = 3


class Attribute(object):
    """
    Base descriptor class for a Strava model attribute.
    """
    _type = None

    def __init__(self, type_, resource_states=None, units=None):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.type = type_
        self.resource_states = resource_states
        self.data = WeakKeyDictionary()
        self.units = units

    def __get__(self, obj, clazz):
        if obj is not None:
            # It is being called on an object (not class)
            # This can cause infinite loops, when we're attempting to get the resource_state attribute ...
            #if hasattr(clazz, 'resource_state') \
            #   and obj.resource_state is not None \
            #   and not obj.resource_state in self.resource_states:
            #    raise AttributeError("attribute required resource state not satisfied by object")
            return self.data.get(obj)
        else:
            # Rather than return the wrapped value, return the actual descriptor object
            return self

    def __set__(self, obj, val):
        if val is not None:
            self.data[obj] = self.unmarshal(val)
        else:
            self.data[obj] = None

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, v):
        self._type = v

    def marshal(self, v):
        """
        Turn this value into format for wire (JSON).

        (By default this will just return the underlying object; subclasses
        can override for specific behaviors -- e.g. date formatting.)
        """
        return v

    def unmarshal(self, v):
        """
        Convert the value from parsed JSON structure to native python representation.

        By default this will leave the value as-is since the JSON parsing routines
        typically convert to native types. The exception may be date strings or other
        more complex types, where subclasses will override this behavior.
        """
        if self.units:
            # Note that we don't want to cast to type in this case!
            if not isinstance(v, Quantity):
                v = self.units(v)
        elif not isinstance(v, self.type):
            v = self.type(v)
        return v


class DateAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None):
        super(DateAttribute, self).__init__(date, resource_states=resource_states)

    def unmarshal(self, v):
        """
        Convert a date in "2012-12-13" format to a :class:`datetime.date` object.
        """
        if not isinstance(v, date):
            # 2012-12-13
            v = datetime.strptime(v, "%Y-%m-%d").date()
        return v


class TimestampAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None, tzinfo=pytz.utc):
        super(TimestampAttribute, self).__init__(datetime, resource_states=resource_states)
        self.tzinfo = tzinfo

    def unmarshal(self, v):
        """
        Convert a timestamp in "2012-12-13T03:43:19Z" format to a `datetime.datetime` object.
        """
        if not isinstance(v, datetime):
            # 2012-12-13T03:43:19Z
            v = datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=self.tzinfo)
        return v


LatLon = namedtuple('LatLon', ['lat', 'lon'])


class LocationAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None):
        super(LocationAttribute, self).__init__(LatLon, resource_states=resource_states)

    def unmarshal(self, v):
        """
        """
        if not isinstance(v, LatLon):
            v = LatLon(lat=v[0], lon=v[1])
        return v


class TimezoneAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None):
        super(TimezoneAttribute, self).__init__(pytz.timezone, resource_states=resource_states)

    def unmarshal(self, v):
        """
        Convert a timestamp in format "(GMT-08:00) America/Los_Angeles" to
        a `pytz.timestamp` object.
        """
        if not isinstance(v, tzinfo):
            # (GMT-08:00) America/Los_Angeles
            tzname = v.split(' ')[-1]
            v = pytz.timezone(tzname)
        return v


class TimeIntervalAttribute(Attribute):
    """
    Handles time durations, assumes upstream int value in seconds.
    """
    def __init__(self, resource_states=None):
        super(TimeIntervalAttribute, self).__init__(int, resource_states=resource_states)

    def unmarshal(self, v):
        """
        Convert the value from parsed JSON structure to native python representation.

        By default this will leave the value as-is since the JSON parsing routines
        typically convert to native types. The exception may be date strings or other
        more complex types, where subclasses will override this behavior.
        """
        if not isinstance(v, timedelta):
            v = timedelta(seconds=v)
        return v


class EntityAttribute(Attribute):
    """
    Attribute for another entity.
    """
    _lazytype = None

    def __init__(self, *args, **kwargs):
        super(EntityAttribute, self).__init__(*args, **kwargs)
        self.bind_clients = WeakKeyDictionary()

    @property
    def type(self):
        if self._lazytype:
            clazz = getattr(stravalib.model, self._lazytype)
        else:
            clazz = self._type
        return clazz

    @type.setter
    def type(self, v):
        if isinstance(v, (str, bytes)):
            # Supporting lazy class referencing
            self._lazytype = v
        else:
            self._type = v

    def __set__(self, obj, val):
        if val is not None:
            # If the "owning" object has a bind_client set, we want to pass that
            # down into the objects we are deserializing here
            self.data[obj] = self.unmarshal(val, bind_client=getattr(obj, 'bind_client'))
        else:
            self.data[obj] = None

    def unmarshal(self, value, bind_client=None):
        """
        Cast the specified value to the entity type.
        """
        #self.log.debug("Unmarshall {0!r}: {1!r}".format(self, value))
        if not isinstance(value, self.type):
            o = self.type()
            if bind_client is not None and hasattr(o.__class__, 'bind_client'):
                o.bind_client = bind_client

            if isinstance(value, dict):
                for (k, v) in value.items():
                    if not hasattr(o.__class__, k):
                        self.log.warning("Unable to set attribute {0} on entity {1!r}".format(k, o))
                    else:
                        #self.log.debug("Setting attribute {0} on entity {1!r}".format(k, o))
                        setattr(o, k, v)
                value = o
            else:
                raise Exception("Unable to unmarshall object {0!r}".format(value))
        return value


class EntityCollection(EntityAttribute):

    def unmarshal(self, values, bind_client=None):
        """
        Cast the list.
        """
        results = []
        for v in values:
            #print "-------- Processing value: %r" % (v,)
            entity = super(EntityCollection, self).unmarshal(v, bind_client=bind_client)
            #print "-------- Got entity: %r" % (entity,)
            results.append(entity)
        return results
