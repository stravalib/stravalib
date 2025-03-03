# Welcome to stravalib

[![All Contributors](https://img.shields.io/github/all-contributors/stravalib/stravalib?color=ee8449&style=flat-square)](#contributors)
[![DOI](https://zenodo.org/badge/8828908.svg)](https://zenodo.org/badge/latestdoi/8828908)
![PyPI](https://img.shields.io/pypi/v/stravalib?style=plastic) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stravalib?style=plastic) [![Documentation Status](https://readthedocs.org/projects/stravalib/badge/?version=latest)](https://stravalib.readthedocs.io/en/latest/?badge=latest) ![Package Tests Status](https://github.com/stravalib/stravalib/actions/workflows/build-test.yml/badge.svg) ![PyPI - Downloads](https://img.shields.io/pypi/dm/stravalib?style=plastic) [![codecov](https://codecov.io/gh/stravalib/stravalib/branch/main/graph/badge.svg?token=sHbFJn7epy)](https://codecov.io/gh/stravalib/stravalib)

The **stravalib** Python package provides easy-to-use tools for accessing and
downloading Strava data from the Strava V3 API. Stravalib provides a `Client` class that supports:

- Authenticating with stravalib
- Managing your authentication to ensure it's current (if you have your environment setup)
- Accessing and downloading Strava activity, club, and profile data
- Making changes to account activities

It also provides support for working with date/time/temporal attributes
and quantities through the [Python Pint library](https://pypi.org/project/Pint/).

## Dependencies

- Python 3.10+
- [Setuptools](https://pypi.org/project/setuptools/) for building stravalib
- Other Python libraries (installed automatically when using pip):
     - [requests](https://pypi.org/project/requests/),
     - [pytz](https://pypi.org/project/pytz/)
     - [pint](https://pypi.org/project/pint/)
     - [arrow](https://pypi.org/project/arrow/),
     - [pydantic 2.x](https://pypi.org/project/pydantic/)

## Installation

stravalib is available on [PyPI](https://pypi.org/project/stravalib/) and can be installed using `pip`:

`pip install stravalib`


## Get started using Stravalib

Most of the methods you will use with stravalib are in the `stravalib.client.Client` class.

You may be interested in the following tutorials to get started

1. [How to create
a Strava app.](https://stravalib.readthedocs.io/en/latest/get-started/authenticate-with-strava.html#authenticate-with-the-strava-api-using-stravalib)
1. [How to refresh and auto refresh your app token using stravalib.](https://stravalib.readthedocs.io/en/latest/get-started//get-started/authenticate-with-strava.html#step-3-refresh-your-token.html)
1. [How to get activities using stravalib.](https://stravalib.readthedocs.io/en/latest/get-started/activities.html)
2. [Athlete data using stravalib](https://stravalib.readthedocs.io/en/latest/get-started/athletes.html)
3. [Unit conversion and stravalib](https://stravalib.readthedocs.io/en/latest/get-started/activities.html#stravalib-offers-unit-conversion-helpers)

We welcome contributions to our tutorials and get-started documentation if you are a stravalib user and want to contribute!


## How to Contribute to Stravalib

### Contributing quickstart

Ready to contribute? Here's how to set up Stravalib for local development.

1. Fork the repository on GitHub

To create your own copy of the repository on GitHub, navigate to the
`stravalib/stravalib <https://github.com/stravalib/stravalib>` repository
and click the **Fork** button in the top-right corner of the page.

2. Clone your fork locally

Use `git clone` to get a local copy of your stravalib repository on your
local filesystem:

```console
git clone git@github.com:your_name_here/stravalib.git
cd stravalib/
```

3. Set up your fork for local development

Read through our [development guide](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html) to learn how to:

* [Run our test suite](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html#about-the-stravalib-test-suite)
* [Build our docs](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html#documentation)
* [Lint and format our code](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html#code-format-and-syntax)

### Building from source

To build the project locally and install in editable mode:

1. access the project root directory
2. run:

```bash
$ pip install -e .
```


### Pull Requests and tests

Please add tests that cover any changes that you make to stravalib. Adding tests will greatly reduce the effort of reviewing
and merging your Pull Request. [Read more about our test suite here.](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html#about-the-stravalib-test-suite). We developed a [mock fixture](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html#tests-the-stravalib-mock-fixture) that ensures that when tests are run, they are not hitting the Strava API.


## Still reading?

The [published sphinx documentation](https://stravalib.readthedocs.io/) provides much more.

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://towardsdatascience.com/@djcunningham0"><img src="https://avatars.githubusercontent.com/u/38900370?v=4?s=100" width="100px;" alt="Danny Cunningham"/><br /><sub><b>Danny Cunningham</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=djcunningham0" title="Documentation">📖</a> <a href="#ideas-djcunningham0" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://hugovk.dev"><img src="https://avatars.githubusercontent.com/u/1324225?v=4?s=100" width="100px;" alt="Hugo van Kemenade"/><br /><sub><b>Hugo van Kemenade</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=hugovk" title="Code">💻</a> <a href="https://github.com/stravalib/stravalib/pulls?q=is%3Apr+reviewed-by%3Ahugovk" title="Reviewed Pull Requests">👀</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www-ljk.imag.fr/membres/Jerome.Lelong/"><img src="https://avatars.githubusercontent.com/u/2910140?v=4?s=100" width="100px;" alt="Jerome Lelong"/><br /><sub><b>Jerome Lelong</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/issues?q=author%3Ajlelong" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://vortza.com"><img src="https://avatars.githubusercontent.com/u/1788027?v=4?s=100" width="100px;" alt="Jonatan Samoocha"/><br /><sub><b>Jonatan Samoocha</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=jsamoocha" title="Code">💻</a> <a href="https://github.com/stravalib/stravalib/pulls?q=is%3Apr+reviewed-by%3Ajsamoocha" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/stravalib/stravalib/commits?author=jsamoocha" title="Documentation">📖</a> <a href="#maintenance-jsamoocha" title="Maintenance">🚧</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.leahwasser.com"><img src="https://avatars.githubusercontent.com/u/7649194?v=4?s=100" width="100px;" alt="Leah Wasser"/><br /><sub><b>Leah Wasser</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=lwasser" title="Code">💻</a> <a href="https://github.com/stravalib/stravalib/pulls?q=is%3Apr+reviewed-by%3Alwasser" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/stravalib/stravalib/commits?author=lwasser" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://eagereyes.org/"><img src="https://avatars.githubusercontent.com/u/20810?v=4?s=100" width="100px;" alt="Robert Kosara"/><br /><sub><b>Robert Kosara</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/issues?q=author%3Aeagereyes" title="Bug reports">🐛</a> <a href="#question-eagereyes" title="Answering Questions">💬</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/yotam5"><img src="https://avatars.githubusercontent.com/u/69643410?v=4?s=100" width="100px;" alt="Yotam"/><br /><sub><b>Yotam</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=yotam5" title="Documentation">📖</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/enadeau"><img src="https://avatars.githubusercontent.com/u/12940089?v=4?s=100" width="100px;" alt="Émile Nadeau"/><br /><sub><b>Émile Nadeau</b></sub></a><br /><a href="https://github.com/stravalib/stravalib/commits?author=enadeau" title="Code">💻</a> <a href="https://github.com/stravalib/stravalib/pulls?q=is%3Apr+reviewed-by%3Aenadeau" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/stravalib/stravalib/commits?author=enadeau" title="Documentation">📖</a> <a href="#maintenance-enadeau" title="Maintenance">🚧</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
