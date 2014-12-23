import warnings
import os
import ConfigParser

from stravalib import model
from stravalib.client import Client


from stravalib.tests import TestBase, TESTS_DIR, RESOURCES_DIR

TEST_CFG = os.path.join(TESTS_DIR, 'test.ini')

class FunctionalTestBase(TestBase):
    
    def setUp(self):
        super(FunctionalTestBase, self).setUp()
        if not os.path.exists(TEST_CFG):
            raise Exception("Unable to run the write tests without a test.ini in that defines an access_token with write privs.")
        
        cfg = ConfigParser.SafeConfigParser()
        with open(TEST_CFG) as fp:
            cfg.readfp(fp, 'test.ini')  
            access_token = cfg.get('write_tests', 'access_token')
        
        self.client = Client(access_token=access_token)
    
