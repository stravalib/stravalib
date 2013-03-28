from __future__ import absolute_import

from stravalib import model
from stravalib.client import Client, IMPERIAL
from stravalib.tests import TestBase

class ClientTest(TestBase):
    
    def setUp(self):
        super(ClientTest, self).setUp()
        self.client = Client(units=IMPERIAL)
    
    def test_get_ride(self):
        """ Test basic ride fetching. """
        ride = self.client.get_ride(34813017)
        self.assertTrue(isinstance(ride, model.Ride))
        self.assertEquals(u'Arlington Big Loop - Windy', ride.name)
        self.assertAlmostEqual(22.52, ride.distance, places=2)
        
        
    def test_get_segment_efforts(self):
        
        efforts = self.client.get_segment_efforts(1154455)
        print efforts
        
        assert False
        
        