.. _activities:

Activities
**********

Examples of working with activities.

Retrieve An Activity
====================
To get a given activity, use the get_activity function and provide activity_id,
The function will return a :class:`stravalib.model.Activity` object.::

    activity = client.get_activity(207650614)
    print("type = " + activity.type)

Activity object has many basic properties such as type and distance.::

    print("type={0.type} distance={1} km".format(activity,
                                             unithelper.kilometers(activity.distance)))

But also many secondary properties like kudos, comments and photos which follow the following pattern.::

    # Number of comments on activity
    activity.comment_count

    # print each comment
    for comment in activity.comments:
        print("{} : {}".format(comment.athlete.lastname, comment.text))


Activity information
--------------------

Most information pertaining to actitity is available directly on the :class:`stravalib.model.Activity` object.  Some additional information can be retrieved relevant methods.

Below is example of :meth:`stravalib.client.Client.get_activity_streams`::

    # Activities can have many streams, you can request desired stream types
    types = ['time', 'latlng', 'altitude', 'heartrate', 'temp', ]

    streams = client.get_activity_streams(123, types=types, resolution='medium')

    #  Result is a dictionary object.  The dict's key are the stream type.
    if 'altitude' in streams.keys():
        print(streams['altitude'].data)


Additionally, activity zones can be retrieved with :meth:`stravalib.client.Client.get_activity_zones` and activity laps can be retrieved with :meth:`stravalib.client.Client.get_activity_laps` .




List of Activities
==================

Three functions return lists of activities.

List the authenticated athlete's activities with :meth:`stravalib.client.Client.get_activities`.::

    for activity in client.get_activities(after = "2010-01-01T00:00:00Z",  limit=5):
        print("{0.name} {0.moving_time}".format(activity))

.. tip::
   To get activities in oldest to newest, specify a value for the `after` argument. To get newest to oldest use `before` argument.

Additionally list the authenticated athlete's friends activities with :meth:`stravalib.client.Client.get_friend_activities`, or list a club member's activities with :meth:`stravalib.client.Client.get_club_activities`.


Manage Activities
=================
(TODO)

=============== ================================================
method           doc
=============== ================================================
create_activity  :meth:`stravalib.client.Client.create_activity`
upload_activity :meth:`stravalib.client.Client.upload_activity`
update_activity :meth:`stravalib.client.Client.update_activity`
=============== ================================================

