"""
Attributes
==============
Attribute types used for the model.

The types system provides a mechanism for serializing/un the data to/from JSON
structures and for capturing additional information about the model attributes.
"""
import logging
from collections import namedtuple
from datetime import date, datetime
from weakref import WeakKeyDictionary

import arrow
import pytz

from stravalib.unithelper import is_quantity_type

# Depending on the type of request, objects will be returned in meta,  summary or detailed representations. The
# representation of the returned object is indicated by the resource_state attribute.
# (For more info, see https://developers.strava.com/docs/reference/)

META = 1
SUMMARY = 2
DETAILED = 3


class Attribute(object):
    """
    Base descriptor class for a Strava model attribute.
    """

    _type = None

    def __init__(self, type_, resource_states=None, units=None):
        self.log = logging.getLogger(
            "{0.__module__}.{0.__name__}".format(self.__class__)
        )
        self.type = type_
        self.resource_states = resource_states
        self.data = WeakKeyDictionary()
        self.units = units

    def __get__(self, obj, clazz):
        if obj is not None:
            # It is being called on an object (not class)
            # This can cause infinite loops, when we're attempting to get the resource_state attribute ...
            # if hasattr(clazz, 'resource_state') \
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
        if is_quantity_type(v):
            return v.num
        else:
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
            if not is_quantity_type(v):
                v = self.units(v)
        elif not isinstance(v, self.type):
            v = self.type(v)
        return v


class DateAttribute(Attribute):
    """ """

    def __init__(self, resource_states=None):
        super(DateAttribute, self).__init__(
            date, resource_states=resource_states
        )

    def marshal(self, v):
        """

        :param v: The date object to convert.
        :type v: date
        :return:
        """
        return v.isoformat() if v else None

    def unmarshal(self, v):
        """
        Convert a date in "2012-12-13" format to a :class:`datetime.date` object.
        """
        if not isinstance(v, date):
            # 2012-12-13
            v = datetime.strptime(v, "%Y-%m-%d").date()
        return v


class TimestampAttribute(Attribute):
    """ """

    def __init__(self, resource_states=None, tzinfo=pytz.utc):
        super(TimestampAttribute, self).__init__(
            datetime, resource_states=resource_states
        )
        self.tzinfo = tzinfo

    def marshal(self, v):
        """
        Serialize the timestamp to string.

        :param v: The timestamp.
        :type v: datetime
        :return: The serialized date time.
        """
        return v.isoformat() if v else None

    def unmarshal(self, v):
        """
        Convert a timestamp in "2012-12-13T03:43:19Z" format to a `datetime.datetime` object.
        """
        if not isinstance(v, datetime):
            if isinstance(v, int):
                v = arrow.get(v)
            else:
                try:
                    # Most dates are in this format 2012-12-13T03:43:19Z
                    v = datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    # ... but not all.
                    v = arrow.get(v).datetime
            # Translate to specified TZ
            v = v.replace(tzinfo=self.tzinfo)

        return v


LatLon = namedtuple("LatLon", ["lat", "lon"])
