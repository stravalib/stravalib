# stravalib

**IMPORTANT**
This is currently under active development.  Expect it to be very broken.

The stravalib project aims to provide a simple API for interacting with Strava web services, in particular
abstracting over the various REST APIs that Strava supports in addition to some functionality for interacting
with the website directly.

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

We will assume for all subsequent shell examples that you are running in that activated virtualenv.  (This is denoted by using 
the "(env) shell$" prefix before shell commands.)    


## Basic Usage
   
Please take a look at the source if you'd like to play around with the API.  At time of writing only
ride and club fetching is supported.  More comprehensive entity support (and much more documentation) 
to come.

```python

from stravalib.simple import Client, IMPERIAL

client = Client(units=IMPERIAL)
ride = client.get_ride(44708813)
print("Ride name: {0}".format(ride.name))
# etc.
```