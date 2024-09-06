# How to get your data from the Strava API using Python

Here, we walk you through setting up your application (or your code running
locally on your computer) to access Strava data from the V3 Strava REST API
using **Stravalib**. To begin, you need to set up authentication with Strava.

Authentication includes a few steps:

1. First, you create a free developer "app" in your Strava account.
This app will be your primary interface for interacting with the API.
1. Second, you set up authentication with the developer app. Authentication
involves specifying permission scope (read or write data), allowing Strava users
to authenticate / login to their account, and allowing permissions to read or write data.
1. Once you log in to Strava and accept the permission scope (discussed below), you will get a code from Strava that your code can use to request an access token.
1. The access token is valid for 6 hours. After 6 hours, you can refresh the
token using `stravalib.Client.refresh_token()` as many times as you need.

Once you complete steps 1-3 above, you only have to refresh the token in the
future to interact with the Strava API.

An example workflow (that doesn't rely upon a web app tool like Flask) is below.

```python
# You will use this to login to your Strava account
import webbrowser

from stravalib.client import Client

# Open the secrets file and store the client ID and client secret as objects, separated by a comma
# Read below to learn how to set up the app that provides you with the client ID
# and client secret
client_id, client_secret = open("client_secrets.txt").read().strip().split(",")

# Create a client object
client = Client()
# Define your scope (this is read-only - see below for a "write" example which
# allows you to update activities and publish new activities to your Strava account).
# read_all allows read access for both private and public activities
scope = ["read_all", "profile:read_all", "activity:read_all"]

# Create a localhost URL for authorization (for local development)
redirect_url = "http://127.0.0.1:5000/authorization"
# This is your scope - read-only in this case
request_scope = ["read_all", "profile:read_all", "activity:read_all"]
# Create url to use - notice that your app client_id is included in your
# authorization url
url = client.authorization_url(
    client_id=client_id,
    redirect_uri=redirect_url,
    scope=request_scope,
)

# Open the URL in a web browser (this is where you login and accept the scope
# read vs write) of access to your Strava account data
webbrowser.open(url)

print(
    """You will see a url that looks like this. """,
    """http://127.0.0.1:5000/authorization?state=&code=12323423423423423423423550&scope=read,activity:read_all,profile:read_all,read_all")""",
    """Copy the values between code= and & in the url that you see in the
 browser. """,
)
# Using input allows you to copy the code into your Python console
# (or Jupyter Notebook)
code = input("Please enter the code that you received: ")
print(
    f"Great! Your code is {code}\n"
    "Next, I will exchange that code for a token.\n"
    "I only have to do this once."
)

# Exchange the code returned from Strava for an access token
token_response = client.exchange_code_for_token(
    client_id=client_id, client_secret=client_secret, code=code
)

token_response
# Example output of token_response
# {'access_token': 'value-here-123123123', 'refresh_token': # '123123123',
# 'expires_at': 1673665980}

# Get current athlete details
athlete = client.get_athlete()
# Print athlete name :) If this works your connection is successful!
print(f"Hi, {athlete.firstname} Welcome to stravalib!")

# You can also start exploring stats
stats = client.get_athlete_stats()
stats.all_run_totals.count
```

Below you will get a detailed overview of the above steps. You will also learn how to
refresh your access token. You can only use a new token for 6 hours; then it needs to be refreshed.

## First, create a developer app in your Strava account

```{note}
In this tutorial, we assume you are playing locally with your
own Strava data in Python. However, the steps below can also be used and
expanded to create a web application. There is an example Flask application
that provides an example of web authentication in the `examples/strava-oath`
directory of this package.
```

First, you will need to create a free developer application in
your Strava account.
[Click here and follow Strava's steps to create a developer
application.](https://developers.strava.com/docs/getting-started/#account)

The figures below are from the Strava setup link provided above. They show you:
1. The Strava application setup screen and
2. The Strava application, once it's been set up with the client ID and access token values.

:::{figure-md} fig-target
:class: myclass

<img src="https://developers.strava.com/images/getting-started-2.png" alt="Image showing the settings for the application that you will create in your Strava account" class="bg-primary mb-1" width="700px">

Figure from the Strava documentation showing the application settings. You can
name your application whatever you wish. You can add any website URL if you are grabbing your data locally. For this tutorial, use `localhost` for the Authorization Callback
Domain if you are only using this locally. Otherwise, you likely have a website
URL that will enter here.
:::

:::{figure-md} fig-target
:class: myclass

<img src="https://developers.strava.com/images/getting-started-1.png" alt="Image showing the application and application client secret, access token and refresh token." class="bg-primary mb-1" width="700px">

Figure from the Strava documentation showing the application settings. This screenshot shows the final application you should have once you follow the
steps above. You will want to copy the client ID and client secret to a file
(see below for more). Be sure never to share these values. Also, NEVER commit
these values openly to GitHub. You will want to encrypt these values if they need to be stored online.
:::

```{important}
Remember to store your client ID and client secret values somewhere safe.
Do not EVER commit that information to `.git` or push it to GitHub (unless you have
encrypted it well)!

## Save your secret and access token values in a text file

Notice that there is a client secret (hidden
in the screenshot) and a token in the first screenshot above. Below, you will copy both
values to a text file to use in your code.

Do the following:

* Create a `client_secrets.txt` file.
* Add the client secret and access token values on a single line separated
by a comma in the format that you see below:

`secret_value_here, access_token_value_here`


```{tip}
If you were creating an application, you would store this information
securely somewhere in your app's online database.
```

## Time to authenticate!

Once you have created your `client_secrets.txt` file, you are ready to setup
authentication using **Python**.

At the top of your code, import the `stravalib.client.Client` class.
Below you also import `webbrowser` to launch a web browser from your code to
login to Strava. `webbrowser` behaves like a web app.

```{tip}
If you were using Flask, you'd create an HTML template. See our example in the GitHub repo.
```

```python
# Use webbrowser to launch a browser from Python
import webbrowser

from stravalib.client import Client
```

Next, read the `client_id` and `access_token` from the
`client_secrets.txt` file that you created above. You then create a
stravalib `Client()` object.

The `Client()` object is what you will use to get and push data to Strava.
This object stores your authentication information. It also contains methods that you can call that will perform different operations including:

* Getting different types of data from Strava such as activities and club data, and
* Modifying activity and club data on Strava (if you provide the token with write permissions).

You will learn more about read vs write token scopes below.

```python
# Open the secrets file and store the client_id and secret as objects
# Note that .read() reads the file, .strip() gets rid of extra spaces and
# split, splits the file (2) elements at the comma into two Python objects.
client_id, access_token = open("client_secrets.txt").read().strip().split(",")
# Next, generate a stravalib Client() object
client = Client()
```

## Authenticate with Strava

Now, you have all the pieces needed to authenticate with Strava.

1. You have the client secret and token from your Strava account's developer app, and
2. You have the stravalib `Client()` object.

### Create a URL to authenticate and define the token scope

Next, you will create two variables:

1. The scope of the authentication token that you wish to receive from Strava:
The scope refers to permissions you need when interacting
with your Strava data. For example, if you only wish to download data, then read-only permissions
are enough. However, if you want to push data to Strava (for example, upload or create activities), you will also
need write access.

2. You must specify a URL (`redirect_url`) that Strava will redirect the user to after they
have authenticated (signed in and provided the permissions you requested in
step one). If you are only authenticating locally to grab your data, you can
use a localhost value for your `redirect_url.`

```{tip}
However, if you are building an app, then your redirect URL might be the
url of your app. You must grab the code that Strava provides in that
`redirect_url.`
```

### Set your authentication scope & create a redirect url

If you only wish to download your data, your scope can be read (see
below). The scope below provides your code access to the users' profile and activity data. Notice that all of the scope values are `read`:

```python
# Python list containing read-only scope values
request_scope = ["read_all", "profile:read_all", "activity:read_all"]
```

However, if you wish to upload data to Strava, then you will need a write scope
included in your URL. Like this:

```python
# Python list containing both read and write (activity) scope values
request_scope = ["read_all", "profile:read_all", "activity:write", "activity:read_all"]
```

:::{tip}
[Learn more about request scope options from the Strava docs here.](https://developers.strava.com/docs/authentication/#details-about-requesting-access)
:::

Below, you limit your scope to **read-only** as you are only
looking at data in this tutorial rather than modifying it.

You also set the `redirect_url` to **localhost** (to be opened on your computer
locally) url:

```python
# This is a localhost url
redirect_url = "http://127.0.0.1:5000/authorization"
# This is your scope - read-only in this case
request_scope = ["read_all", "profile:read_all", "activity:read_all"]
# Create URL to use - notice that your client_id is included in your authorization URL
url = client.authorization_url(
    client_id=client_id,
    redirect_uri=redirect_url,
    scope=request_scope,
)
```

Your URL will look something like this:

```python
print(url)

# 'https://www.strava.com/oauth/authorize?client_id=123456&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fauthorization&approval_prompt=auto&response_type=code&scope=read_all%2Cprofile%3Aread_all%2Cactivity%3Aread_all'
```

### Time to put the above into action

Above, you created your Strava authentication URL that will allow a user to
gives you (read-only) permission to access their data on Strava via the API.

Below you will use that URL using the Python
`webbrowser.open` method. This will allow you to:

1. Open the url in a web browser directly from your Python code,
2. Authenticate with Strava (you will log in to Strava and provide permission for your code to access the developer app you created above).
3. If you are working locally and not building an app, once you have provided access to Strava, you will get a `page not found` page with a long URL. It looks like a mistake, but the URL in your browser contains the code you need to authenticate with the API! Don't close the browser window just yet.

`http://127.0.0.1:5000/authorization?state=&code=xxxxxxxxxxx&scope=read`.

4. Copy the values in the URL between **code** and the **&** symbol. Above, the
x's represent the values that you need to copy.

```python
# Open the url that you created above in a web browser
webbrowser.open(url)
print(
    """You will see a URL that looks like this:
    http://127.0.0.1:5000/authorization?state=&code=12323423423423423423423550&scope=read,activity:read_all,profile:read_all,read_all
    Copy the values between code= and & in the URL that you see in the browser."""
)
# Using input allows you to copy the code into your Python console (or Jupyter Notebook)
code = input("Please enter the code that you received: ")

print(
    f"Great! Your code is {code}\n"
    "Next, I will exchange that code for a token.\n"
    "I only have to do this once."
)
```

You only need to get a code from Strava once.

Next, you are ready to exchange the code for a token. After this, you can
refresh your token as often as you need to to grab your data.

```python
token_response = client.exchange_code_for_token(
    client_id=client_id, client_secret=client_secret, code=code
)
# Save token locally as a pickle
with open(path_to_save, "wb") as f:
    pickle.dump(token_response, f)

print("Token saved - hooray!")

# Access token and refresh tokens
access_token = token_response["access_token"]
refresh_token = token_response["refresh_token"]  # You'll need this in 6 hours
```

## Token refresh

Strava provides you with an access token that is good for 6 hours. However, you can refresh the token as needed if you wish to grab
more data in the future.

Above you save the token as a pickle so you can access it in the future.

```python
client.get_athlete()  # Get current athlete details
```

If you want to get more data in the future / after your 6-hour window that
the current token is good for, you can refresh the token using the
`client.refresh_access_token()` method.

```python
# Open the token object that you saved locally earlier
with open(token_path_pickle, "rb") as f:
    tokens = pickle.load(f)

refresh_response = client.refresh_access_token(
    client_id=client_id,
    client_secret=client_secret,
    refresh_token=refresh_token,
)

# TODO: Again this seems weird. Why doesn't this all get updated when you refresh
# above in that method?

# Update your client object with the refreshed token values
# TODO: this seems like extra work? method should do this
client.access_token = refresh_response["access_token"]
client.refresh_token = refresh_response["refresh_token"]
client.token_expires_at = refresh_response["expires_at"]

# Check that the refresh worked by grabbing the athlete details
client.get_athlete()
```

To refresh the token you call the :meth:`stravalib.client.Client.refresh_access_token` method.

```python
from stravalib import Client

code = request.args.get("code")  # e.g.
client = Client()
token_response = client.refresh_access_token(
    client_id=MY_STRAVA_CLIENT_ID,
    client_secret=MY_STRAVA_CLIENT_SECRET,
    refresh_token=last_refresh_token,
)
new_access_token = token_response["access_token"]
```

```{tip}
[See the](https://github.com/stravalib/stravalib/tree/master/examples/strava-oauth)
 directory for an example Flask application for fetching a Strava auth token.
```
