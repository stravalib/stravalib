This is an example Flask application showing how you can use stravalib to help
with getting access tokens.

## Create A Virtualenv with venv

We'll assume you're using Python 3.

```bash
$ cd /path/to/stravalib
$ python3 -m venv env
$ source env/bin/activate
(env) $ pip install -r requirements.txt && pip install -e . 
# Because flask is the only install in that file right now
(env) $ pip install flask
```

## Create a Config File
====================

Create a file -- for example `settings.cfg`
that contains your client id and secret in it:

```bash
(env) $ cd examples/strava-oauth/
(env) $ vi settings.cfg
```

Paste in your Strava developer app client ID and secret:

```markdown
STRAVA_CLIENT_ID=123
STRAVA_CLIENT_SECRET='deadbeefdeadbeefdeadbeef'
```

## Run your flask server 

Run the Flask server, specifying the path to this file in your `APP_SETTINGS`
environment var:

```
(env) $ APP_SETTINGS=settings.cfg python server.py
```
