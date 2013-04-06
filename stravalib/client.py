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
        self.v1client = v1.ApiV1Client(units=units)
        self.v2client = v2.ApiV2Client(units=units)

    def get_rides(self, full_objects=True, limit=50, include_geo=False, **kwargs):
        """
        Enumerate rides for specified attribute/value.
        
        :keyword full_objects: Whether to return full ride objects (as opposed to just id+name, which is faster).
        :type full_objects: bool
        
        :keyword limit: The maximum number of rides to return. Defaults to 50, set to None to retrieve all results.
        :type limit: int
        
        :keyword include_geo: Whether to include lat/lon information on full objects (requires additional call).
        :type include_geo: bool
        
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
        result_fetcher = functools.partial(self.v1client.get_rides, **kwargs)
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
        Internal function to populate a ride/segment effort model for specified ID.
        
        :param effort_id: The effort ID.
        :type effort_id: int
        :param effort_model: The model object to populate.
        :type effort_model: :class:`stravalib.model.Effort`
        """
        v1effort = self.v1client.get_effort(effort_id)
        self.v1client.mapper.populate_effort(effort_model, v1effort)

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
            # Need to get from a segment to an effort and then back to a segment ... since
            # V2 API only allows for getting efforts.  Luckly the geo in the v2 efforts appears to be
            #  specific to the segment (and not where the effort began matching the segment, etc.)
            v2segment = None
            first_effort = self.get_segment_efforts(segment_id, full_objects=False, limit=1)[0]
            for eff in self.v2client.get_ride_efforts(first_effort.activity_id):
                if eff['segment']['id'] == segment_id:
                    v2segment = eff['segment']
                    break
            else:
                raise RuntimeError("Exhausted effort {0} looking for segment {1} match".format(first_effort.activity_id, segment_id))
            
            print "Effort raw = %r" % (v2segment,)
            self.v2client.mapper.populate_segment(segment_model, v2segment)
            
                    
    def get_ride_efforts(self, ride_id, full_objects=False):
        """
        Get the efforts (segment performance) on a specific ride.
        
        :param ride_id: The activity id.
        :type ride_id: int
        :keyword full_objects: Whether to return full effort objects (as opposed to just basic attributes, which is much faster).
        :type full_objects: bool
        """
        # This one appears to return all results w/o batching?
        v1efforts = self.v1client.get_ride_efforts(ride_id)
        
        # TODO: Consider how best (or whether) to integrate the V2 ride efforts data.
        
        efforts = []
        for v1effort in v1efforts:
            if full_objects:
                effort = model.Effort(bind_client=self)
                self._populate_effort(v1effort['id'], effort)
            else:
                effort = model.Effort(bind_client=self)
                self.v1client.mapper.populate_minimal_ride_effort(effort, v1effort)
                effort.activity_id = ride_id
                
            efforts.append(effort)
        
        return efforts

    def get_segment_efforts(self, segment_id, full_objects=False, limit=50, **kwargs):
        """
        Get efforts for a specific segment.
        
        :param segment_id: The ID of the segment for which to fetch efforts.
        :type segment_id: int
        
        :keyword full_objects: Whether to return full effort objects (as opposed to just id+name, which is faster).
        :type full_objects: bool
        
        :keyword limit: The maximum number of efforts to return. Defaults to 50, set to None to retrieve all results. 
        :type limit: int
        
        :keyword club_id: Optional. Id of the Club for which to search for member's Efforts.
        :type club_id: int
        
        :keyword athlete_id: Optional. Id of the Athlete for which to search for Efforts.
        :type athlete_id: int
        
        :keyword athlete_name: Optional. Username of the Athlete for which to search for Efforts.
        :type athlete_name: str
        
        :keyword start_date: Optional. Day on which to end search for Efforts. The date is the local time of when the effort started.
        :type start_date: :class:`datetime.datetime`
        
        :keyword end_date: Optional. Day on which to end search for Efforts. The date is the local time of when the effort ended.
        :type end_date: :class:`datetime.datetime`
        
        :keyword start_id: Optional. Only return Efforts with an Id greater than or equal to the startId.
        :type start_id: int
        
        :keyword best: Optional. Shows an best efforts per athlete sorted by elapsed time ascending (segment leaderboard).
        :type best: bool
        
        :rtype: list
        """
        result_fetcher = functools.partial(self.v1client.get_segment_efforts, segment_id, **kwargs)
        v1efforts = v1.BatchedResultsIterator(result_fetcher=result_fetcher, limit=limit)
        
        efforts = []
        for v1effort in v1efforts:
            if full_objects:
                effort = model.Effort(bind_client=self)
                self._populate_effort(v1effort['id'], effort)
            else:
                effort = model.Effort(bind_client=self)
                self.v1client.mapper.populate_minimal_segment_effort(effort, v1effort)
                effort.segment_id = segment_id
            efforts.append(effort)
        
        return efforts
    
    def get_effort(self, effort_id):
        """
        Gets a specific Effort (including both activity and segment information) by ID.
        
        :rtype: :class:`stravalib.model.Effort`
        """
        effort = model.Effort(bind_client=self)
        self._populate_effort(effort_id, effort)
        return effort
    
    def get_segment(self, segment_id, include_geo=False):
        """
        Gets a specific segment.
        
        :rtype: :class:`stravalib.model.Segment`
        """
        segment = model.Segment(bind_client=self)
        self._populate_segment(segment_id, segment, include_geo=include_geo)
        return segment

    def _populate_club(self, club_id, club_model):
        """
        Internal function to populate a club model for specified ID.
        :param club_id:
        :param club_model:
        :type club_model: :class:`stravalib.model.Club`
        """
        v1ride = self.v1client.get_club(club_id)
        self.v1client.mapper.populate_club(club_model, v1ride)

    def get_clubs(self, name, full_objects=False):
        """
        Search for clubs by name (substring/keyword match).
        
        :param name: The name (or substring) of club.
        :type name: str
        
        :param full_objects: Whether to return full ride objects (as opposed to just id+name, which is faster).
        :type full_objects: bool
        
        :rtype: list of :class:`stravalib.model.Club`
        """
        v1clubs = self.v1client.get_clubs(name)
        clubs = []
        for v1club in v1clubs:
            club = model.Club(bind_client=self)
            if full_objects:
                self._populate_club(v1club['id'], club)
            else:
                self.v1client.mapper.populate_minimal(club, v1club)
            clubs.append(club)
        return clubs
        
    def get_club(self, club_id):
        """
        Gets a club for specified ID.
        
        :rtype: :class:`stravalib.model.Club`
        """
        club = model.Club(bind_client=self)
        self._populate_club(club_id, club)
        return club
    
    def get_club_members(self, club_id):
        """
        Get the members for club specified by ID.
        
        :param club_id: The numeric ID of the club.
        :type club_id: int
        """
        v1clubmembers = self.v1client.get_club_members(club_id)
        members = []
        for athlete_struct in v1clubmembers:
            a = model.Athlete(bind_client=self)
            self.v1client.mapper.populate_athlete(a, athlete_struct)
            members.append(a)
        return members