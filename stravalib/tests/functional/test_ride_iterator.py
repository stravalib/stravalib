import functools

from stravalib.protocol.v1 import BatchedResultsIterator, ApiV1Client

from stravalib.tests import TestBase

class RideIteratorTest(TestBase):
    
    def setUp(self):
        super(RideIteratorTest, self).setUp()
        self.v1client = ApiV1Client(units='imperial')
        
    def test_limit(self):
        """ Test setting the limit on iterator. """
        ri = BatchedResultsIterator(self.v1client.get_rides, limit=10)
        results = list(ri)
        self.assertEquals(10, len(results))

    def test_more_than_50(self):
        """ Test fetching more than 50 (this should result in multiple fetches). """
        ri = BatchedResultsIterator(self.v1client.get_rides, limit=51)
        results = list(ri)
        self.assertEquals(51, len(results))
                          
    def test_empty(self):
        """ Test iterating over empty results. """
        # Specify two thing that we happen to know will return 0 results
        ri = BatchedResultsIterator(functools.partial(self.v1client.get_rides, club_id=8123, athlete_id=66162), limit=10)
        results = list(ri)
        self.assertEquals(0, len(results))
    
#    def test_club(self):
#        ri = RideIterator(self.v1client, limit=10, club_id=8123)
#        results = list(ri)
#        #print results
#        # ... I don't really have any anything to positively assert here. the rides are always returned newest-first
#        self.assertEquals(10, len(results))
        