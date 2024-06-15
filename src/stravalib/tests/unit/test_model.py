from datetime import datetime, timezone

import pytest
from dateutil.parser import ParserError

from stravalib import model
from stravalib.model import (
    ActivityPhoto,
    ActivityTotals,
    AthletePrEffort,
    AthleteSegmentStats,
    AthleteStats,
    BaseEffort,
    DetailedActivity,
    Lap,
    LatLon,
    RelaxedActivityType,
    RelaxedSportType,
    Route,
    Segment,
    SegmentEffort,
    SegmentExplorerResult,
    Split,
    SubscriptionCallback,
    SummarySegmentEffort,
    naive_datetime,
)
from stravalib.tests import TestBase


@pytest.mark.parametrize(
    "model_class,raw,expected_value",
    (
        (
            DetailedActivity,
            {"start_latlng": []},
            None,
        ),
        (
            DetailedActivity,
            {"end_latlng": []},
            None,
        ),
        (
            DetailedActivity,
            {"end_latlng": "5.4,4.3"},
            LatLon([5.4, 4.3]),
        ),
        (
            DetailedActivity,
            {"start_latlng": "5.4,4.3"},
            LatLon([5.4, 4.3]),
        ),
        (DetailedActivity, {"start_latlng": []}, None),
        (Segment, {"start_latlng": []}, None),
        (SegmentExplorerResult, {"start_latlng": []}, None),
        (ActivityPhoto, {"location": []}, None),
        # TODO re-add this Activity test when custom types are implemented
        # (DetailedActivity, {"timezone": "foobar"}, None),
        (
            DetailedActivity,
            {"start_date_local": "2023-01-17T11:06:07Z"},
            datetime(2023, 1, 17, 11, 6, 7),
        ),
        (
            BaseEffort,
            {"start_date_local": "2023-01-17T11:06:07Z"},
            datetime(2023, 1, 17, 11, 6, 7),
        ),
        (
            Lap,
            {"start_date_local": "2023-01-17T11:06:07Z"},
            datetime(2023, 1, 17, 11, 6, 7),
        ),
        (
            SummarySegmentEffort,
            {"start_date_local": "2023-01-17T11:06:07Z"},
            datetime(2023, 1, 17, 11, 6, 7),
        ),
        (
            SegmentEffort,
            {"start_date_local": "2023-01-17T11:06:07Z"},
            datetime(2023, 1, 17, 11, 6, 7),
        ),
    ),
)
def test_deserialization_edge_cases(model_class, raw, expected_value):
    obj = model_class.model_validate(raw)
    assert getattr(obj, list(raw.keys())[0]) == expected_value


@pytest.mark.parametrize(
    "model_class,raw,parsed_attr,expected_parsed_attr_value",
    (
        (SummarySegmentEffort, {"pr_activity_id": 42}, "activity_id", 42),
        (SummarySegmentEffort, {"activity_id": 42}, "activity_id", 42),
        (
            SummarySegmentEffort,
            {"pr_elapsed_time": 42},
            "elapsed_time",
            42,
        ),
        (
            SummarySegmentEffort,
            {"elapsed_time": 42},
            "elapsed_time",
            42,
        ),
        (AthletePrEffort, {"pr_activity_id": 42}, "activity_id", 42),
        (AthletePrEffort, {"activity_id": 42}, "activity_id", 42),
        (
            AthletePrEffort,
            {"pr_elapsed_time": 42},
            "elapsed_time",
            42,
        ),
        (
            AthletePrEffort,
            {"elapsed_time": 42},
            "elapsed_time",
            42,
        ),
    ),
)
def test_strava_api_field_name_inconsistencies(
    model_class, raw, parsed_attr, expected_parsed_attr_value
):
    obj = model_class.model_validate(raw)
    assert getattr(obj, parsed_attr) == expected_parsed_attr_value


def test_subscription_callback_field_names():
    sub_callback_raw = {
        "hub.mode": "subscribe",
        "hub.verify_token": "STRAVA",
        "hub.challenge": "15f7d1a91c1f40f8a748fd134752feb3",
    }
    sub_callback = SubscriptionCallback.model_validate(sub_callback_raw)
    assert sub_callback.hub_mode == "subscribe"
    assert sub_callback.hub_verify_token == "STRAVA"


# TODO: do we want to continue to support type?
@pytest.mark.parametrize(
    "klass,attr,given_type,expected_type",
    (
        (DetailedActivity, "sport_type", "Run", "Run"),
        (DetailedActivity, "sport_type", "FooBar", "Workout"),
        (DetailedActivity, "type", "Run", "Run"),
        (DetailedActivity, "type", "FooBar", "Workout"),
        (Segment, "activity_type", "Run", "Run"),
        (Segment, "activity_type", "FooBar", "Workout"),
    ),
)
def test_relaxed_activity_type_validation(
    klass, attr, given_type, expected_type
):
    obj = getattr(klass(**{attr: given_type}), attr)
    if attr == "sport_type":
        assert obj == RelaxedSportType(root=expected_type)
    else:
        assert obj == RelaxedActivityType(root=expected_type)


# TODO: these classes are just temporary placeholders and should be replace with
# actual custom types.


class DistanceType:
    pass


class TimeDeltaType:
    pass


class TimezoneType:
    pass


class VelocityType:
    pass


@pytest.mark.skip(reason="not implemented yet")
@pytest.mark.parametrize(
    "model_type,attr,expected_base_type,expected_extended_type",
    (
        (ActivityTotals, "distance", float, DistanceType),
        (ActivityTotals, "elevation_gain", float, DistanceType),
        (ActivityTotals, "elapsed_time", int, TimeDeltaType),
        (ActivityTotals, "moving_time", int, TimeDeltaType),
        (AthleteStats, "biggest_ride_distance", float, DistanceType),
        (AthleteStats, "biggest_climb_elevation_gain", float, DistanceType),
        (Lap, "distance", float, DistanceType),
        (Lap, "total_elevation_gain", float, DistanceType),
        (Lap, "average_speed", float, VelocityType),
        (Lap, "max_speed", float, VelocityType),
        (Lap, "elapsed_time", int, TimeDeltaType),
        (Lap, "moving_time", int, TimeDeltaType),
        (Split, "distance", float, DistanceType),
        (Split, "elevation_difference", float, DistanceType),
        (Split, "average_speed", float, VelocityType),
        (Split, "average_grade_adjusted_speed", float, VelocityType),
        (Split, "elapsed_time", int, TimeDeltaType),
        (Split, "moving_time", int, TimeDeltaType),
        (SegmentExplorerResult, "elev_difference", float, DistanceType),
        (SegmentExplorerResult, "distance", float, DistanceType),
        (AthleteSegmentStats, "distance", float, DistanceType),
        (AthleteSegmentStats, "elapsed_time", int, TimeDeltaType),
        (AthletePrEffort, "distance", float, DistanceType),
        (AthletePrEffort, "pr_elapsed_time", int, TimeDeltaType),
        (Segment, "distance", float, DistanceType),
        (Segment, "elevation_high", float, DistanceType),
        (Segment, "elevation_low", float, DistanceType),
        (Segment, "total_elevation_gain", float, DistanceType),
        (BaseEffort, "distance", float, DistanceType),
        (BaseEffort, "elapsed_time", int, TimeDeltaType),
        (BaseEffort, "moving_time", int, TimeDeltaType),
        (DetailedActivity, "distance", float, DistanceType),
        (DetailedActivity, "timezone", str, TimezoneType),
        (DetailedActivity, "total_elevation_gain", float, DistanceType),
        (DetailedActivity, "average_speed", float, VelocityType),
        (DetailedActivity, "max_speed", float, VelocityType),
        (DetailedActivity, "elapsed_time", int, TimeDeltaType),
        (DetailedActivity, "moving_time", int, TimeDeltaType),
        (Route, "distance", float, DistanceType),
        (Route, "elevation_gain", float, DistanceType),
    ),
)
def test_extended_types(
    model_type, attr, expected_base_type, expected_extended_type
):
    obj = model_type.model_validate(dict(**{attr: 42}))
    assert isinstance(getattr(obj, attr), expected_base_type)
    assert isinstance(getattr(obj, attr), expected_extended_type)


class ModelTest(TestBase):
    def setUp(self):
        super(ModelTest, self).setUp()

    def test_entity_collections(self) -> None:
        """Test that club information parsed from the API in a dict format can
        be correctly ingested into the Athlete model.

        Notes
        -----
        In Pydantic 2.x we use `model_validate` instead of `parse_object`.
        Model_Validate always returns a new model. In this test we
        instantiate a new instance a when calling `model_validate` aligning with
        Pydantic's immutability approach.

        """

        d = {
            "clubs": [
                {"resource_state": 2, "id": 7, "name": "Team Roaring Mouse"},
                {"resource_state": 2, "id": 1, "name": "Team Strava Cycling"},
                {
                    "resource_state": 2,
                    "id": 34444,
                    "name": "Team Strava Cyclocross",
                },
            ]
        }
        a = model.DetailedAthlete.model_validate(d)

        self.assertEqual(3, len(a.clubs))
        self.assertEqual("Team Roaring Mouse", a.clubs[0].name)

    def test_subscription_deser(self):
        d = {
            "id": 1,
            "object_type": "activity",
            "aspect_type": "create",
            "callback_url": "http://you.com/callback/",
            "created_at": "2015-04-29T18:11:09.400558047-07:00",
            "updated_at": "2015-04-29T18:11:09.400558047-07:00",
        }
        sub = model.Subscription.model_validate(d)
        self.assertEqual(d["id"], sub.id)

    def test_subscription_update_deser(self):
        d = {
            "subscription_id": "1",
            "owner_id": 13408,
            "object_id": 12312312312,
            "object_type": "activity",
            "aspect_type": "create",
            "event_time": 1297286541,
        }
        subupd = model.SubscriptionUpdate.model_validate(d)
        self.assertEqual(
            "2011-02-09 21:22:21",
            subupd.event_time.strftime("%Y-%m-%d %H:%M:%S"),
        )


# Test cases for the naive_datetime function
@pytest.mark.parametrize(
    "input_value, expected_output, exception",
    [
        ("2024-04-28T12:00:00Z", datetime(2024, 4, 28, 12, 0), None),
        (
            int(datetime(2022, 4, 28, 12, 0).timestamp()),
            datetime(2022, 4, 28, 12, 0),
            None,
        ),
        (
            str(int(datetime(2022, 4, 28, 12, 0).timestamp())),
            datetime(2022, 4, 28, 12, 0),
            None,
        ),
        (
            datetime(2024, 4, 28, 12, 0, tzinfo=timezone.utc),
            datetime(2024, 4, 28, 12, 0),
            None,
        ),
        (
            "April 28, 2024 12:00 PM UTC",
            datetime(2024, 4, 28, 12, 0),
            None,
        ),
        ("Foo", None, ParserError),
    ],
)
def test_naive_datetime(input_value, expected_output, exception):
    """Make sure our datetime parses properly reformats dates
    in various formats. This test is important given the pydantic
    `parse_datetime` method was removed in 2.x
    # https://docs.pydantic.dev/1.10/usage/types/#datetime-types
    Values
    1. date time as a formatted string
    2. datetime as a UNIX or POSIX format
    """
    if exception:
        with pytest.raises(exception):
            naive_datetime(input_value)
    else:
        assert naive_datetime(input_value) == expected_output
