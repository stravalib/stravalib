from datetime import timedelta
from unittest import skip

import pytest

from stravalib import model
from stravalib import unithelper as uh
from stravalib.model import ActivityTotals, Club
from stravalib.tests import TestBase
from stravalib.unithelper import Quantity, UnitConverter


@pytest.mark.parametrize("model_class,attr,value", ((Club, "name", "foo"),))
class TestLegacyModelSerialization:
    def test_legacy_deserialize(self, model_class, attr, value):
        with pytest.warns(DeprecationWarning):
            model_obj = model_class.deserialize({attr: value})
            assert getattr(model_obj, attr) == value

    def test_legacy_from_dict(self, model_class, attr, value):
        with pytest.warns(DeprecationWarning):
            model_obj = model_class()
            model_obj.from_dict({attr: value})
            assert getattr(model_obj, attr) == value

    def test_legacy_to_dict(self, model_class, attr, value):
        with pytest.warns(DeprecationWarning):
            model_obj = model_class(**{attr: value})
            model_dict_legacy = model_obj.to_dict()
            model_dict_modern = model_obj.dict()
            assert model_dict_legacy == model_dict_modern


@pytest.mark.parametrize(
    "model_class,raw,expected_value,expected_warning",
    (
        (Club, {"name": "foo"}, "foo", None),
        (ActivityTotals, {"elapsed_time": 100}, timedelta(seconds=100), None),
        (
            ActivityTotals,
            {"distance": 100.0},
            UnitConverter("meters")(100.0),
            None,
        ),
    ),
)
def test_backward_compatibility_mixin(
    model_class, raw, expected_value, expected_warning
):
    obj = model_class.parse_obj(raw)
    if expected_warning:
        with pytest.warns(expected_warning):
            assert getattr(obj, list(raw.keys())[0]) == expected_value
    else:
        assert getattr(obj, list(raw.keys())[0]) == expected_value


class ModelTest(TestBase):
    def setUp(self):
        super(ModelTest, self).setUp()

    @skip
    def test_entity_collections(self):
        a = model.Athlete()
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
        a.from_dict(d)

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

    @skip
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
        sub = model.Subscription.deserialize(d)
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
        subupd = model.SubscriptionUpdate.deserialize(d)
        self.assertEqual(
            "2011-02-09 21:22:21",
            subupd.event_time.strftime("%Y-%m-%d %H:%M:%S"),
        )
