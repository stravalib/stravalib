import arrow

from stravalib.tests import TestBase
from stravalib.util.limiter import get_rates_from_response_headers, XRateLimitRule, get_seconds_until_next_quarter, \
    get_seconds_until_next_day

test_response = {'Status': '404 Not Found', 'X-Request-Id': 'a1a4a4973962ffa7e0f18d7c485fe741',
                 'Content-Encoding': 'gzip', 'Content-Length': '104', 'Connection': 'keep-alive',
                 'X-RateLimit-Limit': '600,30000', 'X-UA-Compatible': 'IE=Edge,chrome=1',
                 'Cache-Control': 'no-cache, private', 'Date': 'Tue, 14 Nov 2017 11:29:15 GMT',
                 'X-FRAME-OPTIONS': 'DENY', 'Content-Type': 'application/json; charset=UTF-8',
                 'X-RateLimit-Usage': '4,67'}

test_response_no_rates = {'Status': '200 OK', 'X-Request-Id': 'd465159561420f6e0239dc24429a7cf3',
                          'Content-Encoding': 'gzip', 'Content-Length': '371', 'Connection': 'keep-alive',
                          'X-UA-Compatible': 'IE=Edge,chrome=1', 'Cache-Control': 'max-age=0, private, must-revalidate',
                          'Date': 'Tue, 14 Nov 2017 13:19:31 GMT', 'X-FRAME-OPTIONS': 'DENY',
                          'Content-Type': 'application/json; charset=UTF-8'}


class LimiterTest(TestBase):
    def test_get_rates_from_response_headers(self):
        """Should return namedtuple with rates"""
        request_rates = get_rates_from_response_headers(test_response)
        self.assertEqual(600, request_rates.short_limit)
        self.assertEqual(30000, request_rates.long_limit)
        self.assertEqual(4, request_rates.short_usage)
        self.assertEqual(67, request_rates.long_usage)

    def test_get_rates_from_response_headers_missing_rates(self):
        """Should return namedtuple with None values for rates in case of missing rates in headers"""
        request_rates = get_rates_from_response_headers(test_response_no_rates)
        self.assertIsNone(request_rates.short_limit)
        self.assertIsNone(request_rates.long_limit)
        self.assertIsNone(request_rates.short_usage)
        self.assertIsNone(request_rates.long_usage)

    def test_get_seconds_until_next_quarter(self):
        """Should return number of seconds to next quarter of an hour"""
        self.assertEqual(59, get_seconds_until_next_quarter(arrow.get(2017, 11, 1, 17, 14, 0, 0)))
        self.assertEqual(59, get_seconds_until_next_quarter(arrow.get(2017, 11, 1, 17, 59, 0, 0)))
        self.assertEqual(0, get_seconds_until_next_quarter(arrow.get(2017, 11, 1, 17, 59, 59, 999999)))
        self.assertEqual(899, get_seconds_until_next_quarter(arrow.get(2017, 11, 1, 17, 0, 0, 1)))

    def test_get_seconds_until_next_day(self):
        """Should return the number of seconds until next day"""
        self.assertEqual(59, get_seconds_until_next_day(arrow.get(2017, 11, 1, 23, 59, 0, 0)))
        self.assertEqual(86399, get_seconds_until_next_day(arrow.get(2017, 11, 1, 0, 0, 0, 0)))


class XRateLimitRuleTest(TestBase):
    def test_rule_normal_response(self):
        rule = XRateLimitRule({'short': {'usage': 0, 'limit': 600, 'time': (60*15), 'lastExceeded': None},
                               'long': {'usage': 0, 'limit': 30000, 'time': (60*60*24), 'lastExceeded': None}})
        rule(test_response)
        self.assertEqual(4, rule.rate_limits['short']['usage'])
        self.assertEqual(67, rule.rate_limits['long']['usage'])

    def test_rule_missing_rates_response(self):
        rule = XRateLimitRule({'short': {'usage': 0, 'limit': 600, 'time': (60*15), 'lastExceeded': None},
                               'long': {'usage': 0, 'limit': 30000, 'time': (60*60*24), 'lastExceeded': None}})
        rule(test_response_no_rates)
        self.assertEqual(0, rule.rate_limits['short']['usage'])
        self.assertEqual(0, rule.rate_limits['long']['usage'])
