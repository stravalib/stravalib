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
from collections.abc import Iterable
from datetime import datetime, timedelta
from io import BytesIO
from typing import (
    TYPE_CHECKING,
    Any,
    Deque,
    Generic,
    Literal,
    NoReturn,
    Protocol,
    TypeVar,
    cast,
)

import arrow
import pint
import pytz
from pydantic import BaseModel
from requests import Session

from stravalib import exc, model, strava_model, unithelper
from stravalib.exc import (
    ActivityPhotoUploadNotSupported,
    warn_attribute_unofficial,
    warn_method_unofficial,
    warn_param_deprecation,
    warn_param_unofficial,
    warn_param_unsupported,
)
from stravalib.protocol import AccessInfo, ApiV3, Scope
from stravalib.unithelper import is_quantity_type
from stravalib.util import limiter

if TYPE_CHECKING:
    from _typeshed import SupportsRead

ActivityType = str
SportType = str
StreamType = str
PhotoMetadata = Any


class Client:
    """Main client class for interacting with the exposed Strava v3 API methods.

    This class can be instantiated without an access_token when performing
    authentication; however, most methods will require a valid access token.

    """

    def __init__(
        self,
        access_token: str | None = None,
        rate_limit_requests: bool = True,
        rate_limiter: limiter.RateLimiter | None = None,
        requests_session: Session | None = None,
    ) -> None:
        """
        Initialize a new client object.

        Parameters
        ----------
        access_token : str
            The token that provides access to a specific Strava account. If
            empty, assume that this account is not yet authenticated.
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
                "Cannot specify rate_limiter object when rate_limit_requests is"
                " False"
            )

        self.protocol = ApiV3(
            access_token=access_token,
            requests_session=requests_session,
            rate_limiter=rate_limiter,
        )

    @property
    def access_token(self) -> str | None:
        """The currently configured authorization token."""
        return self.protocol.access_token

    @access_token.setter
    def access_token(self, token_value: str) -> None:
        """Set the currently configured authorization token.

        Parameters
        ----------
        token_value : int
             User's access token for authentication.


        Returns
        -------

        """
        self.protocol.access_token = token_value

    def authorization_url(
        self,
        client_id: int,
        redirect_uri: str,
        approval_prompt: Literal["auto", "force"] = "auto",
        scope: list[Scope] | Scope | None = None,
        state: str | None = None,
    ) -> str:
        """Get the URL needed to authorize your application to access a Strava
        user's information.

        See https://developers.strava.com/docs/authentication/

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
        redirect_uri : str
            The URL that Strava will redirect to after successful (or failed)
            authorization.
        approval_prompt : str, default='auto'
            Whether to prompt for approval even if approval already granted to
            app.
            Choices are 'auto' or 'force'.
        scope : list[str], default = None
            The access scope required.  Omit to imply "read" and "activity:read"
            Valid values are 'read', 'read_all', 'profile:read_all',
            'profile:write', 'activity:read', 'activity:read_all',
            'activity:write'.
        state : str, default=None
            An arbitrary variable that will be returned to your application in
            the redirect URI.

        Returns
        -------
        str:
            A string containing the url required to authorize with the Strava
            API.

        """
        return self.protocol.authorization_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            approval_prompt=approval_prompt,
            scope=scope,
            state=state,
        )

    def exchange_code_for_token(
        self, client_id: int, client_secret: str, code: str
    ) -> AccessInfo:
        """Exchange the temporary authorization code (returned with redirect
        from strava authorization URL)  for a short-lived access token and a
        refresh token (used to obtain the next access token later on).

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
        dict
            Dictionary containing the access_token, refresh_token and
            expires_at (number of seconds since Epoch when the provided access
            token will expire)


        """
        return self.protocol.exchange_code_for_token(
            client_id=client_id, client_secret=client_secret, code=code
        )

    def refresh_access_token(
        self, client_id: int, client_secret: str, refresh_token: str
    ) -> AccessInfo:
        """Exchanges the previous refresh token for a short-lived access token
        and a new refresh token (used to obtain the next access token later on).

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
        dict:
            Dictionary containing the access_token, refresh_token and expires_at
            (number of seconds since Epoch when the provided access
            token will expire)

        """
        return self.protocol.refresh_access_token(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )

    def deauthorize(self) -> None:
        """Deauthorize the application. This causes the application to be
        removed from the athlete's "My Apps" settings page.

        https://developers.strava.com/docs/authentication/#deauthorization

        """
        self.protocol.post("oauth/deauthorize")

    def _utc_datetime_to_epoch(self, activity_datetime: str | datetime) -> int:
        """Convert the specified datetime value to a unix epoch timestamp
        (seconds since epoch).

        Parameters
        ----------
        activity_datetime : str
            A string which may contain tzinfo (offset) or a datetime object
            (naive datetime will be considered to be UTC).

        Returns
        -------
        datetime value in univ epoch time stamp format (seconds since epoch)


        """
        if isinstance(activity_datetime, str):
            activity_datetime = arrow.get(activity_datetime).datetime
        assert isinstance(activity_datetime, datetime)
        if activity_datetime.tzinfo:
            activity_datetime = activity_datetime.astimezone(pytz.utc)

        return calendar.timegm(activity_datetime.timetuple())

    def get_activities(
        self,
        before: datetime | str | None = None,
        after: datetime | str | None = None,
        limit: int | None = None,
    ) -> BatchedResultsIterator[model.Activity]:
        """Get activities for authenticated user sorted by newest first.

        https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities

        Parameters
        ----------
        before : datetime.datetime or str or None, default=None
            Result will start with activities whose start date is
            before specified date. (UTC)
        after : datetime.datetime or str or None, default=None
            Result will start with activities whose start date is after
            specified value. (UTC)
        limit : int or None, default=None
            How many maximum activities to return.

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Activity` objects.

        """

        before_epoch = self._utc_datetime_to_epoch(before) if before else None
        after_epoch = self._utc_datetime_to_epoch(after) if after else None
        params = dict(before=before_epoch, after=after_epoch)
        result_fetcher = functools.partial(
            self.protocol.get, "/athlete/activities", **params
        )

        return BatchedResultsIterator(
            entity=model.Activity,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_athlete(self) -> model.Athlete:
        """Gets the specified athlete; if athlete_id is None then retrieves a
        detail-level representation of currently authenticated athlete;
        otherwise summary-level representation returned of athlete.

        https://developers.strava.com/docs/reference/#api-Athletes

        https://developers.strava.com/docs/reference/#api-Athletes-getLoggedInAthlete

        Parameters
        ----------

        Returns
        -------
        class:`stravalib.model.Athlete`
            The athlete model object.

        """
        raw = self.protocol.get("/athlete")
        return model.Athlete.parse_obj({**raw, **{"bound_client": self}})

    def update_athlete(
        self,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        sex: str | None = None,
        weight: float | None = None,
    ) -> model.Athlete:
        """Updates the properties of the authorized athlete.

        https://developers.strava.com/docs/reference/#api-Athletes-updateLoggedInAthlete

        Parameters
        ----------
        city : str, default=None
            City the athlete lives in
            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        state : str, default=None
            State the athlete lives in
            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        country : str, default=None
            Country the athlete lives in
            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        sex : str, default=None
            Sex of the athlete
            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        weight : float, default=None
            Weight of the athlete in kg (float)


        """
        params: dict[str, Any] = {
            "city": city,
            "state": state,
            "country": country,
            "sex": sex,
        }
        params = {k: v for (k, v) in params.items() if v is not None}
        for p in params.keys():
            if p != "weight":
                warn_param_unsupported(p)
        if weight is not None:
            params["weight"] = float(weight)

        raw_athlete = self.protocol.put("/athlete", **params)
        return model.Athlete.parse_obj(
            {**raw_athlete, **{"bound_client": self}}
        )

    def get_athlete_koms(
        self, athlete_id: int, limit: int | None = None
    ) -> BatchedResultsIterator[model.SegmentEffort]:
        """Gets Q/KOMs/CRs for specified athlete.

        KOMs are returned as `stravalib.model.SegmentEffort` objects.

        Parameters
        ----------
        athlete_id : int
            The ID of the athlete.
        limit : int
            Maximum number of KOM segment efforts to return (default unlimited).

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.SegmentEffort` objects.

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

    def get_athlete_stats(
        self, athlete_id: int | None = None
    ) -> model.AthleteStats:
        """Returns Statistics for the athlete.
        athlete_id must be the id of the authenticated athlete or left blank.
        If it is left blank two requests will be made - first to get the
        authenticated athlete's id and second to get the Stats.

        https://developers.strava.com/docs/reference/#api-Athletes-getStats

        Note that this will return the stats for _public_ activities only,
        regardless of the scopes of the current access token.

        Parameters
        ----------
        athlete_id : int, default=None
            Strava ID value for the athlete.

        Returns
        -------
        py:class:`stravalib.model.AthleteStats`
            A model containing the Stats

        """
        if athlete_id is None:
            athlete_id = self.get_athlete().id

        raw = self.protocol.get("/athletes/{id}/stats", id=athlete_id)
        # TODO: Better error handling - this will return a 401 if this athlete
        #       is not the authenticated athlete.

        return model.AthleteStats.parse_obj(raw)

    def get_athlete_clubs(self) -> list[model.Club]:
        """List the clubs for the currently authenticated athlete.

        https://developers.strava.com/docs/reference/#api-Clubs-getLoggedInAthleteClubs


        Returns
        -------
        py:class:`list`
            A list of :class:`stravalib.model.Club`

        """

        # TODO: This should return a BatchedResultsIterator or otherwise at
        # most 30 clubs are returned!
        club_structs = self.protocol.get("/athlete/clubs")
        return [
            model.Club.parse_obj({**raw, **{"bound_client": self}})
            for raw in club_structs
        ]

    def join_club(self, club_id: int) -> None:
        """Joins the club on behalf of authenticated athlete.

        (Access token with write permissions required.)

        Parameters
        ----------
        club_id : int
            The numeric ID of the club to join.

        Returns
        -------
        No actual return. This implements a post action that allows the athlete
        to join a club via an API.

        """
        self.protocol.post("clubs/{id}/join", id=club_id)

    def leave_club(self, club_id: int) -> None:
        """Leave club on behalf of authenticated user.

        (Access token with write permissions required.)

        Parameters
        ----------
        club_id : int


        Returns
        -------
        No actual return. This implements a post action that allows the athlete
        to leave a club via an API.

        """
        self.protocol.post("clubs/{id}/leave", id=club_id)

    def get_club(self, club_id: int) -> model.Club:
        """Return a specific club object.

        https://developers.strava.com/docs/reference/#api-Clubs-getClubById

        Parameters
        ----------
        club_id : int
            The ID of the club to fetch.

        Returns
        -------
        class: `model.Club` object containing the club data.

        """
        raw = self.protocol.get("/clubs/{id}", id=club_id)
        return model.Club.parse_obj({**raw, **{"bound_client": self}})

    def get_club_members(
        self, club_id: int, limit: int | None = None
    ) -> BatchedResultsIterator[model.Athlete]:
        """Gets the member objects for specified club ID.

        https://developers.strava.com/docs/reference/#api-Clubs-getClubMembersById

        Parameters
        ----------
        club_id : int
            The numeric ID for the club.
        limit : int
            Maximum number of athletes to return. (default unlimited)

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Athlete` objects.

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

    def get_club_activities(
        self, club_id: int, limit: int | None = None
    ) -> BatchedResultsIterator[model.Activity]:
        """Gets the activities associated with specified club.

        https://developers.strava.com/docs/reference/#api-Clubs-getClubActivitiesById

        Parameters
        ----------
        club_id : int
            The numeric ID for the club.
        limit : int
            Maximum number of activities to return. (default unlimited)

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Activity` objects.

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

    def get_activity(
        self, activity_id: int, include_all_efforts: bool = False
    ) -> model.Activity:
        """Gets specified activity.

        Will be detail-level if owned by authenticated user; otherwise
        summary-level.

        https://developers.strava.com/docs/reference/#api-Activities-getActivityById

        Parameters
        ----------
        activity_id : int
            The ID of activity to fetch.
        include_all_efforts : bool, default=False
            Whether to include segment efforts - only
            available to the owner of the activity.

        Returns
        -------
        class: `model.Activity`
            An Activity object containing the requested activity data.

        """
        raw = self.protocol.get(
            "/activities/{id}",
            id=activity_id,
            include_all_efforts=include_all_efforts,
        )
        return model.Activity.parse_obj({**raw, **{"bound_client": self}})

    # TODO: REMOVE from API altogether given deprecation of end point
    def get_friend_activities(self, limit: int | None = None) -> NoReturn:
        """DEPRECATED This endpoint was removed by Strava in Jan 2018.

        Parameters
        ----------
        limit : int
            Maximum number of activities to return. (default unlimited)

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Activity` objects.

        """
        raise NotImplementedError(
            "The /activities/following endpoint was removed by Strava.  "
            "See https://developers.strava.com/docs/january-2018-update/"
        )

    def create_activity(
        self,
        name: str,
        activity_type: ActivityType,
        start_date_local: datetime | str,
        elapsed_time: int | timedelta,
        description: str | None = None,
        distance: pint.Quantity | float | None = None,
    ) -> model.Activity:
        """Create a new manual activity.

        If you would like to create an activity from an uploaded GPS file, see the
        :meth:`stravalib.client.Client.upload_activity` method instead.

        Parameters
        ----------
        name : str
            The name of the activity.
        activity_type : str
            The activity type (case-insensitive).
            Possible values: ride, run, swim, workout, hike, walk, nordicski,
            alpineski, backcountryski, iceskate, inlineskate, kitesurf,
            rollerski, windsurf, workout, snowboard, snowshoe
        start_date_local : class:`datetime.datetime` or string in ISO8601 format
            Local date/time of activity start. (TZ info will be ignored)
        elapsed_time : class:`datetime.timedelta` or int (seconds)
            The time in seconds or a :class:`datetime.timedelta` object.
        description : str, default=None
            The description for the activity.
        distance : class:`pint.Quantity` or float (meters), default=None
            The distance in meters (float) or a :class:`pint.Quantity` instance.

        """
        if isinstance(elapsed_time, timedelta):
            elapsed_time = elapsed_time.seconds

        if is_quantity_type(distance):
            distance = float(unithelper.meters(cast(pint.Quantity, distance)))

        if isinstance(start_date_local, datetime):
            start_date_local = start_date_local.strftime("%Y-%m-%dT%H:%M:%SZ")

        if not activity_type.lower() in [
            t.lower() for t in model.Activity.TYPES
        ]:
            raise ValueError(
                f"Invalid activity type: {activity_type}. Possible values: {model.Activity.TYPES!r}"
            )

        params: dict[str, Any] = dict(
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
        activity_id: int,
        name: str | None = None,
        activity_type: ActivityType | None = None,
        sport_type: SportType | None = None,
        private: bool | None = None,
        commute: bool | None = None,
        trainer: bool | None = None,
        gear_id: int | None = None,
        description: str | None = None,
        device_name: str | None = None,
        hide_from_home: bool | None = None,
    ) -> model.Activity:
        """Updates the properties of a specific activity.

        https://developers.strava.com/docs/reference/#api-Activities-updateActivityById

        Parameters
        ----------
        activity_id : int
            The ID of the activity to update.
        name : str, default=None
            The name of the activity.
        activity_type : str, default=None
            The activity type (case-insensitive).
            Deprecated. Prefer to use sport_type. In a request where both type
            and sport_type are present, this field will be ignored.
            See https://developers.strava.com/docs/reference/#api-models-UpdatableActivity.
            Possible values: ride, run, swim, workout, hike, walk, nordicski,
            alpineski, backcountryski, iceskate, inlineskate, kitesurf,
            rollerski, windsurf, workout, snowboard, snowshoe
        sport_type : str, default=None
            Possible values (case-sensitive): AlpineSki, BackcountrySki,
            Badminton, Canoeing, Crossfit, EBikeRide, Elliptical,
            EMountainBikeRide, Golf, GravelRide, Handcycle,
            HighIntensityIntervalTraining, Hike, IceSkate, InlineSkate,
            Kayaking, Kitesurf, MountainBikeRide, NordicSki, Pickleball,
            Pilates, Racquetball, Ride, RockClimbing, RollerSki, Rowing, Run,
            Sail, Skateboard, Snowboard, Snowshoe, Soccer, Squash,
            StairStepper, StandUpPaddling, Surfing, Swim, TableTennis, Tennis,
            TrailRun, Velomobile, VirtualRide, VirtualRow, VirtualRun, Walk,
            WeightTraining, Wheelchair, Windsurf, Workout, Yoga
        private : bool, default=None
            Whether the activity is private.
            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        commute : bool, default=None
            Whether the activity is a commute.
        trainer : bool, default=None
            Whether this is a trainer activity.
        gear_id : int, default=None
            Alphanumeric ID of gear (bike, shoes) used on this activity.
        description : str, default=None
            Description for the activity.
        device_name : str, default=None
            Device name for the activity
            .. deprecated:: 1.0
            This param is not supported by the Strava API and may be
            removed in the future.
        hide_from_home : bool, default=None
            Whether the activity is muted (hidden from Home and Club feeds).

        Returns
        -------
            Updates the activity in the selected Strava account


        """

        # Convert the kwargs into a params dict
        params: dict[str, Any] = {}

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
            warn_param_deprecation(
                "activity_type",
                "sport_type",
                "https://developers.strava.com/docs/reference/#api-models-UpdatableActivity",
            )

        if sport_type is not None:
            if not sport_type in model.Activity.SPORT_TYPES:
                raise ValueError(
                    f"Invalid activity type: {sport_type}. Possible values: {model.Activity.SPORT_TYPES!r}"
                )
            params["sport_type"] = sport_type
            params.pop(
                "type", None
            )  # Just to be sure we don't confuse the Strava API

        if private is not None:
            warn_param_unsupported("private")
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
            warn_param_unsupported("device_name")
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
        activity_file: SupportsRead[str | bytes],
        data_type: Literal["fit", "fit.gz", "tcx", "tcx.gz", "gpx", "gpx.gz"],
        name: str | None = None,
        description: str | None = None,
        activity_type: ActivityType | None = None,
        private: bool | None = None,
        external_id: str | None = None,
        trainer: bool | None = None,
        commute: bool | None = None,
    ) -> ActivityUploader:
        """Uploads a GPS file (tcx, gpx) to create a new activity for current
        athlete.

        https://developers.strava.com/docs/reference/#api-Uploads-createUpload

        Parameters
        ----------
        activity_file : TextIOWrapper, str or bytes
            The file object to upload or file contents.
        data_type : str
            File format for upload. Possible values: fit, fit.gz, tcx, tcx.gz,
            gpx, gpx.gz
        name : str, optional, default=None
            If not provided, will be populated using start date and location,
            if available
        description : str, optional, default=None
            The description for the activity
        activity_type : str, optional
            case-insensitive type of activity.
            possible values: ride, run, swim, workout, hike, walk,
            nordicski, alpineski, backcountryski, iceskate, inlineskate,
            kitesurf, rollerski, windsurf, workout, snowboard, snowshoe
            Type detected from file overrides, uses athlete's default type if
            not specified
            WARNING - This param is supported (as of 2022-11-15), but not
            documented and may be removed in the future.
        private : bool, optional, default=None
            Set to True to mark the resulting activity as private,
            'view_private' permissions will be necessary to view the activity.

            .. deprecated:: 1.0
                This param is not supported by the Strava API and may be
                removed in the future.
        external_id : str, optional, default=None
            An arbitrary unique identifier may be specified which
            will be included in status responses.
        trainer : bool, optional, default=None
            Whether the resulting activity should be marked as having
            been performed on a trainer.
        commute : bool, optional, default=None
            Whether the resulting activity should be tagged as a commute.

        """
        if not hasattr(activity_file, "read"):
            if isinstance(activity_file, str):
                activity_file = BytesIO(activity_file.encode("utf-8"))
            elif isinstance(activity_file, bytes):
                activity_file = BytesIO(activity_file)
            else:
                raise TypeError(
                    "Invalid type specified for activity_file: {}".format(
                        type(activity_file)
                    )
                )

        valid_data_types = ("fit", "fit.gz", "tcx", "tcx.gz", "gpx", "gpx.gz")
        if data_type not in valid_data_types:
            raise ValueError(
                f"Invalid data type {data_type}. Possible values {valid_data_types!r}"
            )

        params: dict[str, Any] = {"data_type": data_type}
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
            warn_param_unsupported("private")
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

    def delete_activity(self, activity_id: int) -> None:
        """Deletes the specified activity.

        https://developers.strava.com/docs/reference/#api-Activities

        Parameters
        ----------
        activity_id : int
            The activity to delete.

        """
        self.protocol.delete("/activities/{id}", id=activity_id)

    def get_activity_zones(
        self, activity_id: int
    ) -> list[model.BaseActivityZone]:
        """Gets zones for activity.

        Requires premium account.

        https://developers.strava.com/docs/reference/#api-Activities-getZonesByActivityId

        Parameters
        ----------
        activity_id : int
            The activity for which to get zones.

        Returns
        -------
        py:class:`list`
            A list of :class:`stravalib.model.BaseActivityZone` objects.

        """
        zones = self.protocol.get("/activities/{id}/zones", id=activity_id)
        return [
            model.BaseActivityZone.parse_obj({**z, **{"bound_client": self}})
            for z in zones
        ]

    def get_activity_comments(
        self,
        activity_id: int,
        markdown: bool = False,
        limit: int | None = None,
    ) -> BatchedResultsIterator[model.ActivityComment]:
        """Gets the comments for an activity.

        https://developers.strava.com/docs/reference/#api-Activities-getCommentsByActivityId

        Parameters
        ----------
        activity_id : int
            The activity for which to fetch comments.
        markdown : bool
            Whether to include markdown in comments (default is false/filterout)
        limit : int
            Max rows to return (default unlimited).

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.ActivityComment` objects.

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

    def get_activity_kudos(
        self, activity_id: int, limit: int | None = None
    ) -> BatchedResultsIterator[model.ActivityKudos]:
        """Gets the kudos for an activity.

        https://developers.strava.com/docs/reference/#api-Activities-getKudoersByActivityId

        Parameters
        ----------
        activity_id : int
            The activity for which to fetch kudos.
        limit : int
            Max rows to return (default unlimited).

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.ActivityKudos` objects.

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

    def get_activity_photos(
        self,
        activity_id: int,
        size: int | None = None,
        only_instagram: bool = False,
    ) -> BatchedResultsIterator[model.ActivityPhoto]:
        """Gets the photos from an activity.

        https://developers.strava.com/docs/reference/#api-Activities

        Parameters
        ----------
        activity_id : int
            The activity for which to fetch photos.
        size : int, default=None
            the requested size of the activity's photos. URLs for the photos
            will be returned that best match the requested size. If not
            included, the smallest size is returned
        only_instagram : bool, default=False
            Parameter to preserve legacy behavior of only returning Instagram
            photos.

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.ActivityPhoto` objects.

        """
        params: dict[str, Any] = {}

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

    def get_activity_laps(
        self, activity_id: int
    ) -> BatchedResultsIterator[model.ActivityLap]:
        """Gets the laps from an activity.

        https://developers.strava.com/docs/reference/#api-Activities-getLapsByActivityId

        Parameters
        ----------
        activity_id : int
            The activity for which to fetch laps.

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.ActivityLaps` objects.

        """
        result_fetcher = functools.partial(
            self.protocol.get, "/activities/{id}/laps", id=activity_id
        )

        return BatchedResultsIterator(
            entity=model.ActivityLap,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

    # TODO remove this method given deprecation of end point
    def get_related_activities(
        self, activity_id: int, limit: int | None = None
    ) -> NoReturn:
        """Deprecated. This endpoint was removed by strava in Jan 2018.

        Parameters
        ----------
        activity_id : int
            The activity for which to fetch related activities.
        limit : int, default=None
             Rate limit value for getting activities

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Activity` objects.

        """
        raise NotImplementedError(
            "The /activities/{id}/related endpoint was removed by Strava.  "
            "See https://developers.strava.com/docs/january-2018-update/"
        )

    def get_gear(self, gear_id: str) -> model.Gear:
        """Get details for an item of gear.

        https://developers.strava.com/docs/reference/#api-Gears

        Parameters
        ----------
        gear_id : str
            The gear id.

        Returns
        -------
        class:`stravalib.model.Gear`
            The Bike or Shoe subclass object.

        """
        return model.Gear.parse_obj(
            self.protocol.get("/gear/{id}", id=gear_id)
        )

    def get_segment_effort(self, effort_id: int) -> model.SegmentEffort:
        """Return a specific segment effort by ID.

        https://developers.strava.com/docs/reference/#api-SegmentEfforts

        Parameters
        ----------
        effort_id : int
            The id of associated effort to fetch.

        Returns
        -------
        class:`stravalib.model.SegmentEffort`
            The specified effort on a segment.

        """
        return model.SegmentEffort.parse_obj(
            self.protocol.get("/segment_efforts/{id}", id=effort_id)
        )

    def get_segment(self, segment_id: int) -> model.Segment:
        """Gets a specific segment by ID.

        https://developers.strava.com/docs/reference/#api-SegmentEfforts-getSegmentEffortById

        Parameters
        ----------
        segment_id : int
            The segment to fetch.

        Returns
        -------
        class:`stravalib.model.Segment`
            A segment object.

        """
        return model.Segment.parse_obj(
            {
                **self.protocol.get("/segments/{id}", id=segment_id),
                **{"bound_client": self},
            }
        )

    def get_starred_segments(
        self, limit: int | None = None
    ) -> BatchedResultsIterator[model.Segment]:
        """Returns a summary representation of the segments starred by the
         authenticated user. Pagination is supported.

        https://developers.strava.com/docs/reference/#api-Segments-getLoggedInAthleteStarredSegments

        Parameters
        ----------
        limit : int, optional, default=None
            Limit number of starred segments returned.

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Segment` starred by authenticated user.

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

    def get_athlete_starred_segments(
        self, athlete_id: int, limit: int | None = None
    ) -> BatchedResultsIterator[model.Segment]:
        """Returns a summary representation of the segments starred by the
         specified athlete. Pagination is supported.

        https://developers.strava.com/docs/reference/#api-Segments-getLoggedInAthleteStarredSegments

        Parameters
        ----------
        athlete_id : int
            The ID of the athlete.
        limit : int, optional, default=None
            Limit number of starred segments returned.

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Segment` starred by
            authenticated user.

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
        segment_id: int,
        athlete_id: int | None = None,
        start_date_local: datetime | str | None = None,
        end_date_local: datetime | str | None = None,
        limit: int | None = None,
    ) -> BatchedResultsIterator[model.BaseEffort]:
        """Gets all efforts on a particular segment sorted by start_date_local

        Returns an array of segment effort summary representations sorted by
        start_date_local ascending or by elapsed_time if an athlete_id is
        provided.

        If no filtering parameters is provided all efforts for the segment
        will be returned.

        Date range filtering is accomplished using an inclusive start and end
        time, thus start_date_local and end_date_local must be sent together.
        For open ended ranges pick dates significantly in the past or future.
        The filtering is done over local time for the segment, so there is no
        need for timezone conversion. For example, all efforts on Jan. 1st, 2014
        for a segment in San Francisco, CA can be fetched using
        2014-01-01T00:00:00Z and 2014-01-01T23:59:59Z.

        https://developers.strava.com/docs/reference/#api-SegmentEfforts-getEffortsBySegmentId

        Parameters
        ----------
        segment_id : int
            ID for the segment of interest
        athlete_id: int, optional
            ID of athlete.
        start_date_local : datetime.datetime or str, optional, default=None
            Efforts before this date will be excluded.
            Either as ISO8601 or datetime object
        end_date_local : datetime.datetime or str, optional, default=None
            Efforts after this date will be excluded.
            Either as ISO8601 or datetime object
        limit : int, default=None, optional
            limit number of efforts.
        athlete_id : int, default=None
            Strava ID for the athlete

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.SegmentEffort` efforts on
            a segment.

        """
        params: dict[str, Any] = {"segment_id": segment_id}

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
        self,
        bounds: tuple[float, float, float, float]
        | tuple[tuple[float, float], tuple[float, float]],
        activity_type: ActivityType | None = None,
        min_cat: int | None = None,
        max_cat: int | None = None,
    ) -> list[model.SegmentExplorerResult]:
        """Returns an array of up to 10 segments.

        https://developers.strava.com/docs/reference/#api-Segments-exploreSegments

        Parameters
        ----------
        bounds : tuple of 4 floats or tuple of 2 (lat,lon) tuples
            list of bounding box corners lat/lon
            [sw.lat, sw.lng, ne.lat, ne.lng] (south,west,north,east)
        activity_type : str
            optional, default is riding)  'running' or 'riding'
        min_cat : int, optional, default=None
            Minimum climb category filter
        max_cat : int, optional, default=None
            Maximum climb category filter

        Returns
        -------
        py:class:`list`
            An list of :class:`stravalib.model.Segment`.

        """
        if len(bounds) == 2:
            bounds = (
                bounds[0][0],
                bounds[0][1],
                bounds[1][0],
                bounds[1][1],
            )
        elif len(bounds) != 4:
            raise ValueError(
                "Invalid bounds specified: {0!r}. Must be tuple of 4 float "
                "values or tuple of 2 (lat,lon) tuples."
            )

        params: dict[str, Any] = {"bounds": ",".join(str(b) for b in bounds)}

        valid_activity_types = ("riding", "running")
        if activity_type is not None:
            if activity_type not in ("riding", "running"):
                raise ValueError(
                    "Invalid activity type: {}.  Possible values: {!r}".format(
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

    def _get_streams(
        self,
        stream_url: str,
        types: list[StreamType] | None = None,
        resolution: Literal["low", "medium", "high"] | None = None,
        series_type: Literal["time", "distance"] | None = None,
    ) -> dict[StreamType, model.Stream]:
        """
        Generic method to retrieve stream data for activity, effort or
        segment.

        https://developers.strava.com/docs/reference/#api-Streams-getActivityStreams

        Streams represent the raw spatial data for the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                           heartrate, cadence, watts, temp, moving, grade_smooth

        Parameters
        ----------
        stream_url : str
            Resource locator for the streams
        types : list[str], optional, default=None
            A list of the types of streams to fetch.
        resolution : str, optional
            Indicates desired number of data points. 'low' (100), 'medium'
            (1000) or 'high' (10000).
            .. deprecated::
                This param is not officially supported by the Strava API and may be
                removed in the future.
        series_type : str, optional
            Relevant only if using resolution either 'time' or 'distance'.
            Used to index the streams if the stream is being reduced.
            .. deprecated::
                This param is not officially supported by the Strava API and may be
                removed in the future.

        Returns
        -------
        py:class:`dict`
            An dictionary of :class:`stravalib.model.Stream` from the activity
        """
        extra_params: dict[str, Any] = {}
        if resolution is not None:
            warn_param_unofficial("resolution")
            extra_params["resolution"] = resolution
        if series_type is not None:
            warn_param_unofficial("series_type")
            extra_params["series_type"] = series_type
        if not types:
            types = strava_model.StreamType.schema()["enum"]
        assert types is not None
        invalid_types = set(types).difference(
            strava_model.StreamType.schema()["enum"]
        )
        if invalid_types:
            raise ValueError(
                f"Types {invalid_types} not supported by StravaApi"
            )
        types_arg = ",".join(types)

        response = self.protocol.get(
            stream_url, keys=types_arg, key_by_type=True, **extra_params
        )
        return {
            stream_type: model.Stream.parse_obj(stream)
            for stream_type, stream in response.items()
        }

    def get_activity_streams(
        self,
        activity_id: int,
        types: list[StreamType] | None = None,
        resolution: Literal["low", "medium", "high"] | None = None,
        series_type: Literal["time", "distance"] | None = None,
    ) -> dict[StreamType, model.Stream]:
        """Returns a stream for an activity.

        https://developers.strava.com/docs/reference/#api-Streams-getActivityStreams

        Streams represent the raw spatial data for the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                            heartrate, cadence, watts, temp, moving, grade_smooth

        Parameters
        ----------
        activity_id : int
            The ID of activity.
        types : list[str], optional, default=None
            A list of the types of streams to fetch.
        resolution : str, optional
            Indicates desired number of data points. 'low' (100), 'medium'
            (1000) or 'high' (10000).
            .. deprecated::
                This param is not officially supported by the Strava API and
                may be removed in the future.
        series_type : str, optional
            Relevant only if using resolution either 'time' or 'distance'.
            Used to index the streams if the stream is being reduced.
            .. deprecated::
                This param is not officially supported by the Strava API and may be
                removed in the future.

        Returns
        -------
        py:class:`dict`
            A dictionary of :class:`stravalib.model.Stream` from the activity
        """
        return self._get_streams(
            f"/activities/{activity_id}/streams",
            types=types,
            resolution=resolution,
            series_type=series_type,
        )

    def get_effort_streams(
        self,
        effort_id: int,
        types: list[StreamType] | None = None,
        resolution: Literal["low", "medium", "high"] | None = None,
        series_type: Literal["time", "distance"] | None = None,
    ) -> dict[StreamType, model.Stream]:
        """Returns an streams for an effort.

        https://developers.strava.com/docs/reference/#api-Streams-getSegmentEffortStreams

        Streams represent the raw data of the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
                           heartrate, cadence, watts, temp, moving, grade_smooth

        Parameters
        ----------
        effort_id : int
            The ID of effort.
        types : list, optional, default=None
            A list of the the types of streams to fetch.
        resolution : str, optional
            Indicates desired number of data points. 'low' (100), 'medium'
            (1000) or 'high' (10000).
            .. deprecated::

                This param is not officially supported by the Strava API and
                may be removed in the future.

        series_type : str, optional
            Relevant only if using resolution either 'time' or 'distance'.
            Used to index the streams if the stream is being reduced.
            .. deprecated::

                This param is not officially supported by the Strava API and
                may be removed in the future.

        Returns
        -------
        py:class:`dict`
            An dictionary of :class:`stravalib.model.Stream` from the effort.

        """
        return self._get_streams(
            f"/segment_efforts/{effort_id}/streams",
            types=types,
            resolution=resolution,
            series_type=series_type,
        )

    def get_segment_streams(
        self,
        segment_id: int,
        types: list[StreamType] | None = None,
        resolution: Literal["low", "medium", "high"] | None = None,
        series_type: Literal["time", "distance"] | None = None,
    ) -> dict[StreamType, model.Stream]:
        """Returns an streams for a segment.

        https://developers.strava.com/docs/reference/#api-Streams-getSegmentStreams

        Streams represent the raw data of the uploaded file. External
        applications may only access this information for activities owned
        by the authenticated athlete.

        Streams are available in 11 different types. If the stream is not
        available for a particular activity it will be left out of the request
        results.

        Streams types are: time, latlng, distance, altitude, velocity_smooth,
        heartrate, cadence, watts, temp, moving, grade_smooth

        Parameters
        ----------
        segment_id : int
            The ID of segment.
        types : list, optional, default=None
            A list of the the types of streams to fetch.
        resolution : str, optional
            Indicates desired number of data points. 'low' (100), 'medium'
            (1000) or 'high' (10000).
            .. deprecated::
                This param is not officially supported by the Strava API and may be
                removed in the future.
        series_type : str, optional
            Relevant only if using resolution either 'time' or 'distance'.
            Used to index the streams if the stream is being reduced.
            .. deprecated::
                This param is not officially supported by the Strava API and may be
                removed in the future.

        Returns
        -------
        py:class:`dict`
            An dictionary of :class:`stravalib.model.Stream` from the effort.

        """
        return self._get_streams(
            f"/segments/{segment_id}/streams",
            types=types,
            resolution=resolution,
            series_type=series_type,
        )

    def get_routes(
        self, athlete_id: int | None = None, limit: int | None = None
    ) -> BatchedResultsIterator[model.Route]:
        """Gets the routes list for an authenticated user.

        https://developers.strava.com/docs/reference/#api-Routes-getRoutesByAthleteId

        Parameters
        ----------
        athlete_id : int, default=None
            Strava athlete ID
        limit : int, default=unlimited
            Max rows to return.

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Route` objects.

        """
        if athlete_id is None:
            athlete_id = self.get_athlete().id

        result_fetcher = functools.partial(
            self.protocol.get, f"/athletes/{athlete_id}/routes"
        )

        return BatchedResultsIterator(
            entity=model.Route,
            bind_client=self,
            result_fetcher=result_fetcher,
            limit=limit,
        )

    def get_route(self, route_id: int) -> model.Route:
        """Gets specified route.

        Will be detail-level if owned by authenticated user; otherwise
        summary-level.

        https://developers.strava.com/docs/reference/#api-Routes-getRouteById

        Parameters
        ----------
        route_id : int
            The ID of route to fetch.

        Returns
        -------
        class: `model.Route`
            A model.Route object containing the route data.

        """
        raw = self.protocol.get("/routes/{id}", id=route_id)
        return model.Route.parse_obj({**raw, **{"bound_client": self}})

    def get_route_streams(
        self, route_id: int
    ) -> dict[StreamType, model.Stream]:
        """Returns streams for a route.

        Streams represent the raw data of the saved route. External
        applications may access this information for all public routes and for
        the private routes of the authenticated athlete. The 3 available route
        stream types `distance`, `altitude` and `latlng` are always returned.

        See: https://developers.strava.com/docs/reference/#api-Streams-getRouteStreams

        Parameters
        ----------
        route_id : int
            The ID of activity.

        Returns
        -------
        py:class:`dict`
            A dictionary of :class:`stravalib.model.Stream` from the route.

        """

        result_fetcher = functools.partial(
            self.protocol.get, f"/routes/{route_id}/streams/"
        )

        streams = BatchedResultsIterator(
            entity=model.Stream,
            bind_client=self,
            result_fetcher=result_fetcher,
        )

        # Pack streams into dictionary
        return {cast(StreamType, i.type): i for i in streams}

    # TODO: removed old link to create a subscription but can't find new equiv
    # in current strava docs
    def create_subscription(
        self,
        client_id: int,
        client_secret: str,
        callback_url: str,
        verify_token: str = model.Subscription.VERIFY_TOKEN_DEFAULT,
    ) -> model.Subscription:
        """Creates a webhook event subscription.

        Parameters
        ----------
        client_id : int
            application's ID, obtained during registration
        client_secret : str
            application's secret, obtained during registration
        callback_url : str
            callback URL where Strava will first send a GET request to validate,
            then subsequently send POST requests with updates
        verify_token : str
            a token you can use to verify Strava's GET callback request (Default
            value = model.Subscription.VERIFY_TOKEN_DEFAULT)

        Returns
        -------
        class:`stravalib.model.Subscription`

        Notes
        -----

        `verify_token` is set to a default in the event that the author
        doesn't want to specify one.

        The application must have permission to make use of the webhook API.
        Access can be requested by contacting developers -at- strava.com.
        An instance of :class:`stravalib.model.Subscription`.

        """
        params: dict[str, Any] = dict(
            client_id=client_id,
            client_secret=client_secret,
            callback_url=callback_url,
            verify_token=verify_token,
        )
        raw = self.protocol.post("/push_subscriptions", **params)
        return model.Subscription.parse_obj({**raw, **{"bound_client": self}})

    # TODO: UPDATE - this method uses (de)serialize which is deprecated
    def handle_subscription_callback(
        self,
        raw: dict[str, Any],
        verify_token: str = model.Subscription.VERIFY_TOKEN_DEFAULT,
    ) -> dict[str, str]:
        """Validate callback request and return valid response with challenge.

        Parameters
        ----------
        raw : dict
            The raw JSON response which will be serialized to a Python dict.
        verify_token : default=model.Subscription.VERIFY_TOKEN_DEFAULT

        Returns
        -------
        dict[str, str]
            The JSON response expected by Strava to the challenge request.

        """
        callback = model.SubscriptionCallback.deserialize(raw)
        callback.validate_token(verify_token)

        assert callback.hub_challenge is not None
        response_raw = {"hub.challenge": callback.hub_challenge}
        return response_raw

    def handle_subscription_update(
        self, raw: dict[str, Any]
    ) -> model.SubscriptionUpdate:
        """Converts a raw subscription update into a model.

        Parameters
        ----------
        raw : dict
            The raw json response deserialized into a dict.

        Returns
        -------
        class:`stravalib.model.SubscriptionUpdate`
            The subscription update model object.

        """
        return model.SubscriptionUpdate.parse_obj(
            {**raw, **{"bound_client": self}}
        )

    def list_subscriptions(
        self, client_id: int, client_secret: str
    ) -> BatchedResultsIterator[model.Subscription]:
        """List current webhook event subscriptions in place for the current
        application.

        Parameters
        ----------
        client_id : int
            application's ID, obtained during registration
        client_secret : str
            application's secret, obtained during registration

        Returns
        -------
        class:`BatchedResultsIterator`
            An iterator of :class:`stravalib.model.Subscription` objects.

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

    def delete_subscription(
        self, subscription_id: int, client_id: int, client_secret: str
    ) -> None:
        """Unsubscribe from webhook events for an existing subscription.

        Parameters
        ----------
        subscription_id : int
            ID of subscription to remove.
        client_id : int
            application's ID, obtained during registration
        client_secret : str
            application's secret, obtained during registration

        Returns
        -------
        Deletes the specific subscription using the subscription ID

        """
        self.protocol.delete(
            "/push_subscriptions/{id}",
            id=subscription_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        # Expects a 204 response if all goes well.


T = TypeVar("T", bound=BaseModel)


class ResultFetcher(Protocol):
    def __call__(self, *, page: int, per_page: int) -> Iterable[Any]:
        ...


class BatchedResultsIterator(Generic[T]):
    """An iterator that enables iterating over requests that return
    paged results."""

    # Number of results returned in a batch. We maximize this to minimize
    # requests to server (rate limiting)
    default_per_page = 200

    def __init__(
        self,
        entity: type[T],
        result_fetcher: ResultFetcher,
        bind_client: Client | None = None,
        limit: int | None = None,
        per_page: int | None = None,
    ):
        """

        Parameters
        ----------
        entity : type
            The class for the model entity.
        result_fetcher: callable
            The callable that will return another batch of results.
        bind_client: :class:`stravalib.client.Client`
            The client object to pass to the entities for supporting further
            fetching of objects.
        limit: int
            The maximum number of rides to return.
        per_page: int
            How many rows to fetch per page (default is 200).
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
            self.per_page = BatchedResultsIterator.default_per_page

        self._buffer: None | Deque[T]
        self.reset()

    def __repr__(self) -> str:
        return "<{} entity={}>".format(
            self.__class__.__name__, self.entity.__name__
        )

    def reset(self) -> None:
        self._counter = 0
        self._buffer = None
        self._page = 1
        self._all_results_fetched = False

    def _fill_buffer(self) -> None:
        """Fills the internal buffer from Strava API."""
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
                # Entity doesn't have a parse_obj() method, so must be of a
                # legacy type
                new_entity = self.entity.deserialize(  # type: ignore[attr-defined]
                    raw, bind_client=self.bind_client
                )
            entities.append(new_entity)

        self._buffer = collections.deque(entities)

        self.log.debug(
            "Requested page {} (got: {} items)".format(
                self._page, len(self._buffer)
            )
        )
        if len(self._buffer) < self.per_page:
            self._all_results_fetched = True

        self._page += 1

    def __iter__(self) -> BatchedResultsIterator[T]:
        return self

    def _eof(self) -> NoReturn:
        """ """
        self.reset()
        raise StopIteration

    def __next__(self) -> T:
        return self.next()

    def next(self) -> T:
        if self.limit and self._counter >= self.limit:
            self._eof()
        if not self._buffer:
            self._fill_buffer()
        assert self._buffer is not None
        try:
            result = self._buffer.popleft()
        except IndexError:
            self._eof()
        else:
            self._counter += 1
            return result


class ActivityUploader:
    """
    The "future" object that holds information about an activity file
    upload and can wait for upload to finish, etc.

    """

    def __init__(
        self, client: Client, response: dict[str, Any], raise_exc: bool = True
    ) -> None:
        """
        client: `stravalib.client.Client`
            The :class:`stravalib.client.Client` object that is handling the
            upload.
        response: Dict[str,Any]
            The initial upload response.
        raise_exc: bool
            Whether to raise an exception if the response
            indicates an error state. (default True)
        """
        self.client = client
        self.response = response
        self.update_from_response(response, raise_exc=raise_exc)
        self._photo_metadata

    @property
    def photo_metadata(self) -> PhotoMetadata:
        """photo metadata for the activity upload response, if any.
        it contains a pre-signed uri for uploading the photo.

        Notes
        -----
        * This is only available after the upload has completed.
        * This metadata is only available for partner apps. If you have a
        regular / non partner related Strava app / account it will not work.

        """

        warn_attribute_unofficial("photo_metadata")

        return self._photo_metadata

    @photo_metadata.setter
    def photo_metadata(self, value: PhotoMetadata) -> PhotoMetadata:
        """

        Parameters
        ----------
        value : list of dictionaries or none
            Contains an optional list of dictionaries with photo metadata or a
            value of `None`.

        Returns
        -------
        Updates the `_photo_metadata` value in the object

        """
        self._photo_metadata = value

    def update_from_response(
        self, response: dict[str, Any], raise_exc: bool = True
    ) -> None:
        """Updates internal state of object.

        Parameters
        ----------
        response : py:class:`dict`
            The response object (dict).
        raise_exc : bool

        Raises
        ------
        stravalib.exc.ActivityUploadFailed
            If the response indicates an
            error and raise_exc is True. Whether to raise an exception if the
            response indicates an error state. (default True)

        Returns
        -------

        """
        self.upload_id = response.get("id")
        self.external_id = response.get("external_id")
        self.activity_id = response.get("activity_id")
        self.status = response.get("status") or response.get("message")
        # Undocumented field, it contains pre-signed uri to upload photo to
        self._photo_metadata = response.get("photo_metadata")

        if response.get("error"):
            self.error = response.get("error")
        elif response.get("errors"):
            # This appears to be an undocumented API; this is a temp hack
            self.error = str(response.get("errors"))
        else:
            self.error = None

        if raise_exc:
            self.raise_for_error()

    @property
    def is_processing(self) -> bool:
        """ """
        return self.activity_id is None and self.error is None

    @property
    def is_error(self) -> bool:
        """ """
        return self.error is not None

    @property
    def is_complete(self) -> bool:
        """ """
        return self.activity_id is not None

    def raise_for_error(self) -> None:
        """ """
        # FIXME: We need better handling of the actual responses, once those are
        # more accurately documented.
        if self.error:
            raise exc.ActivityUploadFailed(self.error)
        elif self.status == "The created activity has been deleted.":
            raise exc.CreatedActivityDeleted(self.status)

    def poll(self) -> None:
        """Update internal state from polling strava.com.

        Raises
        -------
        class: `stravalib.exc.ActivityUploadFailed` If poll returns an error.

        """
        response = self.client.protocol.get(
            "/uploads/{upload_id}",
            upload_id=self.upload_id,
            check_for_errors=False,
        )

        self.update_from_response(response)

    def wait(
        self, timeout: float | None = None, poll_interval: float = 1.0
    ) -> model.Activity:
        """Wait for the upload to complete or to err out.

        Will return the resulting Activity or raise an exception if the
        upload fails.

        Parameters
        ----------
        timeout : float, default=None
            The max seconds to wait. Will raise TimeoutExceeded
            exception if this time passes without success or error response.
        poll_interval : float, default=1.0 (seconds)
            How long to wait between upload checks.  Strava
            recommends 1s minimum.

        Returns
        -------
        class:`stravalib.model.Activity`

        Raises
        ------
        stravalib.exc.TimeoutExceeded
            If a timeout was specified and activity is still processing
            after timeout has elapsed.
        stravalib.exc.ActivityUploadFailed
            If the poll returns an error.
            The uploaded Activity object (fetched from server)

        """
        start = time.time()
        while self.activity_id is None:
            self.poll()
            time.sleep(poll_interval)
            if timeout and (time.time() - start) > timeout:
                raise exc.TimeoutExceeded()
        # If we got this far, we must have an activity!
        return self.client.get_activity(self.activity_id)

    def upload_photo(
        self, photo: SupportsRead[bytes], timeout: float | None = None
    ) -> None:
        """Uploads a photo to the activity.

        Parameters
        ----------
        photo : bytes
            The file-like object to upload.
        timeout : float, default=None
            The max seconds to wait. Will raise TimeoutExceeded

        Notes
        -----
        In order to upload a photo, the activity must be uploaded and
        processed.

        The ability to add photos to activity is currently limited to
        partner apps & devices such as Zwift, Peloton, Tempo Move, etc...
        Given that the ability isn't in the public API, neither are the docs


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

            photos_data: list[dict[Any, Any]] = [
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
