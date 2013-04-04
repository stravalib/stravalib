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
        
    def test_get_club(self):
        club = self.client.get_club(15)
        self.assertEquals('Mission Cycling', club.name)
        self.assertEquals('San Francisco, California', club.location)
            
    def test_get_clubs(self):
        clubs = self.client.get_clubs('mission')
        self.assertTrue(len(clubs) > 1)
        self.assertEquals(None, clubs[0].location)
        
        clubs = self.client.get_clubs('mission', full_objects=True)
        self.assertTrue(len(clubs) > 1)
        self.assertNotEqual(None, clubs[0].location)
        