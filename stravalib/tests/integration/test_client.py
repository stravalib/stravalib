import datetime
import os

import pytest
from responses import matchers

from stravalib.tests import RESOURCES_DIR
from stravalib.unithelper import miles


def test_get_athlete(mock_strava_api, client):
    mock_strava_api.get('/athlete', response_update={'id': 42})
    athlete = client.get_athlete()
    assert athlete.id == 42
    assert athlete.measurement_preference == 'feet'


@pytest.mark.parametrize(
    'include_all_efforts,expected_url',
    (
        (None, '/activities/42?include_all_efforts=False'),
        (False, '/activities/42?include_all_efforts=False'),
        (True, '/activities/42?include_all_efforts=True'),
    )
)
def test_get_activity(mock_strava_api, client, include_all_efforts, expected_url):
    test_activity_id = 42
    mock_strava_api.get('/activities/{id}', response_update={'id': test_activity_id})
    if include_all_efforts is not None:
        activity = client.get_activity(test_activity_id, include_all_efforts)
    else:
        activity = client.get_activity(test_activity_id)
    assert mock_strava_api.calls[-1].request.url.endswith(expected_url)
    assert activity.id == test_activity_id


@pytest.mark.parametrize(
    'update_kwargs,expected_params,expected_warning,expected_exception',
    (
        ({}, {}, None, None),
        ({'name': 'foo'}, {'name': 'foo'}, None, None),
        ({'activity_type': 'foo'}, {}, None, ValueError),
        ({'activity_type': 'Run'}, {'type': 'run'}, None, None),
        ({'activity_type': 'run'}, {'type': 'run'}, None, None),
        ({'activity_type': 'RUN'}, {'type': 'run'}, None, None),
        ({'private': True}, {'private': '1'}, DeprecationWarning, None),
        ({'commute': True}, {'commute': '1'}, None, None),
        ({'trainer': True}, {'trainer': '1'}, None, None),
        ({'gear_id': 'fb42'}, {'gear_id': 'fb42'}, None, None),
        ({'description': 'foo'}, {'description': 'foo'}, None, None),
        ({'device_name': 'foo'}, {'device_name': 'foo'}, DeprecationWarning, None),
        ({'hide_from_home': False}, {'hide_from_home': '0'}, None, None),
    )
)
def test_update_activity(
        mock_strava_api,
        client,
        update_kwargs,
        expected_params,
        expected_warning,
        expected_exception
):
    activity_id = 42

    def _call_update_activity():
        _ = client.update_activity(activity_id, **update_kwargs)
        assert mock_strava_api.calls[-1].request.params == expected_params

    if expected_exception:
        with pytest.raises(expected_exception):
            _call_update_activity()
    else:
        mock_strava_api.put('/activities/{id}', status=200)
        if expected_warning:
            with pytest.warns(expected_warning):
                _call_update_activity()
        else:
            _call_update_activity()


@pytest.mark.parametrize(
    'activity_file_type,data_type,upload_kwargs,expected_params,expected_warning,expected_exception',
    (
        ('file', 'tcx', {}, {'data_type': 'tcx'}, None, None),
        ('str', 'tcx', {}, {'data_type': 'tcx'}, None, None),
        ('not_supported', 'tcx', {}, {}, None, TypeError),
        ('file', 'invalid', {}, {}, None, ValueError),
        ('file', 'tcx', {'name': 'name'}, {'data_type': 'tcx', 'name': 'name'}, None, None),
        ('file', 'tcx', {'description': 'descr'}, {'data_type': 'tcx', 'description': 'descr'}, None, None),
        ('file', 'tcx', {'activity_type': 'run'}, {'data_type': 'tcx', 'activity_type': 'run'}, FutureWarning, None),
        ('file', 'tcx', {'activity_type': 'Run'}, {'data_type': 'tcx', 'activity_type': 'run'}, FutureWarning, None),
        ('file', 'tcx', {'activity_type': 'sleep'}, None, None, ValueError),
        ('file', 'tcx', {'private': True}, {'data_type': 'tcx', 'private': '1'}, DeprecationWarning, None),
        ('file', 'tcx', {'external_id': 42}, {'data_type': 'tcx', 'external_id': '42'}, None, None),
        ('file', 'tcx', {'trainer': True}, {'data_type': 'tcx', 'trainer': '1'}, None, None),
        ('file', 'tcx', {'commute': False}, {'data_type': 'tcx', 'commute': '0'}, None, None)
    )
)
def test_upload_activity(
        mock_strava_api,
        client,
        activity_file_type,
        data_type,
        upload_kwargs,
        expected_params,
        expected_warning,
        expected_exception
):
    init_upload_response = {
        'id': 1,
        'id_str': 'abc',
        'external_id': 'abc',
        'status': 'default_status',
        'error': ''
    }

    def _call_and_assert(file):
        _ = client.upload_activity(file, data_type, **upload_kwargs)
        assert mock_strava_api.calls[-1].request.params == expected_params

    def _call_upload(file):
        if expected_exception:
            with pytest.raises(expected_exception):
                _call_and_assert(file)
        else:
            mock_strava_api.post('/uploads', status=201, json=init_upload_response)
            if expected_warning:
                with pytest.warns(expected_warning):
                    _call_and_assert(file)
            else:
                _call_and_assert(file)

    with open(os.path.join(RESOURCES_DIR, 'sample.tcx')) as f:
        if activity_file_type == 'file':
            _call_upload(f)
        elif activity_file_type == 'str':
            _call_upload(f.read())
        else:
            _call_upload({})


@pytest.mark.parametrize(
    'update_kwargs,expected_params,expected_warning,expected_exception',
    (
        ({}, {}, None, None),
        ({'city': 'foo'}, {'city': 'foo'}, DeprecationWarning, None),
        ({'state': 'foo'}, {'state': 'foo'}, DeprecationWarning, None),
        ({'country': 'foo'}, {'country': 'foo'}, DeprecationWarning, None),
        ({'sex': 'foo'}, {'sex': 'foo'}, DeprecationWarning, None),
        ({'weight': 'foo'}, {}, None, ValueError),
        ({'weight': '99.9'}, {'weight': '99.9'}, None, None),
        ({'weight': 99.9}, {'weight': '99.9'}, None, None),
        ({'weight': 99}, {'weight': '99.0'}, None, None)
    )
)
def test_update_athlete(
        mock_strava_api,
        client,
        update_kwargs,
        expected_params,
        expected_warning,
        expected_exception
):
    def _call_and_assert():
        _ = client.update_athlete(**update_kwargs)
        assert mock_strava_api.calls[-1].request.params == expected_params

    if expected_exception:
        with pytest.raises(expected_exception):
            _call_and_assert()
    else:
        mock_strava_api.put('/athlete', status=200)
        if expected_warning:
            with pytest.warns(expected_warning):
                _call_and_assert()
        else:
            _call_and_assert()


@pytest.mark.parametrize(
    'extra_create_kwargs,extra_expected_params,expected_exception',
    (
        ({}, {}, None),
        ({'activity_type': 'run'}, {'type': 'run'}, None),
        ({'activity_type': 'Run'}, {'type': 'run'}, None),
        ({'activity_type': 'sleep'}, {}, ValueError),
        (
                {'start_date_local': datetime.datetime(2022, 1, 1, 10, 0, 0)},
                {'start_date_local': '2022-01-01T10:00:00Z'},
                None
        ),
        ({'elapsed_time': datetime.timedelta(minutes=1)}, {'elapsed_time': '60'}, None),
        ({'distance': 1000}, {'distance': '1000'}, None),
        ({'distance': miles(1)}, {'distance': '1609.344'}, None),
        ({'description': 'foo'}, {'description': 'foo'}, None)
    )
)
def test_create_activity(
        mock_strava_api,
        client,
        extra_create_kwargs,
        extra_expected_params,
        expected_exception
):
    default_call_kwargs = {
        'name': 'test',
        'activity_type': 'Run',
        'start_date_local': '2022-01-01T09:00:00',
        'elapsed_time': 3600
    }
    default_request_params = {
        'name': 'test',
        'type': 'run',
        'start_date_local': '2022-01-01T09:00:00',
        'elapsed_time': '3600'
    }
    call_kwargs = {**default_call_kwargs, **extra_create_kwargs}
    expected_params = {**default_request_params, **extra_expected_params}

    def _call_and_assert():
        _ = client.create_activity(**call_kwargs)
        assert mock_strava_api.calls[-1].request.params == expected_params

    if expected_exception:
        with pytest.raises(expected_exception):
            _call_and_assert()
    else:
        mock_strava_api.post('/activities', status=201)
        _call_and_assert()


def test_activity_uploader(mock_strava_api, client):
    test_activity_id = 42
    init_upload_response = {
        'id': 1,
        'id_str': 'abc',
        'external_id': 'abc',
        'status': 'default_status',
        'error': ''
    }
    mock_strava_api.post('/uploads', status=201, json=init_upload_response)
    mock_strava_api.get('/uploads/{uploadId}', json=init_upload_response)
    mock_strava_api.get('/uploads/{uploadId}', json=init_upload_response)
    mock_strava_api.get(
        '/uploads/{uploadId}',
        json={**init_upload_response, 'activity_id': test_activity_id}
    )
    mock_strava_api.get('/activities/{id}', response_update={'id': test_activity_id})
    with open(os.path.join(RESOURCES_DIR, 'sample.tcx')) as activity_file:
        uploader = client.upload_activity(activity_file, data_type='tcx')
        assert uploader.is_processing
        activity = uploader.wait()
        assert uploader.is_complete
        assert activity.id == test_activity_id


def test_get_route(mock_strava_api, client):
    mock_strava_api.get('/routes/{id}', status=200, response_update={'name': 'test_route'})
    route = client.get_route(42)
    assert route.name == 'test_route'


@pytest.mark.parametrize(
    'limit,n_raw_results,expected_n_segments',
    (
        (None, 0, 0),
        (None, 10, 10),
        (10, 10, 10),
        (10, 20, 10),
        (10, 1, 1),
        (10, 0, 0)
    )

)
def test_get_starred_segments(mock_strava_api, client, limit, n_raw_results, expected_n_segments):
    mock_strava_api.get(
        '/segments/starred',
        response_update={'name': 'test_segment'},
        n_results=n_raw_results
    )
    kwargs = {'limit': limit} if limit is not None else {}
    activity_list = list(client.get_starred_segments(**kwargs))
    assert len(activity_list) == expected_n_segments
    if expected_n_segments > 0:
        assert activity_list[0].name == 'test_segment'


@pytest.mark.parametrize(
    'limit,n_raw_results,expected_n_activities',
    (
        (None, 10, 10),
        (None, 0, 0),
        (10, 10, 10),
        (10, 20, 10),
        (10, 1, 1),
        (10, 0, 0)
    )
)
def test_get_activities(mock_strava_api, client, limit, n_raw_results, expected_n_activities):
    mock_strava_api.get(
        '/athlete/activities',
        response_update={'name': 'test_activity'},
        n_results=n_raw_results
    )
    kwargs = {'limit': limit} if limit is not None else {}
    activity_list = list(client.get_activities(**kwargs))
    assert len(activity_list) == expected_n_activities
    if expected_n_activities > 0:
        assert activity_list[0].name == 'test_activity'


def test_get_activities_paged(mock_strava_api, client):
    for i in range(1, 4):
        params = {'page': i, 'per_page': 200}
        mock_strava_api.get(
            '/athlete/activities',
            response_update={'id': i},
            n_results=(200 if i < 3 else 100),
            match=[matchers.query_param_matcher(params)]
        )
    activity_list = list(client.get_activities())
    assert len(activity_list) == 500
    assert activity_list[0].id == 1
    assert activity_list[400].id == 3
