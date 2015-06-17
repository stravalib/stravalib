from __future__ import absolute_import, unicode_literals

from stravalib.attributes import EntityAttribute, SUMMARY, DETAILED, ChoicesAttribute
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


class ChoicesAttributeTest(TestBase):

    def test_no_choices_kwarg_means_choices_empty_dict(self):
        c = ChoicesAttribute(unicode, (SUMMARY, ))
        self.assertEqual(c.choices, {})

    def test_choices_kwarg_init_works(self):
        c = ChoicesAttribute(unicode, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertEqual(c.choices, {1: "one", 2: "two"})

    def test_unmarshal_data(self):
        c = ChoicesAttribute(unicode, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertEqual(c.unmarshal(2), "two")
        self.assertEqual(c.unmarshal(1), "one")

    def test_unmarshal_val_not_in_choices_gives_sam_val(self):
        # TODO: Test that logging is done as well
        c = ChoicesAttribute(unicode, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertEqual(c.unmarshal(0), 0)
        self.assertEqual(c.unmarshal(None), None)

    def test_marshal_data(self):
        c = ChoicesAttribute(unicode, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertEqual(c.marshal("two"), 2)
        self.assertEqual(c.marshal("one"), 1)

    def test_marshal_no_key(self):
        c = ChoicesAttribute(unicode, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertRaises(NotImplementedError, c.marshal, "zero")

    def test_marshal_too_many_keys(self):
        c = ChoicesAttribute(unicode, (SUMMARY, ), choices={1: "one", 2: "one"})
        self.assertRaises(NotImplementedError, c.marshal, "one")

    def test_with_athlete_type_example_on_model(self):
        a = Athlete.deserialize({"athlete_type": 1})
        self.assertEqual(a.athlete_type, "runner")

    def test_wrong_athlete_type(self):
        # Only allowed options are 0 and 1
        a = Athlete.deserialize({"athlete_type": 100})
        self.assertEqual(a.athlete_type, 100)
