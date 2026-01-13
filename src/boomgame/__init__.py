"""BOOM remake based on pygame."""

import importlib.metadata
import sys

# Following https://setuptools.pypa.io/en/latest/userguide/datafiles.html#accessing-data-files-at-runtime
# We use importlib.resources for python > 3.10 and fallback with importlib_resources

if sys.version_info < (3, 10):
    import importlib_resources
else:
    import importlib.resources as importlib_resources


try:
    __version__ = importlib.metadata.version("boomgame")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

sound_extension = ".wav"
if sys.platform == "emscripten":
    sound_extension = ".ogg"

resources = importlib_resources.files("boomgame.data")
