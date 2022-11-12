This is an example Flask application showing how you can use stravalib to help
with getting access tokens.

Create Virtualenv
=================

We'll assume you're using python3.

```
$ cd /path/to/stravalib
$ python3 -m venv env
$ source env/bin/activate
(env) $ pip install -r requirements.txt && python setup.py develop
(env) $ pip install -r examples/strava-oauth/requirements.txt
```

Create a Config File
====================

Create a file -- for example `settings.cfg`:

```
(env) $ cd examples/strava-oauth/
(env) $ vi settings.cfg
```
Paste in your Strava client ID and secret:

```python
STRAVA_CLIENT_ID=123
STRAVA_CLIENT_SECRET='deadbeefdeadbeefdeadbeef'
```

Run Server
==========

Run the Flask server, specifying the path to this file in your `APP_SETTINGS`
environment var:

```
(env) $ APP_SETTINGS=settings.cfg python server.py
```
