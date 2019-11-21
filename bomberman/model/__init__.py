"""Data model of the bomberman.

Defines all the data classes used in it.
"""

__all__ = ['maze', 'obstacle', 'player']

BOX_SIZE = 50


# pylint: disable = wrong-import-position
from . import maze
from . import obstacle
from . import player
