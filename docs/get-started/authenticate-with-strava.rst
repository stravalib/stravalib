.. _auth:

Authentication and Authorization
********************************

In order to use this library to retrieve information about athletes and actitivies,
you will need authorization to do so.

`This is a nice tutorial that has information about
setting up a free app within STRAVA <https://medium.com/analytics-vidhya/accessing-user-data-via-the-strava-api-using-stravalib-d5bee7fdde17>`_
.

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
