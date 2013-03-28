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
        Initialize a new client object.
        
        :param units: Whether to use imperial or metric units (value must be 'imperial' or 'metric', 
                      also provided by module-level constants)
        :type units: str
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.v1client = v1.V1ServerProxy(units=units)
        self.v2client = v2.V2ServerProxy(units=units)

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
                ride = model.Ride(bind_client=self)
                self._populate_ride(v1ride['id'], ride, include_geo=include_geo)
            else:
                ride = model.Ride(bind_client=self)
                self.v1client.mapper.populate_minimal(ride, v1ride)
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
        self.v1client.mapper.populate_ride(ride_model, v1ride)
        if include_geo:
            v2ride = self.v2client.get_ride(ride_id)
            self.v2client.mapper.populate_ride(ride_model, v2ride)
        
    def get_ride(self, ride_id, include_geo=False):
        """
        :param ride_id:
        :param include_geo: Whether to include lat/lon for the ride start/end (adds a call to v2 api). 
        :rtype: :class:`stravalib.model.Ride`
        """
        ride = model.Ride(bind_client=self)
        self._populate_ride(ride_id, ride)
        return ride
    
    def _populate_effort(self, effort_id, effort_model):
        """
        Internal function to populate a ride effort model for specified ID.
        :param effort_id:
        :param effort_model:
        """
        v1effort = self.v1client.get_effort(effort_id)
        self.v1client.mapper.populate_effort(effort_model, v1effort)
#        
#        if include_geo:
#            # Look up the v2 ride efforts
#            v2ride_efforts = self.v2client.get_ride_efforts(v1effort['ride']['id'])
#            # Find the effort from the ride that matches this one ...
#            for v2ride_effort in v2ride_efforts:
#                if v2ride_effort['id'] == effort_id:
#                    # FIXME .... WORK IN PROGRESS
#                    # ... it's only the segment that actually has geo data ....
#                    break
#            else:
#                raise RuntimeError("Unable to find effort {0} in v2 data for ride {1}".format(effort_id, v1effort['ride']['id']))
#            
    def _populate_segment(self, segment_id, segment_model, include_geo=False):
        """
        Internal function to populate a segment model for specified ID.
        
        :param segment_id:
        :param segment_model:
        :param include_geo: Whether to include lat/lon for the segment start/end (adds a call to v2 api).
        """
        v1segment = self.v1client.get_segment(segment_id)
        self.v1client.mapper.populate_segment(segment_model, v1segment)
        
        if include_geo:
            raise NotImplementedError("Start/end geo for segments is not yet implemented.")
            # Need to get from a segment to an effort and then back to a segment ... since
            # V2 API only allows for getting efforts
                    
    def get_ride_efforts(self, ride_id, full_objects=False):
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
                effort = model.RideEffort(bind_client=self)
                self._populate_effort(v1effort['id'], effort)
            else:
                effort = model.RideEffort(bind_client=self)
                self.v1client.mapper.populate_minimal_effort(effort, v1effort)
            efforts.append(effort)
        
        return efforts

    def get_segment_efforts(self, segment_id, full_objects=False, limit=None, **kwargs):
        """
        :param ride_id:
        
        :keyword full_objects: Whether to return full ride objects (as opposed to just id+name, which is faster).
        :type full_objects: bool
        
        :keyword limit: The maximum number of rides to return. Defaults to 50, set to None to retrieve all results.
        :type limit: int
        
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
        
        :keyword best: Optional. Shows an best efforts per athlete sorted by elapsed time ascending (segment leaderboard).
        :type best: bool
        
        :rtype: list
        """
        # This one appears to return all results w/o batching?
        v1efforts = self.v1client.get_segment_efforts(segment_id, **kwargs)
        
        # FIXME:
        # (This is what I was working on last.)
        # Segment Efforts are not the same thing as regular Efforts.  In particular the summary info returned for 
        # segment efforts include information about the ride and athlete.
        #
        #
        
        efforts = []
        for v1effort in v1efforts:
            if full_objects:
                effort = model.RideEffort(bind_client=self)
                self._populate_effort(v1effort['id'], effort)
            else:
                effort = model.RideEffort(bind_client=self)
                print v1effort
                self.v1client.mapper.populate_minimal_effort(effort, v1effort)
            efforts.append(effort)
        
        return efforts
    
    def get_effort(self, effort_id):
        """
        :rtype: :class:`stravalib.model.RideEffort`
        """
        effort = model.RideEffort(bind_client=self)
        self._populate_effort(effort_id, effort)
        return effort
    
    def get_segment(self, segment_id, include_geo=False):
        """
        :rtype: :class:`stravalib.model.Segment`
        """
        segment = model.Segment(bind_client=self)
        self._populate_segment(segment_id, segment, include_geo=include_geo)
        return segment
    
    def get_club(self, club_id):
        """
        :rtype: :class:`stravalib.model.Club`
        """
        v1club = self.v1client.get_club(club_id)
        club = model.Club(bind_client=self)
        self.v1client.mapper.populate_club(club, v1club)
        return club
    
    def get_club_members(self, club_id):
        """
        """
        v1clubmembers = self.v1client.get_club_members(club_id)
        members = []
        for athlete_struct in v1clubmembers:
            a = model.Athlete(bind_client=self)
            self.v1client.mapper.populate_athlete(a, athlete_struct)
            members.append(a)
        return members