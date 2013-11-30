from stravalib import model
from stravalib.client import Client, STANDARD

from stravalib.tests import TestBase

TEST_ACCESS_TOKEN = "83ebeabdec09f6670863766f792ead24d61fe3f9"

class FunctionalTestBase(TestBase):
    
    def setUp(self):
        super(FunctionalTestBase, self).setUp()
        self.client = Client(units=STANDARD)
        self.client.