============
GeoDataFrame
============
.. currentmodule:: stravalib

The ``Client`` object class for interacting with the Strava v3 API. While
you can create this object without an access token, you will likely want
to create an access token to authenticate and access most of the Strava data
accessible via the API.

Constructor
-----------
.. autosummary::
   :toctree: api/

   Client

General methods and attributes
-------------------------------

.. autosummary::
   :toctree: api/

   Client.authorization_url
   Client.exchange_code_for_token
   Client.refresh_access_token
   Client.deauthorize
   Client.get_activities
   Client.get_athlete
   Client.get_athlete_friends