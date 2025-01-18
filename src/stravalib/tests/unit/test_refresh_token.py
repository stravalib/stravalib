"""A series of unit tests to ensure the refresh token operations
work as expected whether the user has set things up or not.



"""

import logging
import os
import time
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.parametrize(
    "token_expires, expected_result",
    [
        (time.time() - 10, True),  # Token expired
        (time.time() + 10, False),
    ],
)
def test_token_expired(apiv3_instance, token_expires, expected_result):
    """Test the _token_expired method for both expired and valid tokens."""

    apiv3_instance.token_expires = token_expires
    assert apiv3_instance._token_expired() == expected_result


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
    """Test that `refresh_access_token` method is called when token is expired
    and not called when valid.
    """

    apiv3_instance.refresh_token = "dummy_refresh_token"

    # Patch os get envt variables and populate envt vals
    with patch.dict(
        os.environ,
        {"STRAVA_CLIENT_ID": "12345", "STRAVA_CLIENT_SECRET": "secret"},
    ):
        apiv3_instance._token_expired = MagicMock(return_value=token_expired)
        apiv3_instance.refresh_access_token = MagicMock()

        apiv3_instance.refresh_expired_token(
            client_id=12345, client_secret="123secret"
        )

        assert apiv3_instance.refresh_access_token.call_count == expected_call
        if token_expired:
            apiv3_instance.refresh_access_token.assert_called_once_with(
                client_id=12345,
                client_secret="123secret",
                refresh_token="dummy_refresh_token",
            )


def test_refresh_expired_token_no_refresh(apiv3_instance, caplog):
    """Test that we fail gracefully and log an error if the refresh
    token isn't populated.
    """

    apiv3_instance.refresh_token = None

    apiv3_instance._token_expired = MagicMock(return_value=True)
    apiv3_instance.refresh_access_token = MagicMock()
    apiv3_instance.refresh_expired_token(client_id=12345, client_secret="foo")

    with caplog.at_level(logging.WARNING):
        # Should log an error if refresh is missing.
        assert "Please make sure you've set up your environment" in caplog.text


def test_refresh_access_token_client_id_valid(apiv3_instance):
    """Test that a valid string `client_id` is converted to an int and works correctly."""
    apiv3_instance.refresh_token = "dummy_refresh_token"

    apiv3_instance._token_expired = MagicMock(return_value=True)
    apiv3_instance.refresh_access_token = MagicMock()

    apiv3_instance.refresh_expired_token(
        client_id=123456, client_secret="yoursecret"
    )

    # In this case refresh_access_token should be called
    apiv3_instance.refresh_access_token.assert_called_once_with(
        client_id=123456,
        client_secret="yoursecret",
        refresh_token="dummy_refresh_token",
    )
