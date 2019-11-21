"""Defines the basics obstacles that could be found."""

from __future__ import annotations

from ..designpattern import observable
from . import events
from . import maze
from . import player

from . import BOX_SIZE

class Obstacle(observable.Observable):
    blocking = True
    resists_bomb = True

    size = (BOX_SIZE, BOX_SIZE)

    def __init__(self, i: int, j: int):
        super().__init__()
        self.i = i
        self.j = j
        self.pos = (j * BOX_SIZE, i * BOX_SIZE)
        self.maze: maze.Maze = None

    def __str__(self):
        return self.__class__.__name__[0].lower()

    def set_maze(self, maze_: maze.Maze):
        if self.maze is None:
            self.maze = maze_

    def bombed(self):  # Could transform self.resists_bomb in an int.
        self.changed(events.ObstacleBombedEvent)
        if not self.resists_bomb:
            self.maze.remove_obstacle(self)

    @staticmethod
    def from_char(char: str):
        return {
            's': StoneWall,
            'w': WoodWall,
            'b': Bomb,
        }[char]


class StoneWall(Obstacle):
    pass


class WoodWall(Obstacle):
    resists_bomb = False


class Bomb(Obstacle):
    blocking = False
    resists_bomb = False

    DEFAULT_TIMEOUT = 5
    DEFAULT_RADIUS = 2

    def __init__(self, player_: player.Player):
        super().__init__(
            (player_.pos[1] + player_.size[1]/2) // BOX_SIZE,
            (player_.pos[0] + player_.size[0]/2) // BOX_SIZE,
        )
        self.player = player_
        self.time_to_leave = self.player.bombs_timeout
        self.radius = self.player.bombs_radius

    def time_spend(self, delta_time: float):
        self.time_to_leave -= delta_time
        if self.time_to_leave < 0:
            self.bombed()

    def bombed(self):
        self.changed(events.ObstacleBombedEvent)
        if not self.resists_bomb:
            self.maze.remove_bomb(self)
        #TODO: Generate ray
        self.player.bomb_explodes()
