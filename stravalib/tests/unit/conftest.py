import pytest

from unit.strava_api_stub import StravaAPIMock


@pytest.fixture
def mock_strava_api():
    with StravaAPIMock() as api_mock:
        api_mock.add_passthru('https://developers.strava.com/swagger')
        yield api_mock
