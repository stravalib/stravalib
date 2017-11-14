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


RequestRate = collections.namedtuple('RequestRate', ['short_usage', 'long_usage', 'short_limit', 'long_limit'])


def get_rates_from_response_headers(headers):
    try:
        usage_rates = map(int, headers['X-RateLimit-Usage'].split(','))
    except KeyError:
        usage_rates = (None, None)

    try:
        limit_rates = map(int, headers['X-RateLimit-Limit'].split(','))
    except KeyError:
        limit_rates = (None, None)

    return RequestRate(short_usage=usage_rates[0], long_usage=usage_rates[1],
                       short_limit=limit_rates[0], long_limit=limit_rates[1])


class RateLimiter(object):

    def __init__(self):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.rules = []

    def __call__(self, args):
        """
        Register another request is being issued.
        """
        for r in self.rules:
            r(args)


class XRateLimitRule(object):
    
    def __init__(self, limits):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.rate_limits = limits
        self.limit_time_invalid = 0
        # should limit args be validated?

    @property
    def limit_timeout(self):
        return self.limit_time_invalid

    def __call__(self, response_headers):
        self._updateUsage(response_headers)
        
        for limit in self.rate_limits.values():
            self._checkLimitTimeInvalid(limit)
            self._checkLimitRates(limit)
            
    def _updateUsage(self, response_headers):
        rates = get_rates_from_response_headers(response_headers)
        self.rate_limits['short']['usage'] = rates.short_usage or self.rate_limits['short']['usage']
        self.rate_limits['long']['usage'] = rates.long_usage or self.rate_limits['long']['usage']

    def _checkLimitRates(self, limit):
        if (limit['usage'] >= limit['limit']):
            self.log.debug("Rate limit of {0} reached.".format(limit['limit']))
            limit['lastExceeded'] = datetime.now()
            self._raiseRateLimitException(limit['limit'], limit['time'])

    def _checkLimitTimeInvalid(self, limit):
        self.limit_time_invalid = 0
        if (limit['lastExceeded'] is not None):
            delta = (datetime.now() - limit['lastExceeded']).total_seconds()
            if (delta < limit['time']):
                self.limit_time_invalid = limit['time'] - delta
                self.log.debug("Rate limit invalid duration {0} seconds."
                               .format(self.limit_time_invalid))
                self._raiseRateLimitTimeout(self.limit_timeout, limit['limit'])
                
    def _raiseRateLimitException(self, timeout, limitRate):
        raise exc.RateLimitExceeded("Rate limit of {0} exceeded. Try again in {1} seconds."
                                    .format(limitRate, timeout))
    
    def _raiseRateLimitTimeout(self, timeout, limitRate):
        raise exc.RateLimitTimeout("Rate limit of {0} exceeded. Try again in {1} seconds."
                                    .format(limitRate, timeout))        
        
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

    def __call__(self, args):
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
        """
        Strava API usage is limited on a per-application basis using a short term, 
        15 minute, limit and a long term, daily, limit. The default rate limit
        allows 600 requests every 15 minutes, with up to 30,000 requests per day. 
        This limit allows applications to make 40 requests per minute for about half the day.
        """

        super(DefaultRateLimiter, self).__init__()
        
        self.rules.append(XRateLimitRule(
            {'short': {'usageFieldIndex': 0, 'usage': 0,
                         # 60s * 15 = 15 min
                         'limit': 600, 'time': (60*15),
                         'lastExceeded': None},
             'long': {'usageFieldIndex': 1, 'usage': 0,
                        # 60s * 60m * 24 = 1 day
                        'limit': 30000, 'time': (60*60*24),
                        'lastExceeded': None}}))
        
        # XRateLimitRule used instead of timer based RateLimitRule        
        # self.rules.append(RateLimitRule(requests=40, seconds=60, raise_exc=False))
        # self.rules.append(RateLimitRule(requests=30000, seconds=(3600 * 24), raise_exc=True))
