
from stravalib.protocol.v1 import RideIterator, V1ServerProxy

from stravalib.tests import TestBase

class RideIteratorTest(TestBase):
    
    def setUp(self):
        super(RideIteratorTest, self).setUp()
        self.v1client = V1ServerProxy()
        
    def test_limit(self):
        """ Test setting the limit on iterator. """
        ri = RideIterator(self.v1client, limit=10)
        results = list(ri)
        self.assertEquals(10, len(results))

    def test_more_than_50(self):
        """ Test fetching more than 50 (this should result in multiple fetches). """
        ri = RideIterator(self.v1client, limit=51)
        results = list(ri)
        self.assertEquals(51, len(results))
                          
    def test_empty(self):
        """ Test iterating over empty results. """
        # Specify two thing that we happen to know will return 0 results
        ri = RideIterator(self.v1client, limit=10, club_id=8123, athlete_id=66162)
        results = list(ri)
        self.assertEquals(0, len(results))
    
#    def test_club(self):
#        ri = RideIterator(self.v1client, limit=10, club_id=8123)
#        results = list(ri)
#        #print results
#        # ... I don't really have any anything to positively assert here. the rides are always returned newest-first
#        self.assertEquals(10, len(results))
        