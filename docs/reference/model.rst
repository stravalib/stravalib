============
Model
============

.. currentmodule:: stravalib.model


.. We were using automodule here but autosummary was also used
.. automodule supersedes autosummary. but also had an inheritance
.. setting (BaseModel) see below. Testing a custom page that is
.. cleaner to read.
.. .. automodule:: stravalib.model
..     :inherited-members: BaseModel



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
   ActivityPhotoPrimary
   ActivityPhotoMeta
   ActivityPhoto
   Lap
   Split
   RelaxedActivityType
   RelaxedSportType
   Activity
   ActivityComment
   ActivityPhotoPrimary
   ActivityPhotoMeta
   ActivityPhoto
   ActivityKudos
   ActivityLap
   ActivityTotals

Summary Athlete Classes
-------------------------
.. autosummary::
   :toctree: api/

   AthleteStats
   MetaAthlete
   SummaryAthlete
   DetailedAthlete
   AthletePrEffort
   AthleteSegmentStats


Gear Classes
-------------------------
.. autosummary::
   :toctree: api/

   Gear
   Bike
   Shoe

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
