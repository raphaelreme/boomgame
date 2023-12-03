"""BOOM remake based on pygame."""

import sys

# Following https://setuptools.pypa.io/en/latest/userguide/datafiles.html#accessing-data-files-at-runtime
# We use importlib.resources for python > 3.10 and fallback with importlib_resources

assert sys.version_info.major == 3
if sys.version_info.minor < 10:
    import importlib_resources
else:
    import importlib.resources as importlib_resources  # type: ignore


__version__ = "0.4.1"
resources = importlib_resources.files("boomgame.data")


def display_version() -> None:
    """Entry point of boom_version command

    Print the version on stdout
    """
    print(__version__)
