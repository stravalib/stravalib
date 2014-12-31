from stravalib.client import Client
from stravalib.tests import TestBase
import datetime
import pytz

class ClientUtilsTest(TestBase):
    client = Client()

    def test_utc_datetime_to_epoch_utc_datetime_given_correct_epoch_returned(self):
        dt = pytz.utc.localize(datetime.datetime(2014, 1, 1, 0, 0, 0))
        self.assertEquals(1388534400, self.client._utc_datetime_to_epoch(dt))