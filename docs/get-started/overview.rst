.. _overview:

Usage Overview
**************

The :class:`stravalib.client.Client` class exposes methods that loosely correspond
with the REST methods exposed by the Strava API.

Retrieving Single Entities
==========================

The simplest case are the client methods that return single entities. The entity object
types are instances of :mod:`stravalib.model` classes. For example::

   client = Client(access_token=JOHNS_ACCESS_TOKEN)
   athlete = client.get_athlete() # Get John's full athlete record
   print("Hello, {}. I know your email is {}".format(athlete.firstname, athlete.email))
   # "Hello, John.  I know your email is john@example.com"

Entity Resource States
----------------------

Entities in Strava's API exist at different detail levels, denoted by the numeric
`resource_state` attribute (1=metadata, 2=summary, 3=detailed).  In general, detail level
3 ("detailed") is only available to the user that is authenticated.  Detail level 2 ("summary")
information is available to others.  For example::

   other_athlete = client.get_athlete(123) # Some other Athlete ID
   other_athlete.firstname  # This is accessible
   # But this is not:
   # other_athlete.email


Retrieving Entity Result Sets
=============================

A number of Strava API endpoints return paged results.  The stravalib library abstracts over
the paging to provide an iterator that will iterate over the entire resultset, fetching 200-page
result sets under the hood.

This capability is provided by the :class:`stravalib.client.BatchedResultsIterator` class.  If
you only wish to fetch a few objects, you can specify a limit in the method call or set the limit
on the resulting iterator.::

   activities = client.get_activities(limit=10)
   assert len(list(activities)) == 10

   # or:
   activities = client.get_activities()
   activities.limit = 10
   assert len(list(activities)) == 10

Note that setting the limit on the iterator is the only option when you are using the collection
attributes on entities.::

   activity = client.get_activity(activity_id)
   comments = activity.comments
   comments.limit = 1
   assert len(list(comments)) == 1


Attribute Types and Units
=========================

Many of the attributes in the Strava API are either temporal (or interval) types or quantities
that have implicit units associated with them. In both cases these are represented using
richer python types than the simple string or numeric values that Strava REST API returns.

Date/Time Types
---------------

The date+time responses are encoded as python native :class:`datetime.datetime` objects.::

   a = client.get_activity(96089609)
   print(a.start_date)
   # 2013-11-17 16:00:00+00:00

Date values which have no time component are encoded as python native :class:`datetime.date` objects.::

   me = client.get_athlete()
   print(me.dateofbirth)
   # 2010-12-26

Interval/duration values are represented using :class:`datetime.timedelta` objects, which allows
them to be added to datetime objects, etc.::

   a = client.get_activity(96089609)
   print(a.elapsed_time)
   # 10:45:00
   print(a.elapsed_time.seconds)
   # 38700


Quantities and Units
--------------------

Typically the units for quantity attributes returned by the Strava REST API are not
what people would actually want to see (e.g. meters-per-second instead of
kilometers-per-hour or miles-per-hour).

To facilitate working with these quantities, stravalib makes use of the
`pint library <https://pypi.org/project/Pint/>`_.  You can simply cast the values string
to see a representation that includes the units::

   activity = client.get_activity(96089609)
   print(activity.distance)
   # 22530.80 m

Hmmm, meters.  Well, here in the US we like to see miles.  While you can certainly do this using the units
library directly, stravalib provides a preconfigured set of common units to simplify matters.::

   from stravalib import unithelper

   activity = client.get_activity(96089609)
   print(unithelper.miles(activity.distance))
   # 14.00 mi

Of course, if you want to do something besides display those values, you'll likely
want a number.  You can directly access the 'magnitude' attribute of the :class:`pint.Quantity` instance,
or just cast to a numeric type (e.g. float).::

   activity = client.get_activity(96089609)
   print(float(activity.distance))
   # 22530.8
   print(float(unithelper.miles(activity.distance)))
   # 13.9999900581
