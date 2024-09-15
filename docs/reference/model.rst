============
Model
============
.. currentmodule:: stravalib.model

Athletes
------------------------
.. autosummary::
   :toctree: api/
   :recursive:

    AthleteStats
    MetaAthlete
    SummaryAthlete
    DetailedAthlete
    AthletePrEffort
    AthleteSegmentStats

Activities
-------------------------
.. autosummary::
    :toctree: api/
    :recursive:

    MetaActivity
    SummaryActivity
    DetailedActivity
    ClubActivity
    ActivityTotals
    Lap
    Split
    RelaxedActivityType
    RelaxedSportType
    ActivityZone
    TimedZoneDistribution

Activity Photos
-------------------------
Note: the activity photo classes are defined differently in the Strava spec.
This section will likely need to be updated. These endpoints are not well
documented.

.. autosummary::
    :toctree: api/

    ActivityPhotoPrimary
    ActivityPhoto

Clubs
-------------
.. autosummary::
   :toctree: api/

   MetaClub
   SummaryClub
   DetailedClub

Routes and Segments
-------------------------
.. autosummary::
   :toctree: api/

   LatLon
   SummarySegment
   Segment
   SegmentExplorerResult
   Map
   Route
   Stream

Segment Efforts
-----------------------------
.. autosummary::
   :toctree: api/

   Split
   BaseEffort
   BestEffort
   SegmentEffort
   SegmentEffortAchievement
   SummarySegmentEffort

Webhook Subscriptions
-------------------------
.. autosummary::
   :toctree: api/

   Subscription
   SubscriptionCallback
   SubscriptionUpdate

.. _custom-types-anchor:

Custom Types
--------------------------
.. autosummary::
    :toctree: api/

    Distance
    Duration
    Timezone
    Velocity

Stravalib helpers
-----------------
.. autosummary::
    :toctree: api/

    BoundClientEntity
    naive_datetime
    lazy_property
    check_valid_location
