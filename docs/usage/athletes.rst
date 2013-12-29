.. _athletes:

Athletes
********

This page is designed to mirror the structure of the documentation at http://strava.github.io/api/v3/athlete/ and
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

Friends and Followers
=====================

Strava allows fetching both an athlete's friends and those that are following (have friended) the specified athlete.

List athlete friends
--------------------

The :meth:`stravalib.client.Client.get_athete_friends` method may be called with our without an athlete ID parameter,
depending on whether the friends for another or the current athlete (respectively) are being requested.::

   johns_friends = client.get_athlete_friends(227615)
   for a in johns_friends:
      print("{} is john's friend.".format(a.firstname))
   
   # Now do the same for the currently authenticated athlete
   friends = client.get_athlete_friends()
   for a in friends:
      print("{} is your friend.".format(a.firstname))

List athlete followers
----------------------

Listing followers works basically the same as listing friends, and is effectively showing the inverse.::

   johns_followers = client.get_athlete_followers(227615)
   for a in johns_followers:
      print("{} is following john.".format(a.firstname))
   
   # Now do the same for the currently authenticated athlete
   friends = client.get_athlete_followers()
   for a in followers:
      print("{} is following you.".format(a.firstname))
 

Update Current Athlete
======================

(This is not yet implemented by stravalib.)