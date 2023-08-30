from stravalib.client import Client

__all__ = ["Client"]

try:
    from ._version_generated import __version__
except ImportError:
    __version__ = "unreleased"
