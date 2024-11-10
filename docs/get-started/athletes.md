(athletes)=
# Athletes

This page is designed to mirror the documentation structure at [Strava API Athletes](https://developers.strava.com/docs/reference/#api-Athletes) and describe the methods for working with athlete data in the Strava API.

## Retrieve Current Athlete

This is the simplest request. It is provided by the {py:fun}`stravalib.client.Client.get_athlete` when called with no parameters.

```python
athlete = client.get_athlete()
print("Hello, {}".format(athlete.firstname))
```

See the {py:class}`stravalib.model.Athlete` class for details on what is returned. For this method, a full detailed-level attribute set is returned.

## Retrieve Another Athlete

A variation on the above request, this is provided by the `stravalib.client.Client.get_athlete` when called with an athlete ID.

```python
athlete = client.get_athlete(227615)
print("Hello, {}".format(athlete.firstname))
```

See the {py:class}`stravalib.model.Athlete` class for details. Only a summary-level subset of attributes is returned when fetching information about another athlete.

## Update Current Athlete

(This is not yet implemented by stravalib.)


This page is designed to mirror the structure of the documentation at
https://developers.strava.com/docs/reference/#api-Athletes and
describe the methods for working with athlete data in the Strava API.

## Retrieve current athlete

This is the simplest request.  It is provided by the {py:fun}`stravalib.client.Client.get_athlete` when called
with no parameters.

```python
athlete = client.get_athlete()
print("Hello, {}".format(athlete.firstname))
```

See the {py:class}`stravalib.model.Athlete` class for details on what is returned. For this method, a full detailed-level attribute set is returned.

## Retrieve Another Athlete


A variation on the above request, this is provided by the {py:fun}`stravalib.client.Client.get_athlete` when called with an athlete ID.

```python
athlete = client.get_athlete(227615)
print("Hello, {}".format(athlete.firstname))
```

See the {py:class}`stravalib.model.Athlete` class for details.  only summary-level subset of attributes is returned
when fetching information about another athlete.

## Update Current Athlete


(This is not yet implemented by stravalib.)
