# Inheritance

TODO: add text here!!

Stravalib's API is built on top of Strava's 'swagger.json' response which provides a return that in theory maps to the online Strava return specification (spec).

* Overview here of how we generate the API (linking to Jonatan's diagram).
* How we then use `strava_model` to build out objects in `model.py`
* Why we sometimes diverge from the api (undocumented attrs, attrs that are incorrectly typed in the strava spec, etc)

Here we present the inheritance schema for Stravalib.

## Activity-related objects

Below you can see the inheritance pattern of activities.
Strava APi spec defines 3 "levels" of activities:

`DetailedActivity`, `SummaryActivity` and `Activity`

:::{inheritance-diagram} model.DetailedActivity
:parts: -1

:::

## Athlete object hierarchy & inheritance


:::{inheritance-diagram} model.DetailedAthlete
:parts: -1


:::



## Club object hierarchy & inheritance


:::{inheritance-diagram} model.DetailedClub
:parts: -1


:::
