import os.path
import sys

if sys.version_info < (2, 7):
    # TODO: We can probably add this smartly to setup.py
    try:
        from unittest2 import TestCase
    except ImportError:
        raise Exception("Need unittest2 for running tests under python 2.6")
else:
    from unittest import TestCase

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), 'resources')


class TestBase(TestCase):
    
    def setUp(self):
        super(TestBase, self).setUp()
        
    def tearDown(self):
        super(TestBase, self).tearDown()