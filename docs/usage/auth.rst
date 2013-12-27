.. _auth:

Authentication and Authorization
********************************

In order to use this library to retrieve information about athletes and actitivies,
you will need authorization to do so.

See the `official documentation <http://strava.github.io/api/v3/oauth/>`_ for a description of the OAuth2 protocol
that Strava uses to authenticate users.

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
a temporary code for a permanent token. ::

    from stravalib import Client		
    code = request.args.get('code') # e.g.
    client = Client()
    access_token = client.exchange_code_for_token(client_id=MY_STRAVA_CLIENT_ID,
                                                  client_secret=MY_STRAVA_CLIENT_SECRET,
                                                  code=code)

The resulting access_token is valid (until/unless access for your app is revoked by the user) and should be stored 
so that you can access the account data the future without re-authorizing.

Once you have an access token you can begin to perform operations from the perspective of that  user. ::

    from stravalib import Client
    client = Client(access_token=STORED_ACCESS_TOKEN)
    client.get_athlete() # Get current athlete details
 