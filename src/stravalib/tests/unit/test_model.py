from datetime import datetime, timedelta

import pytest

from stravalib import model
from stravalib.model import (
    Activity,
    ActivityLap,
    ActivityPhoto,
    ActivityTotals,
    AthletePrEffort,
    AthleteSegmentStats,
    AthleteStats,
    BaseEffort,
    # Club, # CLUB IS not currently used in this module
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
)
from stravalib.tests import TestBase


@pytest.mark.parametrize(
    "model_class,raw,expected_value",
    (
        (
            # Removing root
            Activity,
            {"start_latlng": "5.4,4.3"},
            LatLon([5.4, 4.3]),
        ),  # pydantic 2.x uses root and may
        (Activity, {"start_latlng": []}, None),
        (Segment, {"start_latlng": []}, None),
        (SegmentExplorerResult, {"start_latlng": []}, None),
        (ActivityPhoto, {"location": []}, None),
        # (Activity, {"timezone": "foobar"}, None),  TODO re-add this test when custom types are implemented
        (
            Activity,
            {"start_date_local": "2023-01-17T11:06:07Z"},
            datetime(2023, 1, 17, 11, 6, 7),
        ),
        (
            BaseEffort,
            {"start_date_local": "2023-01-17T11:06:07Z"},
            datetime(2023, 1, 17, 11, 6, 7),
        ),
        (
            ActivityLap,
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
            timedelta(seconds=42),
        ),
        (
            SummarySegmentEffort,
            {"elapsed_time": 42},
            "elapsed_time",
            timedelta(seconds=42),
        ),
        (AthletePrEffort, {"pr_activity_id": 42}, "activity_id", 42),
        (AthletePrEffort, {"activity_id": 42}, "activity_id", 42),
        (
            AthletePrEffort,
            {"pr_elapsed_time": 42},
            "elapsed_time",
            timedelta(seconds=42),
        ),
        (
            AthletePrEffort,
            {"elapsed_time": 42},
            "elapsed_time",
            timedelta(seconds=42),
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
        (Activity, "sport_type", "Run", "Run"),
        (Activity, "sport_type", "FooBar", "Workout"),
        (Activity, "type", "Run", "Run"),
        (Activity, "type", "FooBar", "Workout"),
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
        (ActivityLap, "distance", float, DistanceType),
        (ActivityLap, "total_elevation_gain", float, DistanceType),
        (ActivityLap, "average_speed", float, VelocityType),
        (ActivityLap, "max_speed", float, VelocityType),
        (ActivityLap, "elapsed_time", int, TimeDeltaType),
        (ActivityLap, "moving_time", int, TimeDeltaType),
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
        (Activity, "distance", float, DistanceType),
        (Activity, "timezone", str, TimezoneType),
        (Activity, "total_elevation_gain", float, DistanceType),
        (Activity, "average_speed", float, VelocityType),
        (Activity, "max_speed", float, VelocityType),
        (Activity, "elapsed_time", int, TimeDeltaType),
        (Activity, "moving_time", int, TimeDeltaType),
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
        In Pydantic 2.x we use model_validate instead of parse_object.
        Model_Validate always returns a new model. so in this test we
        instantiate a new instance a when calling model_validate aligning with
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
        a = model.Athlete.model_validate(d)

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
