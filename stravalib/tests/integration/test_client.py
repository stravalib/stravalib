import os

import pytest

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


def test_upload_activity(mock_strava_api, client):
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
