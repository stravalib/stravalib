import arrow
import pytest

from stravalib.util.limiter import (
    RequestRate,
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


@pytest.mark.parametrize(
    "timestamp,expected_seconds",
    (
        (arrow.get(2017, 11, 1, 17, 14, 0, 0), 59),
        (arrow.get(2017, 11, 1, 17, 59, 0, 0), 59),
        (arrow.get(2017, 11, 1, 17, 59, 59, 999999), 0),
        (arrow.get(2017, 11, 1, 17, 0, 0, 1), 899),
    ),
)
def test_get_seconds_until_next_quarter(timestamp, expected_seconds):
    assert get_seconds_until_next_quarter(timestamp) == expected_seconds


@pytest.mark.parametrize(
    "timestamp,expected_seconds",
    (
        (arrow.get(2017, 11, 1, 23, 59, 0, 0), 59),
        (arrow.get(2017, 11, 1, 0, 0, 0, 0), 86399),
    ),
)
def test_get_seconds_until_next_day(timestamp, expected_seconds):
    assert get_seconds_until_next_day(timestamp) == expected_seconds


def test_create_limiter_invalid_priority():
    """Should raise ValueError in case of invalid priority"""
    with pytest.raises(ValueError):
        SleepingRateLimitRule(priority="foobar")


@pytest.mark.parametrize(
    "priority,rates,seconds_until_short_limit,seconds_until_long_limit,expected_wait_time",
    (
        ("high", RequestRate(42, 42, 100, 100), 60, 3600, 0),
        ("medium", RequestRate(1, 1, 11, 100), 10, 1000, 1),
        ("medium", RequestRate(1, 1, 11, 100), 5, 1000, 0.5),
        ("low", RequestRate(1, 1, 3, 11), 1, 10, 1),
        ("low", RequestRate(1, 1, 3, 11), 1, 5, 0.5),
        ("high", RequestRate(10, 10, 10, 100), 42, 1000, 42),
        ("high", RequestRate(999, 10, 10, 100), 42, 1000, 42),
        ("medium", RequestRate(10, 100, 10, 100), 42, 1000, 1000),
        ("low", RequestRate(10, 1001, 10, 100), 42, 1000, 1000),
    ),
)
def test_get_wait_time(
    priority,
    rates,
    seconds_until_short_limit,
    seconds_until_long_limit,
    expected_wait_time,
):
    rule = SleepingRateLimitRule(priority=priority)
    assert (
        rule._get_wait_time(
            rates, seconds_until_short_limit, seconds_until_long_limit
        )
        == expected_wait_time
    )
