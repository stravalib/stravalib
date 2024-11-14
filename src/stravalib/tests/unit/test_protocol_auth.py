from unittest.mock import patch

import pytest

from stravalib.protocol import ApiV3


@pytest.fixture
def mock_token_exchange_response():
    """A fixture that mocks a token exchange response that includes
    the athlete info"""
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "expires_at": 1234567890,
        "athlete": {
            "id": 12345,
            "username": "mock_athlete",
            "firstname": "Mock",
            "lastname": "Athlete",
        },
    }


@pytest.fixture
def mock_token_refresh_response():
    """A fixture that mocks the response for a refreshed token."""
    return {
        "access_token": "new_mock_access_token",
        "refresh_token": "new_mock_refresh_token",
        "expires_at": 9876543210,
    }


@patch("stravalib.protocol.ApiV3._request")
def test_exchange_code_for_token_athlete(
    mock_request, mock_token_exchange_response
):
    # with patch("stravalib.protocol.ApiV3._request") as mock_request:
    # Set _request to return the raw dictionary
    api_instance = ApiV3()
    mock_request.return_value = mock_token_exchange_response

    result = api_instance.exchange_code_for_token(
        client_id=123,
        client_secret="secret",
        code="auth_code",
        return_athlete=True,
    )

    # If athlete info is requested, return should be a tuple of 2 items
    assert len(result) == 2


@patch("stravalib.protocol.ApiV3._request")
def test_exchange_code_for_token_no_athlete(
    mock_request, mock_token_exchange_response
):
    api_instance = ApiV3()
    mock_request.return_value = mock_token_exchange_response

    result = api_instance.exchange_code_for_token(
        client_id=123,
        client_secret="secret",
        code="auth_code",
    )

    # If athlete info is requested, return should be a dict of 3 items
    assert len(result) == 3
    assert result["access_token"] == "mock_access_token"
