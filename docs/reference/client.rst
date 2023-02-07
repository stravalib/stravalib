============
Client
============
.. currentmodule:: stravalib.client

The ``Client`` object class for interacting with the Strava v3 API. While
you can create this object without an access token, you will likely want
to create an access token to authenticate and access most of the Strava data
accessible via the API.


Main Classes
-------------
.. autosummary::
   :toctree: api/

   Client
   BatchedResultsIterator
   ActivityUploader


General methods and attributes
-------------------------------

.. autosummary::
   :toctree: api/

   Client.authorization_url
   Client.exchange_code_for_token
   Client.refresh_access_token
   Client.deauthorize

Athlete methods
-----------------
.. autosummary::
   :toctree: api/

   Client.get_activities
   Client.get_athlete
   Client.update_athlete
   Client.get_athlete_koms
   Client.get_athlete_stats
   Client.get_athlete_clubs
   Client.get_gear

Club related methods
--------------------
.. autosummary::
   :toctree: api/

   Client.join_club
   Client.leave_club
   Client.get_club
   Client.get_club_members
   Client.get_club_activities

Activity related methods
-------------------------
.. autosummary::
   :toctree: api/

   Client.get_activity
   Client.get_friend_activities
   Client.create_activity
   Client.update_activity
   Client.upload_activity
   Client.delete_activity
   Client.get_activity_zones
   Client.get_activity_comments
   Client.get_activity_kudos
   Client.get_activity_photos
   Client.get_activity_laps
   Client.get_related_activities

Segment related methods
-------------------------
.. autosummary::
   :toctree: api/

   Client.get_segment_effort
   Client.get_segment
   Client.get_starred_segments
   Client.get_athlete_starred_segments
   Client.get_segment_efforts
   Client.explore_segments

Stream related methods
-------------------------

.. autosummary::
   :toctree: api/

   Client.get_activity_streams
   Client.get_effort_streams
   Client.get_segment_streams

Route related methods
----------------------

.. autosummary::
   :toctree: api/

   Client.get_routes
   Client.get_route
   Client.get_route_streams

Subscription related methods
-----------------------------

.. autosummary::
   :toctree: api/

   Client.create_subscription
   Client.handle_subscription_callback
   Client.handle_subscription_update
   Client.list_subscriptions
   Client.delete_subscription


Activity Uploader Constructor
-----------------------------
.. autosummary::
   :toctree: api/

   ActivityUploader

ActivityUploader methods
---------------------------

.. autosummary::
   :toctree: api/

   ActivityUploader.update_from_response
