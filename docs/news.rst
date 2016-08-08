Changes
=======

.. contents::

0.6.0
-----
* Use (reuqire) more modern pip/setuptools.
* Full Python 3 support (using Six). (#69)
* Webhooks support (thanks to loisaidasam) (#77)
* explore_segments bugfix (#71)
* General updates to model/attribs (#64, #73, etc.)

0.5.0
-----
* Renamed `Activity.photos` property to `full_photos` due to new conflict with Strava API (#45)

0.4.0
-----
* Supporting new/removed attribs in Strava API (#41, $42)
* Added support for joining/leaving clubs (#43)
* Respect time zones in datetime objects being converted to epochs. (#44)

0.3.0
-----
* Activity streams data (Ghis)
* Friends/followers model attributes (Ghis)
* Support for photos (Ghis)
* Updates for new Strava exposed API attributes (Hans)

0.2.2
-----
* Fixed the _resolve_url to not assume running on **nix system.

0.2.1
-----
* Changed Activity.gear to be a full entity attribute (Strava API changed)

0.2.0
-----
* Added core functionality for Strava API v3.
* Mostly redesigned codebase based on drastic changes in v3 API.
* Dropped support for API v1, v2 and the "scrape" module.

0.1.0
-----
* First proof-of-concept (very alpha) release.
