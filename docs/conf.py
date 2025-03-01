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
    "sphinx_inline_tabs",
    "sphinxcontrib.mermaid",
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
    "stravalib/docs/reference/api",
]


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# The title in the left hand corner of the docs
html_title = "Stravalib Docs"
# Theme and css
html_theme = "pydata_sphinx_theme"

# Link to our repo for easy PR/ editing
html_theme_options = {
    "header_links_before_dropdown": 5,
    "use_edit_page_button": True,
    "show_toc_level": 1,
    # "navbar_align": "left",  # [left, content, right] For testing that the navbar items align properly
    "github_url": "https://github.com/stravalib/stravalib",
    "footer_start": ["copyright"],
    "announcement": "<a href='whats-new/stravalib-2.html'>Stravalib 2.x is out 🚀! Check out our migration guide for tips on changes from Stravalib V1!</a>",
}

html_context = {
    "github_user": "stravalib",
    "github_repo": "stravalib",
    "github_version": "main",
}

html_static_path = ["_static"]
# html_css_files = ["stravalib.css"]

# Instagram always throws 429 so ignore it
linkcheck_ignore = [r"https://www.instagram.com/accounts/login/"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# Intersphinx configuration
intersphinx_mapping = {
    "Python": ("http://docs.python.org/", None),
}

# Default to using the order defined in source.
autodoc_default_options = {
    "member-order": "alphabetical",
    "members": True,
    "undoc-members": True,
    "inherited-members": True,
}


# Here we globally customize what methods and attrs are included in the docs.
# there is no good way to do this (that I can find) for an entire inherited
# class
int_dir = dir(int)
methods_to_skip = [
    member
    for member in int_dir
    if not (member.startswith("__") and member.endswith("__"))
]


def skip_member(app, what, name, obj, skip, options):
    """
    Determine whether a member should be skipped during Sphinx documentation
    generation.

    This function is used as a callback to the `autodoc-skip-member` event in
    Sphinx. It allows you to programmatically decide whether a particular
    member (such as a method or attribute) should be included in the
    documentation.

    Parameters
    ----------
    app : `sphinx.application.Sphinx`
        The Sphinx application object.
    what : str
        The type of the object which the member belongs to (e.g., 'module',
        'class', 'exception', 'function', 'method', 'attribute').
    name : str
        The name of the member.
    obj : object
        The member object itself.
    skip : bool
        A boolean indicating if autodoc will skip this member if the
        user-defined callback does not override the decision.
    options : object
        The options given to the directive: an object with attributes
        `inherited_members`, `undoc_members`, `show_inheritance`, and `noindex`
        that are `True` if the flag option of the same name was given to the
        auto directive.

    Returns
    -------
    bool
        True if the member should be skipped, False otherwise.
    """
    # Skip methods defined above
    if name in methods_to_skip:
        return True
    # Skip special methods
    if name.startswith("__") and name.endswith("__"):
        return True

    # Otherwise, do not skip
    return skip


def setup(app):
    """
    Connect the `skip_member` function to the `autodoc-skip-member` event in
    Sphinx.

    This function is used to set up the Sphinx extension by connecting the
    `skip_member` function to the `autodoc-skip-member` event. This allows the
    `skip_member` function to control which members are included or excluded
    from the generated documentation.

    Parameters
    ----------
    app : `sphinx.application.Sphinx`
        The Sphinx application object.

    """
    app.connect("autodoc-skip-member", skip_member)
