import logging
import os
import time
from unittest.mock import MagicMock, patch

import pytest

import stravalib

###### _request method responsible for API call ######


@pytest.mark.parametrize(
    "url, should_call_refresh",
    [
        ("/oauth/token", False),  # Skips refreshing for /oauth/token
        (
            "/api/some_other_endpoint",
            True,
        ),
    ],
)
def test_request_skips_refresh_for_oauth_token(
    apiv3_instance, url, should_call_refresh
):
    """Test that _request skips refresh_expired_token when provided with
    a url that includes /oauth/token to avoid recursion"""

    apiv3_instance.refresh_expired_token = MagicMock()
    apiv3_instance.resolve_url = MagicMock(return_value="/oauth/token")
    apiv3_instance.rsession.get = MagicMock(
        return_value=MagicMock(status_code=204, headers={})
    )

    apiv3_instance._request(url)

    if should_call_refresh:
        apiv3_instance.refresh_expired_token.assert_called_once()
    else:
        apiv3_instance.refresh_expired_token.assert_not_called()


###### _check_credentials helper ######


class TestCheckCredentials:
    """Tests for the `_check_credentials` app setup helper method."""

    @pytest.fixture(autouse=True)
    def setup(self, apiv3_instance):
        """Shared setup for all tests in this class."""
        self.apiv3 = apiv3_instance

    def test_check_credentials_success(self):
        """Ensure that if credentials exist in the environment and client_id can
        be cast to a valid int that the method populates self. client ID and
        secret as expected."""

        self.apiv3._check_credentials()
        assert isinstance(self.apiv3.client_id, int)

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
    def test_check_credentials_missing_vals(
        self, caplog, env_vars, expected_log_message
    ):
        """Test that if parts of all of the credentials are missing, the method
        logs the correct warning and returns `None`.

        Here we overwriting environment variables to see if _check_credentials
        works as expected with various user envt edge cases."""

        with patch.dict(os.environ, env_vars, clear=True):
            with caplog.at_level(logging.WARNING):
                credentials = self.apiv3._check_credentials()
                assert expected_log_message in caplog.text
                assert credentials is None


###### refresh_expired_token method ######


@patch.object(stravalib.protocol.ApiV3, "refresh_access_token")
@patch.object(stravalib.protocol.ApiV3, "_token_expired", return_value=True)
def test_refresh_expired_token_calls_refresh_access_token(
    token_expired_mock,
    refresh_access_token_mock,
    apiv3_instance,
):
    """Test that `refresh_access_token` is called when the token is expired and
    the refresh token exists.

    This tests mocks refresh_access_token so it doesn't run, but checks to
    make sure it's called as it should be if all values are present.
    """

    out = apiv3_instance.refresh_expired_token()
    refresh_access_token_mock.assert_called_once()
    # Should return none
    assert not out


###### _token_expired helper ######


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


class TestRefreshExpiredToken:
    """Tests for the `refresh_expired_token` method."""

    @pytest.fixture(autouse=True)
    def setup(self, apiv3_instance):
        """
        Shared setup for all tests in this class.
        Mocks `_token_expired` and `refresh_access_token` and sets up
        the environment variables.
        """
        self.apiv3 = apiv3_instance
        self.apiv3._token_expired = MagicMock()
        self.apiv3.refresh_access_token = MagicMock()

    @pytest.mark.parametrize(
        "token_expired, expected_call", [(True, 1), (False, 0)]
    )
    def test_refresh_expired_token_refresh_called(
        self, token_expired, expected_call
    ):
        """Test that `refresh_access_token` method is called when token is expired
        and not called when valid.
        """
        self.apiv3._token_expired.return_value = token_expired
        self.apiv3.refresh_expired_token()

        assert self.apiv3.refresh_access_token.call_count == expected_call

    def test_refresh_expired_token_no_refresh(self, caplog):
        """Test that we fail gracefully and log an error if the refresh
        token isn't populated.
        """

        self.apiv3.refresh_token = None
        self.apiv3._token_expired.return_value = True

        with caplog.at_level(logging.WARNING):
            self.apiv3.refresh_expired_token()
            assert (
                "Please set client.refresh_token if you want to use"
                in caplog.text
            )
