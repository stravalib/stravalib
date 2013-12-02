"""
Attribute types used for the model.

The types system provides a mechanism for serializing/un the data to/from JSON 
structures and for capturing additional information about the model attributes.  
"""
import logging
from datetime import datetime, timedelta, tzinfo
from collections import namedtuple

import pytz

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
        self.value = None
        self.units = units
        
    def __get__(self, obj, objtype):
        if obj is not None:
            # It is being called on an object (not class)
            # This can cause infinite loops, when we're attempting to get the resource_state attribute ...
            #if hasattr(objtype, 'resource_state') \
            #   and obj.resource_state is not None \
            #   and not obj.resource_state in self.resource_states:
            #    raise AttributeError("attribute required resource state not satisfied by object")
            return self.value
        else:
            # Rather than return the wrapped value, return the actual descriptor object
            return self
    
    def __set__(self, obj, val):
        self.value = val
            
    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, v):
        self._type = v
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        if v is not None:
            self._value = self.unmarshal(v)
        else:
            self._value = None
        
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
        if not isinstance(v, self.type):
            v = self.type(v)
        return v

class UnitAttribute(Attribute):
    def __init__(self, type_, resource_states=None, units=None):
        super(UnitAttribute, self).__init__(int, resource_states=resource_states)
        self.units = units
    
class TimestampAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None):
        super(TimestampAttribute, self).__init__(datetime, resource_states=resource_states)

    def unmarshal(self, v):
        """
        Convert a timestamp in "2012-12-13T03:43:19Z" format to a `datetime.datetime` object.
        """
        if not isinstance(v, datetime):
            # 2012-12-13T03:43:19Z
            # (The time is not necessarily GMT, though that should be considered the default.
            v = pytz.utc.localize(datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ"))
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
    
    @property
    def bind_client(self):
        if hasattr(self.value, 'bind_client'):
            return self.value.bind_client
        else:
            return None
    
    @bind_client.setter
    def bind_client(self, client):
        if hasattr(self.type, 'bind_client'):
            if self.value is not None:
                self.value.bind_client = client
            else:
                raise Exception("Cannot bind client to null value.")
        else:
            self.log.warning("Cannot bind client to unsupported entity: {0}".format(self.type))
    
    def __set__(self, obj, val):
        self.value = val
        if hasattr(obj, 'bind_client'):
            self.bind_client = obj.bind_client
        
    def unmarshal(self, value):
        """
        Cast the specified value to the entity type.
        """
        if not isinstance(value, self._type):
            o = self.type()
            if isinstance(value, dict):
                for (k,v) in value.items():
                    if not hasattr(o.__class__, k):
                        self.log.warning("Unable to set attribute {0} on entity {1!r}".format(k, o))
                    else:
                        self.log.debug("Setting attribute {0} on entity {1!r}".format(k, o))
                        setattr(o, k, v)                    
                value = o
            else:
                raise Exception("Unable to unmarshall object {0!r}".format(value))
        return value
    
class EntityCollection(EntityAttribute):

    @property
    def bind_client(self):
        # We assume homogenous collection, so we grab bind client from the first element
        if self.value and hasattr(self.value[0], 'bind_client'):
            return self.value[0].bind_client
        else:
            return None
    
    @bind_client.setter
    def bind_client(self, client):
        if hasattr(self.type, 'bind_client'):
            if self.value:
                # Set the bind_client on all entities in our list
                for v in self.value:
                    v.bind_client = client
            else:
                self.log.warning("Cannot bind client to empty list (of type {0}".format(self.type))
        else:
            self.log.warning("Cannot bind client to unsupported entity: {0}".format(self.type))
    
    def unmarshal(self, values):
        """
        Cast the list.
        """
        results = []
        for v in values:
            results.append(super(EntityCollection, self).unmarshal(v))
        return results