import os
import pathlib
import shutil
from glob import glob

import nox

nox.options.reuse_existing_virtualenvs = True


# Use this for venv envs nox -s test
@nox.session(python=["3.10", "3.11", "3.12"])
def tests(session):
    """Install requirements in a venv and run tests."""
    session.install(".[tests]")
    session.run(
        "pytest",
        "--cov=src/stravalib",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term",
        "src/stravalib/tests/unit/",
        "src/stravalib/tests/integration/",
    )


# Build docs
build_command = ["-b", "html", "docs/", "docs/_build/html"]


@nox.session(name="docs", python="3.11")
def docs(session):
    session.install(".[docs]")
    cmd = ["sphinx-build"]
    cmd.extend(build_command + session.posargs)
    session.run(*cmd)


@nox.session(name="docs-live", python="3.11")
def docs_live(session):
    session.install(".[docs]")

    AUTOBUILD_IGNORE = [
        "_build",
        "build_assets",
        "tmp",
    ]

    cmd = ["sphinx-autobuild"]
    for folder in AUTOBUILD_IGNORE:
        cmd.extend(["--ignore", f"*/{folder}/*"])
    cmd.extend(build_command + session.posargs)
    session.run(*cmd)


# Use this for venv envs nox -s mypy
@nox.session(python="3.11")
def mypy(session):
    session.install(".[lint]")
    session.run(
        "mypy",
    )


@nox.session(name="docs-clean")
def clean_docs(session):
    """
    Clean out the docs directory used in the
    live build.
    """
    dirs_to_clean = [
        pathlib.Path("docs", "_build"),
        pathlib.Path("docs", "reference", "api"),
    ]
    for dir_path in dirs_to_clean:
        print(f"Cleaning directory: {dir_path}")
        dir_contents = dir_path.glob("*")

        for content in dir_contents:
            print(f"cleaning content from the {dir_path}")
            if content.is_dir():
                shutil.rmtree(content)
            else:
                os.remove(content)


@nox.session()
def build(session):
    """Build the package's SDist and wheel using PyPA build and
    setuptools / setuptools_scm"""

    session.install(".[build]")
    session.run("python", "-m", "build")


@nox.session()
def install_wheel(session):
    """If you have several wheels in your dist/ directory this will
    try to install each one. so be sure to clean things out before
    running."""

    wheel_files = glob(os.path.join("dist", "*.whl"))
    print(wheel_files)

    if wheel_files:
        most_recent_wheel = max(wheel_files, key=os.path.getmtime)
        print("Installing:", most_recent_wheel)
        session.install(most_recent_wheel)
    else:
        print("No wheel files found matching the pattern: *.whl")


@nox.session()
def clean_build(session):
    """Clean out the dist/ directory and also clean out other remnant
    files such as .coverage, etc."""

    dirs_remove = [
        "__pycache__",
        ".mypy_cache",
        "build",
        "dist",
    ]
    files_remove = [
        "*.pyc",
        "*.orig",
        ".coverage",
        "MANIFEST",
        "*.egg-info",
        ".cache",
        ".pytest_cache",
        "src/stravalib/_version_generated.py",
    ]

    for pattern in files_remove:
        matches = glob(pattern, recursive=True)
        print("searching for", matches)
        for match in matches:
            if os.path.isfile(match):
                os.remove(match)
                print(f"Removed file: {match}")

    for a_dir in dirs_remove:
        if os.path.isdir(a_dir):
            shutil.rmtree(a_dir)
            print(f"Removed directory: {a_dir}")
