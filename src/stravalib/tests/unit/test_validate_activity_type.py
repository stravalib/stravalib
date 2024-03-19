import pytest


@pytest.fixture
def params():
    """A fixture that creates a dictionary representing
    parameters associated with a Strava activity."""

    params = {
        "name": "New Activity",
        "start_date_local": "2024-03-04T18:56:47Z",
        "elapsed_time": 9000,
        "description": "An activity description here.",
        "distance": 5700,
    }
    return params


# TODO: potentially redo this so each expected and return type is a dict.
# then simplify the logic below
@pytest.mark.parametrize(
    "sport_type, activity_type, expected_result, expected_exception",
    (
        ("TrailRun", None, {"sport_type": "TrailRun"}, None),
        ("funrun", None, None, ValueError),
        (None, "Run", {"type": "run"}, None),
        (None, "junoDog", None, ValueError),
        ("TrailRun", "Run", {"sport_type": "TrailRun"}, None),
    ),
)
def test_validate_activity_type(
    params,
    client,
    activity_type,
    sport_type,
    expected_result,
    expected_exception,
):
    """Test the validation step for create and update activity.

    Create_activity should require with sport_type (or type but type is
    deprecated). As such we test to ensure that a request to create an
    activity that is missing sport_type returns a ValueError
    """

    if expected_exception:
        # TODO: should we have a error message specific to this error here?
        # value = "output error message"
        with pytest.raises(expected_exception):
            client._validate_activity_type(params, activity_type, sport_type)
    else:
        out_params = client._validate_activity_type(
            params, activity_type, sport_type
        )
        # This is a "merge" or dict union introduced in 3.9
        # It combines the two dictionaries updating overlapping key(/val) pairs
        assert params | expected_result == out_params
