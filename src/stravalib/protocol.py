"""Protocol
==============
Low-level classes for interacting directly with the Strava API webservers.
"""

from __future__ import annotations

import abc
import functools
import logging
import os
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, TypedDict
from urllib.parse import urlencode, urljoin, urlunsplit

import requests

from stravalib import exc

if TYPE_CHECKING:
    from _typeshed import SupportsRead

Scope = Literal[
    "read",
    "read_all",
    "profile:read_all",
    "profile:write",
    "activity:read",
    "activity:read_all",
    "activity:write",
]

RequestMethod = Literal["GET", "POST", "PUT", "DELETE"]


class AccessInfo(TypedDict):
    """Dictionary containing token exchange response from Strava."""

    access_token: str
    """A short live token the access Strava API"""

    refresh_token: str
    """The refresh token for this user, to be used to get the next access token
    for this user. Please expect that this value can change anytime you
    retrieve a new access token. Once a new refresh token code has been
    returned, the older code will no longer work.
    """

    expires_at: int
    """The number of seconds since the epoch when the provided access token
    will expire"""


class ApiV3(metaclass=abc.ABCMeta):
    """This class is responsible for performing the HTTP requests, rate
    limiting, and error handling."""

    server = "www.strava.com"
    api_base = "/api/v3"

    def __init__(
        self,
        access_token: str | None = None,
        requests_session: requests.Session | None = None,
        rate_limiter: (
            Callable[[dict[str, str], RequestMethod], None] | None
        ) = None,
        token_expires: int | None = None,
        refresh_token: str | None = None,
        client_id: int | None = None,
        client_secret: str | None = None,
    ):
        """Initialize this protocol client, optionally providing a (shared)
        :class:`requests.Session` object.

        Parameters
        ----------
        access_token : str
            The token that provides access to a specific Strava account.
        requests_session : :class:`requests.Session`
            An existing :class:`requests.Session` object to use.
        rate_limiter : Callable[[dict[str, str], RequestMethod], None], optional
            A callable used to enforce rate-limiting for API requests.
            The callable accepts a dict of headers and the
            HTTP request method as arguments. Defaults to None.
        token_expires: int
            Epoch time in seconds when the token expires
        refresh_token: str
            Refresh token used to re-authenticate with Strava
        client_id: int
            client id for the Strava APP pulled from the users envt
        client_secret: str
            client secret for the Strava app pulled from the users envt
        """
        self.log = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self.access_token: str | None = access_token
        self.token_expires: int | None = token_expires
        self.refresh_token: str | None = refresh_token
        self.client_id: int | None = None
        self.client_secret: str | None = None
        if requests_session:
            self.rsession: requests.Session = requests_session
        else:
            self.rsession = requests.Session()

        self.rate_limiter = rate_limiter or (
            lambda _request_params, _method: None
        )
        # Check for credentials when initializing
        self._check_credentials()

    def _check_credentials(self) -> None:
        """Gets Strava client_id and secret credentials from user's environment.

        If the user environment is populated with both values and
        client_id is a proper int, it returns a tuple with both values.
        Otherwise it returns None.

        Returns
        -------
        None
            If the client_id and secret are available it populates self
            with both variables to support automatic token refresh.
        """
        # Default both to None; set if they are available in the correct format
        client_id: int | None = None
        client_secret: str | None = None

        client_id_str = os.environ.get("STRAVA_CLIENT_ID")
        client_secret = os.environ.get("STRAVA_CLIENT_SECRET")
        # Make sure client_id exists and can be cast to int
        if client_id_str:
            try:
                # Make sure client_id is a valid int
                client_id = int(client_id_str)
            except ValueError:
                logging.error("STRAVA_CLIENT_ID must be a valid integer.")
        else:
            logging.error(
                "Please make sure your STRAVA_CLIENT_ID is set in your environment."
            )

        if client_id and client_secret:
            self.client_id = client_id
            self.client_secret = client_secret
        else:
            logging.warning(
                "STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET not found in your "
                " environment. Please refresh your access_token manually."
                " Or add STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET to your environment."
            )
        return None

    def _request(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        files: dict[str, SupportsRead[str | bytes]] | None = None,
        method: RequestMethod = "GET",
        check_for_errors: bool = True,
    ) -> Any:
        """Perform the underlying request, returning the parsed JSON results.

        Before running, this method will check to make sure that your
        access_token is valid. If it isn't, it will refresh it and then make
        the requested Strava API call.

        Parameters
        ----------
        url : str
            The request URL.
        params : Dict[str,Any]
            Request parameters
        files : Dict[str,file]
            Dictionary of file name to file-like objects.
        method : str
            The request method (GET/POST/etc.)
        check_for_errors : bool
            Whether to raise an error or not.

        Returns
        -------
        Dict[str, Any]
            The parsed JSON response.
        """

        # Only refresh token if we know the users' environment is setup
        if "/oauth/token" not in url and self.client_id and self.client_secret:
            self.refresh_expired_token()

        url = self.resolve_url(url)
        self.log.info(f"{method} {url!r} with params {params!r}")
        if params is None:
            params = {}
        if self.access_token:
            params["access_token"] = self.access_token

        methods = {
            "GET": self.rsession.get,
            "POST": functools.partial(self.rsession.post, files=files),
            "PUT": self.rsession.put,
            "DELETE": self.rsession.delete,
        }

        try:
            requester = methods[method.upper()]
        except KeyError:
            raise ValueError(
                f"Invalid/unsupported request method specified: {method}"
            )

        raw = requester(url, params=params)  # type: ignore[operator]
        # Rate limits are taken from HTTP response headers
        # https://developers.strava.com/docs/rate-limits/
        self.rate_limiter(raw.headers, method)

        if check_for_errors:
            self._handle_protocol_error(raw)

        # 204 = No content
        if raw.status_code in [204]:
            resp = {}
        else:
            resp = raw.json()

        return resp

    def _token_expired(self) -> bool:
        """Checks if a token has expired or not. Returns True if it's expired.

        Returns
        -------
        bool
            True if token has expired, otherwise returns false
        """
        if self.token_expires:
            if time.time() > self.token_expires:
                print("Your token has expired; Refreshing it now.")
                return True
            else:
                return False
        else:
            logging.warning(
                "Please make sure you've set client.token_expires if you"
                " want automatic token refresh to work"
            )
            return False

    def refresh_expired_token(self) -> None:
        """Checks to see if a token has expired and auto refreshes it
        if the user has setup their environment with the client
        secret information.

        Returns
        -------
        None
            If all is setup properly, updates and resets the access_token
            attribute. Otherwise it logs a warning
        """
        if not self.refresh_token:
            logging.warning(
                "Please set client.refresh_token if you want to use"
                "the auto token-refresh feature"
            )
            return

        # Token is not yet expired, move on
        if not self._token_expired():
            return

        # This should never be false, BUT mypy wants a reminder that these values
        # are populated
        assert self.client_id is not None, "client_id is required but is None."
        assert (
            self.client_secret is not None
        ), "client_secret is required but is None."

        # If the token is expired AND the refresh token exists
        if self._token_expired() and self.refresh_token:
            self.refresh_access_token(
                client_id=self.client_id,
                client_secret=self.client_secret,
                refresh_token=self.refresh_token,
            )
            return

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
            The URL that Strava will redirect to after successful (or
            failed) authorization.
        approval_prompt : str
            Whether to prompt for approval even if approval already
            granted to app. Choices are 'auto' or 'force'.  (Default is
            'auto')
        scope : list[str]
            The access scope required.  Omit to imply "read" and
            "activity:read" Valid values are 'read', 'read_all',
            'profile:read_all', 'profile:write', 'activity:read',
            'activity:read_all', 'activity:write'.
        state : str
            An arbitrary variable that will be returned to your
            application in the redirect URI.

        Returns
        -------
        str
            The URL to use for authorization link.
        """
        assert approval_prompt in ("auto", "force")
        if scope is None:
            scope = ["read", "activity:read"]
        elif isinstance(scope, (str, bytes)):
            scope = [scope]

        unsupported = set(scope) - {
            "read",
            "read_all",
            "profile:read_all",
            "profile:write",
            "activity:read",
            "activity:read_all",
            "activity:write",
        }

        assert not unsupported, f"Unsupported scope value(s): {unsupported}"

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "approval_prompt": approval_prompt,
            "scope": ",".join(scope),
            "response_type": "code",
        }
        if state is not None:
            params["state"] = state

        return urlunsplit(
            ("https", self.server, "/oauth/authorize", urlencode(params), "")
        )

    def exchange_code_for_token(
        self,
        client_id: int,
        client_secret: str,
        code: str,
        return_athlete: bool = False,
    ) -> tuple[AccessInfo, dict[str, Any] | None]:
        """Exchange the temporary authorization code (returned with redirect
        from Strava authorization URL) for a short-lived access token and a
        refresh token (used to obtain the next access token later on).

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
        client_secret : str
            The developer client secret
        code : str
            The temporary authorization code
        return_athlete : bool (optional, default=False)
            Whether to return the `SummaryAthlete` object with the token
            response. This behavior is currently undocumented and could
            change at any time. Default is `False`.

        Returns
        -------
        dict
            Dictionary containing the access_token, refresh_token and
            expires_at (number of seconds since Epoch when the provided
            access token will expire)
        """
        # The method returns: No rates present in response headers
        response = self._request(
            f"https://{self.server}/oauth/token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
            method="POST",
        )
        access_info: AccessInfo = {
            "access_token": response["access_token"],
            "refresh_token": response["refresh_token"],
            "expires_at": response["expires_at"],
        }
        self.access_token = response["access_token"]
        if return_athlete:
            # This will be None if Strava removes undocumented athlete response
            # from the undocumented endpoint return
            return access_info, response.get("athlete")
        else:
            return access_info, None

    def refresh_access_token(
        self,
        client_id: int,
        client_secret: str,
        refresh_token: str,
    ) -> AccessInfo:
        """Exchanges the previous refresh token for a short-lived access token
        and a new refresh token (used to obtain the next access token later on)

        Parameters
        ----------
        client_id : int
            The numeric developer client id.
        client_secret : str
            The developer client secret
        refresh_token : str
            The refresh token obtain from a previous authorization
            request

        Returns
        -------
        dict
            Dictionary containing the access_token, refresh_token and
            expires_at (number of seconds since Epoch when the provided
            access token will expire)

        Notes
        -----
        This method is user facing. Here, we don't populate client_id and
        client_secret from self; A user can call this method and refresh the token manually with
        those values.
        """
        response = self._request(
            f"https://{self.server}/oauth/token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            method="POST",
        )
        access_info: AccessInfo = {
            "access_token": response["access_token"],
            "refresh_token": response["refresh_token"],
            "expires_at": response["expires_at"],
        }
        self.access_token = response["access_token"]
        # Update expires_at and refresh to support automatic refresh
        self.refresh_token = response["refresh_token"]
        self.token_expires = response["expires_at"]

        return access_info

    def resolve_url(self, url: str) -> str:
        """

        Parameters
        ----------
        url : str
            url string to be be accessed / resolved

        Returns
        -------
        str
            A string representing the full properly formatted (https) url.
        """
        if not url.startswith("http"):
            url = urljoin(
                f"https://{self.server}",
                self.api_base + "/" + url.strip("/"),
            )
        return url

    def _handle_protocol_error(
        self, response: requests.Response
    ) -> requests.Response:
        """Parses the raw response from the server, raising a
        :class:`stravalib.exc.Fault` if the server returned an error.

        Parameters
        ----------
        response
            The response object.

        Raises
        ------
        Fault
            If the response contains an error.
        """
        error_str = None
        try:
            json_response = response.json()
        except ValueError:
            pass
        else:
            if "message" in json_response or "errors" in json_response:
                error_str = "{}: {}".format(
                    json_response.get("message", "Undefined error"),
                    json_response.get("errors"),
                )

        # Special subclasses for some errors
        if response.status_code == 404:
            msg = f"{response.reason}: {error_str}"
            raise exc.ObjectNotFound(msg, response=response)
        elif response.status_code == 401:
            msg = f"{response.reason}: {error_str}"
            raise exc.AccessUnauthorized(msg, response=response)
        elif 400 <= response.status_code < 500:
            msg = f"{response.status_code} Client Error: {response.reason} [{error_str}]"
            raise exc.Fault(msg, response=response)
        elif 500 <= response.status_code < 600:
            msg = f"{response.status_code} Server Error: {response.reason} [{error_str}]"
            raise exc.Fault(msg, response=response)
        elif error_str:
            msg = error_str
            raise exc.Fault(msg, response=response)

        return response

    def _extract_referenced_vars(self, s: str) -> list[str]:
        """Utility method to find the referenced format variables in a string.
        (Assumes string.format() format vars.)

        Parameters
        ----------
        s
            The string that contains format variables. (e.g.
            "{foo}-text")

        Returns
        -------
        list
            The list of referenced variable names. (e.g. ['foo'])
        """
        d: dict[str, int] = {}
        while True:
            try:
                s.format(**d)
            except KeyError as exc:
                # exc.args[0] contains the name of the key that was not found;
                # 0 is used because it appears to work with all types of
                # placeholders.
                d[exc.args[0]] = 0
            else:
                break
        return list(d.keys())

    def get(
        self, url: str, check_for_errors: bool = True, **kwargs: Any
    ) -> Any:
        """Performs a generic GET request for specified params, returning the
        response.

        Parameters
        ----------
        url : str
            String representing the url to retrieve
        check-for_errors: bool (default = True)
            Flag used to raise an error (or not)

        Returns
        -------
        dict
            Performs the request and returns a JSON object deserialized as dict

        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = {k: v for k, v in kwargs.items() if k not in referenced}
        return self._request(
            url, params=params, check_for_errors=check_for_errors
        )

    def post(
        self,
        url: str,
        files: dict[str, SupportsRead[str | bytes]] | None = None,
        check_for_errors: bool = True,
        **kwargs: Any,
    ) -> Any:
        """Performs a generic POST request for specified params, returning the
        response.

        Parameters
        ----------
        url : str
            Url string to be requested.
        files: dict
            Dictionary of file name to file-like objects. Used by _requests
        check_for_errors: bool
            Whether to raise an error (or not)

        Returns
        -------
            Deserialized request output.

        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = {k: v for k, v in kwargs.items() if k not in referenced}
        return self._request(
            url,
            params=params,
            files=files,
            method="POST",
            check_for_errors=check_for_errors,
        )

    def put(
        self, url: str, check_for_errors: bool = True, **kwargs: Any
    ) -> Any:
        """Performs a generic PUT request for specified params, returning the
        response.

        Parameters
        ----------
        url : str
            String representing url to access.
        check_for_errors: bool
            Whether to raise an error (or not)

        Returns
        -------
        Replaces current online content with new content.

        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = {k: v for k, v in kwargs.items() if k not in referenced}
        return self._request(
            url, params=params, method="PUT", check_for_errors=check_for_errors
        )

    def delete(
        self, url: str, check_for_errors: bool = True, **kwargs: Any
    ) -> Any:
        """Performs a generic DELETE request for specified params, returning
        the response.

        Parameters
        ----------
        url : str
            String representing url to access.
        check_for_errors: bool
            Whether to raise an error (or not)

        Returns
        -------
        Deletes specified current online content.
        """
        referenced = self._extract_referenced_vars(url)
        url = url.format(**kwargs)
        params = {k: v for k, v in kwargs.items() if k not in referenced}
        return self._request(
            url,
            params=params,
            method="DELETE",
            check_for_errors=check_for_errors,
        )
