import pytz

from stravalib.attributes import (
    DETAILED,
    SUMMARY,
    LatLon,
    LocationAttribute,
    TimezoneAttribute,
)
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
