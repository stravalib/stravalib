from __future__ import absolute_import, unicode_literals

from stravalib.attributes import EntityAttribute, SUMMARY, DETAILED
from stravalib.model import Athlete
from stravalib.tests import TestBase


class EntityAttributeTest(TestBase):

    def setUp(self):
        super(EntityAttributeTest, self).setUp()

    def test_unmarshal_non_ascii_chars(self):
        NON_ASCII_DATA = {
            u'profile': u'http://dgalywyr863hv.cloudfront.net/pictures/athletes/874283/198397/1/large.jpg',
            u'city': u'Ljubljana',
            u'premium': True,
            u'firstname': u'Bla\u017e',
            u'updated_at': u'2014-05-13T06:16:29Z',
            u'lastname': u'Vizjak',
            u'created_at': u'2012-08-01T07:49:43Z',
            u'follower': None,
            u'sex': u'M',
            u'state': u'Ljubljana',
            u'country': u'Slovenia',
            u'resource_state': 2,
            u'profile_medium': u'http://dgalywyr863hv.cloudfront.net/pictures/athletes/874283/198397/1/medium.jpg',
            u'id': 874283,
            u'friend': None
        }
        athlete = EntityAttribute(Athlete, (SUMMARY, DETAILED))
        athlete.unmarshal(NON_ASCII_DATA)
