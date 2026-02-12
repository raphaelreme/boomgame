"""BOOM remake based on pygame."""

import importlib.metadata
import importlib.resources as importlib_resources
import sys

try:
    __version__ = importlib.metadata.version("boomgame")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

sound_extension = ".wav"
if sys.platform == "emscripten":
    sound_extension = ".ogg"

resources = importlib_resources.files("boomgame.data")
