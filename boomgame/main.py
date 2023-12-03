"""Entry point of the game"""

import enum
from typing import Dict, Tuple

import pygame
import pygame.display
import pygame.event
import pygame.locals
import pygame.rect
import pygame.surface
import pygame.time
import pygame.transform

from .controller import control
from .controller import controller
from .menu import menu
from .model import game
from .sound import game_sound
from .view import animation
from .view import game_view
from .view import view


class BoomGame:
    """BOOM Game.

    Handle the main pygame loop of the game. Dispacth events and display. Handle window scaling
    """

    class State(enum.IntEnum):
        LOADING = 0
        MENU = 1
        RUNNING = 2
        # PAUSE = 3

    def __init__(self) -> None:
        self.state = self.State.LOADING

        # Init the display
        width, height = pygame.display.Info().current_w, pygame.display.Info().current_h
        pygame.display.set_mode((int(width * 3 / 4), int(height * 3 / 4)), pygame.locals.RESIZABLE)  # type: ignore
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

    def handle(self, event) -> None:
        """Handle a pygame event"""
        # Scale mouse pos
        if hasattr(event, "pos"):
            event.pos = self.scale(event.pos)

        if self.state == self.State.LOADING:
            return

        if self.state == self.State.MENU:
            self.menu.handle_event(event)

        if self.state == self.State.RUNNING:
            # PAUSE ?
            self.game_controller.handle_user_event(event)

    def forward(self, delta_time: float) -> None:
        """Forward time in the game"""
        if self.state == self.State.LOADING:
            self.loading_animation.forward(delta_time)
            if self.loading_animation.done:
                self.state = self.State.MENU

        if self.state == self.State.MENU:
            self.menu.update(delta_time)

        if self.state == self.State.RUNNING:
            self.game_controller.tick(delta_time)

    def display(self):
        """Display the game on the main surface"""
        views: Dict[BoomGame.State, view.View] = {
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
        surface.fill((0, 0, 0))

        width, height = surface.get_size()
        self.ratio = min(width / size[0], height / size[1])
        game_size = (int(size[0] * self.ratio), int(size[1] * self.ratio))

        game_rect = pygame.rect.Rect(((width - game_size[0]) // 2, (height - game_size[1]) // 2), game_size)
        self.offset = (game_rect.x, game_rect.y)
        inflated_game_surface = surface.subsurface(game_rect)

        pygame.transform.scale(real_game_surface, game_size, inflated_game_surface)

    def main(self):
        timer = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == control.TypeControl.QUIT:
                    self.running = False
                    break
                self.handle(event)

            delta_time = timer.tick(48) / 1000
            self.forward(delta_time)

            self.display()
            pygame.display.flip()

    def scale_mouse_get_pos(self, get_pos):
        """Wraps mouse get_pos  to scale the pos with the current offset/ratio"""

        def get_scaled_pos():
            return self.scale(get_pos())

        return get_scaled_pos

    def scale(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Scale mouse pos"""
        return (int((pos[0] - self.offset[0]) / self.ratio), int((pos[1] - self.offset[1]) / self.ratio))

    def start_game(self, two_players: bool, maze_solved: int):
        self.state = self.State.RUNNING
        self.game = game.GameModel("boom", two_players)
        self.game.maze_solved = maze_solved

        self.game_controller = controller.GameController(self.game)
        self.game_view = game_view.GameView(self.game)
        game_sound.GameSound(self.game)

        self.game.start()

    def quit(self):
        self.running = False


def main() -> None:
    assert pygame.init()[1] == 0, "Unable to initialize pygame"
    BoomGame().main()  # Entry point of the game
    pygame.quit()
