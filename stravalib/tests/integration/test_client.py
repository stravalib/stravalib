from stravalib import Client


def test_get_athlete(mock_strava_api):
    mock_strava_api.get('/athlete', response_update={'id': 42})
    athlete = Client().get_athlete()
    assert athlete.id == 42
    assert athlete.measurement_preference == 'feet'
