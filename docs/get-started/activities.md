(activities)=
# Get Strava activity data

This page overviews working with your Strava activity data using the stravalib Python library.

## Retrieve an activity

To access data for a given activity, use the `client.get_activity` method and provide the `activity_id`.

The `client.get_activity` method returns a {py:class}`stravalib.model.DetailedActivity` object.

:::{note}
All of the commands below require you first to authenticate using a client object containing a token.

`from stravalib.client import Client`

:::

```{code-block} pycon
# This command assumes that you have already authenticated the client object.
>>> activity = client.get_activity(1234)
>>> type(activity)

<class 'stravalib.model.DetailedActivity'>
```

The `DetailedActivity` object has many properties such as type, distance, and elapsed time.

```{code-block} pycon
# Get the activity type
>>> activity = client.get_activity(207650614)
>>> print(f"type = {activity.type}")

# Output
root='Hike'
```

```pycon
# Get activity distance
>>> print(f"The distance is: {a.distance}")
The distance is: 1234
```

## Stravalib offers unit conversion helpers

stravalib uses the [python Pint library](https://pypi.org/project/Pint/) to facilitate working
with the values in the API that have associated units (e.g. distance, speed). You can use the pint library
directly or through the `stravalib.unithelper` module for shortcuts

You can convert the distance value to another unit if you import stravalib's
`stravalib.unit_helper` module.

```python
from stravalib import unit_helper

unit_helper.feet(activity.distance)

# Output: <Quantity(8073.49081, 'foot')>

unit_helper.miles(activity.distance)
# <Quantity(1.52907023, 'mile')>

unit_helper.kilometers(activity.distance)
# <Quantity(2.4608, 'kilometer')>
```

Similarly, you can access elapsed time and
convert it to a `timedelta` object.

```python
activity.elapsed_time

# Output: 2273

activity.elapsed_time.timedelta
# Output: <bound method Duration.timedelta of 2273>
```

### DetailedActivity iterator objects

Some items returned by stravalib will be returned as a
{py:class}`BatchedResultsIterator` object. A `BatchedResultsIterator` object contains a list of
items associated with an activity - for example, a list of comments or kudos.

If an attribute contains a discrete value, you can access the item's value as an attribute like this:

```{code-block} pycon
>>> activity.comment_count
3
```

However if it's a `BatchedResultsIterator`, you will see this:

```{code-block} pycon
>>> activity.comments
<BatchedResultsIterator entity=Comment>
```

You can access each comment or item within a `BatchedResultsIterator` object using a Python loop or a list comprehension:

```{code-block} pycon
>>> for comment in activity.comments:
>>>     print(f"Comment by: {comment.athlete.firstname},  {comment.text}")

Comment by: YourFriendsNameHere: Not the pool!
```

## Get Strava activity streams

{py:func}`stravalib.client.Client.get_activity_streams` returns a dictionary containing time-series
data associated with your activity.

You can specify the stream variables that you want to be returned by providing a list of accepted types to the `types`
parameter. The type options for streaming data can be found here: {py:class}`stravalib.strava_model.StreamType`.


The data returned from this request is a dictionary object that looks something like this:

```python
streams

"""
# Output dict:
{'latlng': Stream(...),
 'distance': Stream(...),
 'altitude': Stream(...)}
"""
```

The Python dictionary's key represent the stream type:

```python
if "altitude" in streams.keys():
    print(streams["altitude"].data)
```



:::{tip}
The resolution of the streaming data refers to the number of data points returned for your activity. Low resolution means fewer points. Low-resolution data returns a smaller dataset; this data will be faster to download. Alternatively, high-resolution data will return a larger dataset and is slower to download. However, the output spatial data will look more "smooth" as more points are associated with the activity path.
:::

:::{warning}
Collecting streaming data is API (and memory) intensive!
:::

### Full-resolution data

When accessing streaming data, if you don't set a resolution value it will default to `None`.
In this case, Strava will return the full-resolution representation of your data.

:::{warning}
The `resolution` parameter for Strava data streams is undocumented and could (and has) changed
at any time.
:::

### Low-resolution data request

```python
# Request desired stream types
types = ["latlng", "altitude"]
streams = client.get_activity_streams(
    activity_id=123456,
    types=types,
    resolution="low",
    series_type="distance",
)
print(type(streams))

# Output
# dict


print(len(streams_low["latlng"].data))
# Output: This will return the lowest resolution data
# 100
```

### Medium resolution data request

```python
# Request desired stream types
types = ["latlng", "altitude"]
streams = client.get_activity_streams(
    activity_id=123456,
    types=types,
    resolution="medium",
    series_type="distance",
)

print(len(streams_med["latlng"].data))
# Output: notice there are more data points compared to a low resolution request
# 983
```

### High resolution data request

```python
# Request desired stream types
types = ["latlng", "altitude"]
streams = client.get_activity_streams(
    activity_id=123456,
    types=types,
    resolution="high",
    series_type="distance",
)

print(len(streams_high["latlng"].data))
# Output: notice there are more data points compared to both low and medium resolution. This is the max resolution possible.
# 1729
```

:::{note}
If your activity is short, the number of data points returned for medium vs. low-resolution data may not be significantly different.
:::

### Access activity zones

Additionally, you can retrieve activity zones using: {py:func}`stravalib.client.Client.get_activity_zones`; activity laps can be retrieved with {py:func}`stravalib.client.Client.get_activity_laps`.

### Access photos for an activity

To get photos for an associated activity, you can use`client.get_activity_photos(activity_id, max_resolution)`. Here, max_resolution is the maximum resolution of photos that you want to
collect in pixels.

```python
photos = client.get_activity_photos(id_w_photos, 2000)
photos

# Expected Output:
# <BatchedResultsIterator entity=ActivityPhoto>
```

The photos endpoint returns a `BatchedResultsIterator` object that you can loop through to access photo metadata and URLs for downloading the photos.

```python
for i, photo in enumerate(photos):
    print("photo")
```

You can access photo attributes like this:

```python
photo.default
True

photo.sizes
{"2000": [2048, 1261]}

photo.urls

{"2000": "https://dgtzuqphqg23d.cloudfront.net/url-is-here.jpg"}
```

## Get a list of Strava activities

You can access multiple activities using the {py:func}`stravalib.client.Client.get_activities` method. This method will return a `BatchedResultsIterator` that you can loop through.

:::{note}
The activities `batchedResultsIterator` object stores data that allows stravalib to access activity data when you iterate through the object. This approach limits the API requests made up front to Strava.
:::

Below, you request activities that were recorded after Jan 1, 2024.

```python
activities = client.get_activities(after="2024-01-01", limit=5)
print(activities)
# Expected output:
# <BatchedResultsIterator entity=SummaryActivity>
```

Using the limit parameter will limit the number of activities
Stravalib will retrieve. Above, you retrieve the first 5 activities.

```python
for i, activity in enumerate(activities):
    print(i)
"""
0
1
2
3
4

print(f"I found {i+1} activities for you.")
I found 5 activities for you.
"""
```

:::{tip}
To get activities starting with the oldest first, specify a value for the `after=` parameter when calling `client.get_activities`. Use the `before=` parameter to get the last 5 activities.
:::

## Get club member activities

You can also use stravalib to access activities associated with a club. To do this, use {py:func}`stravalib.client.Client.get_club_activities`.

<!-- (TODO)
## Create and update activities

I think this should be a new page on updating and creating activities.
=============== ================================================
method           doc
=============== ================================================
create_activity  {py:func}`stravalib.client.Client.create_activity`
upload_activity {py:func}`stravalib.client.Client.upload_activity`
update_activity {py:func}`stravalib.client.Client.update_activity`
=============== ================================================ -->
