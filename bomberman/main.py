"""Entry point of the game"""

from typing import Dict, List

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

# TODO: Menu + Settings


class BoomGame:
    """BOOM Game"""

    name = "BOOM"

    def __init__(self) -> None:
        self.game_name = ""
        self.score = 0
        self.two_players = True

    def main(self):
        while True:
            self.main_menu()
            self.game()

    def main_menu(self) -> None:
        """Main menu, not implemented yet"""

        c = input("Menu not implemented yet. Two players (y|n) ? ")
        self.two_players = c.lower().strip() == "y"
        try:
            self.maze_solved = int(input("Starting maze ? ")) - 1
        except:
            self.maze_solved = 0
        self.game_name = "boom"

    def game(self) -> None:
        """Launch a game."""

        model = game.GameModel(self.game_name, self.two_players)
        model.maze_solved = self.maze_solved
        main_view = game_view.GameView(model)
        main_sound = game_sound.GameSound(model)

        pygame.display.set_mode(main_view.size)
        pygame.display.set_caption(f"{BoomGame.name} - level {model.maze_solved + 1}")
        # pygame.display.set_icon(view.load_image("boom.png", (10, 10)))

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
    assert pygame.init()[1] == 0
    pygame.display.set_mode((0, 0), pygame.HIDDEN)
    BoomGame().main()  # Entry point of the game
    pygame.quit()
