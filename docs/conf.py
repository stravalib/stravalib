# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../stravalib"))

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# sys.path.insert(0, os.path.abspath('.'))

# -- General configuration ------------------------------------------------

# -- Project information -----------------------------------------------------

import datetime

import stravalib

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
    "sphinx.ext.napoleon", # Numpy style doc support
    "sphinx_remove_toctrees", # Remove api generated stubs from doctree
    "sphinxcontrib.autodoc_pydantic",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx.ext.autosummary",
    "myst_nb",
    "sphinx_design",
    "sphinxext.opengraph",
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


# The master toctree document.
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
    #"navbar_align": "left",  # [left, content, right] For testing that the navbar items align properly
    "github_url": "https://github.com/stravalib/stravalib",
    "footer_items": ["copyright"],
}

html_context = {
    "github_user": "stravalib",
    "github_repo": "stravalib",
    "github_version": "master",
}

html_static_path = ["_static"]
#html_css_files = ["stravalib.css"]

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

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = "stravalibdoc"

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ("index", "stravalib", "stravalib Documentation", ["Hans Lellelid"], 1)
]

# If true, show URL addresses after external links.
# man_show_urls = False


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "stravalib",
        "stravalib Documentation",
        "Hans Lellelid",
        "stravalib",
        "One line description of project.",
        "Miscellaneous",
    ),
]

# Documents to append as an appendix to all manuals.
# texinfo_appendices = []

# If false, no module index is generated.
# texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
# texinfo_no_detailmenu = False

# Example configuration for intersphinx: refer to the Python standard library.
# intersphinx_mapping = {'http://docs.python.org/': None}

# Default to using the order defined in source.
autodoc_member_order = "bysource"
