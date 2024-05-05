from datetime import datetime
from typing import List, Optional

import pint
import pytest
from pydantic import BaseModel

from stravalib import model
from stravalib import unithelper as uh
from stravalib.model import (
    Activity,
    ActivityLap,
    ActivityPhoto,
    BackwardCompatibilityMixin,
    BaseEffort,
    BoundClientEntity,
    # Club, # CLUB IS not currently used in this module
    LatLon,
    RelaxedActivityType,
    RelaxedSportType,
    Segment,
    SegmentExplorerResult,
    SubscriptionCallback,
)
from stravalib.strava_model import LatLng
from stravalib.tests import TestBase
from stravalib.unithelper import Quantity


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
        (Activity, {"timezone": "foobar"}, None),
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
    ),
)
def test_deserialization_edge_cases(model_class, raw, expected_value):
    obj = model_class.model_validate(raw)
    assert getattr(obj, list(raw.keys())[0]) == expected_value


def test_subscription_callback_field_names():
    sub_callback_raw = {
        "hub.mode": "subscribe",
        "hub.verify_token": "STRAVA",
        "hub.challenge": "15f7d1a91c1f40f8a748fd134752feb3",
    }
    sub_callback = SubscriptionCallback.model_validate(sub_callback_raw)
    assert sub_callback.hub_mode == "subscribe"
    assert sub_callback.hub_verify_token == "STRAVA"


# Below are some toy classes to test type extensions and attribute lookup:
class A(BaseModel, BackwardCompatibilityMixin):
    x: Optional[int] = None


class ConversionA(A, BackwardCompatibilityMixin):
    _field_conversions = {"x": uh.meters}


class BoundA(A, BoundClientEntity):
    pass


class B(BaseModel, BackwardCompatibilityMixin):
    a: Optional[A] = None
    bound_a: Optional[BoundA] = None


class BoundB(B, BoundClientEntity):
    pass


class C(BaseModel, BackwardCompatibilityMixin):
    a: Optional[List[A]] = None
    bound_a: Optional[List[BoundA]] = None


class BoundC(C, BoundClientEntity):
    pass


class D(BaseModel, BackwardCompatibilityMixin):
    a: Optional[LatLng] = None


class ExtA(A):
    def foo(self):
        return self.x


class ExtLatLng(LatLng):
    def foo(self):
        return f"[{self[0], self[1]}]"


@pytest.mark.parametrize(
    "lookup_expression,expected_result,expected_bound_client",
    (
        (A().x, None, False),
        (B().a, None, False),
        (A(x=1).x, 1, False),
        (B(a=A(x=1)).a, A(x=1), False),
        (C(a=[A(x=1), A(x=2)]).a[1], A(x=2), False),
        (ConversionA(x=1).x, pint.Quantity("1 meter"), False),
        (BoundA(x=1).x, 1, False),
        (B(bound_a=BoundA(x=1)).bound_a, BoundA(x=1), None),
        (
            B(bound_a=BoundA(x=1, bound_client=1)).bound_a,
            BoundA(x=1, bound_client=1),
            True,
        ),
        (BoundB(a=A(x=1)).a, A(x=1), False),
        (BoundB(a=A(x=1), bound_client=1).a, A(x=1), False),
        (BoundB(bound_a=BoundA(x=1)).bound_a, BoundA(x=1), None),
        (
            BoundB(bound_a=BoundA(x=1), bound_client=1).bound_a,
            BoundA(x=1, bound_client=1),
            True,
        ),
        (C(bound_a=[BoundA(x=1), BoundA(x=2)]).bound_a[1], BoundA(x=2), None),
        (
            C(
                bound_a=[
                    BoundA(x=1, bound_client=1),
                    BoundA(x=2, bound_client=1),
                ]
            ).bound_a[1],
            BoundA(x=2, bound_client=1),
            True,
        ),
        (BoundC(a=[A(x=1), A(x=2)]).a[1], A(x=2), False),
        (BoundC(a=[A(x=1), A(x=2)], bound_client=1).a[1], A(x=2), False),
        (
            BoundC(bound_a=[BoundA(x=1), BoundA(x=2)]).bound_a[1],
            BoundA(x=2),
            None,
        ),
        (
            BoundC(bound_a=[BoundA(x=1), BoundA(x=2)], bound_client=1).bound_a[
                1
            ],
            BoundA(x=2, bound_client=1),
            True,
        ),
    ),
)
def test_backward_compatible_attribute_lookup(
    lookup_expression, expected_result, expected_bound_client
):
    assert lookup_expression == expected_result

    if expected_bound_client:
        assert lookup_expression.bound_client is not None
    elif expected_bound_client is None:
        assert lookup_expression.bound_client is None
    elif not expected_bound_client:
        assert not hasattr(lookup_expression, "bound_client")


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
    print(expected_type)
    obj = getattr(klass(**{attr: given_type}), attr)
    if attr == "sport_type":
        assert obj == RelaxedSportType(root=expected_type)
    else:
        assert obj == RelaxedActivityType(root=expected_type)


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

    def test_speed_units(self):
        a = model.Activity()

        a.max_speed = 1000  # m/s
        a.average_speed = 1000  # m/s
        self.assertAlmostEqual(3600.0, float(uh.kph(a.max_speed)))
        self.assertAlmostEqual(3600.0, float(uh.kph(a.average_speed)))

        a.max_speed = uh.mph(1.0)
        # print repr(a.max_speed)

        self.assertAlmostEqual(1.61, float(uh.kph(a.max_speed)), places=2)

    def test_time_intervals(self):
        segment = model.Segment()
        # s.pr_time = XXXX

        split = model.Split()
        split.moving_time = 3.1
        split.elapsed_time = 5.73

    def test_distance_units(self):
        # Gear
        g = model.Gear()
        g.distance = 1000
        self.assertEqual(1.0, float(uh.kilometers(g.distance)))

        # Metric Split
        split = model.Split()
        split.distance = 1000  # meters
        split.elevation_difference = 1000  # meters
        self.assertIsInstance(split.distance, Quantity)
        self.assertIsInstance(split.elevation_difference, Quantity)
        self.assertEqual(1.0, float(uh.kilometers(split.distance)))
        self.assertEqual(1.0, float(uh.kilometers(split.elevation_difference)))
        split = None

        # Segment
        s = model.Segment()
        s.distance = 1000
        s.elevation_high = 2000
        s.elevation_low = 1000
        self.assertIsInstance(s.distance, Quantity)
        self.assertIsInstance(s.elevation_high, Quantity)
        self.assertIsInstance(s.elevation_low, Quantity)
        self.assertEqual(1.0, float(uh.kilometers(s.distance)))
        self.assertEqual(2.0, float(uh.kilometers(s.elevation_high)))
        self.assertEqual(1.0, float(uh.kilometers(s.elevation_low)))

        # Activity
        a = model.Activity()
        a.distance = 1000  # m
        a.total_elevation_gain = 1000  # m
        self.assertIsInstance(a.distance, Quantity)
        self.assertIsInstance(a.total_elevation_gain, Quantity)
        self.assertEqual(1.0, float(uh.kilometers(a.distance)))
        self.assertEqual(1.0, float(uh.kilometers(a.total_elevation_gain)))

    def test_weight_units(self):
        """ """
        # PowerActivityZone

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
