"""Unit tests for error handling in `ApiV3._handle_protocol_error`."""

import json
from typing import Any

import pytest
import requests

from stravalib.exc import (
    AccessUnauthorized,
    ApplicationInactive,
    Fault,
    ObjectNotFound,
)

INACTIVE_APP_BODY = {
    "message": "Forbidden",
    "errors": [
        {"resource": "Application", "field": "Status", "code": "Inactive"}
    ],
}


def _response(
    status_code: int,
    body: Any = None,
    raw_body: str | None = None,
    reason: str = "Forbidden",
) -> requests.Response:
    """Builds a `requests.Response` with the given status and body."""
    response = requests.Response()
    response.status_code = status_code
    response.reason = reason
    if raw_body is not None:
        response._content = raw_body.encode()
    elif body is not None:
        response._content = json.dumps(body).encode()
    else:
        response._content = b""
    return response


def test_inactive_application_raises_application_inactive(apiv3_instance):
    with pytest.raises(ApplicationInactive) as error:
        apiv3_instance._handle_protocol_error(
            _response(403, INACTIVE_APP_BODY)
        )

    message = str(error.value)
    assert "inactive" in message
    assert "subscription" in message
    assert "https://www.strava.com/settings/api" in message
    # The original Strava payload stays in the message.
    assert "Inactive" in message
    assert error.value.response.status_code == 403


def test_other_403_raises_plain_fault(apiv3_instance):
    body = {
        "message": "Forbidden",
        "errors": [
            {
                "resource": "Activity",
                "field": "visibility",
                "code": "forbidden",
            }
        ],
    }
    with pytest.raises(Fault) as error:
        apiv3_instance._handle_protocol_error(_response(403, body))

    assert type(error.value) is Fault
    assert "403 Client Error" in str(error.value)


def test_403_without_json_body_raises_plain_fault(apiv3_instance):
    with pytest.raises(Fault) as error:
        apiv3_instance._handle_protocol_error(
            _response(403, raw_body="not json")
        )

    assert type(error.value) is Fault


@pytest.mark.parametrize(
    "errors",
    (
        "Inactive",
        ["Inactive"],
        [{"resource": "Application", "field": "Status"}],
        [{"resource": "Application", "field": "Status", "code": "Active"}],
    ),
    ids=("string", "list-of-strings", "missing-code", "other-code"),
)
def test_403_with_unexpected_errors_shape_raises_plain_fault(
    apiv3_instance, errors
):
    body = {"message": "Forbidden", "errors": errors}
    with pytest.raises(Fault) as error:
        apiv3_instance._handle_protocol_error(_response(403, body))

    assert type(error.value) is Fault


@pytest.mark.parametrize(
    "body",
    (["Forbidden"], "no message at all", "has errors inside"),
    ids=("list", "string-with-message", "string-with-errors"),
)
def test_non_object_json_body_raises_plain_fault(apiv3_instance, body):
    """A JSON body that is not an object must not break the handler.

    A bare JSON string used to pass the `"message" in json_response`
    membership test as a substring match, after which `.get()` was
    called on a `str` and raised AttributeError.
    """
    with pytest.raises(Fault) as error:
        apiv3_instance._handle_protocol_error(_response(403, body))

    assert type(error.value) is Fault


def test_object_shaped_errors_raises_application_inactive(apiv3_instance):
    """Strava documents an array, but a single object is handled too."""
    body = {
        "message": "Forbidden",
        "errors": {
            "resource": "Application",
            "field": "Status",
            "code": "Inactive",
        },
    }
    with pytest.raises(ApplicationInactive):
        apiv3_instance._handle_protocol_error(_response(403, body))


@pytest.mark.parametrize(
    "status_code,reason,expected_exception",
    (
        (404, "Not Found", ObjectNotFound),
        (401, "Unauthorized", AccessUnauthorized),
        (400, "Bad Request", Fault),
        (500, "Server Error", Fault),
    ),
)
def test_other_status_codes_keep_their_exception(
    apiv3_instance, status_code, reason, expected_exception
):
    with pytest.raises(expected_exception) as error:
        apiv3_instance._handle_protocol_error(
            _response(
                status_code,
                {"message": reason, "errors": []},
                reason=reason,
            )
        )

    assert type(error.value) is expected_exception


def test_successful_response_is_returned(apiv3_instance):
    response = _response(200, {"id": 42}, reason="OK")
    assert apiv3_instance._handle_protocol_error(response) is response
