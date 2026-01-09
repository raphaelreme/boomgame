"""Defines all the control keys for the game."""

from __future__ import annotations

import enum
import json

from pygame import locals as p_locals

from boomgame import importlib_resources, resources


class TypeControl(enum.IntEnum):
    """Mapping of keyboard behavior."""

    QUIT = p_locals.QUIT
    KEY_DOWN = p_locals.KEYDOWN
    KEY_UP = p_locals.KEYUP


class BaseControl(enum.IntEnum):
    """Mapping of some default controls."""

    ESCAPE = p_locals.K_ESCAPE
    RETURN = p_locals.K_RETURN


class PlayerControl:
    """Player control.

    When modified it can be saved and reloaded
    from data/control/player{id}.txt
    """

    # XXX: A default for each player ?
    DEFAULT_UP = p_locals.K_UP
    DEFAULT_DOWN = p_locals.K_DOWN
    DEFAULT_RIGHT = p_locals.K_RIGHT
    DEFAULT_LEFT = p_locals.K_LEFT
    DEFAULT_BOMBS = p_locals.K_SPACE

    def __init__(self, identifier: int) -> None:
        self.identifier = identifier
        self.up = self.DEFAULT_UP
        self.down = self.DEFAULT_DOWN
        self.right = self.DEFAULT_RIGHT
        self.left = self.DEFAULT_LEFT
        self.bombs = self.DEFAULT_BOMBS

    def serialize(self) -> str:
        """Serialize player controls into JSON format."""
        return json.dumps(
            {
                "up": self.up,
                "down": self.down,
                "right": self.right,
                "left": self.left,
                "bombs": self.bombs,
            }
        )

    @staticmethod
    def unserialize(string: str, identifier: int) -> PlayerControl:
        """Build PlayerControl from a JSON formatted string."""
        json_object = json.loads(string)

        control = PlayerControl(identifier)
        control.up = json_object["up"]
        control.down = json_object["down"]
        control.right = json_object["right"]
        control.left = json_object["left"]
        control.bombs = json_object["bombs"]

        return control

    def save(self) -> None:
        """Override PlayerControl in `data/control`."""
        resource = resources.joinpath("control").joinpath(f"player{self.identifier}.txt")

        with importlib_resources.as_file(resource) as file_path:
            file_path.write_text(self.serialize())  # XXX: This will only write into a temporary file if zipped
            # Should us a dedicated folder onto the running device.

    @staticmethod
    def from_identifier(identifier: int) -> PlayerControl:
        """Load default PlayerControl in `data/control`."""
        resource = resources.joinpath("control").joinpath(f"player{identifier}.txt")

        if not resource.is_file():
            return PlayerControl(identifier)

        return PlayerControl.unserialize(resource.read_text(), identifier)
