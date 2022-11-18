Contribute to Stravalib
============================


Get Started!
============

Ready to contribute? Here's how to set up Stravalib for local development.

1. Fork the repository on GitHub
--------------------------------

To create your own copy of the repository on GitHub, navigate to the
`stravalib/stravalib <https://github.com/stravalib/stravalib>`_ repository
and click the **Fork** button in the top-right corner of the page.

2. Clone your fork locally
--------------------------

Use ``git clone`` to get a local copy of your stravalib repository on your
local filesystem::

    $ git clone git@github.com:your_name_here/stravalib.git
    $ cd stravalib/

3. Set up your local development development environment
---------------------------------------------------------
Once you have cloned the repo locally, you are ready to setup your development environment.

We suggest that you create a local virtual environment to work on this package. Instructions
below are for doing that using _conda_. However feel free to create your environment using
pip too.

To begin, install the conda environment::

    $ conda env create -f environment.yml

This will create a local conda environment called stravalib_dev
Next, activate the environment::

    $ conda activate stravalib_dev

Finally install the dependencies and the stravalib package in development mode::

    $ pip install -e .
    $ pip install -r requirements.txt


Test suite
~~~~~~~~~~~
Tests for stravalib are developed using ``pytest``.
Currently, the functional (end-to-end) test suite is set up to actually hit the strava api.
You will thus need an app setup in your Strava account to run the test suite.
We recommend that you create a dummy account for this with a single activity to avoid
any chances of your data being unintentionally modified. Once you have the app setup
and a valid access_token for an account with at least one activity, follow the steps
below.

1. Rename the file stravalib/stravalib/tests/test.ini-example --> test.ini
2. Add your API token to the file by replacing::

    access_token = xxxxxxxxxxxxxxxx

    with

    access_token = your-token-value-here

NOTE: this token needs to have write access to your account. We recommend that you create
a dummy account to ensure you aren't modifying your actual account data.

3. Add a single activity id::

    activity_id = a-valid-activity-id-here

You are now ready to run the test suite. To run tests on python 3.x run ::

    $ pytest

For integration tests that should be run independently from Strava, there's a pytest
fixture :func:`~stravalib.tests.integration.conftest.mock_strava_api`
that is based on :class:`responses.RequestsMock`.
It prevents requests being made to the actual Strava API and instead registers responses
that are based on examples from the published Strava API documentation. Example usages of
this fixture can be found in the :mod:`stravalib.tests.integration.test_client` module.

Documentation
~~~~~~~~~~~~~~
The docs for this library are created using `sphinx`.
To build the documentation, use the command::

    $ make docs -B

You can then open up the documentation locally in a web browser by opening the following
file in a web browser on your computer:

/your-path-to-stravalib-dir/stravalib/docs/_build/html/index.html

About the documentation CI build
--------------------------------
Once your create a pull request, GitHub actions will build the docs and check for any syntax
or url errors. Once the PR is approved and merged into the master branch of the ``stravalib/stravalib``
repository, the docs will build and then get deployed to gh-pages as a live website to:

TODO: ADD URL here. this won't work until the website is live.

