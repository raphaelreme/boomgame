"""Main view of the game"""

from typing import Tuple
import pygame
import pygame.surface
import pygame.rect
import pygame.transform

from ..designpattern import event
from ..designpattern import observer
from ..model import game
from ..model import events
from . import inflate_to_reality
from . import maze_view
from . import panel_view
from . import view


class GameView(view.View, observer.Observer):
    """High level view of a game.

    Has a panel on the left, the maze on the right.
    """

    def __init__(self, model: game.GameModel) -> None:
        super().__init__((0, 0), (0, 0))
        self.model = model
        self.model.add_observer(self)

        self.build_subviews()

    def build_subviews(self):
        """Build all the subviews suited for the current maze"""
        self.panel_view = panel_view.PanelView(self.model)
        self.maze_view = maze_view.MazeView(self.model.maze, self.model.style)
        self.size = (self.panel_view.size[0] + self.maze_view.size[0], self.maze_view.size[1])

        self.panel_rect = pygame.rect.Rect((0, 0), self.panel_view.size)
        self.maze_rect = pygame.rect.Rect((self.panel_view.size[0], 0), self.maze_view.size)

        self.start_text = CenteredText(self.maze_rect.size)
        self.bonus_text = CenteredText(self.maze_rect.size)

    def notify(self, event_: event.Event) -> None:
        if isinstance(event_, events.MazeStartEvent):
            pass

        if isinstance(event_, events.StartScreenEvent):
            self.build_subviews()
            self.start_text.set_text(f"Level {self.model.maze_solved + 1:02d}\nGET READY!")

        if isinstance(event_, events.BonusScreenEvent):
            time = max(0, self.model.time)
            self.bonus_text.set_text(f"TIME BONUS!\n{int(time * 10)}")

    def display(self, surface: pygame.surface.Surface) -> None:
        if self.model.state == game.GameModel.State.MENU:
            return

        # Let's draw on a temporary surface that matches the size
        real_game_surface = pygame.surface.Surface(self.size).convert_alpha()

        self.panel_view.display(real_game_surface.subsurface(self.panel_rect))

        maze_surface = real_game_surface.subsurface(self.maze_rect)
        if self.model.state == game.GameModel.State.RUNNING:
            self.maze_view.display(maze_surface)
        elif self.model.state == game.GameModel.State.START_SCREEN:
            self.start_text.display(maze_surface)
        else:
            self.bonus_text.display(maze_surface)

        # Draw on the real surface and inflate at maximum size
        surface.fill((0, 0, 0))

        width, height = surface.get_size()
        ratio = min(width / self.size[0], height / self.size[1])
        game_size = (int(self.size[0] * ratio), int(self.size[1] * ratio))

        game_rect = pygame.rect.Rect(((width - game_size[0]) // 2, (height - game_size[1]) // 2), game_size)
        inflated_game_surface = surface.subsurface(game_rect)

        pygame.transform.scale(real_game_surface, game_size, inflated_game_surface)


class CenteredText(view.View):
    """Display some text"""

    FONT_SIZE = 1

    def __init__(self, size: Tuple[int, int]) -> None:
        super().__init__((0, 0), size)

        self.background = pygame.surface.Surface(self.size).convert_alpha()
        self.background.fill((0, 0, 0, 255))

        self.font = view.load_font("pf_tempesta_seven_bold.ttf", inflate_to_reality((CenteredText.FONT_SIZE, 1))[1])

        self.set_text("")

    def set_text(self, text: str):
        """Changes the text display by this view"""
        lines = text.split("\n")
        self.images = [self.font.render(line, True, (255, 255, 255)) for line in lines]

        text_height = sum((image.get_size()[1] for image in self.images))
        self.rects = []
        height = (self.size[1] - text_height) // 2
        for image in self.images:
            size = image.get_size()
            pos = ((self.size[0] - size[0]) // 2, height)
            self.rects.append(pygame.rect.Rect(pos, size))
            height += size[1]

    def display(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.background, (0, 0))
        for image, rect in zip(self.images, self.rects):
            surface.subsurface(rect).blit(image, (0, 0))
