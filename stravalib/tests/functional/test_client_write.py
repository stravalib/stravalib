from __future__ import absolute_import, unicode_literals
import os
import ConfigParser
from datetime import datetime, timedelta

from stravalib import model, attributes, unithelper as uh
from stravalib.client import Client
from stravalib.tests import TestBase, TESTS_DIR

TEST_CFG = os.path.join(TESTS_DIR, 'test.ini')

class ClientWriteTest(TestBase):
    
    def setUp(self):
        if not os.path.exists(TEST_CFG):
            raise Exception("Unable to run the write tests without a tests.ini that defines an access_token with write privs.")
        
        cfg = ConfigParser.SafeConfigParser()
        with open(TEST_CFG) as fp:
            cfg.readfp(fp, 'test.ini')  
            access_token = cfg.get('write_tests', 'access_token')
        
        self.client = Client(access_token=access_token)
    
    def test_create_activity(self):
        """
        Test Client.create_activity simple case.
        """
        now = datetime.now().replace(microsecond=0)
        a = self.client.create_activity("test_create_activity#simple",
                                        activity_type=model.Activity.RIDE,
                                        start_date_local=now,
                                        elapsed_time=timedelta(hours=3, minutes=4, seconds=5),
                                        distance=uh.miles(15.2))
        print a
        
        self.assertIsInstance(a, model.Activity)
        self.assertEquals("test_create_activity#simple", a.name)
        self.assertEquals(now, a.start_date_local)
        self.assertEquals(round(float(uh.miles(15.2)), 2), round(float(uh.miles(a.distance)), 2))
        self.assertEquals(timedelta(hours=3, minutes=4, seconds=5), a.elapsed_time)
        