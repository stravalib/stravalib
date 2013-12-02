from __future__ import absolute_import, unicode_literals

from stravalib import model, attributes
from stravalib.client import Client
from stravalib.tests.functional import FunctionalTestBase

class ClientTest(FunctionalTestBase):
    
    def test_get_activity(self):
        """ Test basic ride fetching. """
        activity = self.client.get_activity(96089609)
        self.assertEquals('El Dorado County, CA, USA', activity.location_city)
        
        self.assertIsInstance(activity.start_latlng, attributes.LatLon)
        self.assertEquals(-120.4357631, activity.start_latlng.lon)
        self.assertEquals(38.74263759999999, activity.start_latlng.lat)
        print activity
        print activity.__dict__
        assert False
        #self.assertTrue(isinstance(ride, model.Ride))
        #self.assertEquals(u'Arlington Big Loop - Windy', ride.name)
        #self.assertAlmostEqual(22.52, ride.distance, places=2)
        
    def test_get_club(self):
        club = self.client.get_club(15)
        self.assertEquals('Mission Cycling', club.name)
        
"""            
    def test_get_clubs(self):
        clubs = self.client.get_clubs('mission')
        self.assertTrue(len(clubs) > 1)
        self.assertEquals(None, clubs[0].location)
        
        clubs = self.client.get_clubs('mission', full_objects=True)
        self.assertTrue(len(clubs) > 1)
        self.assertNotEqual(None, clubs[0].location)
    
    def test_get_segment(self):
        segment_id = 708743
        segment = self.client.get_segment(segment_id)
        self.assertTrue('Rosslyn' in segment.name)
        self.assertTrue(segment.end_latlng is None)
        
        segment2 = self.client.get_segment(segment_id, include_geo=True)
        self.assertEquals(segment.id, segment2.id)
        self.assertEquals(segment.name, segment2.name)
        self.assertTrue(segment2.start_latlng is not None)
        self.assertTrue(segment2.end_latlng is not None)
"""