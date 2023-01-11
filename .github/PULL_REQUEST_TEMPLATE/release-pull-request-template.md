# Stravalib Release Pull Request Template

Please use this template when you are preparing to make a release to stravalib

* [An overview of our release workflow can be found in our documentation.](https://stravalib.readthedocs.io/contributing/build-release-guide.md)
* [Before making a release be sure to check out test PyPI](https://pypi.org/project/stravalib/) to ensure that the build is working properly.

## Release checklist
- [ ] Be sure to clearly specify what version you are bumping to in the PR title: Example: Bump to version x.x
- [ ] Add the version of this release to our changelog
- [ ] Organize items changes under the new version in groups as follows: Added, Fixed and Changed
- [ ] Add all contributors to the release below those sections
- [ ] Wait for a maintainer to approve the pull request. Then merge! You are now ready to create the release.

The changelog should look something like this:

```
## Unreleased

## New version here: e.g. v1.0.0

### Added
* Add: Add an option to mute Strava activity on update (@ollyajoke, #227)

### Fixed
* Fix: add new attributes for bikes according to updates to Strava API to fix warning message (@huaminghuangtw, #239)

### Changed
* Change: Improved unknown time zone handling (@jsamoocha, #242)

### Contributors to this release
@jsamoocha, @yihong0618, @tirkarthi, @huaminghuangtw, @ollyajoke, @lwasser
```

Once this PR is merged you are ready to

- [ ] Create a tagged release on GitHub using the same version that you merged in the changelog added here
- [ ] When you publish that release, the GitHub action to push to PyPI will be invoked.
