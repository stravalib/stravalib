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
    "status": "404 Not Found",
    "x-request-id": "a1a4a4973962ffa7e0f18d7c485fe741",
    "content-encoding": "gzip",
    "content-length": "104",
    "connection": "keep-alive",
    "x-ratelimit-limit": "600,30000",
    "x-ua-compatible": "IE=Edge,chrome=1",
    "cache-control": "no-cache, private",
    "date": "Tue, 14 Nov 2017 11:29:15 GMT",
    "x-frame-options": "DENY",
    "content-type": "application/json; charset=UTF-8",
    "x-ratelimit-usage": "4,67",
}

fake_response_unenrolled_limit_exceeded = fake_response_unenrolled | {
    "x-ratelimit-usage": "601, 602"
}

fake_response_unenrolled_no_rates = {
    "status": "200 OK",
    "x-request-id": "d465159561420f6e0239dc24429a7cf3",
    "content-encoding": "gzip",
    "content-length": "371",
    "connection": "keep-alive",
    "x-ua-compatible": "IE=Edge,chrome=1",
    "cache-control": "max-age=0, private, must-revalidate",
    "date": "Tue, 14 Nov 2017 13:19:31 GMT",
    "x-frame-options": "DENY",
    "content-type": "application/json; charset=UTF-8",
}

# Example responses for Strava 3rd party apps that are enrolled:
fake_reponse_enrolled = fake_response_unenrolled | {
    "x-readratelimit-usage": "2,32",
    "x-readratelimit-limit": "300,15000",
}

fake_reponse_enrolled_read_limit_exceeded = fake_reponse_enrolled | {
    "x-readratelimit-usage": "301,302"
}
fake_reponse_enrolled_overall_limit_exceeded = fake_reponse_enrolled | {
    "x-ratelimit-usage": "601,602"
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


@pytest.mark.parametrize(
    "priority,rates,seconds_until_short_limit,seconds_until_long_limit,expected_wait_time",
    (
        # Test 1: "low" priority should respect 15-min limit when tighter
        # Bug scenario: end of day with many daily requests left but few 15-min
        (
            "low",
            RequestRate(595, 20000, 600, 30000),
            600,
            300,
            120.0,  # max(600/5, 300/10000) = max(120, 0.03) = 120
        ),
        # Test 2: "medium" priority should respect daily limit when >50% used
        (
            "medium",
            RequestRate(50, 29990, 600, 30000),  # 99.97% of daily used
            600,
            43200,
            4320.0,  # max(600/550, 43200/10) = max(1.09, 4320) = 4320
        ),
        # Test 3: "medium" priority ignores daily limit when <50% used
        (
            "medium",
            RequestRate(550, 5000, 600, 30000),  # 16.67% of daily used
            600,
            43200,
            12.0,  # Only short_wait: 600/50 = 12 (ignores long_wait)
        ),
        # Test 4: "low" priority normal case (daily is tighter)
        (
            "low",
            RequestRate(100, 28000, 600, 30000),
            600,
            43200,
            21.6,  # max(600/500, 43200/2000) = max(1.2, 21.6) = 21.6
        ),
        # Test 5: "high" priority unchanged (no wait when under limits)
        (
            "high",
            RequestRate(595, 29990, 600, 30000),
            600,
            300,
            0,  # Still returns 0
        ),
        # Test 6: Extreme case - very few requests left in both windows
        (
            "low",
            RequestRate(599, 29999, 600, 30000),
            300,
            300,
            300.0,  # max(300/1, 300/1) = 300
        ),
    ),
)
def test_get_wait_time_respects_both_limits(
    priority,
    rates,
    seconds_until_short_limit,
    seconds_until_long_limit,
    expected_wait_time,
):
    """Test that rate limiter respects BOTH short-term and long-term limits.

    This addresses issue #615 where the limiter could violate the 15-minute
    limit when many daily requests remained at day's end.
    """
    rule = SleepingRateLimitRule(priority=priority)
    actual_wait = rule._get_wait_time(
        rates, seconds_until_short_limit, seconds_until_long_limit
    )
    # Use pytest.approx for floating point comparison
    assert actual_wait == pytest.approx(expected_wait_time, rel=1e-2)
