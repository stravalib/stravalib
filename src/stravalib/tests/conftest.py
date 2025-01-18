import warnings

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
def apiv3_instance():
    """Fixture to create an ApiV3 instance for testing."""

    return ApiV3(access_token="dummy_access_token")
