"""Main part of the model: class Maze.

It holds all the data of the game.
"""

from __future__ import annotations

from typing import Tuple

from ..designpattern import observable
from . import events
from . import obstacle
from . import player

from . import BOX_SIZE


class MazeFullError(Exception):
    pass


class Maze(observable.Observable):
    """Represents the maze.

    It contains all the object of the game.

    Attrs:
        width (int): Number of boxes in a row.
        height (int): Number of boxes in a columns.
        size (Tuple[int, int]): Size in pixel of the maze.
        players_number (int): Number of players that have joined this maze.
        players_initial_positions (List[Tuple[int, int]]): Available initial positions for players.
        players (List[player.Player]): List of the players.
        obstacles (List[obstacle.Obstacle]): List of the obstacles (except bombs).
        bombs (List[bomb.Bomb]): List of the bombs.
    """
    def __init__(self, width: int, height: int):
        """Initialise an empty maze.

        Args:
            width (int): Number of boxes in a row.
            height (int): Number of boxes in a columns.
        """
        super().__init__()
        self.width = width
        self.height = height
        self.size = (self.width * BOX_SIZE, self.height * BOX_SIZE)

        self.players_number = 0
        self.players_initial_positions = []
        self.players = []
        self.obstacles = []
        self.bombs = []

    def __str__(self):
        tmp = ([' '] * (self.width) + ['\n']) * self.height

        for i, j in self.players_initial_positions:
            tmp[i * (self.width + 1) + j] = 'p'
        for obstacle_ in self.obstacles:
            tmp[obstacle_.i * (self.width + 1) + obstacle_.j] = str(obstacle_)
        for bomb in self.bombs:
            tmp[bomb.i * (self.width + 1) + bomb.j] = str(bomb)
        for player_ in self.players:
            i = player_.pos[1] // BOX_SIZE
            j = player_.pos[0] // BOX_SIZE
            tmp[i * (self.width + 1) + j] = str(player_)

        return super().__str__() + '\n\n' + ''.join(tmp)

    def new_player(self) -> player.Player:
        """Create and add a new player to the maze.

        Raises:
            MazeFullError: If the max amount of players has been reached.
        """
        if self.players_number >= len(self.players_initial_positions):
            raise MazeFullError("No more players can be added to this maze.")
        i, j = self.players_initial_positions[self.players_number]
        player_ = player.Player(self.players_number, i, j)
        player_.set_maze(self)

        self.players_number += 1
        self.players.append(player_)
        self.changed(events.NewPlayerEvent(player_))
        return player_

    def remove_player(self, player_: player.Player):
        self.players.remove(player_)
        self.changed(events.DeletePlayerEvent(player))

    def add_bomb(self, bomb: obstacle.Bomb):
        if bomb in self.bombs:
            return
        self.bombs.append(bomb)
        bomb.set_maze(self)
        self.changed(events.NewObstacleEvent(bomb))

    def remove_bomb(self, bomb: obstacle.Bomb):
        self.bombs.remove(bomb)
        self.changed(events.DeleteObstacleEvent(bomb))

    def add_obstacle(self, obstacle_: obstacle.Obstacle):
        if obstacle_ in self.obstacles:
            return
        self.obstacles.append(obstacle_)
        obstacle_.set_maze(self)
        self.changed(events.NewObstacleEvent(obstacle_))

    def remove_obstacle(self, obstacle_: obstacle.Obstacle):
        self.obstacles.remove(obstacle_)
        self.changed(events.DeleteObstacleEvent(obstacle_))

    def obstacle_at(self, pos: Tuple[float, float]) -> obstacle.Obstacle:
        i = pos[1] // BOX_SIZE
        j = pos[0] // BOX_SIZE
        if i < 0 or j < 0 or  i >= self.height or j >= self.width:
            return obstacle.Obstacle(i, j)
        for obstacle_ in self.obstacles:
            if obstacle_.i == i and obstacle_.j == j:
                return obstacle_
        return None

    def bomb_at(self, pos: Tuple[float, float]) -> obstacle.Bomb:
        i = pos[1] // BOX_SIZE
        j = pos[0] // BOX_SIZE
        for bomb in self.bombs:
            if bomb.i == i and bomb.j == j:
                return bomb
        return None

    @staticmethod
    def from_file(file_name: str) -> Maze:
        description = ''
        with open(file_name, 'r') as file:
            description = file.read().split('\n')

        maze = Maze(len(description[0]), len(description))

        for i, line in enumerate(description):
            for j, char in enumerate(line):
                if char == ' ':
                    pass
                elif char == 'p':
                    maze.players_initial_positions.append((i, j))
                else:
                    maze.add_obstacle(obstacle.Obstacle.from_char(char)(i, j))

        return maze
