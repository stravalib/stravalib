"""
Exceptions & Error Handling
============================
Exceptions and error handling for stravalib.
These are classes designed to capture and handle various errors encountered when interacting with the Strava API.
"""
from __future__ import annotations

import logging
import warnings

import requests.exceptions


class AuthError(RuntimeError):
    pass


class LoginFailed(AuthError):
    pass


class LoginRequired(AuthError):
    """
    Login is required to perform specified action.
    """


class UnboundEntity(RuntimeError):
    """
    Exception used to indicate that a model Entity is not bound to client instances.
    """


class Fault(requests.exceptions.HTTPError):
    """
    Container for exceptions raised by the remote server.
    """


class ObjectNotFound(Fault):
    """
    When we get a 404 back from an API call.
    """


class AccessUnauthorized(Fault):
    """
    When we get a 401 back from an API call.
    """


class RateLimitExceeded(RuntimeError):
    """
    Exception raised when the client rate limit has been exceeded.

    https://developers.strava.com/docs/rate-limits/
    """

    def __init__(
        self,
        msg: str,
        timeout: float | None = None,
        limit: float | None = None,
    ) -> None:
        super().__init__()
        self.limit = limit
        self.timeout = timeout


class RateLimitTimeout(RateLimitExceeded):
    """
    Exception raised when the client rate limit has been exceeded
    and the time to clear the limit (timeout) has not yet been reached

    https://developers.strava.com/docs/rate-limits/
    """


class ActivityUploadFailed(RuntimeError):
    pass


class ErrorProcessingActivity(ActivityUploadFailed):
    pass


class CreatedActivityDeleted(ActivityUploadFailed):
    pass


class ActivityPhotoUploadFailed(RuntimeError):
    pass


class ActivityPhotoUploadNotSupported(ActivityPhotoUploadFailed):
    pass


class TimeoutExceeded(RuntimeError):
    pass


class NotAuthenticatedAthlete(AuthError):
    """
    Exception when trying to access data which requires an authenticated athlete
    """

    pass


# Warnings configuration and helper functions
warnings.simplefilter("default")
logging.captureWarnings(True)


def warn_method_deprecation(
    klass: type,
    method_name: str,
    alternative: str,
    alt_url: str | None = None,
) -> None:
    alt_support_msg = (
        f" See {alt_url} for more information." if alt_url else ""
    )
    warnings.warn(
        f'The method "{method_name}" of class "{klass}" is deprecated and will be '
        f'removed in the future. Instead, you can use "{alternative}".{alt_support_msg}',
        DeprecationWarning,
        stacklevel=3,
    )


def warn_param_unsupported(param_name: str) -> None:
    warnings.warn(
        f'The "{param_name}" parameter is unsupported by the Strava API. It has no '
        "effect and may lead to errors in the future.",
        DeprecationWarning,
        stacklevel=3,
    )


def warn_param_deprecation(
    param_name: str, alternative: str, alt_url: str | None = None
) -> None:
    alt_support_msg = (
        f" See {alt_url} for more information." if alt_url else ""
    )
    warnings.warn(
        f'The "{param_name}" parameter is deprecated and will be removed'
        f'in the future. Instead, you can use "{alternative}".{alt_support_msg}',
        DeprecationWarning,
        stacklevel=3,
    )


def warn_param_unofficial(param_name: str) -> None:
    warnings.warn(
        f'The "{param_name}" parameter is undocumented in the Strava API. Its use '
        "may lead to unexpected behavior or errors in the future.",
        FutureWarning,
        stacklevel=3,
    )


def warn_attribute_unofficial(attr_name: str) -> None:
    warnings.warn(
        f'The "{attr_name}" parameter is undocumented in the Strava API. Its use '
        "may lead to unexpected behavior or errors in the future.",
        FutureWarning,
        stacklevel=3,
    )


def warn_method_unofficial(method_name: str) -> None:
    warnings.warn(
        f'The "{method_name}" method is undocumented in the Strava API. Its use '
        "may lead to unexpected behavior or errors in the future.",
        FutureWarning,
        stacklevel=3,
    )


def warn_units_deprecated() -> None:
    warnings.warn(
        "You are using a Quantity object or attributes from the units library, which is "
        "deprecated. Support for these types will be removed in the future. Instead, "
        "please use Quantity objects from the Pint package (https://pint.readthedocs.io).",
        DeprecationWarning,
        stacklevel=3,
    )
