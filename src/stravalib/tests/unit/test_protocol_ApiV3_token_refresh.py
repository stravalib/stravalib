import logging
import os
from unittest.mock import MagicMock, patch

import pytest

import stravalib
from stravalib.protocol import ApiV3




"""Test missing credentials method"""


def test_check_credentials_success(apiv3_instance):
    """Ensure that if credentials exist in the environment and client_id can
    be cast to a valid int that the method returns client ID and secret."""
    with patch.dict(
        os.environ,
        {"STRAVA_CLIENT_ID": "12345", "STRAVA_CLIENT_SECRET": "123ghp234"},
    ):
        credentials = apiv3_instance._check_credentials()
        assert credentials == (12345, "123ghp234")


@pytest.mark.parametrize(
    "env_vars, expected_log_message",
    [
        (
            {
                "STRAVA_CLIENT_ID": "not_an_int",
                "STRAVA_CLIENT_SECRET": "123ghp234",
            },
            "STRAVA_CLIENT_ID must be a valid integer.",
        ),  # Invalid client ID
        (
            {"STRAVA_CLIENT_SECRET": "123ghp234"},
            "Please make sure your STRAVA_CLIENT_ID is set",
        ),  # Missing client ID
        (
            {"STRAVA_CLIENT_ID": "12345"},
            "STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET not found",
        ),  # Missing secret
    ],
)
def test_check_missing_credentials(
    apiv3_instance, caplog, env_vars, expected_log_message
):
    """Test that if parts of all of the credentials are missing, the method
    logs the correct warning."""
    with patch.dict(os.environ, env_vars, clear=True):
        with caplog.at_level(logging.WARNING):
            credentials = apiv3_instance._check_credentials()
            assert expected_log_message in caplog.text
            assert credentials is None


@patch.object(stravalib.protocol.ApiV3, "refresh_access_token")
@patch.object(stravalib.protocol.ApiV3, "_token_expired", return_value=True)
def test_refresh_expired_token_calls_refresh_access_token(
    token_expired_mock, refresh_access_token_mock, apiv3_instance
):
    """Test that `refresh_access_token` is called when the token is expired and
    the refresh token exists.

    This tests mocks refresh_access_token so it doesn't run, but checks to
    make sure it's called as it should be if all values are present.
    """

    apiv3_instance.refresh_token = "refresh_value123"
    out = apiv3_instance.refresh_expired_token(
        client_id=12345, client_secret="secret"
    )
    refresh_access_token_mock.assert_called_once_with(
        client_id=12345,
        client_secret="secret",
        refresh_token="refresh_value123",
    )
    # Should return none
    assert not out


def test_request_skips_refresh_for_oauth_token(apiv3_instance):
    """Test that _request skips refresh_expired_token for /oauth/token URL."""
    # Too many mocks?
    apiv3_instance.refresh_expired_token = MagicMock()
    apiv3_instance._check_credentials = MagicMock(
        return_value=(123456, "client_secret")
    )
    apiv3_instance.resolve_url = MagicMock(return_value="/oauth/token")
    apiv3_instance.rsession.get = MagicMock(
        return_value=MagicMock(status_code=204, headers={})
    )

    # Call _request with a URL containing /oauth/token
    apiv3_instance._request("/oauth/token")

    # refresh_expired_token should NOT be called
    apiv3_instance.refresh_expired_token.assert_not_called()
