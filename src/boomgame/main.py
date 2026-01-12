"""Entry point of the game."""

from __future__ import annotations

import asyncio
import enum
import sys
from typing import TYPE_CHECKING

import pygame
import pygame.display
import pygame.event
import pygame.locals
import pygame.rect
import pygame.surface
import pygame.time
import pygame.transform

from boomgame.controller import control, controller
from boomgame.designpattern import observer
from boomgame.menu import menu
from boomgame.model import events, game
from boomgame.sound import game_sound
from boomgame.view import animation, game_view, view

if TYPE_CHECKING:
    from .designpattern import event


if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override


class BoomGame(observer.Observer):
    """BOOM Game.

    Handle the main pygame loop of the game. Dispatch events and display. Handle window scaling
    """

    class State(enum.IntEnum):
        """High level state of the Game."""

        LOADING = 0
        MENU = 1
        RUNNING = 2
        # Could add a PAUSE = 3 state, triggered by some keys?

    def __init__(self) -> None:
        self.state = self.State.LOADING

        # Init the display
        width, height = pygame.display.Info().current_w, pygame.display.Info().current_h
        pygame.display.set_mode((int(width * 3 / 4), int(height * 3 / 4)), pygame.locals.RESIZABLE)
        pygame.display.set_caption("BOOM")
        pygame.display.set_icon(view.load_image("game_icon.png"))
        self.running = True
        self.offset = (0.0, 0.0)
        self.ratio = 1.0

        # Init all the components
        self.loading_animation = animation.LoadingAnimation()
        self.menu = menu.Menu(self.start_game, self.quit)
        self.game = game.GameModel("boom", False)
        self.game_controller = controller.GameController(self.game)
        self.game_view = game_view.GameView(self.game)

        # Wrap pygame.mouse.get_pos
        pygame.mouse.get_pos = self.scale_mouse_get_pos(pygame.mouse.get_pos)

    def handle(self, event_) -> None:
        """Handle a pygame event."""
        # Scale mouse pos
        if hasattr(event_, "pos"):
            event_.pos = self.scale(event_.pos)

        if self.state == self.State.LOADING:
            return

        if self.state == self.State.MENU:
            self.menu.handle_event(event_)

        if self.state == self.State.RUNNING:
            # PAUSE ?
            self.game_controller.handle_user_event(event_)

    def forward(self, delta_time: float) -> None:
        """Forward time in the game."""
        if self.state == self.State.LOADING:
            self.loading_animation.forward(delta_time)
            if self.loading_animation.done:
                self.state = self.State.MENU

        if self.state == self.State.MENU:
            self.menu.update(delta_time)

        if self.state == self.State.RUNNING:
            self.game_controller.tick(delta_time)

    @override
    def notify(self, event_: event.Event) -> None:
        if isinstance(event_, events.GameEndEvent):
            self.menu = menu.Menu(self.start_game, self.quit)  # Reset the menu
            self.state = self.State.MENU

    def display(self):
        """Display the game on the main surface."""
        views: dict[BoomGame.State, view.View] = {
            BoomGame.State.LOADING: self.loading_animation,
            BoomGame.State.MENU: self.menu,
            BoomGame.State.RUNNING: self.game_view,
        }

        size = views[self.state].size

        # Let's draw on a temporary surface that matches the size of the view
        real_game_surface = pygame.surface.Surface(size).convert_alpha()
        views[self.state].display(real_game_surface)

        # Draw on the real surface and inflate at maximum size
        surface = pygame.display.get_surface()
        if surface is None:
            raise RuntimeError("No active surface to draw on.")

        surface.fill((0, 0, 0))

        width, height = surface.get_size()
        self.ratio = min(width / size[0], height / size[1])
        game_size = (int(size[0] * self.ratio), int(size[1] * self.ratio))

        game_rect = pygame.rect.Rect(((width - game_size[0]) // 2, (height - game_size[1]) // 2), game_size)
        self.offset = (game_rect.x, game_rect.y)
        inflated_game_surface = surface.subsurface(game_rect)

        pygame.transform.scale(real_game_surface, game_size, inflated_game_surface)

    async def async_main(self):
        """Main loop (async for pygbag)."""
        timer = pygame.time.Clock()
        while self.running:
            for event_ in pygame.event.get():
                if event_.type == control.TypeControl.QUIT:
                    self.running = False
                    break
                self.handle(event_)

            delta_time = timer.tick(48) / 1000
            self.forward(delta_time)

            self.display()
            pygame.display.flip()
            await asyncio.sleep(0)

    def main(self):
        """Main loop (sync)."""
        asyncio.run(self.async_main())

    def scale_mouse_get_pos(self, get_pos):
        """Wraps mouse get_pos  to scale the pos with the current offset/ratio."""

        def get_scaled_pos():
            return self.scale(get_pos())

        return get_scaled_pos

    def scale(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Scale mouse pos."""
        return (int((pos[0] - self.offset[0]) / self.ratio), int((pos[1] - self.offset[1]) / self.ratio))

    def start_game(self, two_players: bool, maze_solved: int) -> None:
        """Start a new game."""
        self.state = self.State.RUNNING
        self.game = game.GameModel("boom", two_players)
        self.game.add_observer(self)
        self.game.maze_solved = maze_solved

        self.game_controller = controller.GameController(self.game)
        self.game_view = game_view.GameView(self.game)
        game_sound.GameSound(self.game)

        self.game.start()

    def quit(self):
        """Quit the BOOM."""
        self.running = False


def main() -> None:
    """Run BOOM."""
    assert pygame.init()[1] == 0, "Unable to initialize pygame"
    BoomGame().main()  # Entry point of the game
    pygame.quit()
