import pytest

from stravalib.model import LatLon, SummaryActivity


@pytest.mark.parametrize(
    "start_latlng, end_latlng, start_expected_return, end_expected_return",
    [
        (
            [10.2, 1.02],
            [10.2, 1.02],
            LatLon(root=[10.2, 1.02]),
            LatLon(root=[10.2, 1.02]),
        ),
        (None, None, None, None),
        ([], [], None, None),
    ],
)
def test_summary_activity_latlng(
    start_latlng, end_latlng, start_expected_return, end_expected_return
):
    """Test that a valid lat long, an empty list and None
    all return as expected"""

    activity = SummaryActivity(
        start_latlng=start_latlng, end_latlng=end_latlng
    )
    assert activity.start_latlng == start_expected_return
    assert activity.end_latlng == end_expected_return
