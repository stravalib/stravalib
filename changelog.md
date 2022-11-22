# Change Log

## Unreleased

* Fix: add new attributes for bikes according to updates to Strava API to fix warning message (huaminghuangtw, #239)
* Add an option to mute Strava activity on update (@ollyajoke, #227)
* Update make to build and serve docs and also run current tests (@lwasser,#263)
* FIX: Minor bug in PyPI push and also streamlined action build (@lwasser, #265)
* Fix get_athlete w new attrs for shoes given strava updates to API (@lwasser, #220)
* Refactor deprecated unittest aliases for Python 3.11 compatibility (@tirkarthi, #223)
* Patch: Update readme and fix broken links in docs (@lwasser, #229)
* Improved unknown time zone handling (@jsamoocha, #242)
* Move package to build / setupscm for version / remove setup.py and add CI push to pypi (@lwasser, #259)
* Refactor test suite and implement Ci for tests (@jsamoocha, #246)
* Remove support for python 2.x (@yihong0618, #254)
* Overhaul of documentation, fix links and CI build (@lwasser, #222)

## 0.10.4
* Fix to unicode regression (#217)

0.10.3
------
* Fixes IndexErrors when deserializing empty lists as GPS locations (#216)
* Fix a few fields in Activity model (#201, #214, #207)
* deal with tzname without offset and timedelta in string format (#195)
* Update to docs and repr (#200, #205, #206)
* Now webhooks use the same domain as the rest of API. (#204)
* Setting rate_limit_requests=False in Client causes error (#157)

0.10.2
------
* More fixes to new new authorization scopes (#168)
* Added an example oauth app and some small docs updates.
* Changed missing-attribute warnings to be debug-level logs.

0.10.1
------
* Fixes of authorization_url / new scopes for new oauth (#163, #165)

0.10.0
------
* Implementation of Strava's new auth.  (#162, #163)

0.9.4
-----
* Version bump for dup file upload to pypi. :-[

0.9.3
-----
* Fix mutable parma defaults in rate-limiter util functions (#155)
* Add the missing subscription_permissions attr to Athlete (#156)

0.9.2
-----
* Fix for pip 0.10.0 (paulte) (#149, #150)

0.9.1
-----
* Auto-configure the rate limits (not just usage) from response headers. (#142)

0.9.0
-----
* More API changes to reflect the big privacy changes from Strava. (#139, #140)
* Fix to kom_type attribute (#138)

0.8.0
-----
* Fixes to segment leaderboard models for Strava's API BREAKING CHANGE (#137)
  (See https://groups.google.com/forum/#!topic/strava-api/SsL2ytxtZng)
* Return ObjectNotFound and AccessUnauthorized HTTPError subclasses for 404 and 401
  errors respectively (#134)
* Return None when there are no activity streams (#118)

0.7.0
-----
* Updated Activity for new attributes (#115, #122)
* New segment attributes (JohnnyLChang ) (#106)
* Streams for a route (drixselecta) (#101)
* Activity Uploader improvements (bwalks) (#119)
* Added to_dict() method to model objects (#127)
* Added get_athlete_starred_segments (wjazdbitu) (#117)
* Fixed glitches in activity.laps (#112)
* Fixed bug in club.members (#110)

0.6.6
-----
* Fix for delete_activity (jonderwaater) (#99)

0.6.5
-----
* Updated ActivityPhoto model to support native photos and reverted get_activity_photos behavior for backwards
  compatibility (#98)
* Added missing Club attributes (MMI) (#97)

0.6.4
-----
* Added support for undocumented inclusion of laps in activity details. (#96)
* Added missing parameter for get_activity_photos (#94)
* Added missing activyt pr_count attribute (Wilm0r) (#95)
* add "starred" property on SegmentExplorerResult (mdarmetko) (#92)

0.6.3
-----
* Fixed update_activity to include description (#91)

0.6.2
-----
* More Python3 bugfixes

0.6.1
-----
* Python3 bugfixes (Tafkas, martinogden)
* Added delete_activity
* added context_entries parameter to get_segment_leaderboard method (jedman)

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
* Fixed the _resolve_url to not assume running on **nix** system.

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
