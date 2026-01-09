"""Controllers of the game.

Handle all the events.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from boomgame.controller import control
from boomgame.model import vector

if TYPE_CHECKING:
    import pygame.event

    from boomgame.model import entity, game


class GameController:
    """Main controller during the game.

    Handle pygame events (from the user) and main intern events (like maze change)
    """

    def __init__(self, model: game.GameModel) -> None:
        self.model = model
        self.player_controllers = [PlayerController(model.players[identifier]) for identifier in model.players]

    def handle_user_event(self, event: pygame.event.Event) -> bool:
        """Handle all the graphical events.

        Args:
            event (pygame.event.Event): The event received.

        Returns:
            bool: True if the event has been handled. False otherwise.
        """
        if not self.model.state.RUNNING:
            # Game keys are handled only when playing
            # FIXME: If a player key is pressed it could be stored ?
            return False

        return any(controller.handle_user_event(event) for controller in self.player_controllers)

    def tick(self, delta_time: float) -> None:
        """Called at each time step.

        Update the model and forward time. Will probably evolved

        Args:
            delta_time (float): Time since last call
        """
        self.model.update(delta_time)

        for controller in self.player_controllers:
            controller.tick(delta_time)


class PlayerController:
    """Handle keys for a given player and its controls.

    Each key event will update the direction, and the bombing behavior of the player.
    """

    def __init__(self, player: entity.Player) -> None:
        self.player = player
        self.player_control = control.PlayerControl.from_identifier(self.player.identifier)
        self.key_to_direction = {
            self.player_control.up: vector.Direction.UP,
            self.player_control.down: vector.Direction.DOWN,
            self.player_control.right: vector.Direction.RIGHT,
            self.player_control.left: vector.Direction.LEFT,
        }
        self.direction_pressed: list[int] = []
        self.bombing = False

    def handle_user_event(self, event: pygame.event.Event) -> bool:
        """Handle an event for the player concerned.

        Args:
            event (pygame.event.Event): The event received.

        Returns:
            bool: True if the event has been handled. False otherwise.
        """
        if event.type not in (control.TypeControl.KEY_DOWN, control.TypeControl.KEY_UP):
            return False

        if event.key == self.player_control.bombs:
            self.bombing = event.type == control.TypeControl.KEY_DOWN
            return True

        if event.key not in self.key_to_direction:
            return False

        if event.type == control.TypeControl.KEY_DOWN:
            if event.key in self.direction_pressed:
                # TODO: Remove ? or Handle ?
                raise RuntimeError("This key was already pressed...")

            self.direction_pressed.append(event.key)
        elif event.type == control.TypeControl.KEY_UP:
            self.direction_pressed.remove(event.key)

        if not self.direction_pressed:
            self.player.set_wanted_direction(None)
        else:
            self.player.set_wanted_direction(self.key_to_direction[self.direction_pressed[-1]])

        return True

    def tick(self, _delta_time: float) -> None:
        """Called at each time step, moving time forward."""
        if self.bombing:
            self.player.bombs()  # Try to bomb at each time step when bombing
        # Note that entity update is done by game controller, no need to redo it.
