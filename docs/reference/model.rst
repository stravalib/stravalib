============
Model
============

.. currentmodule:: stravalib.model

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

Unit & Conversion Classes
--------------------------
.. autosummary::
    :toctree: api/

    Distance
    Duration
    Timezone
    Velocity

Summary Activity Classes
-------------------------
.. autosummary::
    :toctree: api/

    MetaActivity
    SummaryActivity
    DetailedActivity
    ClubActivity
    TimedZoneDistribution
    ActivityZone
    ActivityTotals
    ActivityComment
    Lap
    Split
    RelaxedActivityType
    RelaxedSportType

Activity Photo Classes
-------------------------
Note: the activity photo classes are defined differently in the Strava spec.
This section will likely need to be updated. These endpoints are not well
documented.

.. autosummary::
    :toctree: api/

    ActivityPhotoPrimary
    ActivityPhotoMeta
    ActivityPhoto

Summary Athlete Classes
------------------------
.. autosummary::
   :toctree: api/

   AthleteStats
   MetaAthlete
   SummaryAthlete
   DetailedAthlete
   AthletePrEffort
   AthleteSegmentStats

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
   Map
   SegmentExplorerResult
   BaseEffort
   BestEffort
   Route
   Stream



Subscription Classes
-------------------------
.. autosummary::
   :toctree: api/

   Subscription
   SubscriptionCallback
   SubscriptionUpdate

Club / Effort / Performance Classes
------------------------------------
   Split
   Club
   BaseEffort
   BestEffort
   DistributionBucket
   BaseActivityZone

Club Classes
-------------
   MetaClub
   SummaryClub
   DetailedClub
