import logging
import time

import pytest


@pytest.fixture
def api_v3instance():
    """Fixture to create an ApiV3 instance for testing."""
    from stravalib.protocol import ApiV3

    return ApiV3(access_token="dummy_access_token")


def test_token_expired_returns_true(api_v3instance):
    """Test that _token_expired returns True if the token has expired."""
    api_v3instance.token_expires = time.time() - 10
    assert api_v3instance._token_expired()


def test_token_expired_returns_false(api_v3instance):
    """Test that _token_expired returns False if the token is still valid."""
    api_v3instance.token_expires = time.time() + 10
    assert not api_v3instance._token_expired()


def test_token_expires_is_none_logs_warning(api_v3instance, caplog):
    """Test that _token_expired logs a warning if token_expires is None."""
    api_v3instance.token_expires = None

    with caplog.at_level(logging.WARNING):
        assert not api_v3instance._token_expired()
        assert (
            "Please make sure you've set client.token_expires" in caplog.text
        )
