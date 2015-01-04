from __future__ import absolute_import, unicode_literals

from stravalib import model, attributes, unithelper as uh
from stravalib.client import Client
from stravalib.tests.functional import FunctionalTestBase
import datetime

class ClientTest(FunctionalTestBase):
    def test_get_starred_segment(self):
        """
        Test get_starred_segment
        """
        i = 0
        for segment in self.client.get_starred_segment(limit=5):
            self.assertIsInstance(segment, model.Segment)
            i+=1
        self.assertGreater(i, 0) # star at least one segment
        self.assertLessEqual(i, 5)


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

    def test_get_activity_laps(self):
        activity = self.client.get_activity(165094211)
        laps = list(self.client.get_activity_laps(165094211))
        self.assertEquals(5, len(laps))
        # This obviously is far from comprehensive, just a sanity check
        self.assertEquals(u'Lap 1', laps[0].name)
        self.assertEquals(178.0, laps[0].max_heartrate)


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

    def test_activity_photos(self):
        """
        Test photos on activity
        """
        activity = self.client.get_activity(152668627)
        self.assertTrue(activity.photo_count > 0)
        photos = list(activity.photos)
        self.assertEqual(len(photos), 1)
        self.assertEqual(len(photos), activity.photo_count)
        self.assertIsInstance(photos[0], model.ActivityPhoto)

    def test_activity_kudos(self):
        """
        Test kudos on activity
        """
        activity = self.client.get_activity(152668627)
        self.assertTrue(activity.kudos_count > 0)
        kudos = list(activity.kudos)
        self.assertGreater(len(kudos), 6)
        self.assertEqual(len(kudos), activity.kudos_count)
        self.assertIsInstance(kudos[0], model.ActivityKudos )

    def test_activity_streams(self):
        """
        Test activity streams
        """
        stypes = ['time', 'latlng', 'distance','altitude', 'velocity_smooth',
                  'heartrate', 'cadence', 'watts', 'temp', 'moving',
                  'grade_smooth']

        streams = self.client.get_activity_streams(152668627, stypes, 'low')

        self.assertGreater(len(streams.keys()), 3)
        for k in streams.keys():
            self.assertIn(k, stypes)

        # time stream
        self.assertIsInstance(streams['time'].data[0], int)
        self.assertGreater(streams['time'].original_size, 100)
        self.assertEqual(streams['time'].resolution, 'low')
        self.assertEqual(len(streams['time'].data), 100)

        # latlng stream
        self.assertIsInstance(streams['latlng'].data, list)
        self.assertIsInstance(streams['latlng'].data[0][0], float)
        
    def test_related_activities(self):
        """
        Test get_related_activities on an activity and related property of Activity
        """
        activity_id = 152668627
        activity = self.client.get_activity(activity_id)
        related_activities = list(self.client.get_related_activities(activity_id))
        
        # Check the number of related_activities matches what activity would expect
        self.assertEqual(len(related_activities), activity.athlete_count-1)
        
        # Check the related property gives the same result
        related_activities_from_property = list(activity.related)
        self.assertEqual(related_activities, related_activities_from_property)        

    def test_effort_streams(self):
        """
        Test effort streams
        """
        stypes = ['distance']

        activity = self.client.get_activity(165479860) #152668627)
        streams = self.client.get_effort_streams(activity.segment_efforts[0].id,
                                                stypes, 'medium')


        self.assertIn('distance', streams.keys())

        # distance stream
        self.assertIsInstance(streams['distance'].data[0], float) #xxx
        self.assertEqual(streams['distance'].resolution, 'medium')
        self.assertEqual(len(streams['distance'].data),
                         min(1000, streams['distance'].original_size))


    def test_get_curr_athlete(self):
        athlete = self.client.get_athlete()

        print athlete
        self.fail("break")
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

        friends = list(athlete.friends)
        self.assertGreater(len(friends), 1)
        self.assertIsInstance(friends[0], model.Athlete)

        followers = list(athlete.followers)
        self.assertGreater(len(followers), 1)
        self.assertIsInstance(followers[0], model.Athlete)

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

        self.assertEquals(10, len(lb.entries)) # 10 top results
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
        self.assertEquals(10, len(lb)) # 10 top results, 5 bottom results

    def test_get_segment_efforts(self):
        # test with string
        efforts = self.client.get_segment_efforts(4357415,
                                     start_date_local = "2012-12-23T00:00:00Z",
                                     end_date_local   = "2012-12-23T11:00:00Z",)
        print efforts

        i = 0
        for effort in efforts:
            print effort
            self.assertEqual(4357415, effort.segment.id)
            self.assertIsInstance(effort, model.BaseEffort)
            effort_date = effort.start_date_local
            self.assertEqual(effort_date.strftime("%Y-%m-%d"), "2012-12-23")
            i+=1
        print i

        self.assertGreater(i, 2)

        # also test with datetime object
        start_date = datetime.datetime(2012, 12, 31, 6, 0)
        end_date = start_date + datetime.timedelta(hours=12)
        efforts = self.client.get_segment_efforts(4357415,
                                        start_date_local = start_date,
                                        end_date_local = end_date,)
        print efforts

        i = 0
        for effort in efforts:
            print effort
            self.assertEqual(4357415, effort.segment.id)
            self.assertIsInstance(effort, model.BaseEffort)
            effort_date = effort.start_date_local
            self.assertEqual(effort_date.strftime("%Y-%m-%d"), "2012-12-31")
            i+=1
        print i

        self.assertGreater(i, 2)

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

