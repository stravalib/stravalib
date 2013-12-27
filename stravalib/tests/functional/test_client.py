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
        self.assertAlmostEquals(-120.4357631, activity.start_latlng.lon, places=2)
        self.assertAlmostEquals(38.74263759999999, activity.start_latlng.lat, places=2)
        
        self.assertIsInstance(activity.map, model.Map)
        
        self.assertIsInstance(activity.athlete, model.Athlete)
        self.assertEquals(1513, activity.athlete.id)
        
        #self.assertAlmostEqual(first, second, places, msg, delta)
        # Ensure that iw as read in with correct units
        self.assertEquals(22.5308, float(uh.kilometers(activity.distance)))

    def test_get_activity_zones(self):
        """
        Test loading zones for activity.
        """
        zones = self.client.get_activity_zones(99895560)
        print zones
        self.assertEquals(1, len(zones))
        self.assertIsInstance(zones[0], model.PaceActivityZone)
        
        # Indirectly
        activity = self.client.get_activity(99895560)
        self.assertEquals(len(zones), len(activity.zones))
        self.assertEquals(zones[0].score, activity.zones[0].score)
        
    def test_activity_comments(self):
        """
        Test loading comments for already-loaded activity.
        """
        activity = self.client.get_activity(2290897)
        self.assertTrue(activity.comment_count > 0)
        comments= list(activity.comments)
        self.assertEquals(3, len(comments))
        self.assertEquals("I love Gordo's. I've been eating there for 20 years!", comments[0].text)
            
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
        
        clubs_indirect = self.client.get_athlete().clubs
        self.assertEquals(3, len(clubs_indirect))
        self.assertEquals(clubs[0].name, clubs_indirect[0].name)
        self.assertEquals(clubs[1].name, clubs_indirect[1].name)
        self.assertEquals(clubs[2].name, clubs_indirect[2].name)
        
        
    def test_get_gear(self):
        g = self.client.get_gear("g69911")
        self.assertTrue(float(g.distance) >= 3264.67)
        self.assertEquals('Salomon XT Wings 2', g.name)
        self.assertEquals('Salomon', g.brand_name)
        self.assertTrue(g.primary)
        self.assertEquals(model.DETAILED, g.resource_state)
        self.assertEquals('g69911', g.id)
        self.assertEquals('XT Wings 2', g.model_name)
        self.assertEquals('', g.description)

    def test_get_segment_leaderboard(self):
        lb = self.client.get_segment_leaderboard(229781)
        print(lb.effort_count)
        print(lb.entry_count)
        for i,e in enumerate(lb):
            print '{0}: {1}'.format(i, e)
                
        self.assertEquals(15, len(lb.entries)) # 10 top results, 5 bottom results
        self.assertIsInstance(lb.entries[0], model.SegmentLeaderboardEntry)
        self.assertEquals(1, lb.entries[0].rank)
        self.assertTrue(lb.effort_count > 8000) # At time of writing 8206
        
        # Check the relationships
        athlete = lb[0].athlete
        print(athlete)
        self.assertEquals(lb[0].athlete_name, "{0} {1}".format(athlete.firstname, athlete.lastname))
        
        effort = lb[0].effort
        print effort
        self.assertIsInstance(effort, model.SegmentEffort)
        self.assertEquals('Hawk Hill', effort.name)
        
        activity = lb[0].activity
        self.assertIsInstance(activity, model.Activity)
        # Can't assert much since #1 ranked activity will likely change in the future.
        
    def test_get_segment(self):
        segment = self.client.get_segment(229781)
        self.assertIsInstance(segment, model.Segment)
        print segment
        self.assertEquals('Hawk Hill', segment.name)
        self.assertAlmostEqual(2.68, float(uh.kilometers(segment.distance)), places=2)
        
        # Fetch leaderboard
        lb = segment.leaderboard
        self.assertEquals(15, len(lb)) # 10 top results, 5 bottom results
        
    
    def test_segment_explorer(self):
        bounds = (37.821362,-122.505373,37.842038,-122.465977)
        results = self.client.explore_segments(bounds)
        
        # This might be brittle
        self.assertEquals('Hawk Hill', results[0].name)
        
        # Fetch full segment
        segment = results[0].segment
        self.assertEquals(results[0].name, segment.name)
        
        # For some reason these don't follow the simple math rules one might expect (so we round to int)
        self.assertAlmostEqual(results[0].elev_difference, segment.elevation_high - segment.elevation_low, places=0)
        