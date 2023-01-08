# How to Contribute to Stravalib

**Thank you for considering contributing to stravalib!**
This is a community-driven project. It's people like you that make it useful and
successful. We welcome contributions of all kinds. Below are some of the
ways that you can contribute to `stravalib`:

* Submit bug reports and feature requests
* Write tutorials or examples
* Fix typos and improve the documentation
* Submit code fixes

[Please read our development guide](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html)
if you are interested in submitting a pull request to suggest changes to
our code or documentation.

## Contribution ground rules
The `stravalib` maintainers work on `stravalib` in their free time because
they love the package's contribution to the Python ecosystem. As such we
value contributions but also value respectful interactions with `stravalib` users.

**Please be considerate and respectful of others** in all of your communications
in this repository.
Everyone must abide by our [Code of Conduct](https://github.com/stravalib/stravalib/blob/master/CODE_OF_CONDUCT.md).
Please read it carefully. Our goal is to maintain a diverse community of
`stravalib` users and contributors that's pleasant for everyone.

## How to start contributing to stravalib
If you are thinking about submitting a change to stravalib documentation or
code, please start by [submitting an issue in our GitHub repository](https://github.com/stravalib/stravalib/issues/).
We will use that issue to communicate with you about:

1. Whether the change is in scope for the project
2. Any obstacles that you need help with or clarification on.

### Want to submit a pull request with changes to our code or documentation?

We welcome changes to stravalib through pull requests. Before you submit a
pull request please be sure to:

1. Read this document fully
2. Submit an issue about the change as discussed below and
2. [Read our development guide](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html)

### How to report a bug in stravalib or typo in our documentation
Found a bug? Or a typo in our documentation? We want to know about it!
To report a bug or a documentation issue, please submit an issue on GitHub.

If you are submitting a bug report, **please add as much
detail as you can about the bug**. Remember: the more information we have, the easier it
will be for us to solve your problem.

### Documentation fixes
If you're browsing the documentation and notice a typo or something that could be
improved, please let us know by creating an issue. We also welcome you to
submit a documentation fix directly to us using a pull request to our
repository.

## An overview of our stravalib git / GitHub workflow
We follow the [git pull request workflow](https://www.asmeurer.com/git-workflow/) to
make changes to our codebase.
Every change made goes through a pull request, even our own, so that our
[continuous integration](https://en.wikipedia.org/wiki/Continuous_integration) services
can check that the code is up to standards and passes all of our tests.

This workflow allows our  *master* branch to always be stable.

### General guidelines for pull requests (PRs):

* **Open an issue first** describing what you want to do. If there is already an issue that matches your PR, leave a comment there instead to let us know what you plan to do. Be as specific as you can in the issue.
* Each pull request should contain a **small** and logical collection of changes directly related to the issue that you opened.
* Larger changes should be broken down into smaller components and integrated
  separately.
* Bug fixes should be submitted in separate PRs.
* Describe what your pull request changes and *why* this is a good thing (or refer to the issue that you opened if it contains that information). Be as specific as you can.
* Do not commit changes to files that are irrelevant to your feature or bugfix (eg: `.gitignore`, IDE project files, etc).
* Write descriptive commit messages that describe what your change is.
* Be willing to accept feedback and to work on your code through a pull request. We don't want to break other users' code, so care must be taken not to introduce bugs.
* Be aware that the pull request review process is not immediate. The time that it takes to review a pull request is generally proportional to the size of the pull request. Larger pull requests may take longer to review and merge.

### Testing your code
Automated testing ensures that our code is as free of bugs as it can be.
It also lets us know immediately if a change that we make breaks any other part
of the code.

All of our test code and data are stored in the `tests` directory within the
`stravalib` package directory.
We use the [pytest](https://docs.pytest.org/en/latest/) framework to run the
test suite.

If you are submitting a code fix or enhancement, and know how to write tests,
please include tests for your code in your pr. This helps us ensure that your
change doesn't break any of the existing functionality.

Tests also help us be confident that we won't break your code in the future.

If you're **new to testing**, please review existing test files for examples
of how to create tests.

**Don't let the tests keep you from submitting your contribution!**
If you're not sure how to do this or are having trouble, submit your pull
request anyway. We will help you create the tests and sort out any kind of problem during code review.

You can learn more about our test suite in the development guide. However,
if you wish to run the test suite locally, you can use:

```bash
make test
```

### Test coverage
We use `codecov` implemented through the `pytest-cov` extension to sphinx to
track `stravalib`'s test % coverage. When you submit a pull request, you will
see how that pull request affects our package's total test coverage.

### Documentation

Our documentation is in the `doc` folder.
We use [sphinx](https://www.sphinx-doc.org/en/master/) to build the web pages from
these sources. To build the HTML files:

```bash
make -C docs html
```

To serve documentation locally use:

```bash
make -C docs serve
```

You can learn more about our documentation infrastructure in our
[development guide](https://stravalib.readthedocs.io/en/latest/contributing/development-guide.html).

### Code Review and issue response timeline

After you've submitted a pull request or an issue, you should expect to see at the minimum,
a comment within a couple of days to a week depending on how busy the maintainers are at that time.
If you submitted a pull request, we may suggest some changes,  improvements or alternative approaches.

Some things that will increase the chance that your pull request is accepted quickly:

* Write a good and detailed description of what the PR does.
* Write tests for the code you wrote/modified.
* Readable code is better than clever code (even with comments).
* Write documentation for your code (docstrings) and leave comments explaining the
  *reason* behind non-obvious things.
* Include an example of new features in the gallery or tutorials.
* Follow the [numpy style guide](https://numpydoc.readthedocs.io/en/latest/format.html)
  for documentation and docstrings.
* Run the automatic code formatter and style checks.

All pull requests are automatically tested using workflows in GitHub Actions. Our tests include:

* running the test suite
* testing the documentation build (which includes API documentation created from docstrings)
* running code format and syntax tests for code formatters (TODO: code formatters will be added to stravalib soon!)

When you submit a pull request, you will see whether the tests ran or failed.
You will also see the resulting % code coverage based upon your pull request.

Please try to ensure that all tests pass (Green checks) in your pull request
before requesting a review from maintainers. If you have any trouble with the
GitHub action tests, please leave a comment in the Pull Request or open an Issue.
We will do our best to help you.
