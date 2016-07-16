from __future__ import division, absolute_import, print_function, unicode_literals


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


class Fault(RuntimeError):
    """
    Container for exceptions raised by the remote server.
    """


class RateLimitExceeded(RuntimeError):
    """
    Exception raised when the client rate limit has been exceeded.

    http://strava.github.io/api/#access
    """


class ActivityUploadFailed(RuntimeError):
    pass


class ErrorProcessingActivity(ActivityUploadFailed):
    pass


class CreatedActivityDeleted(ActivityUploadFailed):
    pass


class TimeoutExceeded(RuntimeError):
    pass


class NotAuthenticatedAthlete(AuthError):
    """
    Exception when trying to access data which requires an authenticated athlete
    """
    pass
