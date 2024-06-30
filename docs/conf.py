# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

import datetime

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import os
import sys

import stravalib

sys.setrecursionlimit(1500)

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../src"))

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# sys.path.insert(0, os.path.abspath('.'))

# -- General configuration ------------------------------------------------

# -- Project information -----------------------------------------------------

# General project info
# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
project = "stravalib"

# Automagically create the year vs hand code
copyright = (
    f"{datetime.date.today().year}, The {project} Developers"  # noqa: A001
)
# Grab the package version from the version attr
if len(stravalib.__version__.split(".")) > 3:
    version = "dev"
else:
    version = stravalib.__version__


# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.napoleon",  # Numpy style doc support
    "sphinx_remove_toctrees",  # Remove api generated stubs from doctree
    "sphinxcontrib.autodoc_pydantic",  # Add json schema display to pydantic models
    "sphinx.ext.autosummary",  # Generate API stubs for each class
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "myst_nb",
    "sphinx_design",
    # Commented out because matplotlib raises a findfonts warning over and over
    # TODO: fix is to install fonts in CI or remove opengraph
    # "sphinxext.opengraph",
    "sphinx_inline_tabs",
]

remove_from_toctrees = ["docs/reference/api/*"]

# https://autodoc-pydantic.readthedocs.io/en/stable/users/installation.html
autodoc_pydantic_model_show_json = True
autodoc_pydantic_settings_show_json = False
autosummary_generate = True

# Colon fence for card support in md
myst_enable_extensions = ["colon_fence"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]


# The main toctree document.
master_doc = "index"


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = [
    "_build",
    "stravalib/tests",
    "stravalib/tests/functional",
    "stravalib/tests/unit",
    "stravalib/tests/resources",
]


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# The title in the left hand corner of the docs
html_title = "Stravalib Docs"
# Theme and css
html_theme = "pydata_sphinx_theme"
# Add edit button to furo theme

# Link to our repo for easy PR/ editing
html_theme_options = {
    "header_links_before_dropdown": 4,
    "use_edit_page_button": True,
    "show_toc_level": 1,
    # "navbar_align": "left",  # [left, content, right] For testing that the navbar items align properly
    "github_url": "https://github.com/stravalib/stravalib",
    "footer_start": ["copyright"],
<<<<<<< HEAD
    "announcement": "<a href='stravalib-2.html'>Stravalib 2.x is out 🚀! Check out our migration guide for tips on changes from Stravalib V1!</a>",
=======
    "announcement": "Here's a <a href='stravalib-2.html'>Stravalib 2.x is out 🚀! Check out our Migration Guide for tips on changes from Stravalib V1!</a>",
>>>>>>> c24cd93 (Fix: docs part 1 - partial cleanup)
}

html_context = {
    "github_user": "stravalib",
    "github_repo": "stravalib",
    "github_version": "main",
}

html_static_path = ["_static"]
# html_css_files = ["stravalib.css"]

# Short title for the navigation bar.
html_short_title = "Stravalib Python Package Documentation"

# Instagram always throws 429 so ignore it
linkcheck_ignore = [r"https://www.instagram.com/accounts/login/"]
# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
# html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True

# Example configuration for intersphinx: refer to the Python standard library.
# intersphinx_mapping = {'http://docs.python.org/': None}

# Default to using the order defined in source.
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "inherited-members": True,
}
