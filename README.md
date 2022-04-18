# Welcome to stravalib

**NOTE: This library could really use someone to help with (or take over) maintenance. Please reach out to hans@xmpl.org if you are interested in taking project over.**

The **stravalib** project aims to provide a simple API for interacting with Strava v3 web services, in particular
abstracting the v3 REST API around a rich and easy-to-use object model and providing support for date/time/temporal attributes
and quantities with units (using the [python units library](http://pypi.python.org/pypi/units)).

See the [online documentation](http://pythonhosted.org/stravalib/) for more comprehensive documentation.

## Dependencies

* Python 2.7+, 3.4+  (Uses six for 2/3 compatibility.)
* Setuptools for installing dependencies
* Other python libraries (installed automatically when using pip/easy_install): requests, pytz, units, arrow, six

## Installation

The package is available on PyPI to be installed using easy_install or pip:

```bash
shell$ pip install stravalib
```

(Installing in a [virtual environment](https://pypi.python.org/pypi/virtualenv) is always recommended.)

Of course, by itself this package doesn't do much; it's a library.  So it is more likely that you will
list this package as a dependency in your own `install_requires` directive in `setup.py`.  Or you can
download it and explore Strava content in your favorite python REPL.

## How to Contribute to Stravalib

Get Started!
============

Ready to contribute? Here's how to set up Stravalib for local development.

1. Fork the repository on GitHub
--------------------------------

To create your own copy of the repository on GitHub, navigate to the
`hozn/stravalib <https://github.com/hozn/stravalib>`_ repository
and click the **Fork** button in the top-right corner of the page.

2. Clone your fork locally
--------------------------

Use ``git clone`` to get a local copy of your stravalib repository on your
local filesystem::

    $ git clone git@github.com:your_name_here/stravalib.git
    $ cd stravalib/

3. Set up your fork for local development
-----------------------------------------
The docs for this library are created using `sphinx`.
To build the documentation, use the command::

    $ make docs -B

## Building from sources

To build the project from sources access the project root directory and run
```
shell$ python setup.py build
```
Running
```
shell$ python setup.py install
```
will build and install *stravalib* in your *pip* package repository.

To execute **unit tests** you will need to run
```
shell$ nosetests
```
or
```
shell$ nosetests-3
```
if you use Python3.

To run **integration** tests you will need to rename *test.ini-example* (which you can find *<your-root-proj-dir>*/stravalib/tests/) to *test.ini*
In *test.ini* provide your *access_token* and *activity_id*



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
token_response = client.exchange_code_for_token(client_id=1234, client_secret='asdf1234', code=code)
access_token = token_response['access_token']
refresh_token = token_response['refresh_token']
expires_at = token_response['expires_at']

# Now store that short-lived access token somewhere (a database?)
client.access_token = access_token
# You must also store the refresh token to be used later on to obtain another valid access token
# in case the current is already expired
client.refresh_token = refresh_token

# An access_token is only valid for 6 hours, store expires_at somewhere and
# check it before making an API call.
client.token_expires_at = expires_at

athlete = client.get_athlete()
print("For {id}, I now have an access token {token}".format(id=athlete.id, token=access_token))

# ... time passes ...
if time.time() > client.token_expires_at:
    refresh_response = client.refresh_access_token(client_id=1234, client_secret='asdf1234',
        refresh_token=client.refresh_token)
    access_token = refresh_response['access_token']
    refresh_token = refresh_response['refresh_token']
    expires_at = refresh_response['expires_at']
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
