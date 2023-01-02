# Welcome to stravalib
[![DOI](https://zenodo.org/badge/8828908.svg)](https://zenodo.org/badge/latestdoi/8828908)
![PyPI](https://img.shields.io/pypi/v/stravalib?style=plastic) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stravalib?style=plastic) [![Documentation Status](https://readthedocs.org/projects/stravalib/badge/?version=latest)](https://stravalib.readthedocs.io/en/latest/?badge=latest) ![Package Tests Status](https://github.com/stravalib/stravalib/actions/workflows/build-test.yml/badge.svg) ![PyPI - Downloads](https://img.shields.io/pypi/dm/stravalib?style=plastic) [![codecov](https://codecov.io/gh/stravalib/stravalib/branch/master/graph/badge.svg?token=sHbFJn7epy)](https://codecov.io/gh/stravalib/stravalib)

The **stravalib** Python package provides easy-to-use tools for accessing and
downloading Strava data from the Strava V3 web service. Stravalib provides a Client class that supports:
* Authenticating with stravalib
* Accessing and downloading strava activity, club and profile data
* Making changes to account activities

It also provides support for working with date/time/temporal attributes
and quantities through the [Python Pint library](https://pypi.org/project/Pint/).

## Dependencies

* Python 3.8+
* Setuptools for installing dependencies
* Other Python libraries (installed automatically when using pip): requests, pytz, pint, arrow, pydantic

## Installation

The package is available on PyPI to be installed using `pip`:

`pip install stravalib`

## How to Contribute to Stravalib

### Get Started!

Ready to contribute? Here's how to set up Stravalib for local development.

1. Fork the repository on GitHub
--------------------------------

To create your own copy of the repository on GitHub, navigate to the
`stravalib/stravalib <https://github.com/stravalib/stravalib>`_ repository
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
To build the html version of the documentation, use the
command:

`$ make -C docs html`

### Building from sources

To build the project locally in editable mode,
access the project root directory and run:

```bash
$ pip install -e .
```

To execute **unit - or integration tests** you will need to run

```bash
$ make test
```

## Local Tests
To run **end-to-end** tests you will need to rename *test.ini-example* (which you can find *<your-root-proj-dir>*/stravalib/tests/) to *test.ini*
In *test.ini* provide your *access_token* and *activity_id*. Now you can run
```
shell$ pytest stravalib/tests/functional
```

### Pull Requests and tests

Please add tests that cover your changes, these will greatly reduce the effort of reviewing
and merging your Pull Requests. In case you need it, there's a pytest fixture
`mock_strava_api` that is based on `RequestsMock` from the `responses` package. It prevents
requests being made to the actual Strava API and instead registers responses that are
based on examples from the published Strava API documentation. Example usages of this
fixture can be found in the `stravalib.tests.integration` package.

## Basic Usage

Please take a look at the source (in particular the stravalib.client.Client class, if you'd like to play around with the
API.  Most of the Strava API is implemented at this point; however, certain features such as streams are still on the
to-do list.

### Authentication

In order to make use of this library, you will need to create an app in Strava
which is free to do. [Have a look at this tutorial for instructions on creating
an app with Strava - we will be updating our docs with this information soon.](https://medium.com/analytics-vidhya/accessing-user-data-via-the-strava-api-using-stravalib-d5bee7fdde17)

**NOTE** We will be updating our documentation with clear instructions to support this
in the upcoming months

Once you have created your app, stravalib have several helper methods to make
authentication easier.

```python
from stravalib.client import Client

client = Client()
authorize_url = client.authorization_url(client_id=1234, redirect_uri='http://localhost:8282/authorized')
# Have the user click the authorization URL, a 'code' param will be added to the redirect_uri
# .....

# Extract the code from your webapp response
code = requests.get('code') # or whatever your framework does
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

stravalib uses the [python Pint library](https://pypi.org/project/Pint/) to facilitate working
with the values in the API that have associated units (e.g. distance, speed).  You can use the pint library
directly or through the `stravalib.unithelper` module for shortcuts

```python

activity = client.get_activity(96089609)
assert isinstance(activity.distance, unithelper.Quantity)
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

The [published sphinx documentation](https://stravalib.readthedocs.io/) provides much more.
