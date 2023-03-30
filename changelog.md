# Change Log

## Unreleased

- Add: Adds RPE to activity model (@jsamoocha, #355)
- Fix: Move to numpy style docstrings & add black (@lwasser, #365)

## v1.3.0rc0

### Added

- Adds Strava API changes, and datamodel-code-generator bug fix (@jsamoocha, #333)
- Add: Replace full legacy model with extensions from the generated pydantic model (@jsamoocha, #324)
- Add: Add support for lazy loading related entities (@jsamoocha, #322)
- Add: Add support for nested model attributes(@jsamoocha, #316)
- Add: replaces implementations for the classes Club, Gear, ActivityTotals, AthleteStats, and Athlete by the generated Pydantic model & backwards compatibility (@jsamoocha, #315)
- Add: Workflow for updating strava model when the API changes (@jsamoocha, #302)
- Add: `pydantic_autodoc` to sphinx build and reconfigure api structure - p1 (@lwasser, #326)

### Fixed

- Fix: Corrects attribute lookup for enum values (@jsamoocha,#329)

### Deprecated

- The `BaseEntity` methods `deserialize()`, `from_dict()`, and `to_dict()` are deprecated and will raise a `DeprecationWarning` when they're used. They should be replaced by the pydantic methods `parse_obj()` and `dict()` or `json()`.

### Removed

- The complete `attributes` module
- All the abstract entity types (e.g. `IdentifiableEntity`, `LoadableEntity`) from the `model` module
- Constants used for activity types such as `Activity.RIDE`
- `HeartrateActivityZone`, `PowerActivityZone`, `PaceActivityZone` as subtypes of `BaseActivityZone` (the latter is retained)
- Everything related to segment leaderboards as this is not supported by Strava anymore

### Contributors to this release

@jsamoocha, @lwasser, @oliverkurth

## v1.2.0

### Added

- Add: Upload photo to activity (@gitexel, #318)
- Add: Support uploading `activity_file` object with type `bytes` (@gitexel, #308)
- Add: Pre-commit hook + instructions and configure precommit.ci bot (@lwasser, #293)

### Fixed

- Fix: Internal warnings should be ignored in tests (@jsamoocha, #319)
- Fix: `setuptools_scm` bug when installing stravalib remotely via GitHub (@lwasser, #331)
- Fix: fix LatLon unmarshal from string type (@oliverkurth, #334)
- Fix: allows arithmetic and comparison between multiple quantities (@jsamoocha, #335)

### Contributors to this release

@oliverkurth, @gitexel, @jsamoocha, @lwasser

## v1.1.0

### Added

- Add: Development & build/release guide to documentation, edit button to documentation theme, pr template for release (@lwasser, #289)
- Add: Integration tests for /routes/{id} and /segments/starred (GET) (@jsamoocha, #250 (partial))
- Add: Add integration tests for all POST/PUT client methods (@jsamoocha, #250 (partial))
- Add: code cov to test suite (@lwasser, #262)
- Add: add code of conduct to the repo, update contributing guide + readme badges (@lwasser, #269, #274)
- Add: pull request templates for regular pr and release (@lwasser, #294)
- Add: Support for python 3.11

### Fixed

- Fix: Move docs to `furo` theme, add `myst` support for markdown, include CONTRIBUTING.md in documentation, enhance intro documentation page and add linkcheck to docs build (@lwasser, #276)
- Fix: deprecated set-output command in actions build (@yihong0618, #272)
- Fix: Add readthedocs config file to ensure build installs using pip (@lwasser, #270)

### Changed

- Change: Replace `units` dependency by `pint` (@jsamoocha, #281)

### Removed

- Remove: Support for python 3.7

### Contributors to this release

@lwasser, @yihong0618, @jsamoocha

## v1.0.0

### Added

- Add: Add an option to mute Strava activity on update (@ollyajoke, #227)
- Add Update make to build and serve docs and also run current tests (@lwasser,#263)
- Add: Move package to build / `setuptools_scm` for version / remove setup.py and add CI push to pypi (@lwasser, #259)

### Fixed

- Fix: add new attributes for bikes according to updates to Strava API to fix warning message (@huaminghuangtw, #239)
- Fix: Minor bug in PyPI push and also streamlined action build (@lwasser, #265)
- Fix: `get_athlete` w new attrs for shoes given strava updates to API (@lwasser, #220)
- Fix: Refactor deprecated unittest aliases for Python 3.11 compatibility (@tirkarthi, #223)
- Patch: Update readme and fix broken links in docs (@lwasser, #229)

### Changed

- Change: Improved unknown time zone handling (@jsamoocha, #242)
- Change: Refactor test suite and implement Ci for tests (@jsamoocha, #246)
- Change: Remove support for python 2.x (@yihong0618, #254)
- Change: Overhaul of documentation, fix links and CI build (@lwasser, #222)

### Contributors to this release

@jsamoocha, @yihong0618, @tirkarthi, @huaminghuangtw, @ollyajoke, @lwasser

## 0.10.4

- Fix to unicode regression (@hozn, #217)

## 0.10.3

- Fixes IndexErrors when deserializing empty lists as GPS locations (@hozn, #216)
- Fix a few fields in Activity model (@hozn, #201, #214, #207)
- deal with tzname without offset and timedelta in string format (@hozn, #195)
- Update to docs and repr (@hozn, #200, #205, #206)
- Now webhooks use the same domain as the rest of API. (@hozn, #204)
- Setting rate_limit_requests=False in Client causes error (@hozn, #157)

## 0.10.2

- More fixes to new new authorization scopes (@hozn, #168)
- Added an example oauth app and some small docs updates.
- Changed missing-attribute warnings to be debug-level logs.

## 0.10.1

- Fixes of authorization_url / new scopes for new oauth (@hozn, #163, #165)

## 0.10.0

- Implementation of Strava's new auth. (@hozn, #162, #163)

## 0.9.4

- Version bump for dup file upload to pypi. :-[

## 0.9.3

- Fix mutable parma defaults in rate-limiter util functions (@hozn, #155)
- Add the missing subscription_permissions attr to Athlete (@hozn, #156)

## 0.9.2

- Fix for pip 0.10.0 (@paulte, #149, #150)

## 0.9.1

- Auto-configure the rate limits (not just usage) from response headers. (@hozn, #142)

## 0.9.0

- More API changes to reflect the big privacy changes from Strava. (@hozn, #139, #140)
- Fix to kom_type attribute (@hozn, #138)

## 0.8.0

- Fixes to segment leaderboard models for Strava's API BREAKING CHANGE (@hozn, #137)
  (See https://groups.google.com/forum/#!topic/strava-api/SsL2ytxtZng)
- Return ObjectNotFound and AccessUnauthorized HTTPError subclasses for 404 and 401
  errors respectively (@hozn, #134)
- Return None when there are no activity streams (@hozn, #118)

## 0.7.0

- Updated Activity for new attributes (@hozn, #115, #122)
- New segment attributes (@JohnnyLChang, #106)
- Streams for a route (@drixselecta, #101)
- Activity Uploader improvements (@bwalks, #119)
- Added to_dict() method to model objects (@hozn, #127)
- Added get_athlete_starred_segments (@wjazdbitu, #117)
- Fixed glitches in activity.laps (@hozn, #112)
- Fixed bug in club.members (@hozn, #110)

## 0.6.6

- Fix for delete_activity (@jonderwaater, #99)

## 0.6.5

- Updated ActivityPhoto model to support native photos and reverted get_activity_photos behavior for backwards
  compatibility (@hozn, #98)
- Added missing Club attributes (MMI) (@hozn, #97)

## 0.6.4

- Added support for undocumented inclusion of laps in activity details. (@hozn, #96)
- Added missing parameter for get_activity_photos (@hozn, #94)
- Added missing activyt pr_count attribute (@Wilm0r, #95)
- add "starred" property on SegmentExplorerResult (@mdarmetko, #92)

## 0.6.3

- Fixed update_activity to include description (@hozn, #91)

## 0.6.2

- More Python3 bugfixes

## 0.6.1

- Python3 bugfixes (@Tafkas, @martinogden)
- Added delete_activity
- added context_entries parameter to get_segment_leaderboard method (@jedman)

## 0.6.0

- Use (require) more modern pip/setuptools.
- Full Python 3 support (using Six). (@hozn, #69)
- Webhooks support (thanks to loisaidasam) (@hozn, #77)
- explore_segments bugfix (@hozn, #71)
- General updates to model/attribs (@hozn, #64, #73, etc.)

## 0.5.0

- Renamed `Activity.photos` property to `full_photos` due to new conflict with Strava API (@hozn, #45)

## 0.4.0

- Supporting new/removed attribs in Strava API (@hozn, #41, #42)
- Added support for joining/leaving clubs (@hozn, #43)
- Respect time zones in datetime objects being converted to epochs. (@hozn, #44)

## 0.3.0

- Activity streams data (Ghis)
- Friends/followers model attributes (Ghis)
- Support for photos (Ghis)
- Updates for new Strava exposed API attributes (@hozn)

## 0.2.2

- Fixed the \_resolve_url to not assume running on **nix** system.

## 0.2.1

- Changed Activity.gear to be a full entity attribute (Strava API changed)

## 0.2.0

- Added core functionality for Strava API v3.
- Mostly redesigned codebase based on drastic changes in v3 API.
- Dropped support for API v1, v2 and the "scrape" module.

## 0.1.0

- First proof-of-concept (very alpha) release.
