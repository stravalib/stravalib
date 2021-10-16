Welcome to Stravalib!
======================

.. toctree::
   :hidden:
   :maxdepth: 2

   Home <self>
   Get Started <get-started/index>
   How to Contribute <contributing>
   Change Log <changelog>
   API Reference Summary <reference>


**stravalib** is a python library for interacting with
`version 3 <https://developers.strava.com/docs/reference/>`_ of the
`Strava <https://www.strava.com>`_  API.

This library is designed provide a simple and easy-to-use object model paradigm for interacting
with the API, support modern versions of Python (2.7, 3.2+), and expose the full functionality of the REST API.

**Why use stravalib?**  The Strava REST API is fairly straightforward.  The main reasons to use something like
stravalib would be:

- Result structs (dicts) are returned as more "strongly typed" model objects.
- Relationships can be traversed on model objects to pull in related content "seamlessly".
- Units and date/time/durations types are converted to python objects to facilite converting and displaying these values.
- Built-in support for rate limiting and more intelligent error handling.

Getting Started
---------------

The package is available on PyPI to be installed using ``easy_install`` or pip:

.. code-block:: none

   shell$ pip install stravalib

Of course, by itself this package doesn't do much; it's a library.  So it is more likely that you will
list this package as a dependency in your own `install_requires` directive in `setup.py`.  Or you can
download it and explore Strava content in your favorite python REPL.

In order to make use of this library, you will need to have access keys for one or more Strava users.
These access keys can be fetched by using helper methods provided by :class:`stravalib.client.Client` class.
See :ref:`auth` for more details.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
