from __future__ import absolute_import, unicode_literals

from stravalib import model, attributes, unithelper as uh
from stravalib.client import Client
from stravalib.tests.functional import FunctionalTestBase

class ClientTest(FunctionalTestBase):
    
    def test_get_activity(self):
        """ Test basic activity fetching. """
        activity = self.client.get_activity(96089609)
        self.assertEquals('El Dorado County, CA, USA', activity.location_city)
        
        self.assertIsInstance(activity.start_latlng, attributes.LatLon)
        self.assertEquals(-120.4357631, activity.start_latlng.lon)
        self.assertEquals(38.74263759999999, activity.start_latlng.lat)
        
        self.assertIsInstance(activity.map, model.Map)
        
        self.assertIsInstance(activity.athlete, model.Athlete)
        self.assertEquals(1513, activity.athlete.id)
        
        #self.assertAlmostEqual(first, second, places, msg, delta)
        # Ensure that iw as read in with correct units
        self.assertEquals(22.5308, float(uh.kilometers(activity.distance)))
        
    def test_get_curr_athlete(self):
        athlete = self.client.get_athlete()
        
        # Just some basic sanity checks here
        self.assertEquals('Jeff', athlete.firstname)
        self.assertEquals('Remer', athlete.lastname)
        self.assertEquals(3, len(athlete.clubs))
        self.assertEquals('Team Roaring Mouse', athlete.clubs[0].name)
        
        self.assertEquals(1, len(athlete.shoes))
        print athlete.shoes
        
        self.assertIsInstance(athlete.shoes[0], model.Shoe)
        self.assertIsInstance(athlete.clubs[0], model.Club)
        self.assertIsInstance(athlete.bikes[0], model.Bike)
        
    def test_get_athlete_clubs(self):
        clubs = self.client.get_athlete_clubs()
        self.assertEquals(3, len(clubs))
        self.assertEquals('Team Roaring Mouse', clubs[0].name)
        self.assertEquals('Team Strava Cycling', clubs[1].name)
        self.assertEquals('Team Strava Cyclocross', clubs[2].name)
        
    def test_get_gear(self):
        g = self.client.get_gear("g69911")
        self.assertAlmostEqual(3264.67, g.distance, places=2)
        self.assertEquals('Salomon XT Wings 2', g.name)
        self.assertEquals('Salomon', g.brand_name)
        self.assertTrue(g.primary)
        self.assertEquals(model.DETAILED, g.resource_state)
        self.assertEquals('g69911', g.id)
        self.assertEquals('XT Wings 2', g.model_name)
        self.assertEquals('', g.description)
        
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