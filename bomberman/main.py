"""Entry point of the game"""

import pygame
import pygame.display
import pygame.event
import pygame.time
import pygame.locals

from .controller import control
from .controller import controller
from .model import game
from .sound import game_sound
from .view import game_view
from .view import view

# TODO: Menu + Settings

DEBUG = True


class BoomGame:
    """BOOM Game"""

    name = "BOOM"

    def __init__(self) -> None:
        self.game_name = ""
        self.score = 0
        self.two_players = True
        self.maze_solved = 0

        # Init the display
        width, height = pygame.display.Info().current_w, pygame.display.Info().current_h
        pygame.display.set_mode((int(width * 3 / 4), int(height * 3 / 4)), pygame.locals.RESIZABLE)  # type: ignore
        pygame.display.set_caption("BOOM")
        pygame.display.set_icon(view.load_image("game_icon.png"))

    def main(self):
        while True:
            self.main_menu()
            self.game()
            return

    def main_menu(self) -> None:
        """Main menu, not implemented yet"""

        if DEBUG:
            char = input("Menu not implemented yet. Two players (y|n) ? ")
            self.two_players = char.lower().strip() == "y"
            try:
                self.maze_solved = int(input("Starting maze ? ")) - 1
            except ValueError:
                self.maze_solved = 0
        else:
            self.two_players = True
            self.maze_solved = 0
        self.game_name = "boom"

    def game(self) -> None:
        """Launch a game."""

        model = game.GameModel(self.game_name, self.two_players)
        model.maze_solved = self.maze_solved
        main_view = game_view.GameView(model)
        game_sound.GameSound(model)

        model.start()

        main_controller = controller.GameController(model)

        running = True
        timer = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == control.TypeControl.QUIT:
                    running = False
                    break
                main_controller.handle_user_event(event)

            delta_time = timer.tick(48) / 1000
            main_controller.tick(delta_time)

            main_view.display(pygame.display.get_surface())
            pygame.display.flip()


def main() -> None:
    assert pygame.init()[1] == 0, "Unable to initialize pygame"
    BoomGame().main()  # Entry point of the game
    pygame.quit()
