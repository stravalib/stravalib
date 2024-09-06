# Welcome to stravalib

[![All Contributors](https://img.shields.io/github/all-contributors/stravalib/stravalib?color=ee8449&style=flat-square)](#contributors)
[![DOI](https://zenodo.org/badge/8828908.svg)](https://zenodo.org/badge/latestdoi/8828908)
![PyPI](https://img.shields.io/pypi/v/stravalib?style=plastic) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stravalib?style=plastic) [![Documentation Status](https://readthedocs.org/projects/stravalib/badge/?version=latest)](https://stravalib.readthedocs.io/en/latest/?badge=latest) ![Package Tests Status](https://github.com/stravalib/stravalib/actions/workflows/build-test.yml/badge.svg) ![PyPI - Downloads](https://img.shields.io/pypi/dm/stravalib?style=plastic) [![codecov](https://codecov.io/gh/stravalib/stravalib/branch/main/graph/badge.svg?token=sHbFJn7epy)](https://codecov.io/gh/stravalib/stravalib)

The **stravalib** Python package provides easy-to-use tools for accessing and
downloading Strava data from the Strava V3 web service. Stravalib provides a Client class that supports:

- Authenticating with stravalib
- Accessing and downloading Strava activity, club and profile data
- Making changes to account activities

It also provides support for working with date/time/temporal attributes
and quantities through the [Python Pint library](https://pypi.org/project/Pint/).

## Dependencies

- Python 3.9+
- Setuptools for installing dependencies
- Other Python libraries (installed automatically when using pip): requests, pytz, pint, arrow, pydantic

## Installation

The package is available on PyPI to be installed using `pip`:

`pip install stravalib`

## How to Contribute to Stravalib

### Get Started!

Ready to contribute? Here's how to set up Stravalib for local development.

1. Fork the repository on GitHub

---

To create your own copy of the repository on GitHub, navigate to the
`stravalib/stravalib <https://github.com/stravalib/stravalib>`\_ repository
and click the **Fork** button in the top-right corner of the page.

2. Clone your fork locally

---

Use `git clone` to get a local copy of your stravalib repository on your
local filesystem::

    $ git clone git@github.com:your_name_here/stravalib.git
    $ cd stravalib/

3. Set up your fork for local development

---

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

To run **end-to-end** tests you will need to rename _test.ini-example_ (which you can find _<your-root-proj-dir>_/stravalib/tests/) to _test.ini_
In _test.ini_ provide your _access_token_ and _activity_id_. Now you can run

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
API. Most of the Strava API is implemented at this point; however, certain features such as streams are still on the
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
authorize_url = client.authorization_url(
    client_id=1234, redirect_uri="http://localhost:8282/authorized"
)
# Have the user click the authorization URL, a 'code' param will be added to the redirect_uri
# .....

# Extract the code from your webapp response
code = requests.get("code")  # or whatever your framework does
token_response = client.exchange_code_for_token(
    client_id=1234, client_secret="asdf1234", code=code
)
access_token = token_response["access_token"]
refresh_token = token_response["refresh_token"]
expires_at = token_response["expires_at"]

# Now store that short-lived access token somewhere (a database?)
client.access_token = access_token
# You must also store the refresh token to be used later on to obtain another valid access token
# in case the current is already expired
client.refresh_token = refresh_token

# An access_token is only valid for 6 hours, store expires_at somewhere and
# check it before making an API call.
client.token_expires_at = expires_at

athlete = client.get_athlete()
print(
    "For {id}, I now have an access token {token}".format(
        id=athlete.id, token=access_token
    )
)

# ... time passes ...
if time.time() > client.token_expires_at:
    refresh_response = client.refresh_access_token(
        client_id=1234, client_secret="asdf1234", refresh_token=client.refresh_token
    )
    access_token = refresh_response["access_token"]
    refresh_token = refresh_response["refresh_token"]
    expires_at = refresh_response["expires_at"]
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
types = [
    "time",
    "latlng",
    "altitude",
    "heartrate",
    "temp",
]

streams = client.get_activity_streams(123, types=types, resolution="medium")

#  Result is a dictionary object.  The dict's key are the stream type.
if "altitude" in streams.keys():
    print(streams["altitude"].data)
```

### Working with Units

stravalib uses the [python Pint library](https://pypi.org/project/Pint/) to facilitate working
with the values in the API that have associated units (e.g. distance, speed). You can use the pint library
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

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://towardsdatascience.com/@djcunningham0"><img src="https://avatars.githubusercontent.com/u/38900370?v=4?s=100" width="100px;" alt="Danny Cunningham"/><br /><sub><b>Danny Cunningham</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=djcunningham0" title="Documentation">📖</a> <a href="#ideas-djcunningham0" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www-ljk.imag.fr/membres/Jerome.Lelong/"><img src="https://avatars.githubusercontent.com/u/2910140?v=4?s=100" width="100px;" alt="Jerome Lelong"/><br /><sub><b>Jerome Lelong</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/issues?q=author%3Ajlelong" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://vortza.com"><img src="https://avatars.githubusercontent.com/u/1788027?v=4?s=100" width="100px;" alt="Jonatan Samoocha"/><br /><sub><b>Jonatan Samoocha</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=jsamoocha" title="Code">💻</a> <a href="https://github.com/stravalib/stravalib/pulls?q=is%3Apr+reviewed-by%3Ajsamoocha" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/stravalib/stravalib/commits?author=jsamoocha" title="Documentation">📖</a> <a href="#maintenance-jsamoocha" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.leahwasser.com"><img src="https://avatars.githubusercontent.com/u/7649194?v=4?s=100" width="100px;" alt="Leah Wasser"/><br /><sub><b>Leah Wasser</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=lwasser" title="Code">💻</a> <a href="https://github.com/stravalib/stravalib/pulls?q=is%3Apr+reviewed-by%3Alwasser" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/stravalib/stravalib/commits?author=lwasser" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/yotam5"><img src="https://avatars.githubusercontent.com/u/69643410?v=4?s=100" width="100px;" alt="Yotam"/><br /><sub><b>Yotam</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=yotam5" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/enadeau"><img src="https://avatars.githubusercontent.com/u/12940089?v=4?s=100" width="100px;" alt="Émile Nadeau"/><br /><sub><b>Émile Nadeau</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=enadeau" title="Code">💻</a> <a href="https://github.com/stravalib/stravalib/pulls?q=is%3Apr+reviewed-by%3Aenadeau" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/stravalib/stravalib/commits?author=enadeau" title="Documentation">📖</a> <a href="#maintenance-enadeau" title="Maintenance">🚧</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
