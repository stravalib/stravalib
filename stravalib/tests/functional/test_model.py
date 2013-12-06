from __future__ import absolute_import, unicode_literals

from stravalib import model
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
        