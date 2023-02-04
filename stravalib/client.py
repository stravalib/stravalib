"""
Client
==============
Provides the main interface classes for the Strava version 3 REST API.
"""

from __future__ import annotations

import calendar
import collections
import functools
import logging
import time
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, List, Optional

import arrow
import pytz

from stravalib import exc, model, unithelper
from stravalib.exc import (
    ActivityPhotoUploadNotSupported,
    warn_attribute_unofficial,
    warn_method_unofficial,
    warn_param_deprecation,
    warn_param_unofficial,
)
from stravalib.protocol import ApiV3
from stravalib.unithelper import is_quantity_type
from stravalib.util import limiter


class Client(object):
    """
    Main client class for interacting with the exposed Strava v3 API methods.

    This class can be instantiated without an access_token when performing authentication;
    however, most methods will require a valid access token.

    """

    def __init__(
        self,
        access_token=None,
        rate_limit_requests=True,
        rate_limiter=None,
        requests_session=None,
    ):
        """
        Initialize a new client object.

        Parameters
        ----------
        access_token : str
            The token that provides access to a specific Strava account. If empty, assume that this
            account is not yet authenticated.
        rate_limit_requests : bool
            Whether to apply a rate limiter to the requests. (default True)
        rate_limiter : callable
            A :class:`stravalib.util.limiter.RateLimiter` object to use.
            If not specified (and rate_limit_requests is True), then
            :class:`stravalib.util.limiter.DefaultRateLimiter` will be used.
        requests_session : requests.Session() object
            (Optional) pass request session object.

        """
        self.log = logging.getLogger(
            "{0.__module__}.{0.__name__}".format(self.__class__)
        )

        if rate_limit_requests:
            if not rate_limiter:
                rate_limiter = limiter.DefaultRateLimiter()
        elif rate_limiter:
            raise ValueError(
                "Cannot specify rate_limiter object when rate_limit_requests is False"
            )

        self.protocol = ApiV3(
            access_token=access_token,
            requests_session=requests_session,
            rate_limiter=rate_limiter,
        )

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

    def authorization_url(
        self,
        client_id,
        redirect_uri,
        approval_prompt="auto",
        scope=None,
        state=None,
    ):
        """
        Get the URL needed to authorize your application to access a Strava user's information.

        See https://developers.strava.com/docs/authentication/

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
        redirect_uri : str
            The URL that Strava will redirect to after successful (or failed) authorization.
        approval_prompt : str
            Whether to prompt for approval even if approval already granted to app.
            Choices are 'auto' or 'force'.  (Default is 'auto')
        scope : list[str]
            The access scope required.  Omit to imply "read" and "activity:read"
            Valid values are 'read', 'read_all', 'profile:read_all', 'profile:write', 'activity:read',
            'activity:read_all', 'activity:write'.
        state : str
            An arbitrary variable that will be returned to your application in the redirect URI.

        Returns
        -------
        string : The URL string to use for authorization link.
        """
        return self.protocol.authorization_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            approval_prompt=approval_prompt,
            scope=scope,
            state=state,
        )

    def exchange_code_for_token(self, client_id, client_secret, code):
        """
        Exchange the temporary authorization code (returned with redirect from strava authorization URL)
        for a short-lived access token and a refresh token (used to obtain the next access token later on).

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
        client_secret : str
            The developer client secret
        code : str
            The temporary authorization code

        Returns
        -------
        Dictionary containing the access_token, refresh_token
        and expires_at (number of seconds since Epoch when the provided access token will expire)
        """
        return self.protocol.exchange_code_for_token(
            client_id=client_id, client_secret=client_secret, code=code
        )

    def refresh_access_token(self, client_id, client_secret, refresh_token):
        """
        Exchanges the previous refresh token for a short-lived access token and a new
        refresh token (used to obtain the next access token later on).

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
        client_secret : str
            The developer client secret
        refresh_token : str
            The refresh token obtained from a previous authorization request

        Returns
        -------
        Dictionary containing the access_token, refresh_token
        and expires_at (number of seconds since Epoch when the provided access token will expire)
        """
        return self.protocol.refresh_access_token(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )

    def deauthorize(self):
        """
        Deauthorize the application. This causes the application to be removed
        from the athlete's "My Apps" settings page.

        https://developers.strava.com/docs/authentication/#deauthorization
        """
        self.protocol.post("oauth/deauthorize")

    def _utc_datetime_to_epoch(self, activity_datetime):
        """
        Convert the specified datetime value to a unix epoch timestamp (seconds since epoch).

        Parameters
        ----------
        activity_datetime : str
            A string which may contain tzinfo (offset) or a datetime object (naive datetime will
            be considered to be UTC).

        Returns
        -------
        Epoch timestamp in int format.
        """
        if isinstance(activity_datetime, str):
            activity_datetime = arrow.get(activity_datetime).datetime
        assert isinstance(activity_datetime, datetime)
        if activity_datetime.tzinfo:
            activity_datetime = activity_datetime.astimezone(pytz.utc)

        return calendar.timegm(activity_datetime.timetuple())

    def get_activities(self, before=None, after=None, limit=None):
        """
        Get activities for authenticated user sorted by newest first.

        https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities


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
        result_fetcher = functools.partial(
            self.protocol.get, "/athlete/activities", **params
        )

        return BatchedResultsIterator(
            entity=model.Activity,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_athlete(self):
        """
        Gets the specified athlete; if athlete_id is None then retrieves a
        detail-level representation of currently authenticated athlete;
        otherwise summary-level representation returned of athlete.

        https://developers.strava.com/docs/reference/#api-Athletes

        https://developers.strava.com/docs/reference/#api-Athletes-getLoggedInAthlete

        :return: The athlete model object.
        :rtype: :class:`stravalib.model.Athlete`
        """
        raw = self.protocol.get("/athlete")
        return model.Athlete.parse_obj({**raw, **{"bound_client": self}})

    def update_athlete(
        self, city=None, state=None, country=None, sex=None, weight=None
    ):
        """
        Updates the properties of the authorized athlete.

        https://developers.strava.com/docs/reference/#api-Athletes-updateLoggedInAthlete

        Parameters
        -----------
        city : str
            City the athlete lives in

            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        state : str
            State the athlete lives in

            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        country : str
            Country the athlete lives in

            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
             removed in the future.
        sex : str
            Sex of the athlete

            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        weight : float
            Weight of the athlete in kg (float)

        Returns
        --------
        :class:`stravalib.model.Athlete`
            The updated athlete object
        """
        params = {"city": city, "state": state, "country": country, "sex": sex}
        params = {k: v for (k, v) in params.items() if v is not None}
        for p in params.keys():
            if p != "weight":
                warn_param_deprecation(p)
        if weight is not None:
            params["weight"] = float(weight)

        raw_athlete = self.protocol.put("/athlete", **params)
        return model.Athlete.parse_obj(
            {**raw_athlete, **{"bound_client": self}}
        )

    # TODO: Can't find this in the api documentation either. Does it still work?
    def get_athlete_koms(self, athlete_id, limit=None):
        """
        Gets Q/KOMs/CRs for specified athlete.

        KOMs are returned as `stravalib.model.SegmentEffort` objects.

        :param athlete_id: The ID of the athlete.
        :type athlete_id: int

        :param limit: Maximum number of KOM segment efforts to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.SegmentEffort` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(
            self.protocol.get, "/athletes/{id}/koms", id=athlete_id
        )

        return BatchedResultsIterator(
            entity=model.SegmentEffort,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_athlete_stats(self, athlete_id=None):
        """
        Returns Statistics for the athlete.
        athlete_id must be the id of the authenticated athlete or left blank.
        If it is left blank two requests will be made - first to get the
        authenticated athlete's id and second to get the Stats.

        https://developers.strava.com/docs/reference/#api-Athletes-getStats

        Note that this will return the stats for _public_ activities only,
        regardless of the scopes of the current access token.

        :return: A model containing the Stats
        :rtype: :py:class:`stravalib.model.AthleteStats`
        """
        if athlete_id is None:
            athlete_id = self.get_athlete().id

        raw = self.protocol.get("/athletes/{id}/stats", id=athlete_id)
        # TODO: Better error handling - this will return a 401 if this athlete
        #       is not the authenticated athlete.

        return model.AthleteStats.parse_obj(raw)

    def get_athlete_clubs(self):
        """
        List the clubs for the currently authenticated athlete.

        https://developers.strava.com/docs/reference/#api-Clubs-getLoggedInAthleteClubs

        :return: A list of :class:`stravalib.model.Club`
        :rtype: :py:class:`list`
        """

        # TODO: This should return a BatchedResultsIterator or otherwise at most 30 clubs are returned!
        club_structs = self.protocol.get("/athlete/clubs")
        return [
            model.Club.parse_obj({**raw, **{"bound_client": self}})
            for raw in club_structs
        ]

    def join_club(self, club_id):
        """
        Joins the club on behalf of authenticated athlete.

        (Access token with write permissions required.)

        :param club_id: The numeric ID of the club to join.
        """
        self.protocol.post("clubs/{id}/join", id=club_id)

    def leave_club(self, club_id):
        """
        Leave club on behalf of authenticated user.

        (Acces token with write permissions required.)

        :param club_id:
        """
        self.protocol.post("clubs/{id}/leave", id=club_id)

    def get_club(self, club_id):
        """
        Return a specific club object.

        https://developers.strava.com/docs/reference/#api-Clubs-getClubById

        :param club_id: The ID of the club to fetch.
        :type club_id: int

        :rtype: :class:`stravalib.model.Club`
        """
        raw = self.protocol.get("/clubs/{id}", id=club_id)
        return model.Club.parse_obj({**raw, **{"bound_client": self}})

    def get_club_members(self, club_id, limit=None):
        """
        Gets the member objects for specified club ID.

        https://developers.strava.com/docs/reference/#api-Clubs-getClubMembersById

        :param club_id: The numeric ID for the club.
        :type club_id: int

        :param limit: Maximum number of athletes to return. (default unlimited)
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Athlete` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(
            self.protocol.get, "/clubs/{id}/members", id=club_id
        )

        return BatchedResultsIterator(
            entity=model.Athlete,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_club_activities(self, club_id, limit=None):
        """
        Gets the activities associated with specified club.

        https://developers.strava.com/docs/reference/#api-Clubs-getClubActivitiesById

        :param club_id: The numeric ID for the club.
        :type club_id: int

        :param limit: Maximum number of activities to return. (default unlimited)
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Activity` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(
            self.protocol.get, "/clubs/{id}/activities", id=club_id
        )

        return BatchedResultsIterator(
            entity=model.Activity,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_activity(self, activity_id, include_all_efforts=False):
        """
        Gets specified activity.

        Will be detail-level if owned by authenticated user; otherwise summary-level.

        https://developers.strava.com/docs/reference/#api-Activities-getActivityById

        :param activity_id: The ID of activity to fetch.
        :type activity_id: int

        :param include_all_efforts: Whether to include segment efforts - only
                                    available to the owner of the activty.
        :type include_all_efforts: bool

        :rtype: :class:`stravalib.model.Activity`

        TODO: contrary to the Strava API documentation, this endpoint _always_
        returns all segment efforts when the include_all_efforts parameter is provided,
        regardless its value
        """
        raw = self.protocol.get(
            "/activities/{id}",
            id=activity_id,
            include_all_efforts=include_all_efforts,
        )
        return model.Activity.parse_obj({**raw, **{"bound_client": self}})

    def get_friend_activities(self, limit=None):
        """
        DEPRECATED This endpoint was removed by Strava in Jan 2018.

        :param limit: Maximum number of activities to return. (default unlimited)
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Activity` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        raise NotImplementedError(
            "The /activities/following endpoint was removed by Strava.  "
            "See https://developers.strava.com/docs/january-2018-update/"
        )

        # result_fetcher = functools.partial(self.protocol.get, '/activities/following')
        #
        # return BatchedResultsIterator(entity=model.Activity, bind_client=self,
        #                               result_fetcher=result_fetcher, limit=limit)

    def create_activity(
        self,
        name,
        activity_type,
        start_date_local,
        elapsed_time,
        description=None,
        distance=None,
    ):
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

        :param distance: The distance in meters (float) or a :class:`pint.Quantity` instance.
        :type distance: :class:`pint.Quantity` or float (meters)
        """
        if isinstance(elapsed_time, timedelta):
            elapsed_time = elapsed_time.seconds

        if is_quantity_type(distance):
            distance = float(unithelper.meters(distance))

        if isinstance(start_date_local, datetime):
            start_date_local = start_date_local.strftime("%Y-%m-%dT%H:%M:%SZ")

        if not activity_type.lower() in [
            t.lower() for t in model.Activity.TYPES
        ]:
            raise ValueError(
                f"Invalid activity type: {activity_type}. Possible values: {model.Activity.TYPES!r}"
            )

        params = dict(
            name=name,
            type=activity_type.lower(),
            start_date_local=start_date_local,
            elapsed_time=elapsed_time,
        )

        if description is not None:
            params["description"] = description

        if distance is not None:
            params["distance"] = distance

        raw_activity = self.protocol.post("/activities", **params)

        return model.Activity.parse_obj(
            {**raw_activity, **{"bound_client": self}}
        )

    def update_activity(
        self,
        activity_id,
        name=None,
        activity_type=None,
        private=None,
        commute=None,
        trainer=None,
        gear_id=None,
        description=None,
        device_name=None,
        hide_from_home=None,
    ):
        """
        Updates the properties of a specific activity.

        https://developers.strava.com/docs/reference/#api-Activities-updateActivityById

        Parameters
        ----------

        activity_id : int
            The ID of the activity to update.
        name : str
            The name of the activity.
        activity_type : str
            The activity type (case-insensitive).
            Possible values: ride, run, swim, workout, hike,
            walk, nordicski, alpineski, backcountryski,
            iceskate, inlineskate, kitesurf, rollerski,
            windsurf, workout, snowboard, snowshoe
        private : bool
            Whether the activity is private.
            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        commute : bool
            Whether the activity is a commute.
        trainer : bool
            Whether this is a trainer activity.
        gear_id : int
            Alpha-numeric ID of gear (bike, shoes) used on this activity.
        description : str
            Description for the activity.
        device_name : str
            Device name for the activity
            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        hide_from_home : bool
            Whether the activity is muted (hidden from Home and Club feeds).

        Returns
        -------
        stravalib.model.Activity
            The updated activity
        """

        # Convert the kwargs into a params dict
        params = {}

        if name is not None:
            params["name"] = name

        if activity_type is not None:
            if not activity_type.lower() in [
                t.lower() for t in model.Activity.TYPES
            ]:
                raise ValueError(
                    f"Invalid activity type: {activity_type}. Possible values: {model.Activity.TYPES!r}"
                )
            params["type"] = activity_type.lower()

        if private is not None:
            warn_param_deprecation("private")
            params["private"] = int(private)

        if commute is not None:
            params["commute"] = int(commute)

        if trainer is not None:
            params["trainer"] = int(trainer)

        if gear_id is not None:
            params["gear_id"] = gear_id

        if description is not None:
            params["description"] = description

        if device_name is not None:
            warn_param_deprecation("device_name")
            params["device_name"] = device_name

        if hide_from_home is not None:
            params["hide_from_home"] = int(hide_from_home)

        raw_activity = self.protocol.put(
            "/activities/{activity_id}", activity_id=activity_id, **params
        )

        return model.Activity.parse_obj(
            {**raw_activity, **{"bound_client": self}}
        )

    def upload_activity(
        self,
        activity_file,
        data_type,
        name=None,
        description=None,
        activity_type=None,
        private=None,
        external_id=None,
        trainer=None,
        commute=None,
    ):
        """
        Uploads a GPS file (tcx, gpx) to create a new activity for current athlete.

        https://developers.strava.com/docs/reference/#api-Uploads-createUpload

        :param activity_file: The file object to upload or file contents.
        :type activity_file: TextIOWrapper, str or bytes

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
                              WARNING - This param is supported (as of 2022-11-15), but not
                              documented and may be removed in the future.
        :type activity_type: str

        :param private: (optional) set to True to mark the resulting activity as private,
                        'view_private' permissions will be necessary to view the activity.

                        .. deprecated:: 1.0
                        This param is not supported by the Strava API and may be
                        removed in the future.
        :type private: bool

        :param external_id: (optional) An arbitrary unique identifier may be specified which will be included in status responses.
        :type external_id: str

        :param trainer: (optional) Whether the resulting activity should be marked as having been performed on a trainer.
        :type trainer: bool

        :param commute: (optional) Whether the resulting activity should be tagged as a commute.
        :type commute: bool
        """
        if not hasattr(activity_file, "read"):
            if isinstance(activity_file, str):
                activity_file = BytesIO(activity_file.encode("utf-8"))
            elif isinstance(activity_file, bytes):
                activity_file = BytesIO(activity_file)
            else:
                raise TypeError(
                    "Invalid type specified for activity_file: {0}".format(
                        type(activity_file)
                    )
                )

        valid_data_types = ("fit", "fit.gz", "tcx", "tcx.gz", "gpx", "gpx.gz")
        if data_type not in valid_data_types:
            raise ValueError(
                f"Invalid data type {data_type}. Possible values {valid_data_types!r}"
            )

        params = {"data_type": data_type}
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        if activity_type is not None:
            if not activity_type.lower() in [
                t.lower() for t in model.Activity.TYPES
            ]:
                raise ValueError(
                    f"Invalid activity type: {activity_type}. Possible values: {model.Activity.TYPES!r}"
                )
            warn_param_unofficial("activity_type")
            params["activity_type"] = activity_type.lower()
        if private is not None:
            warn_param_deprecation("private")
            params["private"] = int(private)
        if external_id is not None:
            params["external_id"] = external_id
        if trainer is not None:
            params["trainer"] = int(trainer)
        if commute is not None:
            params["commute"] = int(commute)

        initial_response = self.protocol.post(
            "/uploads",
            files={"file": activity_file},
            check_for_errors=False,
            **params,
        )

        return ActivityUploader(self, response=initial_response)

    # TODO: I don't think this is the correct link but can't find it in the docs
    def delete_activity(self, activity_id):
        """
        Deletes the specified activity.

        https://developers.strava.com/docs/reference/#api-Activities

        :param activity_id: The activity to delete.
        :type activity_id: int
        """
        self.protocol.delete("/activities/{id}", id=activity_id)

    def get_activity_zones(self, activity_id):
        """
        Gets zones for activity.

        Requires premium account.

        https://developers.strava.com/docs/reference/#api-Activities-getZonesByActivityId

        :param activity_id: The activity for which to get zones.
        :type activity_id: int

        :return: A list of :class:`stravalib.model.BaseActivityZone` objects.
        :rtype: :py:class:`list`
        """
        zones = self.protocol.get("/activities/{id}/zones", id=activity_id)
        return [
            model.BaseActivityZone.parse_obj({**z, **{"bound_client": self}})
            for z in zones
        ]

    def get_activity_comments(self, activity_id, markdown=False, limit=None):
        """
        Gets the comments for an activity.

        https://developers.strava.com/docs/reference/#api-Activities-getCommentsByActivityId

        :param activity_id: The activity for which to fetch comments.
        :type activity_id: int

        :param markdown: Whether to include markdown in comments (default is false/filterout).
        :type markdown: bool

        :param limit: Max rows to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.ActivityComment` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(
            self.protocol.get,
            "/activities/{id}/comments",
            id=activity_id,
            markdown=int(markdown),
        )

        return BatchedResultsIterator(
            entity=model.ActivityComment,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_activity_kudos(self, activity_id, limit=None):
        """
        Gets the kudos for an activity.

        https://developers.strava.com/docs/reference/#api-Activities-getKudoersByActivityId

        :param activity_id: The activity for which to fetch kudos.
        :type activity_id: int

        :param limit: Max rows to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.ActivityKudos` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(
            self.protocol.get, "/activities/{id}/kudos", id=activity_id
        )

        return BatchedResultsIterator(
            entity=model.ActivityKudos,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    # TODO not sure this is the correct api doc link - couldn't find "photos"
    def get_activity_photos(
        self, activity_id, size=None, only_instagram=False
    ):
        """
        Gets the photos from an activity.

        https://developers.strava.com/docs/reference/#api-Activities

        :param activity_id: The activity for which to fetch photos.
        :type activity_id: int

        :param size: the requested size of the activity's photos. URLs for the photos will be returned that best match
                    the requested size. If not included, the smallest size is returned
        :type size: int

        :param only_instagram: Parameter to preserve legacy behavior of only returning Instagram photos.
        :type only_instagram: bool

        :return: An iterator of :class:`stravalib.model.ActivityPhoto` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        params = {}

        if not only_instagram:
            params["photo_sources"] = "true"

        if size is not None:
            params["size"] = size

        result_fetcher = functools.partial(
            self.protocol.get,
            "/activities/{id}/photos",
            id=activity_id,
            **params,
        )

        return BatchedResultsIterator(
            entity=model.ActivityPhoto,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

    def get_activity_laps(self, activity_id):
        """
        Gets the laps from an activity.

        https://developers.strava.com/docs/reference/#api-Activities-getLapsByActivityId

        :param activity_id: The activity for which to fetch laps.
        :type activity_id: int

        :return: An iterator of :class:`stravalib.model.ActivityLaps` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(
            self.protocol.get, "/activities/{id}/laps", id=activity_id
        )

        return BatchedResultsIterator(
            entity=model.ActivityLap,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

    def get_related_activities(self, activity_id, limit=None):
        """
        Deprecated. This endpoint was removed by strava in Jan 2018.

        :param activity_id: The activity for which to fetch related activities.
        :type activity_id: int

        :return: An iterator of :class:`stravalib.model.Activity` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        raise NotImplementedError(
            "The /activities/{id}/related endpoint was removed by Strava.  "
            "See https://developers.strava.com/docs/january-2018-update/"
        )

        # result_fetcher = functools.partial(self.protocol.get,
        #                                    '/activities/{id}/related',
        #                                    id=activity_id)
        #
        # return BatchedResultsIterator(entity=model.Activity,
        #                               bind_client=self,
        #                               result_fetcher=result_fetcher,
        #                               limit=limit)

    def get_gear(self, gear_id):
        """
        Get details for an item of gear.

        https://developers.strava.com/docs/reference/#api-Gears

        :param gear_id: The gear id.
        :type gear_id: str

        :return: The Bike or Shoe subclass object.
        :rtype: :class:`stravalib.model.Gear`
        """
        return model.Gear.parse_obj(
            self.protocol.get("/gear/{id}", id=gear_id)
        )

    def get_segment_effort(self, effort_id):
        """
        Return a specific segment effort by ID.

        https://developers.strava.com/docs/reference/#api-SegmentEfforts

        :param effort_id: The id of associated effort to fetch.
        :type effort_id: int

        :return: The specified effort on a segment.
        :rtype: :class:`stravalib.model.SegmentEffort`
        """
        return model.SegmentEffort.parse_obj(
            self.protocol.get("/segment_efforts/{id}", id=effort_id)
        )

    def get_segment(self, segment_id):
        """
        Gets a specific segment by ID.

        https://developers.strava.com/docs/reference/#api-SegmentEfforts-getSegmentEffortById

        :param segment_id: The segment to fetch.
        :type segment_id: int

        :return: A segment object.
        :rtype: :class:`stravalib.model.Segment`
        """
        return model.Segment.parse_obj(
            {
                **self.protocol.get("/segments/{id}", id=segment_id),
                **{"bound_client": self},
            }
        )

    def get_starred_segments(self, limit=None):
        """
        Returns a summary representation of the segments starred by the
         authenticated user. Pagination is supported.

        https://developers.strava.com/docs/reference/#api-Segments-getLoggedInAthleteStarredSegments

        :param limit: (optional), limit number of starred segments returned.
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Segment` starred by authenticated user.
        :rtype: :class:`BatchedResultsIterator`
        """

        params = {}
        if limit is not None:
            params["limit"] = limit

        result_fetcher = functools.partial(
            self.protocol.get, "/segments/starred"
        )

        return BatchedResultsIterator(
            entity=model.Segment,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    # TODO: i'm not sure what the diff is between this method and the one above
    # So i used the SAME API doc link for both. may need to revisit
    def get_athlete_starred_segments(self, athlete_id, limit=None):
        """
        Returns a summary representation of the segments starred by the
         specified athlete. Pagination is supported.

        https://developers.strava.com/docs/reference/#api-Segments-getLoggedInAthleteStarredSegments

        :param athlete_id: The ID of the athlete.
        :type athlete_id: int

        :param limit: (optional), limit number of starred segments returned.
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Segment` starred by authenticated user.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(
            self.protocol.get, "/athletes/{id}/segments/starred", id=athlete_id
        )

        return BatchedResultsIterator(
            entity=model.Segment,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_segment_efforts(
        self,
        segment_id,
        athlete_id=None,
        start_date_local=None,
        end_date_local=None,
        limit=None,
    ):
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

        https://developers.strava.com/docs/reference/#api-SegmentEfforts-getEffortsBySegmentId

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

        :param limit: (optional), limit number of efforts.
        :type limit: int

        :return: An iterator of :class:`stravalib.model.SegmentEffort` efforts on a segment.
        :rtype: :class:`BatchedResultsIterator`

        """
        params = {"segment_id": segment_id}

        if athlete_id is not None:
            params["athlete_id"] = athlete_id

        if start_date_local:
            if isinstance(start_date_local, str):
                start_date_local = arrow.get(start_date_local).naive
            params["start_date_local"] = start_date_local.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        if end_date_local:
            if isinstance(end_date_local, str):
                end_date_local = arrow.get(end_date_local).naive
            params["end_date_local"] = end_date_local.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        if limit is not None:
            params["limit"] = limit

        result_fetcher = functools.partial(
            self.protocol.get, "/segments/{segment_id}/all_efforts", **params
        )

        return BatchedResultsIterator(
            entity=model.BaseEffort,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def explore_segments(
        self, bounds, activity_type=None, min_cat=None, max_cat=None
    ):
        """
        Returns an array of up to 10 segments.

        https://developers.strava.com/docs/reference/#api-Segments-exploreSegments

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
            bounds = (bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1])
        elif len(bounds) != 4:
            raise ValueError(
                "Invalid bounds specified: {0!r}. Must be list of 4 float values or list of 2 (lat,lon) tuples."
            )

        params = {"bounds": ",".join(str(b) for b in bounds)}

        valid_activity_types = ("riding", "running")
        if activity_type is not None:
            if activity_type not in ("riding", "running"):
                raise ValueError(
                    "Invalid activity type: {0}.  Possible values: {1!r}".format(
                        activity_type, valid_activity_types
                    )
                )
            params["activity_type"] = activity_type

        if min_cat is not None:
            params["min_cat"] = min_cat
        if max_cat is not None:
            params["max_cat"] = max_cat

        raw = self.protocol.get("/segments/explore", **params)
        return [
            model.SegmentExplorerResult.parse_obj(
                {**v, **{"bound_client": self}}
            )
            for v in raw["segments"]
        ]

    def get_activity_streams(
        self, activity_id, types=None, resolution=None, series_type=None
    ):
        """
        Returns a stream for an activity.

        https://developers.strava.com/docs/reference/#api-Streams-getActivityStreams

        Streams represent the raw spatial data for the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                           heartrate, cadence, watts, temp, moving, grade_smooth

        :param activity_id: The ID of activity.
        :type activity_id: int

        :param types: (optional) A list of the types of streams to fetch.
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

        :return: An dictionary of :class:`stravalib.model.Stream` from the activity or None if there are no streams.
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

        result_fetcher = functools.partial(
            self.protocol.get,
            "/activities/{id}/streams/{types}".format(
                id=activity_id, types=types
            ),
            **params,
        )

        streams = BatchedResultsIterator(
            entity=model.Stream,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

        # Pack streams into dictionary
        try:
            return {i.type: i for i in streams}
        except exc.ObjectNotFound:
            return None  # just to be explicit.

    def get_effort_streams(
        self, effort_id, types=None, resolution=None, series_type=None
    ):
        """
        Returns an streams for an effort.

        https://developers.strava.com/docs/reference/#api-Streams-getSegmentEffortStreams

        Streams represent the raw data of the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                           heartrate, cadence, watts, temp, moving, grade_smooth

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

        result_fetcher = functools.partial(
            self.protocol.get,
            "/segment_efforts/{id}/streams/{types}".format(
                id=effort_id, types=types
            ),
            **params,
        )

        streams = BatchedResultsIterator(
            entity=model.Stream,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

        # Pack streams into dictionary
        return {i.type: i for i in streams}

    def get_segment_streams(
        self, segment_id, types=None, resolution=None, series_type=None
    ):
        """
        Returns an streams for a segment.

        https://developers.strava.com/docs/reference/#api-Streams-getSegmentStreams

        Streams represent the raw data of the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                           heartrate, cadence, watts, temp, moving, grade_smooth

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

        result_fetcher = functools.partial(
            self.protocol.get,
            "/segments/{id}/streams/{types}".format(
                id=segment_id, types=types
            ),
            **params,
        )

        streams = BatchedResultsIterator(
            entity=model.Stream,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

        # Pack streams into dictionary
        return {i.type: i for i in streams}

    def get_routes(self, athlete_id=None, limit=None):
        """
        Gets the routes list for an authenticated user.

        https://developers.strava.com/docs/reference/#api-Routes-getRoutesByAthleteId

        :param athlete_id: id for the

        :param limit: Max rows to return (default unlimited).
        :type limit: int

        :return: An iterator of :class:`stravalib.model.Route` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        if athlete_id is None:
            athlete_id = self.get_athlete().id

        result_fetcher = functools.partial(
            self.protocol.get, "/athletes/{id}/routes".format(id=athlete_id)
        )

        return BatchedResultsIterator(
            entity=model.Route,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_route(self, route_id):
        """
        Gets specified route.

        Will be detail-level if owned by authenticated user; otherwise summary-level.

        https://developers.strava.com/docs/reference/#api-Routes-getRouteById

        :param route_id: The ID of route to fetch.
        :type route_id: int

        :rtype: :class:`stravalib.model.Route`
        """
        raw = self.protocol.get("/routes/{id}", id=route_id)
        return model.Route.parse_obj({**raw, **{"bound_client": self}})

    def get_route_streams(self, route_id):
        """
        Returns streams for a route.

        Streams represent the raw data of the saved route. External
        applications may access this information for all public routes and for
        the private routes of the authenticated athlete. The 3 available route
        stream types `distance`, `altitude` and `latlng` are always returned.

        See: https://developers.strava.com/docs/reference/#api-Streams-getRouteStreams

        :param route_id: The ID of activity.
        :type route_id: int

        :return: A dictionary of :class:`stravalib.model.Stream` from the route.
        :rtype: :py:class:`dict`

        """

        result_fetcher = functools.partial(
            self.protocol.get, "/routes/{id}/streams/".format(id=route_id)
        )

        streams = BatchedResultsIterator(
            entity=model.Stream,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

        # Pack streams into dictionary
        return {i.type: i for i in streams}

    # TODO: removed old link to create a subscription but can't find new equiv
    # in current strava docs
    def create_subscription(
        self,
        client_id,
        client_secret,
        callback_url,
        verify_token=model.Subscription.VERIFY_TOKEN_DEFAULT,
    ):
        """
        Creates a webhook event subscription.

        :param client_id: application's ID, obtained during registration
        :type client_id: int

        :param client_secret: application's secret, obtained during registration
        :type client_secret: str

        :param callback_url: callback URL where Strava will first send a GET request to validate, then subsequently send POST requests with updates
        :type callback_url: str

        :param verify_token: a token you can use to verify Strava's GET callback request
        :type verify_token: str

        :return: An instance of :class:`stravalib.model.Subscription`.
        :rtype: :class:`stravalib.model.Subscription`

        Notes:

        `verify_token` is set to a default in the event that the author doesn't want to specify one.

        The appliction must have permission to make use of the webhook API. Access can be requested by contacting developers -at- strava.com.
        """
        params = dict(
            client_id=client_id,
            client_secret=client_secret,
            callback_url=callback_url,
            verify_token=verify_token,
        )
        raw = self.protocol.post("/push_subscriptions", **params)
        return model.Subscription.parse_obj({**raw, **{"bound_client": self}})

    def handle_subscription_callback(
        self, raw, verify_token=model.Subscription.VERIFY_TOKEN_DEFAULT
    ):
        """
        Validate callback request and return valid response with challenge.

        :return: The JSON response expected by Strava to the challenge request.
        :rtype: Dict[str, str]
        """
        callback = model.SubscriptionCallback.deserialize(raw)
        callback.validate(verify_token)
        response_raw = {"hub.challenge": callback.hub_challenge}
        return response_raw

    def handle_subscription_update(self, raw):
        """
        Converts a raw subscription update into a model.

        :return: The subscription update model object.
        :rtype: :class:`stravalib.model.SubscriptionUpdate`
        """
        return model.SubscriptionUpdate.parse_obj(
            {**raw, **{"bound_client": self}}
        )

    # TODO can't find a api doc link here so just removed old link.
    def list_subscriptions(self, client_id, client_secret):
        """
        List current webhook event subscriptions in place for the current application.

        :param client_id: application's ID, obtained during registration
        :type client_id: int

        :param client_secret: application's secret, obtained during registration
        :type client_secret: str

        :return: An iterator of :class:`stravalib.model.Subscription` objects.
        :rtype: :class:`BatchedResultsIterator`
        """
        result_fetcher = functools.partial(
            self.protocol.get,
            "/push_subscriptions",
            client_id=client_id,
            client_secret=client_secret,
        )

        return BatchedResultsIterator(
            entity=model.Subscription,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

    # TODO can't find a api doc link here so just removed old link.
    def delete_subscription(self, subscription_id, client_id, client_secret):
        """
        Unsubscribe from webhook events for an existing subscription.

        :param subscription_id: ID of subscription to remove.
        :type subscription_id: int

        :param client_id: application's ID, obtained during registration
        :type client_id: int

        :param client_secret: application's secret, obtained during registration
        :type client_secret: str
        """
        self.protocol.delete(
            "/push_subscriptions/{id}",
            id=subscription_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        # Expects a 204 response if all goes well.


class BatchedResultsIterator(object):
    """
    An iterator that enables iterating over requests that return paged results.
    """

    # How many results returned in a batch.  We maximize this to minimize
    #  requests to server (rate limiting)
    default_per_page = 200

    def __init__(
        self,
        entity,
        result_fetcher,
        bind_client=None,
        limit=None,
        per_page=None,
    ):
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
        self.log = logging.getLogger(
            "{0.__module__}.{0.__name__}".format(self.__class__)
        )
        self.entity = entity
        self.bind_client = bind_client
        self.result_fetcher = result_fetcher
        self.limit = limit

        if per_page is not None:
            self.per_page = per_page
        else:
            self.per_page = self.default_per_page

        self.reset()

    def __repr__(self):
        return "<{0} entity={1}>".format(
            self.__class__.__name__, self.entity.__name__
        )

    def reset(self):
        self._counter = 0
        self._buffer = None
        self._page = 1
        self._all_results_fetched = False

    def _fill_buffer(self):
        """
        Fills the internal buffer from Strava API.
        """
        # If we cannot fetch anymore from the server then we're done here.
        if self._all_results_fetched:
            self._eof()
        raw_results = self.result_fetcher(
            page=self._page, per_page=self.per_page
        )

        entities = []
        for raw in raw_results:
            try:
                new_entity = self.entity.parse_obj(
                    {**raw, **{"bound_client": self.bind_client}}
                )
            except AttributeError:
                # entity doesn't have a parse_obj() method, so must be of a legacy type
                new_entity = self.entity.deserialize(
                    raw, bind_client=self.bind_client
                )
            entities.append(new_entity)

        self._buffer = collections.deque(entities)

        self.log.debug(
            "Requested page {0} (got: {1} items)".format(
                self._page, len(self._buffer)
            )
        )
        if len(self._buffer) < self.per_page:
            self._all_results_fetched = True

        self._page += 1

    def __iter__(self):
        return self

    def _eof(self):
        self.reset()
        raise StopIteration

    def __next__(self):
        return self.next()

    def next(self):
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

    def __init__(self, client, response, raise_exc=True):
        """
        :param client: The :class:`stravalib.client.Client` object that is handling the upload.
        :type client: :class:`stravalib.client.Client`

        :param response: The initial upload response.
        :type response: Dict[str,Any]

        :param raise_exc: Whether to raise an exception if the response
                  indicates an error state. (default True)
        :type raise_exc: bool
        """
        self.client = client
        self.response = response
        self.update_from_response(response, raise_exc=raise_exc)

    @property
    def photo_metadata(self):
        """
        photo metadata for the activity upload response, if any.
        it contains a pre-signed uri for uploading the photo.
        Note1: This is only available after the upload has completed.
        Note2: available only for partner apps (not for regular account)
        """

        warn_attribute_unofficial("photo_metadata")

        return self._photo_metadata

    @photo_metadata.setter
    def photo_metadata(self, value):
        self._photo_metadata = value

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
        self.upload_id = response.get("id")
        self.external_id = response.get("external_id")
        self.activity_id = response.get("activity_id")
        self.status = response.get("status") or response.get("message")
        # undocumented field, it contains pre-signed uri to upload photo to
        self._photo_metadata: Optional[List[Dict]] = response.get(
            "photo_metadata"
        )

        if response.get("error"):
            self.error = response.get("error")
        elif response.get("errors"):
            # This appears to be an undocumented API; ths is a bit of a hack for now.
            self.error = str(response.get("errors"))
        else:
            self.error = None

        if raise_exc:
            self.raise_for_error()

    @property
    def is_processing(self):
        return self.activity_id is None and self.error is None

    @property
    def is_error(self):
        return self.error is not None

    @property
    def is_complete(self):
        return self.activity_id is not None

    def raise_for_error(self):
        # FIXME: We need better handling of the actual responses, once those are more accurately documented.
        if self.error:
            raise exc.ActivityUploadFailed(self.error)
        elif self.status == "The created activity has been deleted.":
            raise exc.CreatedActivityDeleted(self.status)

    def poll(self):
        """
        Update internal state from polling strava.com.

        :raise stravalib.exc.ActivityUploadFailed: If the poll returns an error.
        """
        response = self.client.protocol.get(
            "/uploads/{upload_id}",
            upload_id=self.upload_id,
            check_for_errors=False,
        )

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

    def upload_photo(self, photo, timeout=None):
        """
        Uploads a photo to the activity.

        NOTE1: In order to upload a photo, the activity must be uploaded and processed.

        NOTE2: The ability to add photos to activity is currently limited to partner apps & devices such as Zwift,
        Peloton, Tempo Move, etc... Given that the ability isn't in the public API, neither are the docs

        :param photo: The file-like object to upload.
        :type photo: bytes

        :param timeout: The max seconds to wait. Will raise TimeoutExceeded
        :type timeout: float
        """

        warn_method_unofficial("upload_photo")

        try:
            if not isinstance(photo, bytes):
                raise TypeError("Photo must be bytes type")

            self.poll()

            if self.is_processing:
                raise ValueError("Activity upload not complete")

            if not self.photo_metadata:
                raise ActivityPhotoUploadNotSupported(
                    "Photo upload not supported"
                )

            photos_data: List[Dict] = [
                photo_data
                for photo_data in self.photo_metadata
                if photo_data
                and photo_data.get("method") == "PUT"
                and photo_data.get("header", {}).get("Content-Type")
                == "image/jpeg"
            ]

            if not photos_data:
                raise ActivityPhotoUploadNotSupported(
                    "Photo upload not supported"
                )

            if photos_data:
                response = self.client.protocol.rsession.put(
                    url=photos_data[0]["uri"],
                    data=photo,
                    headers=photos_data[0]["header"],
                    timeout=timeout,
                )
                response.raise_for_status()
        except Exception as error:
            raise exc.ActivityPhotoUploadFailed(error)
