import os
import pathlib
import shutil
from glob import glob

import nox

nox.options.reuse_existing_virtualenvs = True


# Use this for venv envs nox -s test
@nox.session(python=["3.9", "3.10", "3.11"])
def tests(session):
    """Install requirements in a venv and run tests."""
    session.install(".[all]")
    session.install("-r", "requirements.txt")
    session.run(
        "pytest",
        "--cov",
        "src/stravalib",
        "src/stravalib/tests/unit/",
        "src/stravalib/tests/integration/",
    )


# Use this for conda/mamba = nox -s test_mamba
@nox.session(venv_backend="mamba", python=["3.9", "3.10", "3.11"])
def test_mamba(session):
    session.install(".[all]")
    session.install("-r", "requirements.txt")
    session.run(
        "pytest",
        "--cov",
        "src/stravalib",
        "src/stravalib/tests/unit/",
        "src/stravalib/tests/integration/",
    )


# Build docs
build_command = ["-b", "html", "docs/", "docs/_build/html"]


@nox.session
def docs(session):
    session.install(".[all]")
    session.install("-r", "requirements.txt")
    cmd = ["sphinx-build"]
    cmd.extend(build_command + session.posargs)
    session.run(*cmd)


@nox.session(name="docs-live")
def docs_live(session):
    session.install("-r", "requirements.txt")
    session.install(".[all]")

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


# Use this for venv envs nox -s test
@nox.session(python="3.10")
def mypy(session):
    session.install(".[all]")
    session.install("-r", "requirements.txt")
    session.run(
        "mypy",
    )


@nox.session(name="docs-clean")
def clean_docs(session):
    """
    Clean out the docs directory used in the
    live build.
    """
    dir_path = pathlib.Path("docs", "_build")
    print(dir_path)
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

    session.install("-r", "requirements-build.txt")
    session.run("python", "-m", "build")


@nox.session()
def install_wheel(session):
    """If you have several wheels in your dist/ directory this will
    try to install each one. so be sure to clean things out before
    running."""

    wheel_files = glob(os.path.join("dist", "*.whl"))
    print(wheel_files)
    session.run(
        "pip",
        "install",
        "--no-deps",
        "dist/stravalib-1.4.post24-py3-none-any.whl",
    )
    if wheel_files:
        for wheel_path in wheel_files:
            print("Installing:", wheel_path)
            session.install(wheel_path)
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
