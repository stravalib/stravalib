import os
import warnings
from unittest.mock import patch

import pytest

from stravalib import Client
from stravalib.protocol import ApiV3
from stravalib.tests.integration.strava_api_stub import StravaAPIMock

warnings.simplefilter("always")


@pytest.fixture
def mock_strava_api():
    with StravaAPIMock() as api_mock:
        api_mock.add_passthru("https://developers.strava.com/swagger")
        yield api_mock


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def mock_strava_env():
    """Fixture that mocks Strava environment variables."""
    with patch.dict(
        os.environ,
        {"STRAVA_CLIENT_ID": "12345", "STRAVA_CLIENT_SECRET": "123ghp234"},
        clear=True,  # Ensures other environment variables are not leaked
    ):
        yield


@pytest.fixture
def apiv3_instance(mock_strava_env):
    """Fixture to create an ApiV3 instance for testing. Takes the
    mock_strava_env which sets up environment variables"""
    mock_strava_env
    return ApiV3(
        access_token="dummy_access_token",
        client_id=123456,
        client_secret="clientfoosecret",
        refresh_token="refresh_value123",
    )
