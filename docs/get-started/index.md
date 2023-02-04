# Get Started Using Stravalib

```{toctree}
:hidden:
:caption: Get Started

Install Stravalib <self>
Overview <overview>
Authentication <authenticate-with-strava>
Activities <activities>
Athletes <athletes>

```

```{toctree}
:hidden:
:caption: Contributing
:maxdepth: 2

Contributing Guide <../contributing/how-to-contribute>
Development Guide <../contributing/development-guide>
Build & Release Guide <../contributing/build-release-guide>
New Contributor Resources <../contributing/resources-for-new-contributors>
Change Log <../contributing/documentation-changelog>
```

## Install stravalib

The package is available on PyPI to be installed using `pip`.

```bash
$ pip install stravalib
```

## Using Stravalib
In order to make use of this library, you will need to have access keys for one or more Strava users. [This is a nice tutorial that has information about
setting up a free app within STRAVA](https://medium.com/analytics-vidhya/accessing-user-data-via-the-strava-api-using-stravalib-d5bee7fdde17).
These access keys can be fetched by using helper methods provided by the `Client` class.
See `auth` for more details.

## Stravalib get started tutorials

::::{grid} 1 1 1 2
:class-container: text-center
:gutter: 3

:::{grid-item-card}
:link: authenticate-with-strava
:link-type: doc

✨ **Authenticate with STRAVA** ✨
^^^

To begin using stravalib you will need to first authenticate with
a Strava application connected to your account or one that you
have access to. Learn how to do that here.
:::

:::{grid-item-card}
:link: activities
:link-type: doc

✨ **Work with STRAVA activity data** ✨
^^^
Once you have authenticated, you can begin to access your data
on STRAVA. Here ou will learn how to work with activity data.
:::

:::{grid-item-card}
:link: athletes
:link-type: doc

✨ **Work with STRAVA athlete / social data** ✨
^^^
The API also gives you access to your athlete account information including
friends, followers and more. Learn how to work with that data here.
:::
::::
