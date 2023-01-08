# How to authenticate with the Strava V3 REST API using Stravalib & Python

The first step in accessing your data using stravalib and Python is 
authentication. 

```{tip}
`This is a nice tutorial that has information about 
setting up a free app within STRAVA <https://medium.com/analytics-vidhya/accessing-user-data-via-the-strava-api-using-stravalib-d5bee7fdde17>`_
.
```

## First, create a app in your stravalib account

```{note}
Here, in this tutorial,  we are assuming that you are just trying to get your 
own Strava data to play with. However, the steps below can also be used and 
expanded upon to create an actual application.
```

To begin, you will need to create an APP that you can use to access your data.
[Click here and follow the steps that Strava provides to create a developer 
application in your account.](https://developers.strava.com/docs/getting-started/#account)

:::{figure-md} fig-target
:class: myclass

<img src="https://developers.strava.com/images/getting-started-2.png" alt="Image showing the settings for the application that you will create in your Strava account" class="bg-primary mb-1" width="700px">

Figure from the stravalib documentation showing the application settings. You can 
name your application whatever you wish. If you are just grabbing your own data locally,
then you can add any website url. Use `localhost` for the Authorization Callback 
Domain.  
:::

```{important}
Remember to store your client secret and access token values somewhere safe.
Do not EVER commit that information to git or push to GitHub!
```
## Save your secret and access token values into a text file 

If you are just working locally, you will want to have access to the secret 
and access token. One way to do that is to save them into a text file.

Save your information into a `client_secrets.txt` file. That file should contain 
two values on a single line separated by a comma as you see below:

`secret_value_here, access_token_value_here`


The exchange above was as follows

1. you authenticate (login) to Strava
2. you provide your code with permission to `read` data from your account 
3. Strava then returns a code to you that confirms you have read access to your account 
4. Finally you exchange that code for a token. The token is an value that will last for 6 hours. You can refresh it as you need to without having to go through steps 1-3 again. 

## Time to authenticate! 

Once you have a secrets file with the client secret and authentication values 
in it, you are ready to setup your authentication. 

At the top of your code, be sure to import the Client class. 

```python
from stravalib.client important Client
# You will use this to enter a url
import webbrowser
```

Next, read in the client id and access token and create a Client() object. 
The `Client()` object is what you will use to get and push data to Strava. 


```python
# Open the secrets file and store the client_id and secret as objects
# Note that .read() reads the file, .strip() gets rid of extra spaces and 
# split, splits the file (2) elements at the comma into two Python objects.
client_id, access_token = (
        open("client_secrets.txt").read().strip().split(",")
    )
# Next, create a stravalib Client object
client = Client()
```

## Authenticate with Strava

Now you are read to actually authenticate with Strava. If ou are authenticating 
just for yourself locally, the redirect_url can just be a localhost value.

However, if you are building an app, then your redirect url might be the 
url of your app.

Here, the scope of permissions that you request is important. 

If you only wish to download your data, then your scope can be read only (see 
below). Notice that all of the cope values are `read`:

```python
scope = ["read_all", "profile:read_all", "activity:write", "activity:read_all"]
```
However, if you wish to upload data to Strava then you will need a write scope 
included in your URL. Like this: 

```python
request_scope = ["read_all", "profile:read_all", "activity:write", "activity:read_all"]
```

For this example we will keep our scope as read only. 
And the url is a local url: 

```python
redirect_url = "http://127.0.0.1:5000/authorization"
request_scope = ["read_all", "profile:read_all", "activity:read_all"]
# Create url to use 
url = client.authorization_url(
        client_id=client_id,
        redirect_uri=redirect_url,
        scope=request_scope,
    )
```

Above you created a URL that. Below you can open that URL using the Python 
`webbrowser.open` method. this will allow you to :

1. Open the url in a browser, 
2. Authenticate with Strava (this step you will login to Strava and provide permission for your code to access the developer app that you created above).
3. If you are working locally and not building an app, once you have provided access to Strava, you will get a page not found page with a long URL It looks like a mistake, but really the url in your browser contains the code that you need to authenticate with the API! 
4. Copy the values here between code and &. See below - the x's represent the 
values that you need to copy!

`http://127.0.0.1:5000/authorization?state=&code=xxxxxxxxxxx&scope=read`.


```python
webbrowser.open(url)
    print(
        """You will see a url that looks like this. """,
        """http://127.0.0.1:5000/authorization?state=&code=12323423423423423423423550&scope=read,activity:read_all,profile:read_all,read_all")""",
        """Copy the values between code= and & in the url that you see in hte 
        browser. """,
    )
    # This allows you to copy the code into your Python console (or Jupyter Notebook)
    # 
    code = input("Please enter the code that you received: ")
    print(
        "Great! Your code is ",
        code,
        "Next I will exchange that code for a token.\n"
        "I only have to do this once.",
    )
```


You only need to get a code from Strava once. 

 above step only needs to happen once. After this, you can refresh your 
token . 

```
```
If you want a more technical overview, see the `official documentation <https://developers.strava.com/docs/authentication/>`_
for a description of the OAuth2 protocol that Strava uses to authenticate users.

Requesting Authorization
========================

The :class:`stravalib.client.Client` class provides the :meth:`stravalib.client.Client.authorization_url` method
to build an authorization URL which can be clicked on by a user in order to grant your application access to
their account data.

In its simplest form::

    from stravalib import Client
    client = Client()
    url = client.authorization_url(client_id=MY_STRAVA_CLIENT_ID,
                                   redirect_uri='http://myapp.example.com/authorization')

Note that for development, you can use localhost or 127.0.0.1 as the redirect host.::

    url = client.authorization_url(client_id=MY_STRAVA_CLIENT_ID,
                                   redirect_uri='http://127.0.0.1:5000/authorization')

Now you can display the resulting URL in your webapp to allow athletes to authorize your
application to read their data.  In the /authorization handler, you will need to exchange
a temporary code for a temporary access token. ::

    from stravalib import Client
    code = request.args.get('code') # e.g.
    client = Client()
    token_response = client.exchange_code_for_token(client_id=MY_STRAVA_CLIENT_ID,
                                                  client_secret=MY_STRAVA_CLIENT_SECRET,
                                                  code=code)
    access_token = token_response['access_token']
    refresh_token = token_response['refresh_token']  # You'll need this in 6 hours

The resulting access_token is valid until the specified expiration time (6 hours,
specified as unix epoch seconds `expires_at` field of returned token) or the user
explicitly revokes application access.  This token can  be stored so that you can access the account data the future without requiring re-authorization.

Once you have an access token you can begin to perform operations from the perspective of that  user. ::

    from stravalib import Client
    client = Client(access_token=STORED_ACCESS_TOKEN)
    client.get_athlete() # Get current athlete details

To refresh the token you would call the :meth:`stravalib.client.Client.refresh_access_token` method. ::

    from stravalib import Client
    code = request.args.get('code') # e.g.
    client = Client()
    token_response = client.refresh_access_token(client_id=MY_STRAVA_CLIENT_ID,
                                          client_secret=MY_STRAVA_CLIENT_SECRET,
                                          refresh_token=last_refresh_token)
    new_access_token = token_response['access_token']

See the https://github.com/stravalib/stravalib/tree/master/examples/strava-oauth directory for an example
Flask application for fetching a Strava auth token.
