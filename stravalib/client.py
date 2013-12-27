"""
Provides the main interface classes for the Strava version 3 REST API. 
"""
import logging
import functools
import time
import collections
from datetime import datetime, timedelta
from io import BytesIO

from dateutil.parser import parser as dateparser
from units.quantity import Quantity

from stravalib import model, exc
from stravalib.protocol import ApiV3
from stravalib.util import limiter
from stravalib import unithelper

class Client(object):
    """
    Main client class for interacting with the exposed Strava v3 API methods.
    
    This class can be instantiated without an access_token when performing authentication;
    however, most methods will require a valid access token.
    """
    
    def __init__(self, access_token=None, rate_limit_requests=True, rate_limiter=None):
        """
        Initialize a new client object.
        
        :param access_token: The token that provides access to a specific Strava account.  If empty, assume that this
                             account is not yet authenticated.
        :type access_token: str
        
        :param rate_limit_requests: Whether to apply a rate limiter to the requests. (default True)
        :type rate_limit_requests: bool
        
        :param rate_limiter: A :class:`stravalib.util.limiter.RateLimiter' object to use.
                             If not specified (and rate_limit_requests is True), then
                             :class:`stravalib.util.limiter.DefaultRateLimiter' will 
                             be used.
        :type rate_limiter: callable
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        
        if rate_limit_requests:
            if not rate_limiter:
                rate_limiter = limiter.DefaultRateLimiter()
        elif rate_limiter:
            raise ValueError("Cannot specify rate_limiter object when rate_limit_requests is False")
        
        self.protocol = ApiV3(access_token=access_token, rate_limiter=rate_limiter)
        
    @property
    def access_token(self):
        """
        The currently configured authorization token.
        """
        return self.protocol.access_token
    
    @access_token.setter
    def access_token(self, v):
        """
        Set the currently configured authorization token.
        """
        self.protocol.access_token = v
    
    def authorization_url(self, client_id, redirect_uri, approval_prompt='auto', scope=None, state=None):
        """
        Get the URL needed to authorize your application to access a Strava user's information.
        
        :param client_id: The numeric developer client id.
        :type client_id: int
        
        :param redirect_uri: The URL that Strava will redirect to after successful (or failed) authorization.
        :type redirect_uri: str
        
        :param approval_prompt: Whether to prompt for approval even if approval already granted to app.
                                Choices are 'auto' or 'force'.  (Default is 'auto')
        :type approval_prompt: str
        
        :param scope: The access scope required.  Omit to imply "public".  Valid values are 'public', 'write', 'view_private', 'view_private,write'
        :type scope: str
        
        :param state: An arbitrary variable that will be returned to your application in the redirect URI.
        :type state: str
        
        :return: The URL to use for authorization link.
        :rtype: str
        """
        return self.protocol.authorization_url(client_id=client_id, redirect_uri=redirect_uri,
                                               approval_prompt=approval_prompt, scope=scope, state=state)
        
    def exchange_code_for_token(self, client_id, client_secret, code):
        """
        Exchange the temporary authorization code (returned with redirect from strava authorization URL)
        for a permanent access token.
        
        :param client_id: The numeric developer client id.
        :type client_id: int
        
        :param client_secret: The developer client secret
        :type client_secret: str
        
        :param code: The temporary authorization code
        :type code: str
        
        :return: The access token.
        :rtype: str
        """
        return self.protocol.exchange_code_for_token(client_id=client_id,
                                                     client_secret=client_secret,
                                                     code=code)
    
    
    def get_activities(self, before=None, after=None, limit=None):
        """
        Get activities for authenticated user sorted by newest first.
        
        
        :param before: Result will start with activities whose start date is 
                       before specified date. (UTC)
        :type before: datetime.datetime or str
        
        :param after: Result will start with activities whose start date is after
                      specified value. (UTC)
        :type after: datetime.datetime or str
        
        :param limit: How many maximum activities to return.
        :type limit: int  
        """
        if before and after:
            raise ValueError("Cannot specify both 'before' and 'after' params.")
        
        if before:
            if isinstance(before, str):
                before = dateparser.parse(before, ignoretz=True)
            before = time.mktime(before.timetuple())
        elif after:
            if isinstance(after, str):
                after = dateparser.parse(after, ignoretz=True)
            after = time.mktime(after.timetuple())
        
        params = dict(before=before, after=after)
        result_fetcher = functools.partial(self.protocol.get, '/athlete/activities', **params)
        
        results = BatchedResultsIterator(entity=model.Activity, bind_client=self, result_fetcher=result_fetcher, limit=limit)
        return results 
    
    def get_athlete(self, athlete_id=None):
        """
        Gets the specified athlete; if athlete_id is None then retrieves a detail-
        level representation of currently authenticated athlete; otherwise 
        summary-level representation returned of athlete.
        
        http://strava.github.io/api/v3/athlete/#get-details
        
        http://strava.github.io/api/v3/athlete/#get-another-details
        
        :param: athlete_id: The numeric ID of the athlete to fetch.
        :type: athlete_id: int
        :return: The athlete model object.
        :rtype: :class:`stravalib.model.Athlete`
        """
        if athlete_id is None:
            raw = self.protocol.get('/athlete')
        else:
            raw = self.protocol.get('/athletes/{athlete_id}', athlete_id=athlete_id)
            
        return model.Athlete.deserialize(raw, bind_client=self)
    
    def get_athlete_friends(self, athlete_id=None, limit=None):
        """
        Gets friends for current (or specified) athlete.
        
        http://strava.github.io/api/v3/follow/#friends
        
        :param athlete_id
        :type athlete_id: int
        :param limit: Maximum number of athletes to return (default unlimited).
        :type limit: int
        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        if athlete_id is None:
            result_fetcher = functools.partial(self.protocol.get, '/athlete/friends')
        else:
            result_fetcher = functools.partial(self.protocol.get, '/athletes/{id}/friends', id=athlete_id)
            
        return BatchedResultsIterator(entity=model.Athlete, bind_client=self, result_fetcher=result_fetcher, limit=limit)
    
    def get_athlete_followers(self, athlete_id=None, limit=None):
        """
        Gets followers for current (or specified) athlete.
        
        http://strava.github.io/api/v3/follow/#followers
        
        :param athlete_id
        :type athlete_id: int
        :param limit: Maximum number of athletes to return (default unlimited).
        :type limit: int
        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        if athlete_id is None:
            result_fetcher = functools.partial(self.protocol.get, '/athlete/followers')
        else:
            result_fetcher = functools.partial(self.protocol.get, '/athletes/{id}/followers', id=athlete_id)
            
        return BatchedResultsIterator(entity=model.Athlete, bind_client=self, result_fetcher=result_fetcher, limit=limit)
        
    def get_both_following(self, athlete_id, limit=None):
        """
        Retrieve the athletes who both the authenticated user and the indicated athlete are following.
        
        http://strava.github.io/api/v3/follow/#both
        
        :param athlete_id: The ID of the other athlete (for follower intersection with current athlete) 
        :type athlete_id: int
        :param limit: Maximum number of athletes to return. (default unlimited)
        :type limit: int
        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get, '/athletes/{id}/both-following', id=athlete_id)
        return BatchedResultsIterator(entity=model.Athlete, bind_client=self, result_fetcher=result_fetcher, limit=limit)
        
    def get_athlete_clubs(self):
        """
        List the clubs for the currently authenticated athlete.
        
        http://strava.github.io/api/v3/clubs/#get-athletes
        
        :rtype: list of :class:`stravalib.model.Club`
        """    
        club_structs = self.protocol.get('/athlete/clubs')
        return [model.Club.deserialize(raw, bind_client=self) for raw in club_structs]
    
    def get_club(self, club_id):
        """
        Return a specific club object.
        
        http://strava.github.io/api/v3/clubs/#get-details
        
        :param club_id: The ID of the club to fetch.
        :rtype: :class:`stravalib.model.Club`
        """
        raw = self.protocol.get("/clubs/{id}", id=club_id)
        return model.Club.deserialize(raw, bind_client=self)
    
    def get_club_members(self, club_id, limit=None):
        """
        Gets the member objects for specified club ID.
        
        http://strava.github.io/api/v3/clubs/#get-members
        
        :param club_id: The numeric ID for the club.
        :param limit: Maximum number of athletes to return. (default unlimited)
        :type limit: int
        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get, '/clubs/{id}/members', id=club_id)
        return BatchedResultsIterator(entity=model.Athlete, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)

    def get_club_activities(self, club_id, limit=None):
        """
        Gets the activities associated with specified club.
        
        http://strava.github.io/api/v3/clubs/#get-activities
        
        :param club_id: The numeric ID for the club.
        :param limit: Maximum number of activities to return. (default unlimited)
        :type limit: int
        :return: An iterator of :class:`stravalib.model.Activity` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get, '/clubs/{id}/activities', id=club_id)
        return BatchedResultsIterator(entity=model.Activity, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)


    def get_activity(self, activity_id):
        """
        Gets specified activity.
        
        Will be detail-level if owned by authenticated user; otherwise summary-level.
        
        http://strava.github.io/api/v3/activities/#get-details
        
        :param activity_id: The ID of activity to fetch.
        :rtype: :class:`stravalib.model.Activity`
        """
        raw = self.protocol.get('/activities/{id}', id=activity_id)
        return model.Activity.deserialize(raw, bind_client=self)
    
    def get_friend_activities(self, limit=None):
        """
        Gets activities for friends (of currently authenticated athlete).
        
        http://strava.github.io/api/v3/activities/#get-feed
        
        :param limit: Maximum number of activities to return. (default unlimited)
        :type limit: int
        :return: An iterator of :class:`stravalib.model.Activity` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get, '/activities/following')
        return BatchedResultsIterator(entity=model.Activity, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)

    def create_activity(self, name, activity_type, start_date_local, elapsed_time, description=None, distance=None):
        """
        Create a new manual activity.
        
        If you would like to create an activity from an uploaded GPS file, see the
        :meth:`stravalib.client.Client.upload_activity` method instead. 
        
        :param name: The name of the activity.
        :param activity_type: The activity type (case-insensitive).  
                              Possible values: ride, run, swim, workout, hike, walk, nordicski, 
                              alpineski, backcountryski, iceskate, inlineskate, kitesurf, rollerski, 
                              windsurf, workout, snowboard, snowshoe
        :param start_date: Local date/time of activity start. (TZ info will be ignored)
        :type start_date: :class:`datetime.datetime` or string in ISO8601 format.
        :param elapsed_time: The time in seconds or a :class:`datetime.timedelta` object.
        :type elapsed_time: :class:`datetime.timedelta` or int (seconds)
        :param description: The description for the activity.
        :type description: str
        :param distance: The distance in meters (float) or a :class:`units.quantity.Quantity` instance.
        :type distance: :class:`units.quantity.Quantity` or float (meters)
        """
        if isinstance(elapsed_time, timedelta):
            elapsed_time = unithelper.timedelta_to_seconds(elapsed_time)
        
        if isinstance(distance, Quantity):
            distance = float(unithelper.meters(distance))
            
        if isinstance(start_date_local, datetime):
            start_date_local = start_date_local.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if not activity_type.lower() in [t.lower() for t in model.Activity.TYPES]:
            raise ValueError("Invalid activity type: {0}.  Possible values: {1!r}".format(activity_type, model.Activity.TYPES))
        
        params = dict(name=name, type=activity_type, start_date_local=start_date_local,
                      elapsed_time=elapsed_time)
        
        if description is not None:
            params['description'] = description
        
        if distance is not None:
            params['distance'] = distance
            
        raw_activity = self.protocol.post('/activities', **params)
        
        return model.Activity.deserialize(raw_activity, bind_client=self)

    def update_activity(self, activity_id, name=None, activity_type=None, private=None, commute=None, trainer=None, gear_id=None, description=None):
        """
        Updates the properties of a specific activity.
         
        http://strava.github.io/api/v3/activities/#put-updates
        
        :param activity_id: The ID of the activity to update.
        :param name: The name of the activity.
        :param activity_type: The activity type (case-insensitive).  
                              Possible values: ride, run, swim, workout, hike, walk, nordicski, 
                              alpineski, backcountryski, iceskate, inlineskate, kitesurf, rollerski, 
                              windsurf, workout, snowboard, snowshoe
        :param private: Whether the activity is private.
        :param commute: Whether the activity is a commute.
        :param trainer: Whether this is a trainer activity.
        :param gear_id: Alpha-numeric ID of gear (bike, shoes) used on this activity.
        :param description: Description for the activity.
        :return: The updated activity.
        :rtype: :class:`stravalib.model.Activity`
        """
        
        # Convert the kwargs into a params dict
        params = dict(activity_id=activity_id)
        if name is not None:
            params['name'] = name
        if activity_type is not None:
            if not activity_type.lower() in [t.lower() for t in model.Activity.TYPES]:
                raise ValueError("Invalid activity type: {0}.  Possible values: {1!r}".format(activity_type, model.Activity.TYPES))
            params['type'] = activity_type
        if private is not None:
            params['private'] = int(private)
        if commute is not None:
            params['commute'] = int(commute)
        if trainer is not None:
            params['trainer'] = int(trainer)            
        if gear_id is not None:
            params['gear_id'] = gear_id
            
        raw_activity = self.protocol.put('/activities/{activity_id}', **params)
        return model.Activity.deserialize(raw_activity, bind_client=self)

    def upload_activity(self, activity_file, data_type, name=None, activity_type=None, private=None, external_id=None):
        """
        Uploads a GPS file (tcx, gpx) to create a new activity for current athlete.
        
        http://strava.github.io/api/v3/athlete/#get-details
        
        :param activity_file: The file object to upload or file contents.
        :type activity_file: file or str
        
        :param data_type: File format for upload. Possible values: fit, fit.gz, tcx, tcx.gz, gpx, gpx.gz
        :type data_type: str
        
        :param name: (optional) if not provided, will be populated using start date and location, if available
        :type name: str
        
        :param activity_type: (optional) case-insensitive type of activity. 
                              possible values: ride, run, swim, workout, hike, walk, 
                              nordicski, alpineski, backcountryski, iceskate, inlineskate, 
                              kitesurf, rollerski, windsurf, workout, snowboard, snowshoe
                              Type detected from file overrides, uses athlete's default type if not specified
        :type activity_type: str
        
        :param private: (optional) set to True to mark the resulting activity as private, 'view_private' permissions will be necessary to view the activity
        :type private: bool
        
        :param external_id: (optional) An arbitrary unique identifier may be specified which will be included in status responses.
        :type external_id: str
        """
        if not hasattr(activity_file, 'read'):
            if isinstance(file, unicode):
                activity_file = BytesIO(file.encode('utf-8'))
            elif isinstance(file, str):
                activity_file = BytesIO(file)
            else:
                raise TypeError("Invalid type specified for actvitity_file: {0}".type(file))
        
        valid_data_types = ('fit', 'fit.gz', 'tcx', 'tcx.gz', 'gpx', 'gpx.gz')
        if not data_type in valid_data_types:
            raise ValueError("Invalid data type {0}. Possible vavlues {1!r}".format(data_type, valid_data_types))
        
        params = {'data_type': data_type}
        if name is not None:
            params['activity_name'] = name
        if activity_type is not None:
            if not activity_type.lower() in [t.lower() for t in model.Activity.TYPES]:
                raise ValueError("Invalid activity type: {0}.  Possible values: {1!r}".format(activity_type, model.Activity.TYPES))
            params['activity_type'] = activity_type
        if private is not None:
            params['private'] = int(private)
        if external_id is not None:
            params['external_id'] = external_id
            
        initial_response = self.protocol.post('/uploads', files={'file': activity_file},
                                              check_for_errors=False, **params)
        return ActivityUploader(self, response=initial_response)
    
    def get_activity_zones(self, activity_id):
        """
        Gets zones for activity.
        
        Requires premium account.
        
        http://strava.github.io/api/v3/activities/#zones
        """
        zones = self.protocol.get('/activities/{id}/zones', id=activity_id)
        # We use a factory to give us the correct zone based on type.
        return [model.BaseActivityZone.deserialize(z, bind_client=self) for z in zones]
    
    def get_activity_comments(self, activity_id, markdown=False, limit=None):
        """
        Gets the comments for an activity.
        
        http://strava.github.io/api/v3/comments/#list
        
        :param activity_id: The activity for which to fetch comments.
        :param markdown: Whether to include markdown in comments (default is false/filterout).
        :param limit: Max rows to return (default unlimited).
        :type limit: int
        :return: An iterator of :class:`stravalib.model.ActivityComment` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get, '/activities/{id}/comments',
                                           id=activity_id, markdown=int(markdown))
        return BatchedResultsIterator(entity=model.ActivityComment, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)
    
    def get_gear(self, gear_id):
        """
        Get details for an item of gear.
        
        http://strava.github.io/api/v3/gear/#show
        
        :param gear_id: The gear id.
        :type gear_id: str
        :return: The Bike or Shoe subclass object.
        :rtype: :class:`stravalib.model.Gear`
        """
        return model.Gear.deserialize(self.protocol.get('/gear/{id}', id=gear_id))
    
    def get_segment_effort(self, effort_id):
        """
        Return a specific segment effort by ID.
        
        http://strava.github.io/api/v3/efforts/#retrieve
        
        :param effort_id: The id of associated effort to fetch.
        :rtype: :class:`stravalib.model.SegmentEffort`
        """
        return model.SegmentEffort.deserialize(self.protocol.get('/segment_efforts/{id}', id=effort_id))

    def get_segment(self, segment_id):
        """
        Gets a specific segment by ID.
        
        http://strava.github.io/api/v3/segments/#retrieve
        
        :param segment_id: The segment to fetch.
        :rtype: :class:`stravalib.model.Segment` 
        """
        return model.Segment.deserialize(self.protocol.get('/segments/{id}', id=segment_id), bind_client=self)
    
    def get_segment_leaderboard(self, segment_id, gender=None, age_group=None, weight_class=None, 
                                following=None, club_id=None, timeframe=None, top_results_limit=None):
        """
        Gets the leaderboard for a segment.
        
        http://strava.github.io/api/v3/segments/#leaderboard
        
        Note that by default Strava will return the top 10 results *and then will also include
        the bottom 5 results*.  The top X results can be configured by setting the top_results_limit
        parameter; however,the bottom 5 results are always included.  (i.e. if you specify top_results_limit=15,
        you will get a total of 20 entries back.)
        
        :param segment_id: ID of the segment.
        :param gender: (optional) 'M' or 'F'
        :param age_group: (optional) '0_24', '25_34', '35_44', '45_54', '55_64', '65_plus'
        :param weight_class: (optional) pounds '0_124', '125_149', '150_164', '165_179', '180_199', '200_plus' 
                             or kilograms '0_54', '55_64', '65_74', '75_84', '85_94', '95_plus'
        :param following: (optional) Limit to athletes current user is following.
        :param club_id: (optional) limit to specific club
        :param timeframe: (optional)  'this_year', 'this_month', 'this_week', 'today'
        :param top_results_limit: (optional, strava default is 10 + 5 from end) How many of leading leaderboard entries to display.
                            See description for why this is a little confusing.
        :rtype: :class:`stravalib.model.SegmentLeaderboard`
        """
        params = {}
        if gender is not None:
            if gender.upper() not in ('M', 'F'):
                raise ValueError("Invalid gender: {0}. Possible values: 'M' or 'F'".format(gender))
            params['gender'] = gender
        
        valid_age_groups = ('0_24', '25_34', '35_44', '45_54', '55_64', '65_plus')
        if age_group is not None:
            if not age_group in valid_age_groups:
                raise ValueError("Invalid age group: {0}.  Possible values: {1!r}".format(age_group, valid_age_groups))
            params['age_group'] = age_group
        
        valid_weight_classes = ('0_124', '125_149', '150_164', '165_179', '180_199', '200_plus', 
                                '0_54', '55_64', '65_74', '75_84', '85_94', '95_plus')
        if weight_class is not None:
            if not weight_class in valid_weight_classes:
                raise ValueError("Invalid weight class: {0}.  Possible values: {1!r}".format(weight_class, valid_weight_classes))
            params['weight_class'] = weight_class
        
        if following is not None:
            params['following'] = int(following)
        
        if club_id is not None:
            params['club_id'] = club_id
            
        if timeframe is not None:
            valid_timeframes = 'this_year', 'this_month', 'this_week', 'today'
            if not timeframe in valid_timeframes:
                raise ValueError("Invalid timeframe: {0}.  Possible values: {1!r}".format(timeframe, valid_timeframes))
            params['date_range'] = timeframe
            
        if top_results_limit is not None:
            params['per_page'] = top_results_limit
        
        return model.SegmentLeaderboard.deserialize(self.protocol.get('/segments/{id}/leaderboard',
                                                                      id=segment_id, **params),
                                                    bind_client=self)
    
    def explore_segments(self, bounds, activity_type=None, min_cat=None, max_cat=None):
        """
        Returns an array of up to 10 segments.
        
        http://strava.github.io/api/v3/segments/#explore
        
        :param bounds: list of bounding box corners lat/lon [sw.lat, sw.lng, ne.lat, ne.lng] (south,west,north,east)
        :type bounds: list of 4 floats or list of 2 (lat,lon) tuples
        :param activity_type: (optional, default is riding)  'running' or 'riding'
        :type activity_type: str
        :param min_cat: (optional) Minimum climb category filter
        :type min_cat: int
        :param max_cat: (optional) Maximum climb category filter
        :type max_cat: int
        """
        if len(bounds) == 2:
            bounds = (bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][2])
        elif len(bounds) != 4:
            raise ValueError("Invalid bounds specified: {0!r}. Must be list of 4 float values or list of 2 (lat,lon) tuples.") 
        
        params = {'bounds': ','.join(str(b) for b in bounds)} 
        
        valid_activity_types = ('riding', 'running')
        if activity_type is not None:
            if activity_type not in ('riding', 'running'):
                raise ValueError('Invalid activity type: {0}.  Possible values: {1!r}'.format(activity_type, valid_activity_types))
            params['activity_type'] = activity_type
        
        if min_cat is not None:
            params['min_cat'] = min_cat
        if max_cat is not None:
            params['max_cat'] = max_cat
        
        raw = self.protocol.get('/segments/explore', **params)
        return [model.SegmentExplorerResult.deserialize(v, bind_client=self) for v in raw['segments']]
    
    
    # TODO: Streams
    
class BatchedResultsIterator(object):
    """
    An iterator that enables iterating over requests that return paged results.
    """
    
    default_per_page = 200 #: How many results returned in a batch.  We maximize this to minimize requests to server (rate limiting)
     
    def __init__(self, entity, result_fetcher, bind_client=None, limit=None, per_page=None):
        """
        :param entity: The class for the model entity.
        :type entity: type
                
        :param result_fetcher: The callable that will return another batch of results.
        :type result_fetcher: callable

        :param bind_client: The client object to pass to the entities for supporting further
                             fetching of objects.
        :type bind_client: :class:`stravalib.client.Client`
        
        :param limit: The maximum number of rides to return.
        :type limit: int
        
        :param per_page: How many rows to fetch per page (default is 200).
        :type per_page: int
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.entity = entity
        self.bind_client = bind_client
        self.result_fetcher = result_fetcher
        self.limit = limit
        
        if per_page is not None:
            self.per_page = per_page
        else:
            self.per_page = self.default_per_page
            
        self._counter = 0
        self._buffer = None
        self._page = 1
        self._all_results_fetched = False
    
    def __repr__(self):
        return '<{0} entity={1}>'.format(self.__class__.__name__, self.entity.__name__)
    
    def _fill_buffer(self):
        """
        Fills the internal size-50 buffer from Strava API.
        """
        # If we cannot fetch anymore from the server then we're done here.
        if self._all_results_fetched:
            raise StopIteration
        
        raw_results = self.result_fetcher(page=self._page, per_page=self.per_page)
        entities = []
        for raw in raw_results:
            entities.append(self.entity.deserialize(raw, bind_client=self.bind_client))
            
        self._buffer = collections.deque(entities)
        
        self.log.debug("Requested page {0} (got: {1} items)".format(self._page,
                                                                    len(self._buffer)))
        if len(self._buffer) < self.per_page:
            self._all_results_fetched = True
        
        self._page += 1

    def __iter__(self):
        return self
    
    def next(self):
        if self.limit and self._counter >= self.limit:
            raise StopIteration
        if not self._buffer:
            self._fill_buffer()
        try:
            result = self._buffer.popleft()
        except IndexError:
            raise StopIteration
        else:
            self._counter += 1
            return result

class ActivityUploader(object):
    """
    The "future" object that holds information about an activity file upload and can
    wait for upload to finish, etc.
    """
    
    def __init__(self, client, response):
        """
        :param client: The :class:`stravalib.client.Client` object that is handling the upload.
        :type client: :class:`stravalib.client.Client`
        :param response: The initial upload response.
        :type response: dict
        """
        self.client = client
        self.update_from_repsonse(response)
        
    def update_from_repsonse(self, response, raise_exc=True):
        """
        Updates internal state of object.
        
        :param response: The response object (dict).
        :type response: dict
        :param raise_exc: Whether to raise an exception if the response indicates an error state. (default True)
        :type raise_exc: bool 
        :raise stravalib.exc.ActivityUploadFailed: If the response indicates an error and raise_exc is True. 
        """
        self.upload_id = response['id']
        self.external_id = response.get('external_id')
        self.activity_id = response.get('activity_id')
        self.status = response['status']
        self.error = response['error']
        if raise_exc:
            self.raise_for_error()
    
    @property
    def is_processing(self):
        return (self.activity_id is None and self.error is None)
    
    @property
    def is_error(self):
        return (self.error is not None)
    
    @property
    def is_complete(self):
        return (self.activity_id is not None)
    
    def raise_for_error(self):
        if self.error:
            raise exc.ActivityUploadFailed(self.error)
        elif self.status == "The created activity has been deleted.":
            raise exc.CreatedActivityDeleted(self.status)
        
    def poll(self):
        """
        Update internal state from polling strava.com. 
        
        :raise stravalib.exc.ActivityUploadFailed: If the poll returns an error.
        """
        response = self.client.protocol.get('/uploads/{upload_id}', upload_id=self.upload_id, check_for_errors=False)
        self.update_from_repsonse(response)
        
    def wait(self, timeout=None, poll_interval=1.0):
        """
        Wait for the upload to complete or to err out.
        
        Will return the resulting Activity or raise an exception if the upload fails.
        
        :param timeout: The max seconds to wait. Will raise TimeoutExceeded exception if this 
                        time passes without success or error response.
        :type timeout: float
        :param poll_interval: How long to wait between upload checks.  Strava recommends 1s minimum. (default 1.0s)
        :type poll_interval: float
        :return: The uploaded Activity object (fetched from server)
        :rtype: :class:`stravalib.model.Activity`
        :raise stravalib.exc.TimeoutExceeded: If a timeout was specified and activity is 
                                              still processing after timeout has elapsed.
        :raise stravalib.exc.ActivityUploadFailed: If the poll returns an error.
        """
        start = time.time()
        while self.activity_id is None:
            self.poll()
            time.sleep(poll_interval)
            if timeout and (time.time() - start) > timeout:
                raise exc.TimeoutExceeded()
        # If we got this far, we must have an activity!        
        return self.client.get_activity(self.activity_id)