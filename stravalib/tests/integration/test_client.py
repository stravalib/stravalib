import os

import pytest
from responses import matchers

from stravalib.tests import RESOURCES_DIR


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
    'activity_file_type,data_type,name,description,activity_type,private,external_id,'
    'trainer,commute,expected_params,expected_exception',
    (
        ('file', 'tcx', None, None, None, None, None, None, None, {'data_type': 'tcx'}, None),
        ('str', 'tcx', None, None, None, None, None, None, None, {'data_type': 'tcx'}, None),
        ('not_supported', 'tcx', None, None, None, None, None, None, None, None, TypeError),
        ('file', 'invalid', None, None, None, None, None, None, None, None, ValueError),
        ('file', 'tcx', 'name', None, None, None, None, None, None, {'data_type': 'tcx', 'name': 'name'}, None),
        ('file', 'tcx', None, 'descr', None, None, None, None, None, {'data_type': 'tcx', 'description': 'descr'}, None),
        ('file', 'tcx', None, None, 'Run', None, None, None, None, {'data_type': 'tcx', 'activity_type': 'Run'}, None),
        ('file', 'tcx', None, None, 'run', None, None, None, None, {'data_type': 'tcx', 'activity_type': 'run'}, None),
        ('file', 'tcx', None, None, 'sleep', None, None, None, None, None, ValueError),
        ('file', 'tcx', None, None, None, True, None, None, None, {'data_type': 'tcx', 'private': '1'}, None),
        ('file', 'tcx', None, None, None, None, 42, None, None, {'data_type': 'tcx', 'external_id': '42'}, None),
        ('file', 'tcx', None, None, None, None, None, True, None, {'data_type': 'tcx', 'trainer': 'true'}, None),
        ('file', 'tcx', None, None, None, None, None, None, True, {'data_type': 'tcx', 'commute': 'true'}, None)
    )
)
def test_upload_activity(
        mock_strava_api,
        client,
        activity_file_type,
        data_type,
        name,
        description,
        activity_type,
        private,
        external_id,
        trainer,
        commute,
        expected_params,
        expected_exception
):
    init_upload_response = {
        'id': 1,
        'id_str': 'abc',
        'external_id': 'abc',
        'status': 'default_status',
        'error': ''
    }
    upload_kwargs = {
        **({'name': name} if name is not None else {}),
        **({'description': description} if description is not None else {}),
        **({'activity_type': activity_type} if activity_type is not None else {}),
        **({'private': private} if private is not None else {}),
        **({'external_id': external_id} if external_id is not None else {}),
        **({'trainer': trainer} if trainer is not None else {}),
        **({'commute': commute} if commute is not None else {})
    }

    def _call_upload(*args, **kwargs):
        if expected_exception:
            with pytest.raises(expected_exception):
                client.upload_activity(*args, **kwargs)
        else:
            mock_strava_api.post('/uploads', status=201, json=init_upload_response)
            _ = client.upload_activity(*args, **kwargs)
            assert mock_strava_api.calls[-1].request.params == expected_params

    with open(os.path.join(RESOURCES_DIR, 'sample.tcx')) as f:
        if activity_file_type == 'file':
            _call_upload(f, data_type, **upload_kwargs)
        elif activity_file_type == 'str':
            _call_upload(f.read(), data_type, **upload_kwargs)
        else:
            _call_upload({}, data_type, **upload_kwargs)


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
