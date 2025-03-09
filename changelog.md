# Change Log

## Unreleased

## v2.3.0

### Added

- Add: Support for Python 3.13 (@hugovk, #627)
- Add: Documentation on using auto-token-refresh in stravalib (@lwasser, 622)

### Fixed

- Fix: Setup trusted publishing & enhance publish step security (@lwasser, #617)


### Contributors to this release
@hugovk, @lwasser

## v2.2.0

### Added

- Add: `SummaryAthlete` return to exchange_code_for_token (@lwasser, #552)
- Add: Add more information about how our mock fixture works (@lwasser, #292)
- Add(feature): Automatic token refresh :sparkles: built into stravalib (@lwasser, @jsamoocha, #585)

### Fixed

- Fix: Docs should be linked rather than repeating information (@lwasser, #613)
- Fix: Update `segment_efforts` api and return warnings (@lwasser, #321)

### Contributors to this release
@jsamoocha, @lwasser

## v2.1.0

### Added

- Add: update activities doc page and migrate to myst (@lwasser, #508)
- Add: `get_athlete_zones` method on client (@enadeau, #508)
- Add: tutorial on authenticating with Strava + stravalib + update get-started & docs fixes (@lwasser, #317)
- Add: inheritance diagrams & explain overrides (@lwasser, #531)
- Add: update examples to stravalib 2.x (@lwasser, #581)
- Add: rename RST files to MD (@lwasser, #589)

### Fixed

- Fix: some overrides moved from `DetailedActivity` to `SummaryActivity` (@enadeau, #570)
- Fix: ensures `ActivityType` instances can be compared to str (@jsamoocha, #583)
- Fix: moved several undocumented attributes from `DetailedActivity` to `SummaryActivity` (@jsamoocha, #594)
- Fix: broken link (@lwasser, #597)
- Fix: do not create PDF files in CI (@lwasser, #563)
- Fix: banner URL to relative path (@lwasser, #565)
- Fix: missing comma in all-contributors JSON config (@lwasser, #573)
- Fix: tiny update to streaming data documentation (@lwasser, #588)
- Fix: summary activity undocumented attributes (@jsamoocha, #595)
- Fix: update pre-commit configuration (@lwasser, #591)

### Changed

- Change: Strava API update (@github-actions, #592)

### Contributors to this release
@yotam5 made their first contribution to stravalib!
@jsamoocha, @lwasser, @enadeau, @yotam5

## v2.0.0

### Major Changes in This Release

1. **Breaking:** Added support for Pydantic 2.x; 1.x behavior is no longer supported.
   Refer to [Pydantic’s V2 migration guide](https://docs.pydantic.dev/latest/migration/)
   if you use extensions of Stravalib model classes or Pydantic’s serialization
   mechanisms (`parse_obj()`, `dict()`, `json()`).

2. Removed deprecated (de-)serialization methods `deserialize()`, `from_dict()`,
   and `to_dict()`. Use [Pydantic’s serialization mechanisms](https://docs.pydantic.dev/latest/concepts/serialization/).

3. Renamed `unithelper` module to `unit_helper`. Helper functions like `feet()`
   and `miles()` now return a Pint `Quantity` object.

4. Introduced new types for distances, velocities, durations, and time zones.
   `activity.distance` now returns a `Distance` type. Retrieve distance in meters
   with `activity.distance` or as a `Quantity` using `activity.distance.quantity`.

Please see the migration guide in our docs for more details on the changes.

### Added

- Add: `naive_datetime()` test to the `pydantic-v2 branch`. (@bmeares, #522)
- Add: custom types that pass static type checks (@jsamoocha, #534)
- Add: Strava type hierarchy for Activity type (@jsamoocha, #505)
- Add: Athlete stats (@jsamoocha, #507)
- Add: Summary segments (@jsamoocha, #509)
- Add: SummarySegmentEffort superclass (@jsamoocha, #518)
- Add: test for latlon values (@lwasser, #516)
- Add: correct type returns following clubs/{id} & clubs/{id}/activities spec (@lwasser, #519)

### Fixed

- Fix: Update enhanced types doc (@jsamoocha, #546)
- Fix: Replace invariant with covariant container types (@lwasser, @jsamoocha, #510)
- Fix: generated model using Pydantic v2 (@jsamoocha, #495)
- Fix: Gear and Athlete type hierarchies (+ naive_datetime typing fixes) (@jsamoocha, #526)
- Fix: docstrings in model.py (@lwasser, #484)
- Fix: return types -- athlete clubs endpoint (@lwasser, #517)
- Fix: Updates for activities/id endpoint 🙈 (@lwasser, #520)
- Fix: Activities/{id}/zones & Laps (@lwasser, #524)
- Fix: Rename `unithelper.py` --> `unit_helper.py` (@lwasser, #535)
- Fix: Update & check photos endpoint (@lwasser)
- Fix: Photos endpoint cleanup (@lwasser, #540)
- Fix: Activity Comment check / cleanup (@lwasser, #541)
- Fix: Migrate to covariant types to fix typing (@lwasser, #530)
- Fix: Typing upgrade to Python 3.10+ (@lwasser, #547)
- Fix(docs): Cleanup API docs & add migration guide (@jsamoocha, @lwasser, #537)
- Fix(docs): Clean up reference docs (@lwasser, #537, #545)

### Removed

- Remove: backward compatibility mixin (@jsamoocha, #503)
- Remove: deprecated client methods (@lwasser, #514)

### Contributors to this release

@jsamoocha, @lwasser, @bmeares

- @bmeares made their first contribution in https://github.com/stravalib/stravalib/pull/522 :sparkles:



## v1.7

### Added
- Add: Strava API change - Route objects have a new waypoints attribute (@bot, #480)

### Fixed
- Fix: Docs - add contributing section to top bar for easier discovery and a few small syntax fixes in the docs (@lwasser)
- Fix: `Manifest.in` file - remove example dir (@lwasser, #307)
- Fix: Codecov report wasn't generating correctly (@lwasser, #469)
- Fix: Add sport type to create_activity and create type validator method. NOTE: this fix contains a breaking change in `Client.create_activity()` activity_type is now an optional keyword argument rather than a required positional argument (@lwasser, #279)
- Fix: Fixes the Strava API update bot (@jsamoocha, #477)
- Fix: Cleanup dependencies to only use `pyproject.toml` (@lwasser, #466)
- Fix: use `parse_obj` rather than deserialize internally where possible (@lwasser, #358)

## Removed
- Remove: functional test suite from stravalib (@lwasser, #457)
- Remove: `client.delete_activity` method is no longer supported by Strava (@lwasser, #238)
- Remove/Add: Drop Python 3.9, add Python 3.12 (@lwasser, #487)

### Breaking Changes
If you have been using the `client.delete_activity` method then your code will
no longer work as this method was removed due to being deprecated by Strava. We also are dropping support for Python 3.9 (end of life / no more security fixes in October 2024 and now only getting security fixes) in this release and adding support for 3.12.

### Contributors to this release

@jsamoocha, @lwasser, stravalib bot :)

## v1.6

### Added
- Add: Support for Strava's new read rate limits (@jsamoocha, #446)
- Add: Improved handling of unexpected activity types (@jsamoocha, #454)

### Fixed
- Fix: Forgot to update model CI build to follow new src layout (@lwasser, #438)
- Fix: Type annotation on field that are of type timedelta are now correct (@enadeau, #440)
- Fix: Correct type for ActivityPhoto sizes attribute (@jsamoocha, #444)
- Fix: codespell config - ignore resources dir in tests (@lwasser, #445)
- Fix: Ignore documentation autogenerated api stubs (@lwasser, #447)

### Breaking Changes

A potentially breaking change is that the RateLimiter's `__call__()` method now has
an additional `method` argument representing the HTTP method used for that request.
Existing custom rate limiters from users must be updated to this change.

### Contributors to this release

@jsamoocha @endeau, @lwasser,

## v1.5

### Added

- Stravalib now includes types annotation, the package is PEP 561 compatible (@enadeau, #423)
- Add: Add nox to run tests, build docs, build package wheel/sdist(@lwasser, #395, #397)
- Type annotation for all files in the library (@enadeau, #384, #415)
- Add blacken-docs and codespell to pre-commit & apply on docs (@lwasser, #391)

### Fixed

- Allow parsing of activity with segment of type other that Run and Ride (@JohnScolaro, #434)

### Changed

- Infra: Replace flake8 and isort by ruff (@enadeau, #430)

### Removed

- Remove python 3.8 support following NEP-29 (@enadeau, #416)

### Contributors to this release

@endeau, @lwasser, @JohnScolaro

## v1.4

### Fixed

- Apply flake8 and numpy docstrings to limiter & protocol (@lwasser, #326)
- Update client's stream method to warn when using unofficial parameters (@enadeau, #385)
- Fix docstring in SleepingRateLimitRule (@enadeau)
- Fix: rename `SubscriptionCallback.validate` -> `SubscriptionCallback.validate_token` to avoid conflict with `pydantic.BaseModel` (@lwasser, #394)
- Fix: docstrings in model.py, documentation errors, findfonts warning suppression by removing opengraph (temporarily), typing updates (@lwasser, #387)
- Fix: read the docs is breaking due to pydantic json warnings, also update python version on build and sync pr previews (@lwasser, #412)
- Fix: update master to main in all builds (@lwasser)

### Added

- Type annotation to client file (@enadeau, #384)
- Add: issue templates for easier debugging / guide users (@lwasser, #408)
- Fix: read the docs is breaking due to pydantic json warnings, also update python version on build and sync pr previews (@lwasser, #412)
- Fix: update master to main in all builds (@lwasser)

### Contributors to this release

@endeau, @lwasser, @jsamoocha

## v1.3.3

### Fixed

- Fix: pins pydantic to v1 in pyproject.toml dependencies (@jsamoocha, #382)

## v1.3.2

### Added

- Add: type checking to limiter, protocol and exc file (@enadeau , #374)

### Fixed

- Fix: two minor mistakes in documentation (@enadeau , #375)
- Fix: pins pydantic to v1.10.6 (@lwasser, #380)

### Contributors to this release

@enadeau, @lwasser

- Fix two minor mistakes in documentation (@enadeau , #375)
- Add type checking to limiter, protocol and exc file (@enadeau , #374)
- Apply flake8 and numpy docstrings to all modules limiter & protocol (@lwasser, #326)

## v1.3.1

### Added

- Add: Add field override in class Segment to support all activity types (@solorisx, #368)

### Fixed

- Fix: Bumps Flask version in example code (@jsamoocha, #366)

### Contributors to this release

@solorisx, @jsamoocha

## v1.3.0

### Added

- Add: Adds RPE to activity model (@jsamoocha, #355)
- Add: support sport_type in client.update_activitiy() (@think-nice-things, #360)

### Fixed

- Fix: Move to numpy style docstrings & add black (@lwasser, #365)

### Deprecated

- The `activity_type` parameter in the client method `update_activity()` is deprecated and should be replaced by `sport_type`.

### Contributors to this release

@jsamoocha, @lwasser, @think-nice-things

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

- Fix mutable parameter defaults in rate-limiter util functions (@hozn, #155)
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
