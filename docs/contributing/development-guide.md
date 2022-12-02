# Development Guide for Anyone Who Wants to Contribute to Stravalib

```{note}  
Please make sure that you've read our [contributing guide](how-to-contribute.md) before reading this 
guide. 
```

## Fork and clone the stravalib repository

### 1. Fork the repository on GitHub
To create your own copy of the repository on GitHub, navigate to the
[stravalib/stravalib](https://github.com/stravalib/stravalib) repository
and click the **Fork** button in the top-right corner of the page.

### 2. Clone your fork locally
Use ``git clone`` to create a local copy of your stravalib repository on your
local filesystem:

```bash
$ git clone git@github.com:your_name_here/stravalib.git
$ cd stravalib/
```

Once you have cloned the repo locally, you are ready to create the 
development environment.

## Setup a local development environment 

We suggest that you create a local virtual environment to work on this 
package. The steps to do that below use a `conda` environment but you are welcome to 
use pip / `virtualenv` or whatever environment manager that you prefer. 

### Set up your local development environment using conda

Instructions below are for doing that using **conda**. However feel free to 
create your environment using `pip` / `virtualenv` or another tool too.

To begin, install the conda environment.
This will create a local conda environment called `stravalib_dev`

```bash
$ conda env create -f environment.yml
```

Next, activate the environment.

```bash
$ conda activate stravalib_dev
```

Finally install the package dependencies and the `stravalib` package in 
development / editable mode (-e`). Editable mode allows you to make updates
to the package and test them in realtime. 

```bash
# install the package requirements
$ pip install -r requirements.txt
# Install stravalib in editable mode 
$ pip install -e .
```

## Code style and linting

```{warning}
IMPORTANT: THIS SECTION WILL BE UPDATED ONCE WE IMPLEMENT BLACK AND FLAKE8

* black
* isort 
```

We currently use flake8 in our GitHub actions continuous integration build. 
However we will be updating this to include black and isort in the near 
future. THis section will be revised with instructions when update that 
happens!

## Code format and syntax 

### Docstrings 

**All docstrings** should follow the
[numpy style guide](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard).
All functions/classes/methods should have docstrings with a full description of all
arguments and return values.

```{warning}
This also will be updated once we implement a code styler 
While the maximum line length for code is automatically set by *Black*, docstrings
must be formatted manually. To play nicely with Jupyter and IPython, **keep docstrings
limited to 79 characters** per line. 

```

## About the stravalib test suite

Tests for stravalib are developed and run using `pytest`. We have two 
sets of tests that you can run:

1. functional end-to-end test suite: this test set requires an API key to run.
1. unit tests that are setup to run on CI. These tests use mock 
instances of the API to avoid needed to setup an API key yourself locally. 

## Unit / Mocked test suite

```{warning}
We will add more information about the test suite in the near future
```

We have setup the test suite to run on the stravalib package as installed.
Thus when running your tests it is critical that you have a stravalib 
development environment setup and activated with the stravalib package 
installed from your fork using pip `pip install .`

You can run the tests using make as specified below. Note that when you run 
the tests this way, they will run in a temporary environment to ensure that 
they are running against the installed version of the package that you are working on. 

To run the test suite use:

```
make test
```

## Functional end-to-end test suite 

The functional (end-to-end) test suite is set up to hit the STRAVA api.
You will thus need an app setup in your Strava account to run the test suite.
We recommend that you create a dummy account for this with a single activity to avoid
any chances of your data being unintentionally modified. Once you have the app setup
and a valid access_token for an account with at least one activity, follow the steps
below.

1. Rename the file `stravalib/stravalib/tests/test.ini-example` to `test.ini`
2. Add your API token to the file by replacing:

```bash
access_token = xxxxxxxxxxxxxxxx
```
with: 

```bash
access_token = your-authentication-token-value-here
```

NOTE: this token needs to have write access to your account. 
We recommend that you create
a dummy account to ensure you aren't modifying your actual account data.

3. Add a single activity id to your dummy account using stravalib:

```bash
activity_id = a-valid-activity-id-here
```

You are now ready to run the test suite. To run tests on python 3.x run:

```bash
$ pytest
```

For integration tests that should be run independently from Strava, there's a pytest
fixture :func:`~stravalib.tests.integration.conftest.mock_strava_api`
that is based on :class:`responses.RequestsMock`.
It prevents requests being made to the actual Strava API and instead registers responses
that are based on examples from the published Strava API documentation. Example usages of
this fixture can be found in the :mod:`stravalib.tests.integration.test_client` module.


## Documentation

The documentation for this library are created using `sphinx`.
Stravalib documentations is hosted on [ReadtheDocs](https://readthedocs.org)
The final build that you see on readthedocs happens on the readthedocs website. Our CI action to build the documentation only tests that 
the build is working as planned. 

The badge below (also on our README.md file) tells you whether the 
readthedocs build is passing.

[![Documentation Status](https://readthedocs.org/projects/stravalib/badge/?version=latest)](https://stravalib.readthedocs.io/en/latest/?badge=latest)

Documentation will be updated on all merges to the master branch of 
stravalib. 

```{warning}
In the future we plan to add link testing to our CI build.
```
### Build documentation locally  

To build the documentation, first activate your stravalib development 
environment which has all of the packages required to build the documentation. Then, use the command:

```bash
$ make -C docs 
```

You can then open up the documentation locally in a web browser by opening the following
file in a web browser on your computer:

```
/your-path-to-stravalib-dir/stravalib/docs/_build/html/index.html
```

### Build locally with a live server 

We use sphinx-autobuild to build the documentation in a live web server. 
This allows you to see your edits automatically as you are working on the 
text files of the documentation. To run the live server use: 
```bash
$ make -C docs serve
```

### Cleanup documentation folders 

To clean up the documentation folders, run the following command from the 
root of the stravalib directory: 

```bash
$ make -C docs clean
```

### Stravalib API Documentation 

```{warning}
ThIS SECTION WILL BE UPDATED IN THE NEAR FUTURE

The API reference is manually assembled in `doc/api/index.rst`.
The *autodoc* sphinx extension will automatically create pages for each
function/class/module listed there.

You can reference classes, functions, and modules from anywhere (including docstrings)
using <code>:func:\`package.module.function\`</code>,
<code>:class:\`package.module.class\`</code>, or
<code>:mod:\`package.module\`</code>.
Sphinx will create a link to the automatically generated page for that
function/class/module.
```

### About the documentation CI build

Once you create a pull request, GitHub actions will build the docs and 
check for any syntax or url errors. Once the PR is approved and merged into the master branch of the `stravalib/stravalib`
repository, the docs will build and be [available at the readthedocs website](https://stravalib.readthedocs.io/).