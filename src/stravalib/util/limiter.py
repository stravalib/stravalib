"""Utilities
==============
Rate limiter classes.

These are basically callables that when called register that a request was
issued. Depending on how they are configured that may cause a pause or
exception if a rate limit has been exceeded. It is up to the calling
code to ensure that these callables are invoked with every (successful?) call
to the backend API.

TODO: There is probably a better way to hook these into the requests library
directly

From the Strava docs:
  Strava API usage is limited on a per-application basis using a short term,
  15 minute, limit and a long term, daily, limit. The default rate limit allows
  600 requests every 15 minutes, with up to 30,000 requests per day.

  This limit allows applications to make 40 requests per minute for about
  half the day.
"""
from __future__ import annotations

import logging
import time
from logging import Logger
from typing import Callable, Literal, NamedTuple

import arrow

from stravalib.protocol import RequestMethod


class RequestRate(NamedTuple):
    """Tuple containing request usage and usage limit."""

    short_usage: int
    """15-minute usage"""

    long_usage: int
    """Daily usage"""

    short_limit: int
    """15-minutes limit"""

    long_limit: int
    """Daily limit"""


def get_rates_from_response_headers(
    headers: dict[str, str], method: RequestMethod
) -> RequestRate | None:
    """Returns a namedtuple with values for short - and long usage and limit
    rates found in provided HTTP response headers

    Parameters
    ----------
    headers : dict
        HTTP response headers
    method : RequestMethod
        HTTP request method corresponding to the provided response headers

    Returns
    -------
    Optional[RequestRate]
        namedtuple with request rates or None if no rate-limit headers
        present in response.
    """
    usage_rates = limit_rates = []

    if "X-ReadRateLimit-Usage" in headers and method == "GET":
        usage_rates = [
            int(v) for v in headers["X-ReadRateLimit-Usage"].split(",")
        ]
        limit_rates = [
            int(v) for v in headers["X-ReadRateLimit-Limit"].split(",")
        ]
    elif "X-RateLimit-Usage" in headers:
        usage_rates = [int(v) for v in headers["X-RateLimit-Usage"].split(",")]
        limit_rates = [int(v) for v in headers["X-RateLimit-Limit"].split(",")]

    if usage_rates and limit_rates:
        return RequestRate(
            short_usage=usage_rates[0],
            long_usage=usage_rates[1],
            short_limit=limit_rates[0],
            long_limit=limit_rates[1],
        )
    else:
        return None


def get_seconds_until_next_quarter(
    now: arrow.arrow.Arrow | None = None,
) -> int:
    """Returns the number of seconds until the next quarter of an hour. This is
    the short-term rate limit used by Strava.

    Parameters
    ----------
    now : arrow.arrow.Arrow
        A (utc) timestamp

    Returns
    -------
    int
        The number of seconds until the next quarter, as int
    """
    if now is None:
        now = arrow.utcnow()
    return (
        899
        - (
            now
            - now.replace(
                minute=(now.minute // 15) * 15, second=0, microsecond=0
            )
        ).seconds
    )


def get_seconds_until_next_day(now: arrow.arrow.Arrow | None = None) -> int:
    """Returns the number of seconds until the next day (utc midnight). This is
    the long-term rate limit used by Strava.

    Parameters
    ----------
    now : arrow.arrow.Arrow
        A (utc) timestamp

    Returns
    -------
    Int
        The number of seconds until next day, as int
    """
    if now is None:
        now = arrow.utcnow()
    return (now.ceil("day") - now).seconds


class SleepingRateLimitRule:
    """A rate limit rule that can be prioritized and can dynamically adapt its
    limits based on API responses. Given its priority, it will enforce a
    variable "cool-down" period after each response. When rate limits are
    reached within their period, this limiter will wait until the end of that
    period. It will NOT raise any kind of exception in this case.
    """

    def __init__(
        self,
        priority: Literal["low", "medium", "high"] = "high",
    ) -> None:
        """
        Constructs a new SleepingRateLimitRule.

        Parameters
        ----------
        priority : Literal["low", "medium", "high"]
            The priority for this rule. When 'low', the cool-down period
            after each request will be such that the long-term limits will
            not be exceeded. When 'medium', the cool-down period will be such
            that the short-term limits will not be exceeded.  When 'high',
            there will be no cool-down period.
        """
        if priority not in ["low", "medium", "high"]:
            raise ValueError(
                f'Invalid priority "{priority}", expecting one of "low", "medium" or "high"'
            )

        self.log = logging.getLogger(
            "{0.__module__}.{0.__name__}".format(self.__class__)
        )
        self.priority = priority

    def _get_wait_time(
        self,
        rates: RequestRate,
        seconds_until_short_limit: int,
        seconds_until_long_limit: int,
    ) -> float:
        """Calculate how much time user has until they can make another
        request"""

        if rates.long_usage >= rates.long_limit:
            self.log.warning("Long term API rate limit exceeded")
            return seconds_until_long_limit
        elif rates.short_usage >= rates.short_limit:
            self.log.warning("Short term API rate limit exceeded")
            return seconds_until_short_limit

        if self.priority == "high":
            return 0
        elif self.priority == "medium":
            return seconds_until_short_limit / (
                rates.short_limit - rates.short_usage
            )
        elif self.priority == "low":
            return seconds_until_long_limit / (
                rates.long_limit - rates.long_usage
            )

    def __call__(
        self, response_headers: dict[str, str], method: RequestMethod
    ) -> None:
        """Determines wait time until a call can be made again"""
        rates = get_rates_from_response_headers(response_headers, method)
        self.log.debug(f"Throttling based on rates: {rates}")

        if rates:
            time.sleep(
                self._get_wait_time(
                    rates,
                    get_seconds_until_next_quarter(),
                    get_seconds_until_next_day(),
                )
            )
        else:
            self.log.warning("No rates present in response headers")


class RateLimiter:
    def __init__(self) -> None:
        self.log: Logger = logging.getLogger(
            "{0.__module__}.{0.__name__}".format(self.__class__)
        )
        self.rules: list[Callable[[dict[str, str], RequestMethod], None]] = []

    def __call__(self, args: dict[str, str], method: RequestMethod) -> None:
        """Register another request is being issued."""
        for r in self.rules:
            r(args, method)


class DefaultRateLimiter(RateLimiter):
    """Implements something similar to the default rate limit for Strava apps.

    See https://developers.strava.com/docs/rate-limits/ and
    https://communityhub.strava.com/t5/developer-knowledge-base/our-developer-program/ta-p/8849.

    Rate limits are enforced by throttling requests based on their method and
    client/app-specific limits imposed by Strava.
    """

    def __init__(
        self, priority: Literal["low", "medium", "high"] = "high"
    ) -> None:
        """
        Initializes the rate limiter based on the given priority.

        Parameters
        ----------
        priority : Literal["low", "medium", "high"]
            The priority given to the requests. Default is "high"
            (i.e. no throttling).
        """

        super().__init__()

        self.rules.append(SleepingRateLimitRule(priority=priority))

        # TODO: This should be added to our documentation
