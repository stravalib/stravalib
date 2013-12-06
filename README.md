# stravalib

**UPDATE**

The new codebase supports only v3 of the Strava API (since v1 and v2 are no longer available).

**IMPORTANT**
This is currently under active development.  It is only partially implemented and still very broken.  
This documentation is also obviously very basic/incomplete.  It will get better.

The stravalib project aims to provide a simple API for interacting with Strava v3 web services, in particular
abstracting the v3 REST API around a rich and easy-to-use object model.

## Dependencies
 
* Python 2.6+.  (This is intended to work with Python 3, but is being developed on Python 2.x)
* Setuptools/Distribute
* Virtualenv 

## Installation

Eventually this will be installable via setuptools/distribute/pip; however, currently you must 
download / clone the source and run the python setup.py install command.

Here are some instructions for setting up a development environment, which is more appropriate
at this juncture:

	shell$ git clone https://github.com/hozn/stravalib.git
	shell$ cd stravalib
	shell$ python -m virtualenv --no-site-packages --distribute env
	shell$ source env/bin/activate
    (env) shell$ python setup.py develop

We will assume for any subsequent shell examples that you are running in that activated virtualenv.  (This is denoted by using 
the "(env) shell$" prefix before shell commands.)

You can run the functional tests if you like.

	(env) shell$ python setup.py test

Or you can install ipython and play around with stuff:

	(env) shell$ easy_install ipython    

(You can try some of the examples below or explore the client APIs.)

## Basic Usage
   
Please take a look at the source (in particular the stravalib.client.Client class, if you'd like to play around with the 
API.  Most of the Strava API is implemented at this point; however, certain features such as V2API uploads are not yet supported.

### Authentication

Actually getting access to an account requires you to run a webserver; this is outside the scope of this library, but there
are helper methods to make it easier.

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

### Rides and Efforts/Segments

(This is a glimpse into what you can do.)

```python
from stravalib.client import Client

client = Client(access_token='xxxxxxxxx')
ride = client.get_ride(44708813)
print("Ride name: {0}".format(ride.name))

for effort in ride.efforts:
  print "Effort: {0}, segment: {1}".format(effort, effort.segment)
```

### Clubs

```python
from stravalib.client import Client

client = Client()
club = client.get_club(15)
print("Club name: {0}".format(club.name))

for athlete in club.members:
  print "Member: {0}".format(athlete)
 
# Or search by name
clubs = client.get_clubs(name='monkey')
```

## Uploading Files

(TODO)