# stravalib

**UPDATE**

Now that the version 3 API has been opened to the public (and I therefore have a key), I am actively working on updating this library to work with the new API.  Support for v1 and v2 will be dropped from the code as they are not supported by Strava anymore.

Also, expect the API to change to conform to the architecture of the new API (e.g. the 3 detail levels, etc.).  The new version will not be backwards compatible (though hopefully will retain any positive aspects of current codebase).

**IMPORTANT**
This is currently under active development.  Expect it to be very broken.  This documentation is also
obviously very basic/incomplete; the aim here is to get something out there for feedback (and additional help welcome).

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

### Rides and Efforts/Segments

(This is a glimpse into what you can do.)

```python
from stravalib.client import Client, IMPERIAL

client = Client(units=IMPERIAL)
ride = client.get_ride(44708813)
print("Ride name: {0}".format(ride.name))

for effort in ride.efforts:
  # (this is kinda large)
  # print effort.segment.leaderboard
  print "Effort: {0}, segment: {1}".format(effort, effort.segment)
```

### Clubs

```python
from stravalib.client import Client, IMPERIAL

client = Client(units=IMPERIAL)
club = client.get_club(15)
print("Club name: {0}".format(club.name))

for athlete in club.members:
  print "Member: {0}".format(athlete)
 
# Or search by name
clubs = client.get_clubs(name='monkey')
```

## Uploading Files

Currently upload is only supported using the website "API".  (This is a full-featured option, but is a bit more brittle.)  The 
V2API uploader will be implemented soon. 

Here is an example of uploading using the website.  Note that the upload IDs returned may include previous uploads that are
in error or empty states (hence the need to check statuses, etc.)

```python
from stravalib.protocol.scrape import WebsiteClient

strava_client = WebsiteClient(strava_username, strava_password)

upload_ids = []
for f in filenames:
    with open(filename, 'r') as fp:
    	upload_ids.extend(strava_client.upload(fp))    
	
error_statuses = []
success_statuses = []
pending_ids = set(upload_ids)

timeout = 30
start_time = time.time()

while len(pending_ids):
    for upload_id in list(pending_ids): # Make a copy for iteration since we modify it during iteration.
        status = strava_client.check_upload_status(upload_id)
        if status['workflow'] == 'Analyzing':
            logging.debug("Upload still pending: {0}".format(status))
        elif status.get('activity'): # aka workflow=Uploaded
            url = 'http://app.strava.com/activities/{0}'.format(status['activity']['id'])
            logging.info("Upload succeeded, acvitity URL: {0}".format(url))
            success_statuses.append(status)
            pending_ids.remove(upload_id)
        else:
            logging.error("Unhandled workflow; treating as error: {0}".format(status))
            error_statuses.append(status)
            pending_ids.remove(upload_id)
            
        # We don't want to slam the servers
        time.sleep(1.0)
    
    if time.time() - start_time > timeout:
        logging.warning("Bailing out because timeout of {0} exceeded. (last status={1!r})".format(timeout, status))
        break
    
if success_statuses:
    logging.info("{0} rides processed. Visit http://app.strava.com/athlete/training/new to update ride settings.".format(len(success_statuses)))
else:
    logging.warning("Processing complete, but no successfull ride uploads (?)")
```
