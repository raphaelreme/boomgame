"""Defines all the control keys for the game"""

from __future__ import annotations

import json
import enum
import os

from pygame import locals as p_locals


class TypeControl(enum.IntEnum):
    """Mapping of keyboard behavior"""

    QUIT = p_locals.QUIT  # type: ignore
    KEY_DOWN = p_locals.KEYDOWN  # type: ignore
    KEY_UP = p_locals.KEYUP  # type: ignore


class BaseControl(enum.IntEnum):
    """Mapping of some default controls"""

    ESCAPE = p_locals.K_ESCAPE  # type: ignore
    RETURN = p_locals.K_RETURN  # type: ignore


class PlayerControl:
    """Player control

    When modified it can be saved and reloaded
    from data/control/player{id}.txt
    """

    # FIXME: A default for each player ?
    DEFAULT_UP = p_locals.K_UP  # type: ignore
    DEFAULT_DOWN = p_locals.K_DOWN  # type: ignore
    DEFAULT_RIGHT = p_locals.K_RIGHT  # type: ignore
    DEFAULT_LEFT = p_locals.K_LEFT  # type: ignore
    DEFAULT_BOMBS = p_locals.K_SPACE  # type: ignore

    def __init__(self, identifier: int) -> None:
        self.identifier = identifier
        self.up = self.DEFAULT_UP  # pylint: disable = invalid-name
        self.down = self.DEFAULT_DOWN
        self.right = self.DEFAULT_RIGHT
        self.left = self.DEFAULT_LEFT
        self.bombs = self.DEFAULT_BOMBS

    def serialize(self) -> str:
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
        json_object = json.loads(string)

        control = PlayerControl(identifier)
        control.up = json_object["up"]
        control.down = json_object["down"]
        control.right = json_object["right"]
        control.left = json_object["left"]
        control.bombs = json_object["bombs"]

        return control

    def save(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "control", f"player{self.identifier}.txt")
        with open(path, "w") as file:
            file.write(self.serialize())

    @staticmethod
    def from_identifier(identifier: int) -> PlayerControl:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "control", f"player{identifier}.txt")
        if not os.path.exists(path):
            return PlayerControl(identifier)

        with open(path, "r") as file:
            return PlayerControl.unserialize(file.read(), identifier)
