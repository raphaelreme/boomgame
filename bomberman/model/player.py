"""Provides the Player class."""

from __future__ import annotations

import enum
from typing import Tuple

from ..designpattern import observable
from . import obstacle
from . import events
from . import maze

from . import BOX_SIZE


class Direction(enum.Enum):
    """Direction to follow.

    Each value is a tuple (axis, direction):
        axis: 0 for x, 1 for y.
        direction: -1 for descending, 1 for ascending.
    """
    UP = (1, -1)
    DOWN = (1, 1)
    RIGHT = (0, 1)
    LEFT = (0, -1)


class Player(observable.Observable):
    """Player class.

    A player has basically a position in the maze and can move inside the maze.
    It can also drop bombs.
    """
    DEFAULT_SPEED = 2 * BOX_SIZE  # pixels/seconds
    DEFAULT_BOMB_CAPACITY = 6

    def __init__(self, id_: int, i: int, j: int):
        """Constructor.

        Args:
            id (int): The id of the player.
            i, j (int, int): The initial box indexes of the player.
        """
        super().__init__()
        self.maze: maze.Maze = None

        self.id = id_  # pylint: disable = invalid-name

        player_size = BOX_SIZE * 8 // 10
        self.pos = (
            j * BOX_SIZE + (BOX_SIZE - player_size) / 2,
            i * BOX_SIZE + (BOX_SIZE - player_size) / 2,
        )
        self.size = (player_size, player_size)

        self.speed = self.DEFAULT_SPEED
        self.bombs_capacity = self.DEFAULT_BOMB_CAPACITY
        self.bombs_timeout = obstacle.Bomb.DEFAULT_TIMEOUT
        self.bombs_radius = obstacle.Bomb.DEFAULT_RADIUS

    def __str__(self):
        return str(self.id)[0]

    def set_maze(self, maze_: maze.Maze):
        if self.maze is None:
            self.maze = maze_

    def set_pos(self, pos: Tuple[float, float]):
        event = events.PlayerMovedEvent(self.pos, pos)
        self.pos = pos
        self.changed(event)

    def move(self, time: float, direction: Direction):
        """Move the player along the given axis.

        Warning: Do not work if the player move more than a box at once.
            But it should never happen (The player should not be teleported)

        Args:
            time (float): The time spend moving.
            direction (Direction): The direction to take.
        """
        axis, direction = direction.value
        x_axis = (axis == 0)
        y_axis = not x_axis

        next_pos = (
            self.pos[0] + x_axis * direction * time * self.speed,
            self.pos[1] + y_axis * direction * time * self.speed,
        )
        next_pos_right = (next_pos[0] + self.size[0] - 1, next_pos[1])
        next_pos_down = (next_pos[0], next_pos[1] + self.size[1] - 1)
        next_pos_opposite = (next_pos_right[0], next_pos_down[1])

        if direction == 1:
            obstacle_ = self.maze.obstacle_at(next_pos_opposite)
            if obstacle_ and obstacle_.blocking:
                next_pos = (
                    obstacle_.pos[0] - self.size[0] if x_axis else self.pos[0],
                    obstacle_.pos[1] - self.size[1] if y_axis else self.pos[1],
                )
            obstacle_ = self.maze.obstacle_at(next_pos_right if x_axis else next_pos_down)
            if obstacle_ and obstacle_.blocking:
                next_pos = (
                    obstacle_.pos[0] - self.size[0] if x_axis else self.pos[0],
                    obstacle_.pos[1] - self.size[1] if y_axis else self.pos[1],
                )
        else:
            obstacle_ = self.maze.obstacle_at(next_pos)
            if obstacle_ and obstacle_.blocking:
                next_pos = (
                    obstacle_.pos[0] + obstacle_.size[0] if x_axis else self.pos[0],
                    obstacle_.pos[1] + obstacle_.size[1] if y_axis else self.pos[1],
                )
            obstacle_ = self.maze.obstacle_at(next_pos_down if x_axis else next_pos_right)
            if obstacle_ and obstacle_.blocking:
                next_pos = (
                    obstacle_.pos[0] + obstacle_.size[0] if x_axis else self.pos[0],
                    obstacle_.pos[1] + obstacle_.size[1] if y_axis else self.pos[1],
                )

        if next_pos != self.pos:
            self.set_pos(next_pos)

    def bombs(self):
        if self.bombs_capacity > 0:
            if self.maze.bomb_at(self.pos):
                return
            self.maze.add_bomb(obstacle.Bomb(self))
            self.bombs_capacity -= 1

    def bomb_explodes(self):
        self.bombs_capacity += 1
