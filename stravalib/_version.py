"""
Get the automatically generated version information from setuptools_scm
Format it: vX.Y.Z
"""

# This file is generated automatically by setuptools_scm
from . import _version_generated

# Add a "v" to the version number made by setuptools_scm
__version__ = f"v{_version_generated.version}"