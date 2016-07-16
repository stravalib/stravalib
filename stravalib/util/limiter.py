"""
Rate limiter classes.

These are basically callables that when called register that a request was
issued.  Depending on how they are configured that may cause a pause or exception
if a rate limit has been exceeded.  Obviously it is up to the calling code to ensure
that these callables are invoked with every (successful?) call to the backend
API.  (There is probably a better way to hook these into the requests library
directly ... TBD.)

From the Strava docs:
  Strava API usage is limited on a per-application basis using a short term,
  15 minute, limit and a long term, daily, limit. The default rate limit allows
  600 requests every 15 minutes, with up to 30,000 requests per day.

  This limit allows applications to make 40 requests per minute for about
  half the day.
"""
from __future__ import division, absolute_import, print_function, unicode_literals
import time
import logging
import collections
from datetime import datetime, timedelta

from stravalib import exc


def total_seconds(td):
    """Alternative to datetime.timedelta.total_seconds
    total_seconds() only available since Python 2.7
    https://docs.python.org/2/library/datetime.html#datetime.timedelta.total_seconds
    """
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


class RateLimiter(object):

    def __init__(self):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.rules = []

    def __call__(self):
        """
        Register another request is being issued.
        """
        for r in self.rules:
            r()


class RateLimitRule(object):

    def __init__(self, requests, seconds, raise_exc=False):
        """
        :param requests: Number of requests for limit.
        :param seconds: The number of seconds for that number of requests (may be float)
        :param raise_exc: Whether to raise an exception when limit is reached (as opposed to pausing)
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.timeframe = timedelta(seconds=seconds)
        self.requests = requests
        self.tab = collections.deque(maxlen=self.requests)
        self.raise_exc = raise_exc

    def __call__(self):
        """
        Register another request is being issued.

        Depending on configuration of the rule will pause if rate limit has
        been reached, or raise exception, etc.
        """
        # First check if the deque is full; that indicates that we'd better check whether
        # we need to pause.
        if len(self.tab) == self.requests:
            # Grab the oldest (leftmost) timestamp and check to see if it is greater than 1 second
            delta = datetime.now() - self.tab[0]
            if delta < self.timeframe:  # Has it been less than configured timeframe since oldest request?
                if self.raise_exc:
                    raise exc.RateLimitExceeded("Rate limit exceeded (can try again in {0})".format(self.timeframe - delta))
                else:
                    # Wait the difference between timeframe and the oldest request.
                    td = self.timeframe - delta
                    sleeptime = hasattr(td, 'total_seconds') and td.total_seconds() or total_seconds(td)
                    self.log.debug("Rate limit triggered; sleeping for {0}".format(sleeptime))
                    time.sleep(sleeptime)
        self.tab.append(datetime.now())


class DefaultRateLimiter(RateLimiter):
    """
    Implements something similar to the default rate limit for Strava apps.

    To do this correctly we would actually need to change our logic to reset
    the limit at midnight, etc.  Will make this more complex in the future.

    Strava API usage is limited on a per-application basis using a short term,
    15 minute, limit and a long term, daily, limit. The default rate limit allows
    600 requests every 15 minutes, with up to 30,000 requests per day.
    """

    def __init__(self):
        super(DefaultRateLimiter, self).__init__()
        self.rules.append(RateLimitRule(requests=40, seconds=60, raise_exc=False))
        self.rules.append(RateLimitRule(requests=30000, seconds=(3600 * 24), raise_exc=True))
