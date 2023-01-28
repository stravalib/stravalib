.. _athletes:

Athletes
********

This page is designed to mirror the structure of the documentation at
https://developers.strava.com/docs/reference/#api-Athletes and
describe the methods for working with athlete data in the Strava API.

Retrieve Current Athlete
========================

This is the simplest request.  It is provided by the :meth:`stravalib.client.Client.get_athlete` when called
with no parameters.::

   athlete = client.get_athlete()
   print("Hello, {}".format(athlete.firstname))

See the :class:`stravalib.model.Athlete` class for details on what is returned.  For this method, full detailed-level
attribute set is returned.

Retrieve Another Athlete
========================

A variation on the above request, this is provided by the :meth:`stravalib.client.Client.get_athlete` when called
with an athlete ID.::

   athlete = client.get_athlete(227615)
   print("Hello, {}".format(athlete.firstname))

See the :class:`stravalib.model.Athlete` class for details.  only summary-level subset of attributes is returned
when fetching information about another athlete.

Update Current Athlete
======================

(This is not yet implemented by stravalib.)
