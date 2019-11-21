"""All the events used by the model based on the observer/observable event."""

from __future__ import annotations

from typing import Tuple

from . import obstacle
from . import player
from ..designpattern.event import Event


class NewPlayerEvent(Event):
    def __init__(self, player_: player.Player):
        self.player = player_


class DeletePlayerEvent(Event):
    def __init__(self, player_: player.Player):
        self.player = player_


class PlayerMovedEvent(Event):
    def __init__(self, former_pos: Tuple[float, float], new_pos: Tuple[float, float]):
        self.former_pos = former_pos
        self.new_pos = new_pos


# class PlayerBlockedEvent(Event):
#     pass


class NewObstacleEvent(Event):
    def __init__(self, obstacle_: obstacle.Obstacle):
        self.obstacle = obstacle_


class DeleteObstacleEvent(Event):
    def __init__(self, obstacle_: obstacle.Obstacle):
        self.obstacle = obstacle_


class ObstacleBombedEvent(Event):
    pass
