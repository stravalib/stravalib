from unittest import skip

import pytz

from stravalib.attributes import (
    DETAILED,
    SUMMARY,
    ChoicesAttribute,
    LatLon,
    LocationAttribute,
    TimezoneAttribute,
)
from stravalib.model import Athlete
from stravalib.tests import TestBase


class LocationAttributeTest(TestBase):
    def test_with_location(self):
        location = LocationAttribute((SUMMARY, DETAILED))
        self.assertEqual(LatLon(1.0, 2.0), location.unmarshal([1.0, 2.0]))

    def test_without_location(self):
        location = LocationAttribute((SUMMARY, DETAILED))
        self.assertIsNone(location.unmarshal([]))


class TimezoneAttributeTest(TestBase):
    def test_with_correct_timezone(self):
        timezone = TimezoneAttribute((SUMMARY, DETAILED))
        self.assertEqual(
            pytz.timezone("Europe/Amsterdam"),
            timezone.unmarshal("(GMT+01:00) Europe/Amsterdam"),
        )

    def test_with_incorrect_timezone(self):
        timezone = TimezoneAttribute((SUMMARY, DETAILED))
        # These appear sometimes from Strava
        self.assertIsNone(timezone.unmarshal("(GMT+00:00) Factory"))


@skip
class ChoicesAttributeTest(TestBase):
    def test_no_choices_kwarg_means_choices_empty_dict(self):
        c = ChoicesAttribute(str, (SUMMARY,))
        self.assertEqual(c.choices, {})

    def test_choices_kwarg_init_works(self):
        c = ChoicesAttribute(str, (SUMMARY,), choices={1: "one", 2: "two"})
        self.assertEqual(c.choices, {1: "one", 2: "two"})

    def test_unmarshal_data(self):
        c = ChoicesAttribute(str, (SUMMARY,), choices={1: "one", 2: "two"})
        self.assertEqual(c.unmarshal(2), "two")
        self.assertEqual(c.unmarshal(1), "one")

    def test_unmarshal_val_not_in_choices_gives_sam_val(self):
        # TODO: Test that logging is done as well
        c = ChoicesAttribute(str, (SUMMARY,), choices={1: "one", 2: "two"})
        self.assertEqual(c.unmarshal(0), 0)
        self.assertEqual(c.unmarshal(None), None)

    def test_marshal_data(self):
        c = ChoicesAttribute(str, (SUMMARY,), choices={1: "one", 2: "two"})
        self.assertEqual(c.marshal("two"), 2)
        self.assertEqual(c.marshal("one"), 1)

    def test_marshal_no_key(self):
        c = ChoicesAttribute(str, (SUMMARY,), choices={1: "one", 2: "two"})
        self.assertRaises(NotImplementedError, c.marshal, "zero")

    def test_marshal_too_many_keys(self):
        c = ChoicesAttribute(str, (SUMMARY,), choices={1: "one", 2: "one"})
        self.assertRaises(NotImplementedError, c.marshal, "one")

    def test_with_athlete_type_example_on_model(self):
        a = Athlete.deserialize({"athlete_type": 1})
        self.assertEqual(a.athlete_type, "runner")

    def test_wrong_athlete_type(self):
        # Only allowed options are 0 and 1
        a = Athlete.deserialize({"athlete_type": 100})
        self.assertEqual(a.athlete_type, 100)
