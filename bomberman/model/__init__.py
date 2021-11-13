"""Data model of the bomberman.

Defines all the data classes used in it.
"""

__all__ = ["entity", "events", "maze"]


# pylint: disable = wrong-import-position
from . import entity
from . import events
from . import maze
