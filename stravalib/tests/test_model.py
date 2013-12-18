from __future__ import absolute_import, unicode_literals

from stravalib import model
from stravalib import unithelper as uh
from stravalib.tests import TestBase

class ModelTest(TestBase):
    
    def setUp(self):
        super(ModelTest, self).setUp()
    
    def test_entity_collections(self):
        
        a = model.Athlete()
        d = {'clubs': [{'resource_state': 2, 'id': 7, 'name': 'Team Roaring Mouse'},
                   {'resource_state': 2, 'id': 1, 'name': 'Team Strava Cycling'},
                   {'resource_state': 2, 'id': 34444, 'name': 'Team Strava Cyclocross'}]
        }
        a.from_dict(d)
        
        self.assertEquals(3, len(a.clubs))
        self.assertEquals('Team Roaring Mouse', a.clubs[0].name)
    
    def test_speed_units(self):
        a = model.Activity()
        
        a.max_speed = 1000 # m/s
        a.average_speed = 1000 # m/s
        self.assertEquals(3600.0, float(uh.kph(a.max_speed)))
        self.assertEquals(3600.0, float(uh.kph(a.average_speed)))
        
        a.max_speed = uh.mph(1.0)
        #print repr(a.max_speed)
        
        self.assertAlmostEqual(1.61, float(uh.kph(a.max_speed)), places=2)
        

    def test_distance_units(self):
        a = model.Activity()
        
        a.distance = 1000 # m
        self.assertEquals(1.0, float(uh.kilometers(a.distance)))
        