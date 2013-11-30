"""
Attribute types used for the model.

The types system provides a mechanism for serializing/un the data to/from JSON 
structures and for capturing additional information about the model attributes.  
"""
META = 1
SUMMARY = 2
DETAILED = 3

class Attribute(object):
    """
    Base descriptor class for a Strava model attribute.
    """
    
    def __init__(self, type_, resource_states=None):
        if resource_states is None:
            resource_states = tuple()
        self.type_ = type_
        self.resource_states = resource_states
        self.value = None
        
    def __get__(self, obj, objtype):
        if obj is not None:
            # It is being called on an object (not class)
            if not obj.resource_state in self.resource_states:
                raise AttributeError("attribute required resource state not satisfied by object")
            return self.value
        else:
            # Rather than return the wrapped value, return the actual descriptor object
            return self
    
    def __set__(self, obj, val):
        self.value = val
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        # Not sure if this is 100% appropriate here; we aren't leaving a mechanism
        # for setting the value directly (e.g. from python).  Yeah, this is
        # definitely wrong ....
        self._value = self.unserialize(v)
        
    def serialize(self, v):
        """
        Turn this value into format needed for JSON value.
        
        (By default this will just return the underlying object; subclasses
        can override for specific behaviors -- e.g. date formatting.)
        """
        return v
    
    def unserialize(self, v):
        """
        Convert the value from parsed JSON structure to native python
        representation.
        
        By default this will leave the value as-is since the JSON parsing routines
        typically convert to native types. The exception may be date strings or other
        more complex types, where subclasses will override this behavior.
        """
        return v

class Collection(object):
    
    def __init__(self, type_):
        raise NotImplementedError()
    