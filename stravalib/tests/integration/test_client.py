import pytest


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
