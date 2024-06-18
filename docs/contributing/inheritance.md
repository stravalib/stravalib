# Inheritance

TODO: add text here!!
* Overview here of how we generate the API (linking to Jonatan's diagram).
* How we then use strava_model to build out objects in model.py
* Why we sometimes diverge from the api (undocumented attrs, attrs that are incorrectly typed in the strava spec, etc)


Here we present the inheritance schema for Stravalib.

## Activity-related objects

ha

Below you can see the inheritance pattern of activities.
Strava APi spec defines 3 "levels" of activities:

`DetailedActivity`, `SummaryActivity` and `Activity`

:::{inheritance-diagram} model.DetailedActivity
:parts: -1


:::
