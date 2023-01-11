# Stravalib build and release guide

This page outlines the build structure and release workflow for stravalib.

## Stravalib packaging overview

For packaging we use `setuptools` for packaging and the `build` package to
create a wheel and distribution for pushing to PyPI.

## Package versioning
To keep track of stravalib versioning, we use `setuptools_scm`. Setuptools_scm
is a behind the scenes tool that uses the most current tag in the repository
to determine what version of the package is being built.

`setuptools_scm` creates a `_version_generated.py` file upon build using that tag.

```{warning}
If you build the package locally, the `_version_generated.py` file should NEVER
be committed to version control. It should be ignored via our `.gitignore` file
```

If you wish to build stravalib locally to check out the .whl and distribution
tarball you can use:

```
make build
```

When you run `make build`, it will do a few things

1. it will create a `dist` directory with the wheel and the tarball distributions of the package in it. You can see the version of `stravalib` in the name of those files:

```bash
dist/
   stravalib-1.0.0.post27-py3-non-any.whl
   stravalib-1.0.0.post27.tar.gz

```

2. `make build` also invokes `setuptools_scm` to create a `_version_generated.py` file in the stravalib package directory:

```bash
stravalib/
    stravalib/
        _version_generated,py
```

## Our PyPI release workflow

The entire release workflow is automated and can be completed on fully
in the GitHub.com interface if you wish.

We follow [semantic version](https://semver.org/) best practices for our release workflow as follows:

* MAJOR version when you make incompatible API changes
* MINOR version when you add functionality in a backwards compatible manner
* PATCH version when you make backwards compatible bug fixes

### How to make a release to PyPI

```{note}
The build workflow explained below will run and push to test PyPI on every merge to the master branch of stravalib. Thus before you create a pull request to initiate a new release, please check out stravalib on [test pypi](https://pypi.org/project/stravalib/) to:

1. Make sure that the README file and other elements are rendering properly
2. You can also install the package from test PyPI as an additional check!
```

To make a release:

* ✔️ 1. Determine with the other maintainers what release version we are moving to. This can be done in an issue.
* ✔️ 2. Create a new **pull request** using the release pull request template that does the following:

    * Organizes the changelog.md unreleased items into added, fixed and changed sections
    * Lists contributors to this release using GitHub handles
    * Adds the version number of that specific release.

Below you can see an example of what these changelog changes looked like when we bumped to
version 1.0 of stravalib. *(Some fo the original change log content is removed to keep this page shorter)*

```
## Unreleased

## v1.0.0

### Added
* Add: Add an option to mute Strava activity on update (@ollyajoke, #227)
* Add Update make to build and serve docs and also run current tests (@lwasser,#263)
* Add: Move package to build / `setuptools_scm` for version / remove setup.py and add CI push to pypi (@lwasser, #259)

### Fixed
* Fix: add new attributes for bikes according to updates to Strava API to fix warning message (@huaminghuangtw, #239)
* Fix: Refactor deprecated unittest aliases for Python 3.11 compatibility (@tirkarthi, #223)
* Patch: Update readme and fix broken links in docs (@lwasser, #229)

### Changed
* Change: Refactor test suite and implement Ci for tests (@jsamoocha, #246)
* Change: Remove support for python 2.x (@yihong0618, #254)

### Contributors to this release
@jsamoocha, @yihong0618, @tirkarthi, @huaminghuangtw, @ollyajoke, @lwasser

```

* ✔️ 3. Once another maintainer approves the pull request, you can merge it.

You are now ready to make the actual release.
* ✔️ 4. In GitHub.com go to `Releases` and prepare a new release. When you create that release you can specify the tag for this release.

Use `v` in the tag number to maintain consistency with previous releases.

This is the ONLY manual step in the release workflow. Be sure to create the correct tag number: example `v1.0.1` for a patch version.

Copy the updated changelog information into the body of the release.

* ✔️ 5. Now hit `publish release`.

When you publish the release, a GitHub action will be enabled that will:

1. build the wheel and tarball and
2. push the distribution to PyPI!



Congratulations! You've just created a release of stravalib!
