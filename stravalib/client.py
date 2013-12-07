"""
Providing a simplified, protocol-version-abstracting interface to Strava web services. 
"""
import logging
import functools
import time
import collections

from dateutil.parser import parser as dateparser

from stravalib import model
from stravalib.protocol import ApiV3
from stravalib.util import limiter

# TODO: "constants" for access scopes?
# 
#public    default, private activities are not returned, privacy zones are respected in stream requests
#write    modify activities, upload on the user's behalf
#view_private    view private activities and data within privacy zones
#view_private,write    both 'write' and 'view_private' access



class Client(object):
    """
    Main client class for interacting with the Strava backends.
    
    This class abstracts interactions with Strava's various protocols (REST v1 & v2,
    the main website) to provide a simple and full-featured API.
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
        return self.protocol.access_token
    
    @access_token.setter
    def access_token(self, v):
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
    
    
    def get_activities(self, limit=50, before=None, after=None, page=None, per_page=None):
        """
        Get activities for authenticated user sorted by newest first.
        
        :param limit: 
        :param before: Result will start with activities whose start date is 
                       before specified date. (UTC)
        :type before: datetime.datetime or str
        :param after: Result will start with activities whose start date is after
                      specified value. (UTC)
        :type after: datetime.datetime or str
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
        
        params = dict(before=before, after=after, page=page, per_page=per_page)
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
        :rtype: dict
        """
        if athlete_id is None:
            raw = self.protocol.get('/athlete')
        else:
            raw = self.protocol.get('/athletes/{athlete_id}', athlete_id=athlete_id)
            
        return model.Athlete.deserialize(raw, bind_client=self)
    
    def get_athlete_friends(self, athlete_id=None, limit=50):
        """
        http://strava.github.io/api/v3/follow/#friends
        
        :param athlete_id
        :param limit: Maximum number of athletes to return.
        """
        if athlete_id is None:
            result_fetcher = functools.partial(self.protocol.get, '/athlete/friends')
        else:
            result_fetcher = functools.partial(self.protocol.get, '/athletes/{id}/friends', id=athlete_id)
            
        return BatchedResultsIterator(entity=model.Activity, bind_client=self, result_fetcher=result_fetcher, limit=limit)
    
    def get_athlete_followers(self, athlete_id=None, limit=50):
        """
        http://strava.github.io/api/v3/follow/#followers
        
        :param athlete_id
        :param limit: Maximum number of athletes to return.
        """
        if athlete_id is None:
            result_fetcher = functools.partial(self.protocol.get, '/athlete/followers')
        else:
            result_fetcher = functools.partial(self.protocol.get, '/athletes/{id}/followers', id=athlete_id)
            
        return BatchedResultsIterator(entity=model.Athlete, bind_client=self, result_fetcher=result_fetcher, limit=limit)
        
    def get_both_following(self, athlete_id, limit=50):
        """
        Retrieve the athletes who both the authenticated user and the indicated athlete are following.
        
        http://strava.github.io/api/v3/follow/#both
        
        :param athlete_id
        :param limit: Maximum number of athletes to return.
        """
        result_fetcher = functools.partial(self.protocol.get, '/athletes/{id}/both-following', id=athlete_id)
        return BatchedResultsIterator(entity=model.Athlete, bind_client=self, result_fetcher=result_fetcher, limit=limit)
        
    def update_athlete(self, **kwargs):
        """
        http://strava.github.io/api/v3/athlete/#get-details
        """
        raise NotImplementedError()
    
    def get_athlete_clubs(self):
        """
        List the clubs for the currently authenticated athlete.
        
        http://strava.github.io/api/v3/clubs/#get-athletes
        
        :rtype: list
        """    
        club_structs = self.protocol.get('/athlete/clubs')
        return [model.Club.deserialize(raw, bind_client=self) for raw in club_structs]
    
    def get_club(self, club_id):
        """
        Return V3 object structure for club
        http://strava.github.io/api/v3/clubs/#get-details
        
        :param club_id: The ID of the club to fetch.
        """
        raw = self.protocol.get("/clubs/{id}", id=club_id)
        return model.Club.deserialize(raw, bind_client=self)
    
    def get_club_members(self, club_id, limit=50):
        """
        Gets the member objects for specified club ID.
        http://strava.github.io/api/v3/clubs/#get-members
        
        :param club_id: The numeric ID for the club.
        """
        result_fetcher = functools.partial(self.protocol.get, '/clubs/{id}/members', id=club_id)
        return BatchedResultsIterator(entity=model.Athlete, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)

    def get_club_activities(self, club_id, limit=50):
        """
        Gets the activities associated with specified club.
        http://strava.github.io/api/v3/clubs/#get-activities
        
        :param club_id: The numeric ID for the club.
        """
        result_fetcher = functools.partial(self.protocol.get, '/clubs/{id}/activities', id=club_id)
        return BatchedResultsIterator(entity=model.Activity, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)


    def get_activity(self, activity_id):
        """
        Gets specified activity.
        
        Will be detail-level if owned by authenticated user; otherwise summary-level.
        
        http://strava.github.io/api/v3/activities/#get-details
        
        :param activity_id: The activity_id of ride to fetch.
        """
        raw = self.protocol.get('/activities/{id}', id=activity_id)
        return model.Activity.deserialize(raw, bind_client=self)
    
    def get_friend_activities(self, limit=50):
        """
        http://strava.github.io/api/v3/activities/#get-feed
        """
        result_fetcher = functools.partial(self.protocol.get, '/activities/following')
        return BatchedResultsIterator(entity=model.Activity, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)

    def update_activity(self, **kwargs):
        """
        http://strava.github.io/api/v3/activities/#put-updates
        """
        raise NotImplementedError()
    
    def get_activity_zones(self, activity_id):
        """
        http://strava.github.io/api/v3/activities/#zones
        """
        zones = self.protocol.get('/activities/{id}/zones', id=activity_id)
        # We use a factory to give us the correct zone based on type.
        return [model.BaseActivityZone.deserialize(z) for z in zones]
    
    def get_gear(self, gear_id):
        """
        Get details for an item of gear.
        http://strava.github.io/api/v3/gear/#show
        
        :param gear_id: The gear id.
        :type gear_id: str
        """
        return model.Gear.deserialize(self.protocol.get('/gear/{id}', id=gear_id))
    
    def get_segment_effort(self, effort_id):
        """
        Return detailed structure for segment efforts.
        
        http://strava.github.io/api/v3/efforts/#retrieve
        
        :param effort_id: The id of associated effort to fetch.
        """
        return model.SegmentEffort.deserialize(self.protocol.get('/segment_efforts/{id}', id=effort_id))

    def get_segment(self, segment_id):
        """
        http://strava.github.io/api/v3/segments/#retrieve 
        """
        return model.Segment.deserialize(self.protocol.get('/segments/{id}', id=segment_id))
    
    def get_segment_leaderboard(self, segment_id):
        """
        http://strava.github.io/api/v3/segments/#leaderboard
        """
        raise NotImplementedError()
    
    def explore_segments(self, bounds, activity_type, min_cat, max_cat):
        """
        Returns an array of up to 10 segments.
        http://strava.github.io/api/v3/segments/#explore
        """
        assert activity_type in ('riding', 'running')
        raise NotImplementedError()
    
    # TODO: Streams
    # TODO: Uploads
    # TODO: fun.
    
class BatchedResultsIterator(object):
    """
    Iterates over requests that return a batch of (typically 50) results and support an offset parameter.
    
    For example, Strava API only returns 50 rides at a time, so this provides a mechanism to abstract over
    that limitation. 
    """
    
    default_per_page = 50 #: How many results returned in a batch.
     
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
        
        :param per_page: How many rows to fetch per page (default is 50).
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
        self._page = 0
        self._all_results_fetched = False
    
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
        