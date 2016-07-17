# stravalib

**UPDATE**

The new codebase supports only [version 3 API](http://strava.github.io/api/) of the Strava API (since v1 and v2 are no longer available).

**IMPORTANT**
This is currently under active development.  Parts have been tested, but some aspects may be broken.

The stravalib project aims to provide a simple API for interacting with Strava v3 web services, in particular
abstracting the v3 REST API around a rich and easy-to-use object model and providing support for date/time/temporal attributes
and quantities with units (using the [python units library](http://pypi.python.org/pypi/units)).

See the [online documentation](http://pythonhosted.org/stravalib/) for more comprehensive documentation.

## Dependencies

* Python 2.7+.  (Uses six for 2/3 compatibility.)
* Setuptools for installing dependencies
* Other python libraries (installed automatically when using pip/easy_install): requests, pytz, units, arrow, six

## Installation

The package is available on PyPI to be installed using easy_install or pip:

``` none
shell$ pip install stravalib
```

(Installing in a [virtual environment](https://pypi.python.org/pypi/virtualenv) is always recommended.)

Of course, by itself this package doesn't do much; it's a library.  So it is more likely that you will
list this package as a dependency in your own `install_requires` directive in `setup.py`.  Or you can
download it and explore Strava content in your favorite python REPL.

## Basic Usage

Please take a look at the source (in particular the stravalib.client.Client class, if you'd like to play around with the
API.  Most of the Strava API is implemented at this point; however, certain features such as streams are still on the
to-do list.

### Authentication

In order to make use of this library, you will need to have access keys for one or more Strava users. This
effectively requires you to run a webserver; this is outside the scope of this library, but stravalib does provide helper methods to make it easier.

```python
from stravalib.client import Client

client = Client()
authorize_url = client.authorization_url(client_id=1234, redirect_uri='http://localhost:8282/authorized')
# Have the user click the authorization URL, a 'code' param will be added to the redirect_uri
# .....

# Extract the code from your webapp response
code = request.get('code') # or whatever your framework does
access_token = client.exchange_code_for_token(client_id=1234, client_secret='asdf1234', code=code)

# Now store that access token somewhere (a database?)
client.access_token = access_token
athlete = client.get_athlete()
print("For {id}, I now have an access token {token}".format(id=athlete.id, token=access_token))
```

### Athletes and Activities

(This is a glimpse into what you can do.)

```python
# Currently-authenticated (based on provided token) athlete
# Will have maximum detail exposed (resource_state=3)
curr_athlete = client.get_athlete()

# Fetch another athlete
other_athlete = client.get_athlete(123)
# Will only have summary-level attributes exposed (resource_state=2)

# Get an activity
activity = client.get_activity(123)
# If activity is owned by current user, will have full detail (resource_state=3)
# otherwise summary-level detail.
```

### Streams

Streams represent the raw data of the uploaded file. Activities, efforts, and
segments all have streams. There are many types of streams, if activity does
not have requested stream type, returned set simply won't include it.

```python

# Activities can have many streams, you can request n desired stream types
types = ['time', 'latlng', 'altitude', 'heartrate', 'temp', ]

streams = client.get_activity_streams(123, types=types, resolution='medium')

#  Result is a dictionary object.  The dict's key are the stream type.
if 'altitude' in streams.keys():
    print(streams['altitude'].data)

```


### Working with Units

stravalib uses the [python units library](https://pypi.python.org/pypi/units/) to facilitate working
with the values in the API that have associated units (e.g. distance, speed).  You can use the units library
directly
stravalib.unithelper module for shortcuts

```python

activity = client.get_activity(96089609)
assert isinstance(activity.distance, units.quantity.Quantity)
print(activity.distance)
# 22530.80 m

# Meters!?

from stravalib import unithelper

print(unithelper.miles(activity.distance))
# 14.00 mi

# And to get the number:
num_value = float(unithelper.miles(activity.distance))
# Or:
num_value = unithelper.miles(activity.distance).num
```

## Still reading?

The [published sphinx documentation](http://pythonhosted.org/stravalib/) provides much more.
