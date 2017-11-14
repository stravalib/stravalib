from stravalib.tests import TestBase
from stravalib.util.limiter import get_rates_from_response_headers

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
