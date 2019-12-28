"""Controllers of the game.

Handle all the events.
"""

from ..model import maze
from ..model import player
from . import control


class MazeController:
    def __init__(self, maze_: maze.Maze):
        self.maze: maze.Maze = maze_
        self.players = []

        for player_ in self.maze.players:
            self.players.append(PlayerController(player_))

    def handle_event(self, event) -> bool:
        """Handle all the events of the maze.

        Args:
            event (pygame.event.Event): The event received.

        Returns:
            bool: True if the event has been handled. False otherwise.
        """
        if event.type == control.TypeControl.KEY_DOWN and event.key == control.BaseControl.RETURN:
            try:
                player_ = self.maze.new_player()
            except maze.MazeFullError:
                return False
            self.players.append(PlayerController(player_))
            return True

        handled = False
        for player_ in self.players:
            handled |= player_.handle_event(event)
        return handled

    def time_spend(self, delta_time: float):
        for player_ in self.players:
            player_.time_spend(delta_time)
        for bomb in self.maze.bombs:
            bomb.time_spend(delta_time)


class PlayerController:
    def __init__(self, player_: player.Player):
        self.player = player_
        self.player_control = control.PlayerControl.from_id(self.player.id)
        self.current_direction = None
        self.event_to_direction = {
            self.player_control.up: player.Direction.UP,
            self.player_control.down: player.Direction.DOWN,
            self.player_control.right: player.Direction.RIGHT,
            self.player_control.left: player.Direction.LEFT,
        }

    def handle_event(self, event) -> bool:
        """Handle an event for the player concerned.

        Args:
            event (pygame.event.Event): The event received.

        Returns:
            bool: True if the event has been handled. False otherwise.
        """
        if event.type == control.TypeControl.KEY_DOWN:
            direction = self.event_to_direction.get(event.key, None)
            if direction:
                self.current_direction = direction
                return True

            if event.key == self.player_control.bombs:
                self.player.bombs()
                return True
            return False
        if event.type == control.TypeControl.KEY_UP:
            direction = self.event_to_direction.get(event.key, None)

            if direction:
                if direction == self.current_direction:
                    self.current_direction = None
                return True
            return False
        return False

    def time_spend(self, delta_time: float):
        if self.current_direction:
            self.player.move(delta_time, self.current_direction)
