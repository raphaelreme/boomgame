"""Defines all the control key for the game"""

from __future__ import annotations

import json
import enum
import os

from pygame import locals as p_locals


class TypeControl(enum.IntEnum):
    QUIT = p_locals.QUIT  # pylint: disable = no-member
    KEY_DOWN = p_locals.KEYDOWN  # pylint: disable = no-member
    KEY_UP = p_locals.KEYUP  # pylint: disable = no-member


class BaseControl(enum.IntEnum):
    ESCAPE = p_locals.K_ESCAPE  # pylint: disable = no-member
    RETURN = p_locals.K_RETURN  # pylint: disable = no-member


class PlayerControl:
    DEFAULT_UP = p_locals.K_UP  # pylint: disable = no-member
    DEFAULT_DOWN = p_locals.K_DOWN  # pylint: disable = no-member
    DEFAULT_RIGHT = p_locals.K_RIGHT  # pylint: disable = no-member
    DEFAULT_LEFT = p_locals.K_LEFT  # pylint: disable = no-member
    DEFAULT_BOMBS = p_locals.K_SPACE  # pylint: disable = no-member

    def __init__(self, player_id: int):
        self.player_id = player_id
        self.up = self.DEFAULT_UP  # pylint: disable = invalid-name
        self.down = self.DEFAULT_DOWN
        self.right = self.DEFAULT_RIGHT
        self.left = self.DEFAULT_LEFT
        self.bombs = self.DEFAULT_BOMBS

    def __str__(self):
        return json.dumps({
            'id': self.player_id,
            'up': self.up,
            'down': self.down,
            'right': self.right,
            'left': self.left,
            'bombs': self.bombs,
        })

    def save(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'data', 'control', f'player{self.player_id}.txt')
        with open(path, 'w') as file:
            file.write(str(self))

    @staticmethod
    def from_file(player_id: int) -> PlayerControl:
        path = os.path.join(os.path.dirname(__file__), '..', 'data', 'control', f'player{player_id}.txt')
        with open(path, 'r') as file:
            json_object = json.loads(file.read())

        player = PlayerControl(player_id)
        player.up = json_object['up']
        player.down = json_object['down']
        player.right = json_object['right']
        player.left = json_object['left']
        player.bombs = json_object['bombs']

        return player

    @staticmethod
    def from_id(player_id: int) -> PlayerControl:
        try:
            return PlayerControl.from_file(player_id)
        except OSError:
            return PlayerControl(player_id)
