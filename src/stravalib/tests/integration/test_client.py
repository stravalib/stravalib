import datetime
import json
import os
from unittest import mock

import pytest
import responses
from responses import matchers

from stravalib.client import ActivityUploader
from stravalib.exc import AccessUnauthorized, ActivityPhotoUploadFailed
from stravalib.model import DetailedAthlete, SummaryAthlete, SummarySegment
from stravalib.strava_model import SummaryActivity
from stravalib.tests import RESOURCES_DIR
from stravalib.unit_helper import miles


@pytest.fixture
def zone_response():
    file_path = os.path.join(RESOURCES_DIR, "example_zone_response.json")
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


@pytest.fixture
def default_call_kwargs():
    """A fixture containing default input / call parameters for a create
    activity call to the strava API"""

    default_call_kwargs = {
        "name": "test",
        "start_date_local": "2022-01-01T09:00:00",
        "elapsed_time": 3600,
    }
    return default_call_kwargs


@pytest.fixture
def default_request_params():
    """A fixture containing default request parameters for a create activity
    request to the strava API"""

    default_request_params = {
        "name": "test",
        "start_date_local": "2022-01-01T09:00:00",
        "elapsed_time": "3600",
    }
    return default_request_params


def test_get_athlete(mock_strava_api, client):
    mock_strava_api.get("/athlete", response_update={"id": 42})
    athlete = client.get_athlete()
    assert isinstance(athlete, DetailedAthlete)
    assert athlete.id == 42
    assert athlete.measurement_preference == "feet"


@pytest.mark.parametrize(
    "include_all_efforts,expected_url",
    (
        (None, "/activities/42?include_all_efforts=False"),
        (False, "/activities/42?include_all_efforts=False"),
        (True, "/activities/42?include_all_efforts=True"),
    ),
)
def test_get_activity(
    mock_strava_api, client, include_all_efforts, expected_url
):
    test_activity_id = 42
    mock_strava_api.get(
        "/activities/{id}", response_update={"id": test_activity_id}
    )
    if include_all_efforts is not None:
        activity = client.get_activity(test_activity_id, include_all_efforts)
    else:
        activity = client.get_activity(test_activity_id)
    assert mock_strava_api.calls[-1].request.url.endswith(expected_url)
    assert activity.id == test_activity_id


def test_activity_with_segment_that_that_is_not_ride_or_run(
    mock_strava_api, client
):
    """
    Make sure that activity that are not run are ride can still have segment.

    See issue https://github.com/stravalib/stravalib/issues/432
    """
    test_activity_id = 1907
    mock_strava_api.get(
        "/activities/{id}",
        response_update={
            "id": test_activity_id,
            "type": "Hike",
            "segment_efforts": [
                {
                    "id": 3125507031446243384,
                    "resource_state": 2,
                    "name": "Landmannalaugavegur Climb",
                    "activity": {
                        "id": 9634609164,
                        "visibility": "followers_only",
                        "resource_state": 1,
                    },
                    "athlete": {"id": 69911568, "resource_state": 1},
                    "elapsed_time": 454,
                    "moving_time": 426,
                    "start_date": "2023-08-12T05:22:38Z",
                    "start_date_local": "2023-08-12T05:22:38Z",
                    "distance": 709.74,
                    "start_index": 91,
                    "end_index": 213,
                    "average_cadence": 47.7,
                    "device_watts": False,
                    "segment": {
                        "id": 837087,
                        "resource_state": 2,
                        "name": "Landmannalaugavegur Climb",
                        "activity_type": "Hike",
                        "distance": 709.74,
                        "average_grade": 7.7,
                        "maximum_grade": 427.6,
                        "elevation_high": 624.4,
                        "elevation_low": 570.0,
                        "start_latlng": [
                            63.99094129912555,
                            -19.063721196725965,
                        ],
                        "end_latlng": [63.99059135466814, -19.075878812000155],
                        "elevation_profile": None,
                        "climb_category": 0,
                        "city": None,
                        "state": "Suðurland",
                        "country": "Iceland",
                        "private": False,
                        "hazardous": False,
                        "starred": False,
                    },
                    "pr_rank": None,
                    "achievements": [],
                    "visibility": "followers_only",
                    "hidden": False,
                }
            ],
        },
    )
    activity = client.get_activity(test_activity_id)


def test_get_activity_laps(mock_strava_api, client):
    mock_strava_api.get(
        "/activities/{id}/laps",
        response_update={"distance": 1000},
        n_results=2,
    )
    laps = list(client.get_activity_laps(42))
    assert len(laps) == 2
    assert laps[0].distance == 1000


def test_get_club_activities(mock_strava_api, client):
    mock_strava_api.get(
        "/clubs/{id}/activities",
        response_update={"distance": 1000},
        n_results=2,
    )

    activities = list(client.get_club_activities(42))
    assert len(activities) == 2
    assert activities[0].distance == 1000


def test_get_club_admins(mock_strava_api, client):
    mock_strava_api.get(
        "/clubs/{id}/admins",
        response_update={"firstname": "Jane"},
        n_results=2,
    )

    admins = list(client.get_club_admins(42))
    assert isinstance(admins[0], SummaryAthlete)
    assert len(admins) == 2
    assert admins[0].firstname == "Jane"


def test_get_activity_zones(mock_strava_api, client, zone_response):
    """Returns an activities associated zone (related to heart rate and power)

    Notes
    -----
    There is no example response for this endpoint in swagger.json so
    we created a sample json file with the return that we are currently
    seeing. Thus this method could break at any time if Strava changes
    the response output.

    """

    mock_strava_api.get("/activities/{id}/zones", json=zone_response)

    # https://developers.strava.com/docs/reference/#api-models-integer
    activity_zones = client.get_activity_zones(42)
    assert len(activity_zones) == 2
    assert activity_zones[0].type == "heartrate"
    assert activity_zones[0].sensor_based


def test_get_activity_streams(mock_strava_api, client):
    query_params = {"keys": "distance", "key_by_type": True}
    mock_strava_api.get(
        "/activities/{id}/streams",
        json={
            "distance": {
                "data": [1.0, 2.0, 3.0],
                "series_type": "distance",
                "original_size": 9,
                "resolution": "high",
            }
        },
        match=[matchers.query_param_matcher(query_params)],
    )
    streams = client.get_activity_streams(42, types=["distance"])
    assert streams["distance"].data == [1.0, 2.0, 3.0]


def test_get_effort_streams(mock_strava_api, client):
    query_params = {"keys": "distance", "key_by_type": True}
    mock_strava_api.get(
        "/segment_efforts/{id}/streams",
        json={
            "distance": {
                "data": [1.0, 2.0, 3.0],
                "series_type": "distance",
                "original_size": 9,
                "resolution": "high",
            }
        },
        match=[matchers.query_param_matcher(query_params)],
    )
    streams = client.get_effort_streams(42, types=["distance"])
    assert streams["distance"].data == [1.0, 2.0, 3.0]


def test_get_segment_streams(mock_strava_api, client):
    query_params = {"keys": "distance", "key_by_type": True}
    mock_strava_api.get(
        "/segments/{id}/streams",
        json={
            "distance": {
                "data": [1.0, 2.0, 3.0],
                "series_type": "distance",
                "original_size": 9,
                "resolution": "high",
            }
        },
        match=[matchers.query_param_matcher(query_params)],
    )
    streams = client.get_segment_streams(42, types=["distance"])
    assert streams["distance"].data == [1.0, 2.0, 3.0]


def test_get_activity_streams_no_type_specified(mock_strava_api, client):
    query_params = {
        "keys": "time,distance,latlng,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth",
        "key_by_type": True,
    }
    mock_strava_api.get(
        "/activities/{id}/streams",
        json={
            "distance": {
                "data": [1.0, 2.0, 3.0],
                "original_size": 9,
                "resolution": "high",
            }
        },
        match=[matchers.query_param_matcher(query_params)],
    )
    streams = client.get_activity_streams(42)
    assert streams["distance"].data == [1.0, 2.0, 3.0]


def test_get_activity_streams_invalid_type(mock_strava_api, client):
    with pytest.raises(ValueError):
        streams = client.get_activity_streams(
            42, types=["distance", "hhjj", "npt"]
        )


def test_get_activity_streams_resolution_unofficial(mock_strava_api, client):
    mock_strava_api.get(
        "/activities/{id}/streams",
        json={
            "distance": {
                "data": [1.0, 2.0, 3.0],
                "series_type": "distance",
                "original_size": 9,
                "resolution": "high",
            }
        },
    )
    with pytest.warns(FutureWarning):
        streams = client.get_activity_streams(
            42, types=["distance"], resolution="high"
        )


def test_get_activity_streams_series_type_unofficial(mock_strava_api, client):
    mock_strava_api.get(
        "/activities/{id}/streams",
        json={
            "distance": {
                "data": [1.0, 2.0, 3.0],
                "series_type": "distance",
                "original_size": 9,
                "resolution": "high",
            }
        },
    )
    with pytest.warns(FutureWarning):
        streams = client.get_activity_streams(
            42, types=["distance"], series_type="distance"
        )


@pytest.mark.parametrize(
    "update_kwargs,expected_params,expected_warning,expected_exception",
    (
        ({}, {}, None, None),
        ({"activity_type": "Run"}, {"type": "run"}, DeprecationWarning, None),
        ({"sport_type": "TrailRun"}, {"sport_type": "TrailRun"}, None, None),
        (
            {"activity_type": "Run", "sport_type": "TrailRun"},
            {"sport_type": "TrailRun"},
            None,
            None,
        ),
        ({"private": True}, {"private": "1"}, DeprecationWarning, None),
        ({"commute": True}, {"commute": "1"}, None, None),
        ({"trainer": True}, {"trainer": "1"}, None, None),
        ({"gear_id": "fb42"}, {"gear_id": "fb42"}, None, None),
        ({"description": "foo"}, {"description": "foo"}, None, None),
        (
            {"device_name": "foo"},
            {"device_name": "foo"},
            DeprecationWarning,
            None,
        ),
        ({"hide_from_home": False}, {"hide_from_home": "0"}, None, None),
        (
            {"name": "My awesome activity"},
            {"name": "My awesome activity"},
            None,
            None,
        ),
    ),
)
def test_update_activity(
    mock_strava_api,
    client,
    update_kwargs,
    expected_params,
    expected_warning,
    expected_exception,
):
    activity_id = 42

    def _call_update_activity():
        _ = client.update_activity(activity_id, **update_kwargs)
        assert mock_strava_api.calls[-1].request.params == expected_params

    if expected_exception:
        with pytest.raises(expected_exception):
            _call_update_activity()
    else:
        mock_strava_api.put("/activities/{id}", status=200)
        if expected_warning:
            with pytest.warns(expected_warning):
                _call_update_activity()
        else:
            _call_update_activity()


@pytest.mark.parametrize(
    "activity_file_type,data_type,upload_kwargs,expected_params,expected_warning,expected_exception",
    (
        ("file", "tcx", {}, {"data_type": "tcx"}, None, None),
        ("str", "tcx", {}, {"data_type": "tcx"}, None, None),
        ("bytes", "tcx", {}, {"data_type": "tcx"}, None, None),
        ("not_supported", "tcx", {}, {}, None, TypeError),
        ("file", "invalid", {}, {}, None, ValueError),
        (
            "file",
            "tcx",
            {"name": "name"},
            {"data_type": "tcx", "name": "name"},
            None,
            None,
        ),
        (
            "file",
            "tcx",
            {"description": "descr"},
            {"data_type": "tcx", "description": "descr"},
            None,
            None,
        ),
        (
            "file",
            "tcx",
            {"activity_type": "run"},
            {"data_type": "tcx", "activity_type": "run"},
            FutureWarning,
            None,
        ),
        (
            "file",
            "tcx",
            {"activity_type": "Run"},
            {"data_type": "tcx", "activity_type": "run"},
            FutureWarning,
            None,
        ),
        ("file", "tcx", {"activity_type": "sleep"}, None, None, ValueError),
        (
            "file",
            "tcx",
            {"private": True},
            {"data_type": "tcx", "private": "1"},
            DeprecationWarning,
            None,
        ),
        (
            "file",
            "tcx",
            {"external_id": 42},
            {"data_type": "tcx", "external_id": "42"},
            None,
            None,
        ),
        (
            "file",
            "tcx",
            {"trainer": True},
            {"data_type": "tcx", "trainer": "1"},
            None,
            None,
        ),
        (
            "file",
            "tcx",
            {"commute": False},
            {"data_type": "tcx", "commute": "0"},
            None,
            None,
        ),
    ),
)
def test_upload_activity(
    mock_strava_api,
    client,
    activity_file_type,
    data_type,
    upload_kwargs,
    expected_params,
    expected_warning,
    expected_exception,
):
    init_upload_response = {
        "id": 1,
        "id_str": "abc",
        "external_id": "abc",
        "status": "default_status",
        "error": "",
    }

    def _call_and_assert(file):
        _ = client.upload_activity(file, data_type, **upload_kwargs)
        assert mock_strava_api.calls[-1].request.params == expected_params

    def _call_upload(file):
        if expected_exception:
            with pytest.raises(expected_exception):
                _call_and_assert(file)
        else:
            mock_strava_api.post(
                "/uploads", status=201, json=init_upload_response
            )
            if expected_warning:
                with pytest.warns(expected_warning):
                    _call_and_assert(file)
            else:
                _call_and_assert(file)

    with open(os.path.join(RESOURCES_DIR, "sample.tcx")) as f:
        if activity_file_type == "file":
            _call_upload(f)
        elif activity_file_type == "str":
            _call_upload(f.read())
        elif activity_file_type == "bytes":
            _call_upload(f.read().encode("utf-8"))
        else:
            _call_upload({})


@pytest.mark.parametrize(
    "update_kwargs,expected_params,expected_warning,expected_exception",
    (
        ({}, {}, None, None),
        ({"city": "foo"}, {"city": "foo"}, DeprecationWarning, None),
        ({"state": "foo"}, {"state": "foo"}, DeprecationWarning, None),
        ({"country": "foo"}, {"country": "foo"}, DeprecationWarning, None),
        ({"sex": "foo"}, {"sex": "foo"}, DeprecationWarning, None),
        ({"weight": "foo"}, {}, None, ValueError),
        ({"weight": "99.9"}, {"weight": "99.9"}, None, None),
        ({"weight": 99.9}, {"weight": "99.9"}, None, None),
        ({"weight": 99}, {"weight": "99.0"}, None, None),
    ),
)
def test_update_athlete(
    mock_strava_api,
    client,
    update_kwargs,
    expected_params,
    expected_warning,
    expected_exception,
):
    def _call_and_assert():
        _ = client.update_athlete(**update_kwargs)
        assert mock_strava_api.calls[-1].request.params == expected_params

    if expected_exception:
        with pytest.raises(expected_exception):
            _call_and_assert()
    else:
        mock_strava_api.put("/athlete", status=200)
        if expected_warning:
            with pytest.warns(expected_warning):
                _call_and_assert()
        else:
            _call_and_assert()


@pytest.mark.parametrize(
    "extra_create_kwargs,extra_expected_params,expected_exception",
    (
        (
            {
                "sport_type": "TrailRun",
                "start_date_local": datetime.datetime(2022, 1, 1, 10, 0, 0),
            },
            {
                "sport_type": "TrailRun",
                "start_date_local": "2022-01-01T10:00:00Z",
            },
            None,
        ),
        (
            {
                "sport_type": "TrailRun",
                "elapsed_time": datetime.timedelta(minutes=1),
            },
            {"sport_type": "TrailRun", "elapsed_time": "60"},
            None,
        ),
        (
            {"sport_type": "TrailRun", "distance": 1000},
            {"sport_type": "TrailRun", "distance": "1000"},
            None,
        ),
        (
            {"sport_type": "TrailRun", "distance": miles(1)},
            {"sport_type": "TrailRun", "distance": "1609.344"},
            None,
        ),
        (
            {"sport_type": "TrailRun", "description": "foo"},
            {"sport_type": "TrailRun", "description": "foo"},
            None,
        ),
        (
            {"description": "foo"},
            {"description": "foo"},
            ValueError,
        ),
    ),
)
def test_create_activity(
    default_call_kwargs,
    default_request_params,
    mock_strava_api,
    client,
    extra_create_kwargs,
    extra_expected_params,
    expected_exception,
):
    """Test what happens when create activity receives valid and invalid
    sport type values and also what happens when a required API item
    is missing."""

    call_kwargs = default_call_kwargs | extra_create_kwargs
    expected_params = default_request_params | extra_expected_params

    def _call_and_assert():
        _ = client.create_activity(**call_kwargs)
        assert mock_strava_api.calls[-1].request.params == expected_params

    if expected_exception:
        with pytest.raises(expected_exception):
            _call_and_assert()
    else:
        mock_strava_api.post("/activities", status=201)
        _call_and_assert()


def test_activity_uploader(mock_strava_api, client):
    test_activity_id = 42
    init_upload_response = {
        "id": 1,
        "id_str": "abc",
        "external_id": "abc",
        "status": "default_status",
        "error": "",
    }
    mock_strava_api.post("/uploads", status=201, json=init_upload_response)
    mock_strava_api.get("/uploads/{uploadId}", json=init_upload_response)
    mock_strava_api.get("/uploads/{uploadId}", json=init_upload_response)
    mock_strava_api.get(
        "/uploads/{uploadId}",
        json={**init_upload_response, "activity_id": test_activity_id},
    )
    mock_strava_api.get(
        "/activities/{id}", response_update={"id": test_activity_id}
    )
    with open(os.path.join(RESOURCES_DIR, "sample.tcx")) as activity_file:
        uploader = client.upload_activity(activity_file, data_type="tcx")
        assert uploader.is_processing
        activity = uploader.wait()
        assert uploader.is_complete
        assert activity.id == test_activity_id


def test_get_route(mock_strava_api, client):
    with open(
        os.path.join(RESOURCES_DIR, "example_route_response.json"), "r"
    ) as route_response_fp:
        route_response = json.load(route_response_fp)
    mock_strava_api.get("/routes/{id}", status=200, json=route_response)
    route = client.get_route(42)
    assert route.name == "15k, no traffic"


@responses.activate
def test_create_subscription(mock_strava_api, client):
    responses.post(
        "https://www.strava.com/api/v3/push_subscriptions",
        json={
            "application_id": 42,
            "object_type": "activity",
            "aspect_type": "create",
            "callback_url": "https://foobar.com",
            "created_at": 1674660406,
        },
        status=200,
    )
    created_subscription = client.create_subscription(
        42, 42, "https://foobar.com"
    )
    assert created_subscription.application_id == 42


@pytest.mark.parametrize(
    "raw,expected_verify_token,expected_response,expected_exception",
    (
        (
            {"hub.verify_token": "a", "hub.challenge": "b"},
            "a",
            {"hub.challenge": "b"},
            None,
        ),
        (
            {"hub.verify_token": "foo", "hub.challenge": "b"},
            "a",
            None,
            AssertionError,
        ),
    ),
)
def test_handle_subscription_callback(
    client, raw, expected_verify_token, expected_response, expected_exception
):
    if expected_exception:
        with pytest.raises(expected_exception):
            client.handle_subscription_callback(raw, expected_verify_token)
    else:
        assert (
            client.handle_subscription_callback(raw, expected_verify_token)
            == expected_response
        )


@pytest.mark.parametrize(
    "limit,n_raw_results,expected_n_segments",
    (
        (None, 0, 0),
        (None, 10, 10),
        (10, 10, 10),
        (10, 20, 10),
        (10, 1, 1),
        (10, 0, 0),
    ),
)
def test_get_starred_segments(
    mock_strava_api, client, limit, n_raw_results, expected_n_segments
):
    mock_strava_api.get(
        "/segments/starred",
        response_update={"name": "test_segment"},
        n_results=n_raw_results,
    )
    kwargs = {"limit": limit} if limit is not None else {}
    segment_list = list(client.get_starred_segments(**kwargs))
    assert len(segment_list) == expected_n_segments
    if expected_n_segments > 0:
        assert isinstance(segment_list[0], SummarySegment)
        assert segment_list[0].name == "test_segment"


def test_get_club(mock_strava_api, client):
    mock_strava_api.get("/clubs/{id}", response_update={"name": "foo"})
    club = client.get_club(42)
    assert club.name == "foo"


@pytest.mark.parametrize("n_clubs", (0, 2))
def test_get_athlete_clubs_iterator(mock_strava_api, client, n_clubs):
    """Test that athlete clubs returns the correct
    number of clubs"""

    # Create a mock instance with the club name update to my club
    mock_strava_api.get(
        "/athlete/clubs", response_update={"name": "myclub"}, n_results=n_clubs
    )
    # Convert iterator to list
    clubs = list(client.get_athlete_clubs())
    assert len(clubs) == n_clubs
    if clubs:
        assert clubs[0].name == "myclub"


@pytest.mark.parametrize("n_members", (0, 2))
def test_get_club_members(mock_strava_api, client, n_members):
    mock_strava_api.get(
        "/clubs/{id}/members",
        response_update={"lastname": "Doe"},
        n_results=n_members,
    )
    members = list(client.get_club_members(42))
    assert len(members) == n_members
    if members:
        assert members[0].lastname == "Doe"


@pytest.mark.parametrize(
    "athlete_id,authenticated_athlete,expected_biggest_ride_distance,expected_exception",
    (
        (42, True, 1000, None),
        (42, False, None, AccessUnauthorized),
        (None, True, 1000, None),
    ),
)
def test_get_athlete_stats(
    mock_strava_api,
    client,
    athlete_id,
    authenticated_athlete,
    expected_biggest_ride_distance,
    expected_exception,
):
    if athlete_id is None:
        mock_strava_api.get("/athlete", response_update={"id": 42})
    if authenticated_athlete:
        mock_strava_api.get(
            "/athletes/{id}/stats",
            response_update={
                "biggest_ride_distance": expected_biggest_ride_distance
            },
        )
    else:
        mock_strava_api.get(
            "/athletes/{id}/stats",
            json=[
                {
                    "resource": "Athlete",
                    "field": "access_token",
                    "code": "invalid",
                }
            ],
            status=401,
        )
    if expected_exception:
        with pytest.raises(expected_exception):
            client.get_athlete_stats(athlete_id)
    else:
        stats = client.get_athlete_stats(athlete_id)
        assert stats.biggest_ride_distance == expected_biggest_ride_distance


def test_get_gear(mock_strava_api, client):
    mock_strava_api.get("/gear/{id}", response_update={"name": "foo_bike"})
    assert client.get_gear(42).name == "foo_bike"


@pytest.mark.parametrize(
    "limit,n_raw_results,expected_n_activities",
    (
        (None, 10, 10),
        (None, 0, 0),
        (10, 10, 10),
        (10, 20, 10),
        (10, 1, 1),
        (10, 0, 0),
    ),
)
def test_get_activities(
    mock_strava_api, client, limit, n_raw_results, expected_n_activities
):
    mock_strava_api.get(
        "/athlete/activities",
        response_update={"name": "test_activity"},
        n_results=n_raw_results,
    )
    kwargs = {"limit": limit} if limit is not None else {}
    activity_list = list(client.get_activities(**kwargs))
    assert len(activity_list) == expected_n_activities
    if expected_n_activities > 0:
        assert isinstance(activity_list[0], SummaryActivity)
        assert activity_list[0].name == "test_activity"


def test_get_activities_quantity_addition(mock_strava_api, client):
    mock_strava_api.get(
        "/athlete/activities",
        response_update={"distance": 1000.0},
        n_results=2,
    )
    act_list = list(client.get_activities(limit=2))
    total_d = 0
    total_d += act_list[0].distance
    total_d += act_list[1].distance
    assert total_d == 2000.0


def test_get_segment(mock_strava_api, client):
    mock_strava_api.get("/segments/{id}", response_update={"name": "foo"})
    segment = client.get_segment(42)
    assert segment.name == "foo"


def test_get_segment_effort(mock_strava_api, client):
    mock_strava_api.get(
        "/segment_efforts/{id}", response_update={"max_heartrate": 170}
    )
    effort = client.get_segment_effort(42)
    assert effort.max_heartrate == 170


def test_get_activities_paged(mock_strava_api, client):
    for i in range(1, 4):
        params = {"page": i, "per_page": 200}
        mock_strava_api.get(
            "/athlete/activities",
            response_update={"id": i},
            n_results=(200 if i < 3 else 100),
            match=[matchers.query_param_matcher(params)],
        )
    activity_list = list(client.get_activities())
    assert len(activity_list) == 500
    assert activity_list[0].id == 1
    assert activity_list[400].id == 3


@responses.activate
def test_upload_activity_photo_works(client):
    """
    Test uploading an activity with a photo.

    """

    strava_pre_signed_uri = "https://strava-photo-uploads-prod.s3-accelerate.amazonaws.com/12345.jpg"
    photo_bytes = b"photo_data"
    photo_metadata_header = {
        "Content-Type": "image/jpeg",
        "Expect": "100-continue",
        "Host": "strava-photo-uploads-prod.s3-accelerate.amazonaws.com",
    }
    activity_upload_response = {
        "id": 12345,
        "external_id": "external_id",
        "error": None,
        "status": "Your activity is ready.",
        "activity_id": 12345,
        "photo_metadata": [
            {
                "uri": strava_pre_signed_uri,
                "header": photo_metadata_header,
                "method": "PUT",
                "max_size": 1600,
            }
        ],
    }
    with responses.RequestsMock(
        assert_all_requests_are_fired=True
    ) as _responses:
        _responses.add(
            responses.PUT,
            "https://strava-photo-uploads-prod.s3-accelerate.amazonaws.com/12345.jpg",
            status=200,
        )

        _responses.add(
            responses.GET,
            "https://www.strava.com/api/v3/uploads/12345",
            status=200,
            json=activity_upload_response,
        )

        activity_uploader = ActivityUploader(
            client, response=activity_upload_response
        )

        activity_uploader.upload_photo(photo=photo_bytes)


def test_upload_activity_photo_fail_type_error(client):
    activity_uploader = ActivityUploader(client, response={})

    with pytest.raises(ActivityPhotoUploadFailed) as error:
        activity_uploader.upload_photo(photo="photo_str")

    assert str(error.value) == "Photo must be bytes type"


@mock.patch("stravalib.client.ActivityUploader.poll")
def test_upload_activity_photo_fail_activity_upload_not_complete(client):
    activity_upload_response = {
        "id": 1234578,
        "external_id": "external_id",
        "error": None,
        "status": "Your activity is being processed.",
    }
    activity_uploader = ActivityUploader(
        client, response=activity_upload_response
    )

    with pytest.raises(ActivityPhotoUploadFailed) as error:
        activity_uploader.upload_photo(photo=b"photo_bytes")

    assert str(error.value) == "Activity upload not complete"


@pytest.mark.parametrize("photo_metadata", (None, [], [{}]))
@mock.patch("stravalib.client.ActivityUploader.poll")
def test_upload_activity_photo_fail_not_supported(client, photo_metadata):
    activity_upload_response = {
        "id": 1234578,
        "external_id": "external_id",
        "error": None,
        "status": "Your activity is ready.",
        "activity_id": 1234578,
        "photo_metadata": photo_metadata,
    }

    activity_uploader = ActivityUploader(
        client, response=activity_upload_response
    )

    with pytest.raises(ActivityPhotoUploadFailed) as error:
        activity_uploader.upload_photo(photo=b"photo_bytes")

    assert str(error.value) == "Photo upload not supported"


def test_get_activity_comments(mock_strava_api, client):
    mock_strava_api.get(
        "/activities/{id}/comments",
        response_update={"text": "foo"},
        n_results=2,
    )
    comment_list = list(
        client.get_activity_comments(42)
    )  # no idea what the markdown param is supposed to do
    assert len(comment_list) == 2
    assert comment_list[0].text == "foo"


def test_explore_segments(mock_strava_api, client):
    # TODO parameterize test with multiple inputs
    # It is hard to patch the response for this one, since the
    # endpoint returns a nested list of segments.
    mock_strava_api.get("/segments/explore")
    segment_list = client.explore_segments((1, 2, 3, 4))
    assert len(segment_list) == 1
    assert segment_list[0].name == "Hawk Hill"


def test_get_activity_kudos(mock_strava_api, client):
    mock_strava_api.get(
        "/activities/{id}/kudos",
        response_update={"lastname": "Doe"},
        n_results=2,
    )
    kudoer_list = list(client.get_activity_kudos(42))
    assert isinstance(kudoer_list[0], SummaryAthlete)
    assert len(kudoer_list) == 2
    assert kudoer_list[0].lastname == "Doe"
