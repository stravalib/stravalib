"""
Provides the main interface classes for the Strava version 3 REST API.
"""
import logging
import functools
import time
import collections
import calendar
from io import BytesIO
from datetime import datetime, timedelta

import pytz

from dateutil.parser import parser
dateparser = parser()

from units.quantity import Quantity

from stravalib3 import model, exc
from stravalib3.protocol import ApiV3
from stravalib3.util import limiter
from stravalib3 import unithelper

try:
    str
except:
    str = str


class Client(object):
    """
    Main client class for interacting with the exposed Strava v3 API methods.

    This class can be instantiated without an access_token when performing authentication;
    however, most methods will require a valid access token.
    """

    def __init__(self, access_token=None, rate_limit_requests=True,
                 rate_limiter=None, requests_session=None):
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

        :param requests_session: (Optional) pass request session object.
        :type requests_session: requests.Session() object

        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))

        if rate_limit_requests:
            if not rate_limiter:
                rate_limiter = limiter.DefaultRateLimiter()
        elif rate_limiter:
            raise ValueError("Cannot specify rate_limiter object when rate_limit_requests is False")

        self.protocol = ApiV3(access_token=access_token,
                              requests_session=requests_session,
                              rate_limiter=rate_limiter)

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

    def authorization_url(self, client_id, redirect_uri, approval_prompt='auto',
                          scope=None, state=None):
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
        return self.protocol.authorization_url(client_id=client_id,
                                               redirect_uri=redirect_uri,
                                               approval_prompt=approval_prompt,
                                               scope=scope, state=state)

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
        :rtype: :py:class:`str`
        """
        return self.protocol.exchange_code_for_token(client_id=client_id,
                                                     client_secret=client_secret,
                                                     code=code)
                                                     
    def deauthorize(self):
        """
        Deauthorize the application. This causes the application to be removed
        from the athlete's "My Apps" settings page.

        See http://strava.github.io/api/v3/oauth/#deauthorization
        """
        self.protocol.post("oauth/deauthorize")

    def _utc_datetime_to_epoch(self, activity_datetime):
        """
        Convert the specified datetime value to a unix epoch timestamp (seconds since epoch).

        :param activity_datetime: A string which may contain tzinfo (offset) or a datetime object (naive datetime will
                                    be considered to be UTC).
        :return: Epoch timestamp.
        :rtype: int
        """
        if isinstance(activity_datetime, str):
            activity_datetime = dateparser.parse(activity_datetime)
        assert isinstance(activity_datetime, datetime)
        if activity_datetime.tzinfo:
            activity_datetime = activity_datetime.astimezone(pytz.utc)

        return calendar.timegm(activity_datetime.timetuple())

    def get_activities(self, before=None, after=None, limit=None):
        """
        Get activities for authenticated user sorted by newest first.

        http://strava.github.io/api/v3/activities/


        :param before: Result will start with activities whose start date is
                       before specified date. (UTC)
        :type before: datetime.datetime or str or None

        :param after: Result will start with activities whose start date is after
                      specified value. (UTC)
        :type after: datetime.datetime or str or None

        :param limit: How many maximum activities to return.
        :type limit: int or None

        :return: An iterator of :class:`stravalib.model.Activity` objects.
        :rtype: :class:`BatchedResultsIterator`
        """

        if before:
            before = self._utc_datetime_to_epoch(before)

        if after:
            after = self._utc_datetime_to_epoch(after)

        params = dict(before=before, after=after)
        result_fetcher = functools.partial(self.protocol.get,
                                           '/athlete/activities',
                                           **params)

        return BatchedResultsIterator(entity=model.Activity,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

    def get_athlete(self, athlete_id=None):
        """
        Gets the specified athlete; if athlete_id is None then retrieves a
        detail-level representation of currently authenticated athlete;
        otherwise summary-level representation returned of athlete.

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

        :param: athlete_id
        :type: athlete_id: int

        :param limit: Maximum number of athletes to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        if athlete_id is None:
            result_fetcher = functools.partial(self.protocol.get, '/athlete/friends')
        else:
            result_fetcher = functools.partial(self.protocol.get,
                                               '/athletes/{id}/friends',
                                               id=athlete_id)

        return BatchedResultsIterator(entity=model.Athlete,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

    def update_athlete(self, city=None, state=None, country=None, sex=None, weight=None):
        """
        Updates the properties of the authorized athlete.

        http://strava.github.io/api/v3/athlete/#update

        :param city: City the athlete lives in
        :param state: State the athlete lives in
        :param country: Country the athlete lives in
        :param sex: Sex of the athlete
        :param weight: Weight of the athlete in kg (float)

        :return: The updated athlete
        :rtype: :class:`stravalib.model.Athlete`
        """
        params = {'city': city,
                  'state': state,
                  'country': country,
                  'sex': sex}
        params = {k: v for (k, v) in params.items() if v is not None}
        if weight is not None:
            params['weight'] = float(weight)

        raw_athlete = self.protocol.put('/athlete', **params)
        return model.Athlete.deserialize(raw_athlete, bind_client=self)

    def get_athlete_followers(self, athlete_id=None, limit=None):
        """
        Gets followers for current (or specified) athlete.

        http://strava.github.io/api/v3/follow/#followers

        :param: athlete_id
        :type athlete_id: int

        :param limit: Maximum number of athletes to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        if athlete_id is None:
            result_fetcher = functools.partial(self.protocol.get, '/athlete/followers')
        else:
            result_fetcher = functools.partial(self.protocol.get,
                                               '/athletes/{id}/followers',
                                               id=athlete_id)

        return BatchedResultsIterator(entity=model.Athlete,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

    def get_both_following(self, athlete_id, limit=None):
        """
        Retrieve the athletes who both the authenticated user and the indicated
         athlete are following.

        http://strava.github.io/api/v3/follow/#both

        :param athlete_id: The ID of the other athlete (for follower intersection with current athlete)
        :type athlete_id: int

        :param limit: Maximum number of athletes to return. (default unlimited)
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get,
                                           '/athletes/{id}/both-following',
                                           id=athlete_id)

        return BatchedResultsIterator(entity=model.Athlete,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

    def get_athlete_koms(self, athlete_id, limit=None):
        """
        Gets Q/KOMs/CRs for specified athlete.

        KOMs are returned as `stravalib.model.SegmentEffort` objects.

        http://strava.github.io/api/v3/athlete/#koms

        :param athlete_id: The ID of the athlete.
        :type athlete_id: int

        :param limit: Maximum number of KOM segment efforts to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.SegmentEffort` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get,
                                           '/athletes/{id}/koms',
                                           id=athlete_id)

        return BatchedResultsIterator(entity=model.SegmentEffort,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

    def get_athlete_stats(self, athlete_id=None):
        """
        Returns Statistics for the athlete.
        athlete_id must be the id of the authenticated athlete or left blank.
        If it is left blank two requests will be made - first to get the
        authenticated athlete's id and second to get the Stats.

        http://strava.github.io/api/v3/athlete/#stats

        :return: A model containing the Stats
        :rtype: :py:class:`stravalib.model.AthleteStats`
        """
        if athlete_id is None:
            athlete_id = self.get_athlete().id

        raw = self.protocol.get('/athletes/{id}/stats', id=athlete_id)
        # TODO: Better error handling - this will return a 401 if this athlete
        #       is not the authenticated athlete.

        return model.AthleteStats.deserialize(raw)

    def get_athlete_clubs(self):
        """
        List the clubs for the currently authenticated athlete.

        http://strava.github.io/api/v3/clubs/#get-athletes

        :return: A list of :class:`stravalib.model.Club`
        :rtype: :py:class:`list`
        """
        club_structs = self.protocol.get('/athlete/clubs')
        return [model.Club.deserialize(raw, bind_client=self) for raw in club_structs]

    def join_club(self, club_id):
        """
        Joins the club on behalf of authenticated athlete.

        (Access token with write permissions required.)

        :param club_id: The numeric ID of the club to join.
        """
        self.protocol.post('clubs/{id}/join', id=club_id)

    def leave_club(self, club_id):
        """
        Leave club on behalf of authenticated user.

        (Acces token with write permissions required.)

        :param club_id:
        """
        self.protocol.post('clubs/{id}/leave', id=club_id)

    def get_club(self, club_id):
        """
        Return a specific club object.

        http://strava.github.io/api/v3/clubs/#get-details

        :param club_id: The ID of the club to fetch.
        :type club_id: int

        :rtype: :class:`stravalib.model.Club`
        """
        raw = self.protocol.get("/clubs/{id}", id=club_id)
        return model.Club.deserialize(raw, bind_client=self)

    def get_club_members(self, club_id, limit=None):
        """
        Gets the member objects for specified club ID.

        http://strava.github.io/api/v3/clubs/#get-members

        :param club_id: The numeric ID for the club.
        :type club_id: int

        :param limit: Maximum number of athletes to return. (default unlimited)
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get,
                                           '/clubs/{id}/members',
                                           id=club_id)

        return BatchedResultsIterator(entity=model.Athlete, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)

    def get_club_activities(self, club_id, limit=None):
        """
        Gets the activities associated with specified club.

        http://strava.github.io/api/v3/clubs/#get-activities

        :param club_id: The numeric ID for the club.
        :type club_id: int

        :param limit: Maximum number of activities to return. (default unlimited)
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Activity` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get,
                                           '/clubs/{id}/activities',
                                           id=club_id)

        return BatchedResultsIterator(entity=model.Activity, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)

    def get_activity(self, activity_id, include_all_efforts=False):
        """
        Gets specified activity.

        Will be detail-level if owned by authenticated user; otherwise summary-level.

        http://strava.github.io/api/v3/activities/#get-details

        :param activity_id: The ID of activity to fetch.
        :type activity_id: int

        :param inclue_all_efforts: Whether to include segment efforts - only
                                   available to the owner of the activty.
        :type include_all_efforts: bool

        :rtype: :class:`stravalib.model.Activity`
        """
        raw = self.protocol.get('/activities/{id}', id=activity_id,
                                include_all_efforts=include_all_efforts)
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

    def create_activity(self, name, activity_type, start_date_local, elapsed_time,
                        description=None, distance=None):
        """
        Create a new manual activity.

        If you would like to create an activity from an uploaded GPS file, see the
        :meth:`stravalib.client.Client.upload_activity` method instead.

        :param name: The name of the activity.
        :type name: str

        :param activity_type: The activity type (case-insensitive).
                              Possible values: ride, run, swim, workout, hike, walk, nordicski,
                              alpineski, backcountryski, iceskate, inlineskate, kitesurf, rollerski,
                              windsurf, workout, snowboard, snowshoe
        :type activity_type: str

        :param start_date_local: Local date/time of activity start. (TZ info will be ignored)
        :type start_date_local: :class:`datetime.datetime` or string in ISO8601 format.

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

    def update_activity(self, activity_id, name=None, activity_type=None,
                        private=None, commute=None, trainer=None, gear_id=None,
                        description=None):
        """
        Updates the properties of a specific activity.

        http://strava.github.io/api/v3/activities/#put-updates

        :param activity_id: The ID of the activity to update.
        :type activity_id: int

        :param name: The name of the activity.
        :param activity_type: The activity type (case-insensitive).
                              Possible values: ride, run, swim, workout, hike,
                              walk, nordicski, alpineski, backcountryski,
                              iceskate, inlineskate, kitesurf, rollerski,
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

    def upload_activity(self, activity_file, data_type, name=None, description=None,
                        activity_type=None, private=None, external_id=None):
        """
        Uploads a GPS file (tcx, gpx) to create a new activity for current athlete.

        http://strava.github.io/api/v3/athlete/#get-details

        :param activity_file: The file object to upload or file contents.
        :type activity_file: file or str

        :param data_type: File format for upload. Possible values: fit, fit.gz, tcx, tcx.gz, gpx, gpx.gz
        :type data_type: str

        :param name: (optional) if not provided, will be populated using start date and location, if available
        :type name: str

        :param description: (optional) The description for the activity
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
            if isinstance(activity_file, str):
                activity_file = BytesIO(activity_file.encode('utf-8'))
            elif isinstance(activity_file, str):
                activity_file = BytesIO(activity_file)
            else:
                raise TypeError("Invalid type specified for activity_file: {0}".format(type(file)))

        valid_data_types = ('fit', 'fit.gz', 'tcx', 'tcx.gz', 'gpx', 'gpx.gz')
        if not data_type in valid_data_types:
            raise ValueError("Invalid data type {0}. Possible values {1!r}".format(data_type, valid_data_types))

        params = {'data_type': data_type}
        if name is not None:
            params['name'] = name
        if description is not None:
            params['description'] = description
        if activity_type is not None:
            if not activity_type.lower() in [t.lower() for t in model.Activity.TYPES]:
                raise ValueError("Invalid activity type: {0}.  Possible values: {1!r}".format(activity_type, model.Activity.TYPES))
            params['activity_type'] = activity_type
        if private is not None:
            params['private'] = int(private)
        if external_id is not None:
            params['external_id'] = external_id

        initial_response = self.protocol.post('/uploads',
                                              files={'file': activity_file},
                                              check_for_errors=False,
                                              **params)

        return ActivityUploader(self, response=initial_response)

    def get_activity_zones(self, activity_id):
        """
        Gets zones for activity.

        Requires premium account.

        http://strava.github.io/api/v3/activities/#zones

        :param activity_id: The activity for which to zones.
        :type activity_id: int

        :return: An list of :class:`stravalib.model.ActivityComment` objects.
        :rtype: :py:class:`list`
        """
        zones = self.protocol.get('/activities/{id}/zones', id=activity_id)
        # We use a factory to give us the correct zone based on type.
        return [model.BaseActivityZone.deserialize(z, bind_client=self) for z in zones]

    def get_activity_comments(self, activity_id, markdown=False, limit=None):
        """
        Gets the comments for an activity.

        http://strava.github.io/api/v3/comments/#list

        :param activity_id: The activity for which to fetch comments.
        :type activity_id: int

        :param markdown: Whether to include markdown in comments (default is false/filterout).
        :type markdown: bool

        :param limit: Max rows to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.ActivityComment` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get, '/activities/{id}/comments',
                                           id=activity_id, markdown=int(markdown))

        return BatchedResultsIterator(entity=model.ActivityComment,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

    def get_activity_kudos(self, activity_id, limit=None):
        """
        Gets the kudos for an activity.

        http://strava.github.io/api/v3/kudos/#list

        :param activity_id: The activity for which to fetch kudos.
        :type activity_id: int

        :param limit: Max rows to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.ActivityKudos` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get,
                                           '/activities/{id}/kudos',
                                           id=activity_id)

        return BatchedResultsIterator(entity=model.ActivityKudos,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

    def get_activity_photos(self, activity_id):
        """
        Gets the photos from an activity.

        http://strava.github.io/api/v3/photos/

        :param activity_id: The activity for which to fetch kudos.
        :type activity_id: int

        :return: An iterator of :class:`stravalib.model.ActivityPhoto` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get,
                                           '/activities/{id}/photos',
                                           id=activity_id)

        return BatchedResultsIterator(entity=model.ActivityPhoto,
                                      bind_client=self,
                                      result_fetcher=result_fetcher)

    def get_activity_laps(self, activity_id):
        """
        Gets the laps from an activity.

        http://strava.github.io/api/v3/activities/#laps

        :param activity_id: The activity for which to fetch laps.
        :type activity_id: int

        :return: An iterator of :class:`stravalib.model.ActivityLaps` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get,
                                           '/activities/{id}/laps',
                                           id=activity_id)

        return BatchedResultsIterator(entity=model.ActivityLap,
                                      bind_client=self,
                                      result_fetcher=result_fetcher)

    def get_related_activities(self, activity_id, limit=None):
        """
        Returns the activities that were matched as 'with this activity'.

        http://strava.github.io/api/v3/activities/#get-related

        :param activity_id: The activity for which to fetch related activities.
        :type activity_id: int

        :return: An iterator of :class:`stravalib.model.Activity` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(self.protocol.get,
                                           '/activities/{id}/related',
                                           id=activity_id)

        return BatchedResultsIterator(entity=model.Activity,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

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
        :type effort_id: int

        :return: The specified effort on a segment.
        :rtype: :class:`stravalib.model.SegmentEffort`
        """
        return model.SegmentEffort.deserialize(self.protocol.get('/segment_efforts/{id}',
                                                                 id=effort_id))

    def get_segment(self, segment_id):
        """
        Gets a specific segment by ID.

        http://strava.github.io/api/v3/segments/#retrieve

        :param segment_id: The segment to fetch.
        :type segment_id: int

        :return: A segment object.
        :rtype: :class:`stravalib.model.Segment`
        """
        return model.Segment.deserialize(self.protocol.get('/segments/{id}',
                                         id=segment_id), bind_client=self)

    def get_starred_segment(self, limit=None):
        """
        Returns a summary representation of the segments starred by the
         authenticated user. Pagination is supported.

        http://strava.github.io/api/v3/segments/#starred

        :param limit: (optional), limit number of starred segments returned.
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Segment` starred by authenticated user.
        :rtype: :class:`BatchedResultsIterator`
        """

        params = {}
        if limit is not None:
            params["limit"] = limit

        result_fetcher = functools.partial(self.protocol.get,
                                           '/segments/starred')

        return BatchedResultsIterator(entity=model.Segment,
                                      bind_client=self,
                                      result_fetcher=result_fetcher,
                                      limit=limit)

    def get_segment_leaderboard(self, segment_id, gender=None, age_group=None, weight_class=None,
                                following=None, club_id=None, timeframe=None, top_results_limit=None,
                                page=None):
        """
        Gets the leaderboard for a segment.

        http://strava.github.io/api/v3/segments/#leaderboard

        Note that by default Strava will return the top 10 results, and if the current user has ridden
        that segment, the current user's result along with the two results above in rank and the two
        results below will be included.  The top X results can be configured by setting the top_results_limit
        parameter; however, the other 5 results will be included if the current user has ridden that segment.
        (i.e. if you specify top_results_limit=15, you will get a total of 20 entries back.)

        :param segment_id: ID of the segment.
        :type segment_id: int

        :param gender: (optional) 'M' or 'F'
        :type gender: str

        :param age_group: (optional) '0_24', '25_34', '35_44', '45_54', '55_64', '65_plus'
        :type age_group: str

        :param weight_class: (optional) pounds '0_124', '125_149', '150_164', '165_179', '180_199', '200_plus'
                             or kilograms '0_54', '55_64', '65_74', '75_84', '85_94', '95_plus'
        :type weight_class: str

        :param following: (optional) Limit to athletes current user is following.
        :type following: bool

        :param club_id: (optional) limit to specific club
        :type club_id: int

        :param timeframe: (optional)  'this_year', 'this_month', 'this_week', 'today'
        :type timeframe: str

        :param top_results_limit: (optional, strava default is 10 + 5 from end) How many of leading leaderboard entries to display.
                            See description for why this is a little confusing.
        :type top_results_limit: int

        :param page: (optional, strava default is 1) Page number of leaderboard to return, sorted by highest ranking leaders
        :type page: int

        :return: The SegmentLeaderboard for the specified page (default: 1)
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

        if page is not None:
            params['page'] = page

        return model.SegmentLeaderboard.deserialize(self.protocol.get('/segments/{id}/leaderboard',
                                                                      id=segment_id,
                                                                      **params),
                                                    bind_client=self)

    def get_segment_efforts(self, segment_id, athlete_id=None,
                            start_date_local=None, end_date_local=None,
                            limit=None):
        """
        Gets all efforts on a particular segment sorted by start_date_local

        Returns an array of segment effort summary representations sorted by
        start_date_local ascending or by elapsed_time if an athlete_id is
        provided.

        If no filtering parameters is provided all efforts for the segment
        will be returned.

        Date range filtering is accomplished using an inclusive start and end time,
        thus start_date_local and end_date_local must be sent together. For open
        ended ranges pick dates significantly in the past or future. The
        filtering is done over local time for the segment, so there is no need
        for timezone conversion. For example, all efforts on Jan. 1st, 2014
        for a segment in San Francisco, CA can be fetched using
        2014-01-01T00:00:00Z and 2014-01-01T23:59:59Z.

        http://strava.github.io/api/v3/segments/#all_efforts

        :param segment_id: ID of the segment.
        :type segment_id: param

        :int athlete_id: (optional) ID of athlete.
        :type athlete_id: int

        :param start_date_local: (optional) efforts before this date will be excluded.
                                            Either as ISO8601 or datetime object
        :type start_date_local: datetime.datetime or str

        :param end_date_local: (optional) efforts after this date will be excluded.
                                           Either as ISO8601 or datetime object
        :type end_date_local: datetime.datetime or str

        :param top_results_limit: (optional), limit number of efforts.
        :type results_limit: int

        :return: An iterator of :class:`stravalib.model.SegmentEffort` efforts on a segment.
        :rtype: :class:`BatchedResultsIterator`

        """
        params = {"segment_id": segment_id}

        if athlete_id is not None:
            params['athlete_id'] = athlete_id

        if start_date_local:
            if isinstance(start_date_local, str):
                start_date_local = dateparser.parse(start_date_local, ignoretz=True)
            params["start_date_local"] = start_date_local.strftime("%Y-%m-%dT%H:%M:%SZ")

        if end_date_local:
            if isinstance(end_date_local, str):
                end_date_local = dateparser.parse(end_date_local, ignoretz=True)
            params["end_date_local"] = end_date_local.strftime("%Y-%m-%dT%H:%M:%SZ")

        if limit is not None:
            params["limit"] = limit

        result_fetcher = functools.partial(self.protocol.get,
                                           '/segments/{}/all_efforts'.format(segment_id),
                                           **params)

        return BatchedResultsIterator(entity=model.BaseEffort, bind_client=self,
                                      result_fetcher=result_fetcher, limit=limit)

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

        :return: An list of :class:`stravalib.model.Segment`.
        :rtype: :py:class:`list`

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
        return [model.SegmentExplorerResult.deserialize(v, bind_client=self)
                for v in raw['segments']]

    def get_activity_streams(self, activity_id, types=None,
                             resolution=None, series_type=None):
        """
        Returns an streams for an activity.

        http://strava.github.io/api/v3/streams/#activity

        Streams represent the raw data of the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                           heartrate, cadence, watts, temp, moving, grade_smooth

        http://strava.github.io/api/v3/streams/#activity

        :param activity_id: The ID of activity.
        :type activity_id: int

        :param types: (optional) A list of the the types of streams to fetch.
        :type types: list

        :param resolution: (optional, default is 'all') indicates desired number
                            of data points. 'low' (100), 'medium' (1000),
                            'high' (10000) or 'all'.
        :type resolution: str

        :param series_type: (optional, default is 'distance'.  Relevant only if
                             using resolution either 'time' or 'distance'.
                             Used to index the streams if the stream is being
                             reduced.
        :type series_type: str

        :return: An dictionary of :class:`stravalib.model.Stream` from the activity.
        :rtype: :py:class:`dict`

        """

        # stream are comma seperated list
        if types is not None:
            types = ",".join(types)

        params = {}
        if resolution is not None:
            params["resolution"] = resolution

        if series_type is not None:
            params["series_type"] = series_type

        result_fetcher = functools.partial(self.protocol.get,
                                           '/activities/{id}/streams/{types}'.format(id=activity_id, types=types),
                                           **params)

        streams = BatchedResultsIterator(entity=model.Stream,
                                         bind_client=self,
                                         result_fetcher=result_fetcher)

        # Pack streams into dictionary
        return {i.type: i for i in streams}

    def get_effort_streams(self, effort_id, types=None, resolution=None,
                           series_type=None):
        """
        Returns an streams for an effort.

        http://strava.github.io/api/v3/streams/#effort

        Streams represent the raw data of the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                           heartrate, cadence, watts, temp, moving, grade_smooth

        http://strava.github.io/api/v3/streams/#effort

        :param effort_id: The ID of effort.
        :type effort_id: int

        :param types: (optional) A list of the the types of streams to fetch.
        :type types: list

        :param resolution: (optional, default is 'all') indicates desired number
                            of data points. 'low' (100), 'medium' (1000),
                            'high' (10000) or 'all'.
        :type resolution: str

        :param series_type: (optional, default is 'distance'.  Relevant only if
                             using resolution either 'time' or 'distance'.
                             Used to index the streams if the stream is being
                             reduced.
        :type series_type: str

        :return: An dictionary of :class:`stravalib.model.Stream` from the effort.
        :rtype: :py:class:`dict`

        """

        # stream are comma seperated list
        if types is not None:
            types = ",".join(types)

        params = {}
        if resolution is not None:
            params["resolution"] = resolution

        if series_type is not None:
            params["series_type"] = series_type

        result_fetcher = functools.partial(self.protocol.get,
                                           '/segment_efforts/{id}/streams/{types}'.format(id=effort_id, types=types),
                                           **params)

        streams = BatchedResultsIterator(entity=model.Stream,
                                         bind_client=self,
                                         result_fetcher=result_fetcher)

        # Pack streams into dictionary
        return {i.type: i for i in streams}

    def get_segment_streams(self, segment_id, types=None, resolution=None,
                            series_type=None):
        """
        Returns an streams for a segment.

        http://strava.github.io/api/v3/streams/#segment

        Streams represent the raw data of the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                           heartrate, cadence, watts, temp, moving, grade_smooth

        http://strava.github.io/api/v3/streams/#effort

        :param segment_id: The ID of segment.
        :type segment_id: int

        :param types: (optional) A list of the the types of streams to fetch.
        :type types: list

        :param resolution: (optional, default is 'all') indicates desired number
                            of data points. 'low' (100), 'medium' (1000),
                            'high' (10000) or 'all'.
        :type resolution: str

        :param series_type: (optional, default is 'distance'.  Relevant only if
                             using resolution either 'time' or 'distance'.
                             Used to index the streams if the stream is being
                             reduced.
        :type series_type: str

        :return: An dictionary of :class:`stravalib.model.Stream` from the effort.
        :rtype: :py:class:`dict`
        """

        # stream are comma seperated list
        if types is not None:
            types = ",".join(types)

        params = {}
        if resolution is not None:
            params["resolution"] = resolution

        if series_type is not None:
            params["series_type"] = series_type

        result_fetcher = functools.partial(self.protocol.get,
                                           '/segments/{id}/streams/{types}'.format(id=segment_id, types=types),
                                           **params)

        streams = BatchedResultsIterator(entity=model.Stream,
                                         bind_client=self,
                                         result_fetcher=result_fetcher)

        # Pack streams into dictionary
        return {i.type: i for i in streams}


class BatchedResultsIterator(object):
    """
    An iterator that enables iterating over requests that return paged results.
    """

    # How many results returned in a batch.  We maximize this to minimize
    #  requests to server (rate limiting)
    default_per_page = 200

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
        :rtype: :py:class:`int`
        """

        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.entity = entity
        self.bind_client = bind_client
        self.result_fetcher = result_fetcher
        self.limit = limit

        if per_page is not None:
            self.per_page = per_page
        #elif limit is not None:
        #    self.per_page = limit
        else:
            self.per_page = self.default_per_page

        self.reset()

    def __repr__(self):
        return '<{0} entity={1}>'.format(self.__class__.__name__, self.entity.__name__)

    def reset(self):
        self._counter = 0
        self._buffer = None
        self._page = 1
        self._all_results_fetched = False

    def _fill_buffer(self):
        """
        Fills the internal size-50 buffer from Strava API.
        """
        # If we cannot fetch anymore from the server then we're done here.
        if self._all_results_fetched:
            self._eof()

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

    def _eof(self):
        self.reset()
        raise StopIteration

    def __next__(self):
        if self.limit and self._counter >= self.limit:
            self._eof()
        if not self._buffer:
            self._fill_buffer()
        try:
            result = self._buffer.popleft()
        except IndexError:
            self._eof()
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
        :type response: :py:class:`dict`

        """
        self.client = client
        self.update_from_response(response)

    def update_from_response(self, response, raise_exc=True):
        """
        Updates internal state of object.

        :param response: The response object (dict).
        :type response: :py:class:`dict`
        :param raise_exc: Whether to raise an exception if the response
                          indicates an error state. (default True)
        :type raise_exc: bool
        :raise stravalib.exc.ActivityUploadFailed: If the response indicates an error and raise_exc is True.
        """
        self.upload_id = response.get('id')
        self.external_id = response.get('external_id')
        self.activity_id = response.get('activity_id')
        self.status = response.get('status')
        self.error = response.get('error')
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
        response = self.client.protocol.get('/uploads/{upload_id}',
                                            upload_id=self.upload_id,
                                            check_for_errors=False)

        self.update_from_response(response)

    def wait(self, timeout=None, poll_interval=1.0):
        """
        Wait for the upload to complete or to err out.

        Will return the resulting Activity or raise an exception if the upload fails.

        :param timeout: The max seconds to wait. Will raise TimeoutExceeded
                        exception if this time passes without success or error response.
        :type timeout: float

        :param poll_interval: How long to wait between upload checks.  Strava
                              recommends 1s minimum. (default 1.0s)
        :type poll_interval: float

        :return: The uploaded Activity object (fetched from server)
        :rtype: :class:`stravalib.model.Activity`

        :raise stravalib.exc.TimeoutExceeded: If a timeout was specified and
                                              activity is still processing after
                                              timeout has elapsed.
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
