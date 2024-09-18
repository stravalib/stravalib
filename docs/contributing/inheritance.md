# Stravalib's Inheritance Patterns

Stravalib's API is built directly from Strava's `swagger.json` example response
data. We use the Pydantic `BaseModel` combined with `datacodegen` to build our
base model objects (found in `strava_model.py`), which we then enhance and
update to align with the data actually returned by the Strava API.

This page will help you understand Stravalib's inheritance patterns.

In our experience maintaining Stravalib, the Strava API online specification
and the `swagger.json` file don't always align perfectly with the data actually
returned by Strava. As a result, you will notice that we frequently overwrite
data types to match the actual data we see returned from the Strava API for
each endpoint. [More information on this process can be found here.](ci_api_updates)

Below, we present the inheritance schema for Stravalib.

## Inheritance overview

At a high level, there are two modules:

<!-- stravalib.model link doesn't work but strava_model does not.
I'm not sure why. We can fix this later once we get inheritance diagrams working as we expect them to. There is something funky with how I set up api autodoc.
-->
* {py:mod}`stravalib.model` and
* {py:mod}`stravalib.strava_model`.

`strava_model` is generated automatically using a CI build from the Strava API.
Stravalib uses the model.py module to do a few things:

1. It supports inheritance of the {py:class}`stravalib.model.BoundClientEntity`, which supports API calls for lazily loaded properties,
2. it allows us to override {py:mod}`stravalib.strava_model` attributes that have typed attributes that don't align with the actual API responses, and
3. allows us to add attributes that are found in the returned data but not documented or found in the swagger.json response.

The full inheritance pattern, which includes inheritance from both `strava_model` and `pydantic.BaseModel`, is below.

### Inheritance diagram showing the relationship between strava_model.py and model.py

:::{mermaid}

classDiagram
    direction BT
    %% Activities in model namespace
    `model.MetaActivity` --|> `model.BoundClientEntity`
    `model.SummaryActivity` --|> `model.MetaActivity`
    `model.DetailedActivity` --|> `model.SummaryActivity`

    %% Activities in strava_model namespace
    `strava_model.SummaryActivity` --|> `strava_model.MetaActivity`
    `strava_model.DetailedActivity` --|> `strava_model.SummaryActivity`

    %% Define inheritance relationships between model and strava_model
    `model.MetaActivity` --|> `strava_model.MetaActivity`
    `model.SummaryActivity` --|> `strava_model.SummaryActivity`
    `model.DetailedActivity` --|> `strava_model.DetailedActivity`
:::

## Model object inheritance patterns

The {py:mod}`stravalib.model` module contains core objects that inherit
from and modify objects in {py:mod}`strava_model.py`. The `strava_model.py`
file is generated directly from the Strava `swagger.json` API response.

Our main client class provides methods for making API `GET` and `PUT`
requests. To support these requests and enable lazily loaded operations, all
Strava model meta-level objects inherit from `BoundClientEntity`, which stores the token
credentials needed for authenticated API calls. This ensures that summary and detailed-level objects can also support lazily loaded operations.


### Inheritance diagram showing the relationship between Detailed, Summary and Meta classes and BoundClientEntity

:::{mermaid}
classDiagram
    direction BT
    %% Activities
    MetaActivity --|> BoundClientEntity
    SummaryActivity --|> MetaActivity
    DetailedActivity --|> SummaryActivity

    %% Athletes
    MetaAthlete --|> BoundClientEntity
    SummaryAthlete --|> MetaAthlete
    DetailedAthlete --|> SummaryAthlete

    %% Clubs
    MetaClub --|> BoundClientEntity
    SummaryClub --|> MetaClub
    DetailedClub --|> SummaryClub
:::
