import arrow
import pytest

from stravalib.tests import TestBase
from stravalib.util.limiter import (
    SleepingRateLimitRule,
    get_rates_from_response_headers,
    get_seconds_until_next_day,
    get_seconds_until_next_quarter,
)

# Example responses for Strava 3rd party apps that are not enrolled in the
# 2023 developer program:

fake_response_unenrolled = {
    "Status": "404 Not Found",
    "X-Request-Id": "a1a4a4973962ffa7e0f18d7c485fe741",
    "Content-Encoding": "gzip",
    "Content-Length": "104",
    "Connection": "keep-alive",
    "X-RateLimit-Limit": "600,30000",
    "X-UA-Compatible": "IE=Edge,chrome=1",
    "Cache-Control": "no-cache, private",
    "Date": "Tue, 14 Nov 2017 11:29:15 GMT",
    "X-FRAME-OPTIONS": "DENY",
    "Content-Type": "application/json; charset=UTF-8",
    "X-RateLimit-Usage": "4,67",
}

fake_response_unenrolled_limit_exceeded = fake_response_unenrolled | {
    "X-RateLimit-Usage": "601, 602"
}

fake_response_unenrolled_no_rates = {
    "Status": "200 OK",
    "X-Request-Id": "d465159561420f6e0239dc24429a7cf3",
    "Content-Encoding": "gzip",
    "Content-Length": "371",
    "Connection": "keep-alive",
    "X-UA-Compatible": "IE=Edge,chrome=1",
    "Cache-Control": "max-age=0, private, must-revalidate",
    "Date": "Tue, 14 Nov 2017 13:19:31 GMT",
    "X-FRAME-OPTIONS": "DENY",
    "Content-Type": "application/json; charset=UTF-8",
}

# Example responses for Strava 3rd party apps that are enrolled:
fake_reponse_enrolled = fake_response_unenrolled | {
    "X-ReadRateLimit-Usage": "2,32",
    "X-ReadRateLimit-Limit": "300,15000",
}

fake_reponse_enrolled_read_limit_exceeded = fake_reponse_enrolled | {
    "X-ReadRateLimit-Usage": "301,302"
}
fake_reponse_enrolled_overall_limit_exceeded = fake_reponse_enrolled | {
    "X-RateLimit-Usage": "601,602"
}


@pytest.mark.parametrize(
    "headers,request_method,expected_rates",
    # rates = (short_usage,long_usage,short_limit,long_limit)
    (
        (fake_response_unenrolled, "GET", (4, 67, 600, 30000)),
        (fake_response_unenrolled, "POST", (4, 67, 600, 30000)),
        (fake_response_unenrolled_no_rates, "GET", None),
        (fake_response_unenrolled_no_rates, "PUT", None),
        (fake_reponse_enrolled, "GET", (2, 32, 300, 15000)),
        (fake_reponse_enrolled, "PUT", (4, 67, 600, 30000)),
    ),
)
def test_get_rates_from_response_headers(
    headers, request_method, expected_rates
):
    assert (
        get_rates_from_response_headers(headers, request_method)
        == expected_rates
    )


class LimiterTest(TestBase):
    def test_get_seconds_until_next_quarter(self):
        """Should return number of seconds to next quarter of an hour"""
        self.assertEqual(
            59,
            get_seconds_until_next_quarter(
                arrow.get(2017, 11, 1, 17, 14, 0, 0)
            ),
        )
        self.assertEqual(
            59,
            get_seconds_until_next_quarter(
                arrow.get(2017, 11, 1, 17, 59, 0, 0)
            ),
        )
        self.assertEqual(
            0,
            get_seconds_until_next_quarter(
                arrow.get(2017, 11, 1, 17, 59, 59, 999999)
            ),
        )
        self.assertEqual(
            899,
            get_seconds_until_next_quarter(
                arrow.get(2017, 11, 1, 17, 0, 0, 1)
            ),
        )

    def test_get_seconds_until_next_day(self):
        """Should return the number of seconds until next day"""
        self.assertEqual(
            59,
            get_seconds_until_next_day(arrow.get(2017, 11, 1, 23, 59, 0, 0)),
        )
        self.assertEqual(
            86399,
            get_seconds_until_next_day(arrow.get(2017, 11, 1, 0, 0, 0, 0)),
        )


class SleepingRateLimitRuleTest(TestBase):
    def setUp(self):
        self.test_response = fake_response_unenrolled.copy()

    def test_invalid_priority(self):
        """Should raise ValueError in case of invalid priority"""
        with self.assertRaises(ValueError):
            SleepingRateLimitRule(priority="foobar")

    def test_get_wait_time_high_priority(self):
        """Should never sleep/wait after high priority requests"""
        self.assertEqual(
            0, SleepingRateLimitRule()._get_wait_time(42, 42, 60, 3600)
        )

    def test_get_wait_time_medium_priority(self):
        """Should return number of seconds to next short limit divided by number of remaining requests
        for that period"""
        rule = SleepingRateLimitRule(priority="medium", short_limit=11)
        self.assertEqual(1, rule._get_wait_time(1, 1, 10, 1000))
        self.assertEqual(0.5, rule._get_wait_time(1, 1, 5, 1000))

    def test_get_wait_time_low_priority(self):
        """Should return number of seconds to next long limit divided by number of remaining requests
        for that period"""
        rule = SleepingRateLimitRule(priority="low", long_limit=11)
        self.assertEqual(1, rule._get_wait_time(1, 1, 1, 10))
        self.assertEqual(0.5, rule._get_wait_time(1, 1, 1, 5))

    def test_get_wait_time_limit_reached(self):
        """Should wait until end of period when limit is reached, regardless priority"""
        rule = SleepingRateLimitRule(short_limit=10, long_limit=100)
        self.assertEqual(42, rule._get_wait_time(10, 10, 42, 1000))
        self.assertEqual(42, rule._get_wait_time(1234, 10, 42, 1000))
        self.assertEqual(21, rule._get_wait_time(10, 100, 42, 21))
        self.assertEqual(21, rule._get_wait_time(10, 1234, 42, 21))

    def test_invocation_unchanged_limits(self):
        """Should not update limits if these don't change"""
        self.test_response["X-RateLimit-Usage"] = "0, 0"
        self.test_response["X-RateLimit-Limit"] = "10000, 1000000"
        rule = SleepingRateLimitRule()
        self.assertEqual(10000, rule.short_limit)
        self.assertEqual(1000000, rule.long_limit)
        rule(self.test_response)
        self.assertEqual(10000, rule.short_limit)
        self.assertEqual(1000000, rule.long_limit)

    def test_invocation_changed_limits(self):
        """Should update limits in case of changes, depending on limit enforcement"""
        self.test_response["X-RateLimit-Usage"] = "0, 0"
        self.test_response["X-RateLimit-Limit"] = "600, 30000"

        # without limit enforcement (default)
        rule = SleepingRateLimitRule()
        rule(self.test_response)
        self.assertEqual(600, rule.short_limit)
        self.assertEqual(30000, rule.long_limit)

        # with limit enforcement
        rule = SleepingRateLimitRule(force_limits=True)
        rule(self.test_response)
        self.assertEqual(10000, rule.short_limit)
        self.assertEqual(1000000, rule.long_limit)
