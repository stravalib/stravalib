"""A series of unit tests to ensure the refresh token operations
work as expected whether the user has set things up or not.

TODO:

exchange_code_for_token
* make sure that access token and token expires are set properly in the
 - protocol.py:360-370 & 414-419 (how are these different?)

 ## Client.py
 * in client - make sure the access token, refresh value and expires at are all
  set client.py:120-179
* refresh access token: 258
i think these will be integration tests to add to client?
vs unit


"""

import logging
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from stravalib.protocol import ApiV3


@pytest.fixture
def apiv3_instance():
    """Fixture to create an ApiV3 instance for testing."""

    return ApiV3(access_token="dummy_access_token")


def test_token_expired_returns_true(apiv3_instance):
    """Test that _token_expired returns True if the token has expired."""
    apiv3_instance.token_expires = time.time() - 10
    assert apiv3_instance._token_expired()


def test_token_expired_returns_false(apiv3_instance):
    """Test that _token_expired returns False if the token is still valid."""
    apiv3_instance.token_expires = time.time() + 10
    assert not apiv3_instance._token_expired()


# caplog is a builtin fixture in pytest that captures logging outputs
def test_token_expires_is_none_logs_warning(apiv3_instance, caplog):
    """Test that _token_expired logs a warning if token_expires is None."""
    apiv3_instance.token_expires = None

    with caplog.at_level(logging.WARNING):
        assert not apiv3_instance._token_expired()
        assert (
            "Please make sure you've set client.token_expires" in caplog.text
        )


##### Test refresh_expired_token #####


@pytest.mark.parametrize(
    "token_expired, expected_call", [(True, 1), (False, 0)]
)
def test_refresh_expired_token_called(
    apiv3_instance, token_expired, expected_call
):
    """Test that refresh_access_token method is called when token is expired
    and not called when valid.
    """

    apiv3_instance.refresh_token = "dummy_refresh_token"

    with patch.dict(
        os.environ,
        {"STRAVA_CLIENT_ID": "12345", "STRAVA_CLIENT_SECRET": "secret"},
    ):
        apiv3_instance._token_expired = MagicMock(return_value=token_expired)
        apiv3_instance.refresh_access_token = MagicMock()

        apiv3_instance.refresh_expired_token()

        # Check how many times refresh_access_token was called
        assert apiv3_instance.refresh_access_token.call_count == expected_call
        if token_expired:
            apiv3_instance.refresh_access_token.assert_called_once_with(
                client_id=12345,
                client_secret="secret",
                refresh_token="dummy_refresh_token",
            )


def test_refresh_expired_token_client_id_bad(apiv3_instance, caplog):
    """Test that we fail gracefully and log an error if CLIENT_ID has
    characters in it (should be all ints).
    """

    apiv3_instance.refresh_token = "dummy_refresh_token"

    with patch.dict(
        os.environ,
        {"STRAVA_CLIENT_ID": "a12345", "STRAVA_CLIENT_SECRET": "secret"},
    ):
        apiv3_instance._token_expired = MagicMock(return_value=True)
        apiv3_instance.refresh_access_token = MagicMock()

        # Check how many times refresh_access_token was called
        with caplog.at_level(logging.WARNING):
            # Should return None if client_id is bad & log an error.
            assert not apiv3_instance.refresh_expired_token()
            assert "STRAVA_CLIENT_ID must be a valid integer" in caplog.text


def test_refresh_access_token_client_id_valid(apiv3_instance):
    """Test that a valid string `client_id` is converted to an int and works correctly."""
    apiv3_instance.refresh_token = "dummy_refresh_token"

    with patch.dict(
        os.environ,
        {"STRAVA_CLIENT_ID": "67890", "STRAVA_CLIENT_SECRET": "secret"},
    ):
        apiv3_instance._token_expired = MagicMock(return_value=True)
        apiv3_instance.refresh_access_token = MagicMock()

        apiv3_instance.refresh_expired_token()

        apiv3_instance.refresh_access_token.assert_called_once_with(
            client_id=67890,
            client_secret="secret",
            refresh_token="dummy_refresh_token",
        )


def test_missing_client_id_and_secret_logs_warning(apiv3_instance, caplog):
    """Test that a warning is logged if `STRAVA_CLIENT_ID` and
    `STRAVA_CLIENT_SECRET` are missing.
    """

    apiv3_instance.refresh_token = "dummy_refresh_token"

    # No environment variables set
    with patch.dict(os.environ, {}, clear=True):
        with caplog.at_level(logging.WARNING):
            apiv3_instance.refresh_expired_token()

            assert (
                "STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET not found"
                in caplog.text
            )
