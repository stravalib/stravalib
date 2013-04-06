from __future__ import absolute_import

from stravalib import model
from stravalib.client import Client, IMPERIAL
from stravalib.tests import TestBase

class ModelTest(TestBase):
    
    def setUp(self):
        super(ModelTest, self).setUp()
        self.client = Client(units=IMPERIAL)
    
    def test_ride(self):
        """ Test ride properties. """
        ride = self.client.get_ride(34813017)
        
        self.assertTrue(isinstance(ride, model.Ride))
        self.assertEquals(u'Arlington Big Loop - Windy', ride.name)
        self.assertAlmostEqual(22.52, ride.distance, places=2)
        
        
        self.assertTrue(isinstance(ride.athlete, model.Athlete))
        self.assertEquals(u'Hans Lellelid', ride.athlete.name)
        
        #print ride.efforts
        segment = ride.efforts[0].segment
        self.assertTrue(isinstance(segment, model.Segment))
        
    def test_club(self):
        """ Test club properties. """
        # {"clubs":[{"name":"Mission Cycling","id":15}]}
        club = self.client.get_club(15)
        
        self.assertEquals('Mission Cycling', club.name)
        self.assertEquals('San Francisco, California', club.location)
        
        club = self.client.get_clubs('mission')[0]
        self.assertEqual(None, club.location)
        club.hydrate()
        self.assertNotEqual(None, club.location)
        
    