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


@pytest.mark.parametrize(
    "sport_type, activity_type, expected_result, expected_exception, create",
    (
        ("TrailRun", None, "TrailRun", None, False),
        ("funrun", None, None, ValueError, False),
        (None, "Run", "run", None, False),
        (None, "junoDog", None, ValueError, False),
        ("TrailRun", "Run", "TrailRun", None, False),
        (None, None, None, ValueError, True),  # Create activity
    ),
)
def test_validate_activity_type(
    params,
    client,
    activity_type,
    sport_type,
    expected_result,
    expected_exception,
    create,
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
            client._validate_activity_type(
                params, activity_type, sport_type, create
            )
    else:
        out = client._validate_activity_type(
            params, activity_type, sport_type, create
        )
        # If both keys are in the dictionary - validate should only return one
        # A keyerror should be returned
        if sport_type and activity_type:
            assert out["sport_type"] == expected_result
            assert "type" not in out.keys()
            # Run tests
        # If only sport type is available
        elif sport_type:
            assert out["sport_type"] == expected_result
        elif activity_type:
            assert out["type"] == expected_result
