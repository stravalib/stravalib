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

Clubs
-------------
.. autosummary::
   :toctree: api/

   MetaClub
   SummaryClub
   DetailedClub

Summary Functions
------------------
.. autosummary::
    :toctree: api/

    check_valid_location
    lazy_property
    naive_datetime


Helper Classes
----------------------
.. autosummary::
    :toctree: api/

    BoundClientEntity

Unit Conversion
--------------------------
.. autosummary::
    :toctree: api/

    Distance
    Duration
    Timezone
    Velocity

Activity Photo Classes
-------------------------
Note: the activity photo classes are defined differently in the Strava spec.
This section will likely need to be updated. These endpoints are not well
documented.

.. autosummary::
    :toctree: api/

    ActivityPhotoPrimary
    ActivityPhoto

Webhook Subscriptions
-------------------------
.. autosummary::
   :toctree: api/

   Subscription
   SubscriptionCallback
   SubscriptionUpdate

Effort / Performance
-----------------------------
.. autosummary::
   :toctree: api/

   Split
   BaseEffort
   BestEffort

Route / Segment Classes
-------------------------
.. autosummary::
   :toctree: api/

   LatLon
   SummarySegment
   Segment
   SegmentEffort
   SegmentEffortAchievement
   SummarySegmentEffort
   SegmentExplorerResult
   Map
   BaseEffort
   BestEffort
   Route
   Stream
