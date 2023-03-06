# Welcome to the Stravalib Documentation!

::::{grid} 2
:reverse:

:::{grid-item}
:columns: 12
:class: sd-fs-3

stravalib is a open source Python package that makes it easier for you to authenticate
with the Strava v3 REST API, and access your STRAVA data using
the Python programming language.

```{only} html
![GitHub release (latest by date)](https://img.shields.io/github/v/release/stravalib/stravalib?color=purple&display_name=tag&style=plastic)
[![](https://img.shields.io/github/stars/stravalib/stravalib?style=social)](https://github.com/pyopensci/contributing-guide)
[![DOI](https://zenodo.org/badge/8828908.svg)](https://zenodo.org/badge/latestdoi/8828908)

```
:::
::::

::::{grid} 1 1 1 2
:class-container: text-center
:gutter: 3

:::{grid-item-card}
:link: get-started/index
:link-type: doc

✨ **Get Started Using Stravalib** ✨
^^^

New to Stravalib? This section is for you!
:::

:::{grid-item-card}
:link: contributing/how-to-contribute
:link-type: doc

✨ **Want to contribute?** ✨
^^^
We welcome contributions of all kinds to stravalib. Learn more about the many
ways that you can contribute.
:::

:::{grid-item-card}
:link: reference
:link-type: doc

✨ **Package Code (API) Documentation** ✨
^^^
Documentation for every method and class available to you
in the stravalib package.
:::
::::

## About the stravalib Python package

**stravalib** is a Python library for interacting with
[version 3](https://developers.strava.com/docs/reference/) of the
[Strava](https://www.strava.com) API. Our goal is to expose the entire user-facing
Strava V3 API.

The **stravalib** Python package provides easy-to-use tools for accessing and
downloading Strava data from the Strava V3 web service. Stravalib provides a
`Client` class that supports:

* Authenticating with stravalib
* Accessing and downloading strava activity, club and profile data
* Making changes to account activities

It also provides support for working with date/time/temporal attributes
and quantities through the [Python Pint library](https://pypi.org/project/Pint/).

## Why use stravalib?

There are numerous reasons to use stravalib in your workflows:

* Stravalib returns your data in structured Python dictionaries with associated data types that make it easier to work with the data in Python.
* Relationships can be traversed on model objects to pull in related content "seamlessly".
* dates, times and durations are imported as Python objects making it easier to convert and work with this data.
* Stravalib provides built-in support for rate-limiting
*  and more intelligent error handling.


```{toctree}
:hidden:
:maxdepth: 2

🏠 Home <self>
```

```{toctree}
:hidden:
:caption: Get Started

Get Started <get-started/index>

```

```{toctree}
:hidden:
:caption: API Documentation
:maxdepth: 2

Code/API Reference <reference>
```
