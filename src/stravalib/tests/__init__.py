import os.path

# Removing unittest - exception for python  < 3.0 as we no longer support it
from unittest import TestCase

TESTS_DIR = os.path.dirname(__file__)
RESOURCES_DIR = os.path.join(TESTS_DIR, "resources")


class TestBase(TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
