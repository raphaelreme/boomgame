"""Model that handle data for the whole game"""

import enum
import json
from typing import Dict, List

from .. import resources
from ..designpattern import observable
from . import maze
from . import entity
from . import events
from . import timer


class GameModel(observable.Observable):
    """Observable model of the game

    Will handle the current maze, the players and everything else.

    Switch the maze when resolved, keep the players between mazes.

    Attrs:
        levels (List[Dict[str, int]]): List of description for the levels (style, time, maze_id)
        two_players (bool): Whether to use one or two player(s)
        state (GameModel.State): State of the game
        maze (maze.Maze): The current maze. Valid only when the state is RUNNING
        players (Dict[int, entity.Player]): The players
        maze_solved (int): Number of mazes currently solved
        style (int): Style of the maze
        time (float): Remaining time in the maze before Hurry Up
    """

    class State(enum.Enum):
        MENU = 0
        START_SCREEN = 1
        RUNNING = 2
        BONUS_SCREEN = 3

    DEFAULT_MAZE_SIZE = (13, 15)
    START_SCREEN_DELAY = 2.0
    END_SCREEN_DELAY = 2.0

    def __init__(self, game_name: str, two_players: bool = False) -> None:
        super().__init__()
        resource = resources.joinpath("game").joinpath(f"{game_name}.json")
        self.levels: List[Dict[str, int]] = json.loads(resource.read_text())

        self.state = GameModel.State.MENU

        # Create the players
        self.two_players = two_players
        self.players = {i: entity.Player(i) for i in (1, 2)}

        if not self.two_players:
            self.players[2].life = 0

        # Running attributes
        self.maze = maze.Maze(self.DEFAULT_MAZE_SIZE)  # Create an empty default maze
        self.maze_solved = 0
        self.style = 0
        self.time = 0.0

        self.start_timer = timer.Timer()
        self.end_timer = timer.Timer()

    def start(self) -> None:
        """Launch the start screen.

        The maze will be started after some delay.
        """
        assert self.state in {GameModel.State.BONUS_SCREEN, GameModel.State.MENU}
        self.state = GameModel.State.START_SCREEN
        self.start_timer.start(GameModel.START_SCREEN_DELAY)

        level = self.levels[self.maze_solved]  # TODO: Handle when out of ranged: Game end
        self.style = level["style"]
        self.time = level["time"]
        maze_id = level["maze_id"]

        resource = resources.joinpath("maze").joinpath(f"{maze_id}.txt")
        self.maze = maze.Maze.unserialize(resource.read_text())
        # assert self.maze.size == self.MAZE_SIZE, f"This game only supports maze with a size {self.MAZE_SIZE}"

        for player in self.players.values():
            if player.life:
                self.maze.add_player(player)

        self.changed(events.StartScreenEvent())

    def start_maze(self) -> None:
        """Start the maze"""
        assert self.state == GameModel.State.START_SCREEN
        self.state = GameModel.State.RUNNING

        self.changed(events.MazeStartEvent())

    def end_maze(self, success: bool) -> None:
        """End the current maze

        Args:
            success (bool): Is the current maze a success
        """
        assert self.state == GameModel.State.RUNNING

        if not success:
            self.state = GameModel.State.MENU
            self.changed(events.GameEndEvent())
            return

        self.state = GameModel.State.BONUS_SCREEN
        self.end_timer.start(GameModel.END_SCREEN_DELAY)

        self.changed(events.MazeEndEvent())

        self.maze_solved += 1
        self.changed(events.BonusScreenEvent())

    def update(self, delay: float) -> None:
        """Handle time forwarding.

        Args:
            delay (float): Seconds spent since last call.
        """
        if self.state == GameModel.State.MENU:
            return

        if self.state == GameModel.State.START_SCREEN:
            if self.start_timer.update(delay):
                self.start_timer.reset()
                self.start_maze()
            else:
                pass
                # self.changed(events.ForwardStartScreenEvent())
            return

        if self.state == GameModel.State.BONUS_SCREEN:
            if self.end_timer.update(delay):
                self.end_timer.reset()
                self.start()
            else:
                pass
                # self.changed(events.ForwardBonusScreenEvent())
            return

        # RUNNING
        self.maze.update(delay)

        if self.maze.end_timer.is_done:
            self.end_maze(self.maze.state == maze.Maze.State.SOLVED)

        self.time -= delay
        if int(self.time) <= self.maze.HURRY_UP_DELAY:
            self.maze.hurry_up()
