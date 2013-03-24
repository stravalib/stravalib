"""
Providing a simplified, protocol-version-abstracting interface to Strava web services. 
"""
import logging
import functools

from stravalib import model
from stravalib.protocol import v1, v2, scrape
from stravalib.measurement import IMPERIAL, METRIC

class Client(object):
    """
    Main client class for interacting with the Strava backends.
    
    This class abstracts interactions with Strava's various protocols (REST v1 & v2,
    the main website) to provide a simple and full-featured API.
    """
    
    def __init__(self, units=IMPERIAL):
        """
        
        :param units: Whether to use imperial or metric units (value must be 'imperial' or 'metric', 
                      also provided by module-level constants)
        :type units: str
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.v1mapper = v1.V1ModelMapper(units=units)
        self.v1client = v1.V1ServerProxy()
        
        self.v2mapper = v2.V2ModelMapper(units=units)
        self.v2client = v2.V2ServerProxy()
        

    def get_rides(self, full_objects=True, limit=50, include_geo=False, **kwargs):
        """
        Enumerate rides for specified attribute/value.
        
        :keyword full_objects: Whether to return full ride objects (as opposed to just id+name, which is faster).
        :type full_objects: bool
        
        :keyword limit: The maximum number of rides to return. Defaults to 50, set to None to retrieve all results.
        :type limit: int
        
        :keyword include_geo: Whether to include lat/lon information on full objects (requires additional call).
        :type limit: bool
        
        :keyword club_id: Optional. Id of the Club for which to search for member's Rides.
        :type club_id: int
        
        :keyword athlete_id: Optional. Id of the Athlete for which to search for Rides.
        :type athlete_id: int
        
        :keyword athlete_name: Optional. Username of the Athlete for which to search for Rides.
        :type athlete_name: str
        
        :keyword start_date: Optional. Day on which to start search for Rides.  The date is the local time of when the ride started.
        :type start_date: :class:`datetime.datetime`
        
        :keyword end_date: Optional. Day on which to end search for Rides. The date is the local time of when the ride ended.
        :type end_date: :class:`datetime.datetime`
        
        :keyword start_id: Optional. Only return Rides with an Id greater than or equal to the startId.
        :type start_id: int
        
        :rtype: list
        """
        result_fetcher = functools.partial(self.v1client.get_rides(**kwargs))
        v1rides = v1.BatchedResultsIterator(result_fetcher=result_fetcher, limit=limit)
        rides = []
        for v1ride in v1rides:
            if full_objects:
                ride = model.Ride()
                self._populate_ride(v1ride['id'], ride, include_geo=include_geo)
            else:
                ride = model.Ride(entity_pouplator=functools.partial(self._populate_ride, v1ride['id']))
                self.v1mapper.populate_minimal(ride, v1ride)
            rides.append(ride)
        
        return rides
    
    def _populate_ride(self, ride_id, ride_model, include_geo=False):
        """
        Internal function to populate a ride model for specified ID.
        :param ride_id:
        :param ride_model:
        :param include_geo: Whether to include lat/lon for the ride start/end (adds a call to v2 api).
        """
        v1ride = self.v1client.get_ride(ride_id)
        self.v1mapper.populate_ride(ride_model, v1ride)
        if include_geo:
            v2ride = self.v2client.get_ride(ride_id)
            self.v2mapper.populate_ride(ride_model, v2ride)
        
    def get_ride(self, ride_id, include_geo=False):
        """
        :param ride_id:
        :param include_geo: Whether to include lat/lon for the ride start/end (adds a call to v2 api). 
        :rtype: :class:`stravalib.model.Ride`
        """
        ride = model.Ride(client=self)
        self._populate_ride(ride_id, ride)
        return ride
    
    def _populate_effort(self, effort_id, effort_model, include_geo=False):
        """
        Internal function to populate a ride model for specified ID.
        :param effort_id:
        :param effort_model:
        :param include_geo: Whether to include lat/lon for the ride start/end (adds a call to v2 api).
        """
        v1effort = self.v1client.get_effort(effort_id)
        self.v1mapper.populate_effort(effort_model, v1effort)
        if include_geo:
            # Look up the v2 ride efforts
            v2ride_efforts = self.v2client.get_ride_efforts(v1effort['ride']['id'])
            # Find the effort from the ride that matches this one ...
            for v2ride_effort in v2ride_efforts:
                if v2ride_effort['id'] == effort_id:
                    # FIXME .... WORK IN PROGRESS
                    # ... it's only the segment that actually has geo data ....
                    break
            else:
                raise RuntimeError("Unable to find effort {0} in v2 data for ride {1}".format(effort_id, v1effort['ride']['id']))
            
                    
    def get_ride_efforts(self, ride_id, full_objects=False, include_geo=False):
        """
        :param ride_id:
        
        :keyword full_objects: Whether to return full ride objects (as opposed to just id+name, which is faster).
        :type full_objects: bool
        
        :param include_geo: Whether to include lat/lon for the ride start/end (adds a call to v2 api). 
        :rtype: list
        """
        # This one appears to return all results w/o batching?
        v1efforts = self.v1client.get_ride_efforts(ride_id)
        
        efforts = []
        for v1effort in v1efforts:
            if full_objects:
                effort = model.Effort(bind_client=self)
                self._populate_effort(v1effort['id'], effort)
            else:
                effort = model.Effort(bind_client=self)
                self.v1mapper.populate_minimal(effort, v1effort)
            efforts.append(effort)
        
        return efforts

    def get_segment_efforts(self, segment_id, full_objects=False, include_geo=False):
        """
        :param ride_id:
        
        :keyword full_objects: Whether to return full ride objects (as opposed to just id+name, which is faster).
        :type full_objects: bool
        
        :param include_geo: Whether to include lat/lon for the ride start/end (adds a call to v2 api). 
        :rtype: list
        """
        # This one appears to return all results w/o batching?
        v1efforts = self.v1client.get_segment_efforts(segment_id)
        
        efforts = []
        for v1effort in v1efforts:
            if full_objects:
                effort = model.Effort(bind_client=self)
                self._populate_effort(v1effort['id'], effort)
            else:
                effort = model.Effort(bind_client=self)
                self.v1mapper.populate_minimal(effort, v1effort)
            efforts.append(effort)
        
        return efforts
    
    def get_effort(self, effort_id):
        raise NotImplementedError()
    
    def get_segment(self, segment_id, include_geo=False):
        raise NotImplementedError()
        # To get Geo here we need to go circuitously via ride efforts
    
    # Alias with assumption that one of these will be deprecated in the future.
    get_activity = get_ride 
    
    def get_club(self, club_id):
        """
        :rtype: :class:`stravalib.model.Club`
        """
        v1club = self.v1client.get_club(club_id)
        
        get_members = functools.partial(self.get_club_members, club_id)
        
        club = model.Club(members_fetcher=get_members)
        self.v1mapper.populate_club(club, v1club)
        return club
    
    def get_club_members(self, club_id):
        """
        """
        v1clubmembers = self.v1client.get_club_members(club_id)
        members = []
        for athlete_struct in v1clubmembers:
            a = model.Athlete()
            self.v1mapper.populate_athlete(a, athlete_struct)
            members.append(a)
        return members