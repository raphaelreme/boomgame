"""Handle the Maze to display it on the screen."""

import time
from typing import List, Tuple

import pygame
import pygame.rect
import pygame.surface

from ..designpattern import event
from ..designpattern import observer
from ..model import entity
from ..model import events
from ..model import maze
from . import TILE_SIZE, inflate_to_reality
from . import entity_view
from . import view


class MazeView(view.View, observer.Observer):
    """View for a maze.

    It displays the entire maze (Background, borders, entities).
    """

    border_file = "border.png"
    background_file = "background.png"

    def __init__(self, maze_: maze.Maze, style: int) -> None:
        """Constructor

        Args:
            maze_ (maze.Maze): The maze to represent
            style (int): Style to adopt from 0 to 7
        """
        maze_size = inflate_to_reality(maze_.size)
        self.maze_rect = pygame.rect.Rect(TILE_SIZE, maze_size)

        super().__init__((0, 0), (maze_size[0] + 2 * TILE_SIZE[0], maze_size[1] + 2 * TILE_SIZE[1]))

        self.maze = maze_
        self.maze.add_observer(self)

        ## Build the background once for all
        self.background = pygame.surface.Surface(self.size)
        self._build_background(style)

        # Set of all the views for each component of the maze
        self.entity_views = {entity_view.EntityView.from_entity(entity_) for entity_ in self.maze.entities}
        for view_ in self.entity_views:
            view_.set_style(style)

        # Sliders
        self.sliders_views: List[SliderView] = []

    def _build_background(self, style: int) -> None:
        """Build the background surface for the given style"""
        background_sprite = view.load_image(self.background_file, inflate_to_reality((8, 1)))
        border_sprite = view.load_image(self.border_file, inflate_to_reality((8, 8)))

        # First add background everywhere
        current_sprite = pygame.rect.Rect(inflate_to_reality((style, 0)), TILE_SIZE)

        for i in range(self.maze.size[0] + 2):
            for j in range(self.maze.size[1] + 2):
                self.background.blit(background_sprite, inflate_to_reality((i, j)), current_sprite)

        # Then display the borders
        rows, cols = self.maze.size

        for j in (0, cols + 1):  # Columns
            for i in range(1, rows + 1):
                current_sprite = pygame.rect.Rect(inflate_to_reality((style, j != 0)), TILE_SIZE)
                self.background.blit(border_sprite, inflate_to_reality((i, j)), current_sprite)

        for i in (0, rows + 1):  # Rows
            for j in range(1, cols + 1):
                current_sprite = pygame.rect.Rect(inflate_to_reality((style, 2 + (i != 0))), TILE_SIZE)
                self.background.blit(border_sprite, inflate_to_reality((i, j)), current_sprite)

        for n, i, j in [(4, rows + 1, 0), (5, rows + 1, cols + 1), (6, 0, cols + 1), (7, 0, 0)]:  # Corners
            current_sprite = pygame.rect.Rect(inflate_to_reality((style, n)), TILE_SIZE)
            self.background.blit(border_sprite, inflate_to_reality((i, j)), current_sprite)

    def display(self, surface: pygame.surface.Surface) -> None:
        # Display the background
        surface.blit(self.background, self.position)

        # And the components of the maze
        maze_surface = surface.subsurface(self.maze_rect)

        for view_ in sorted(self.entity_views):
            view_.display(maze_surface)

        # Display sliders
        for slider in self.sliders_views:
            slider.display(surface)

    def notify(self, event_: event.Event) -> None:
        if isinstance(event_, events.NewEntityEvent):
            self.entity_views.add(entity_view.EntityView.from_entity(event_.entity))
            event_.handled = True
            return

        if isinstance(event_, events.RemovedEntityEvent):
            for view_ in self.entity_views:
                if view_.entity == event_.entity:  # FIXME: Directly remove ?
                    self.entity_views.remove(view_)
                    event_.handled = True
                    return

        if isinstance(event_, events.MazeFailedEvent):
            self.sliders_views.append(GameOverSlider(self.size))
            return

        if isinstance(event_, events.ExtraGameEvent):
            self.sliders_views.append(ExtraGameSlider(self.size))
            return

        if isinstance(event_, events.HurryUpEvent):
            self.sliders_views.append(HurryUpSlider(self.size))
            return

        if isinstance(event_, events.ScoreEvent):
            image_name = f"score_{event_.entity.SCORE.value}.png"
            self.sliders_views.append(AnchoredSliderView(image_name, event_.entity))


class SliderView(view.ImageView):
    """Specific view that display an image by sliding it from top to bottom

    Used for ExtraGame, GameOver and HurryUp images
    """

    FILE_NAME: str
    SLIDE_IN = 0.7
    SLIDE_STILL = SLIDE_IN + 1.4
    SLIDE_OUT = SLIDE_STILL + 0.7

    def __init__(self, maze_size: Tuple[int, int]) -> None:
        super().__init__(view.load_image(self.FILE_NAME), (0, 0))
        self.start_time = time.time()
        self.maze_size = maze_size

        self.x_position = (self.maze_size[0] - self.size[0]) // 2
        self.y_position_init = -self.size[1]
        self.y_position_mid = (self.maze_size[1] - self.size[1]) // 2
        self.y_position_final = self.maze_size[1]

    def display(self, surface: pygame.surface.Surface) -> None:
        delay = time.time() - self.start_time

        if delay > self.SLIDE_OUT:
            return

        if delay <= self.SLIDE_IN:
            t = delay / self.SLIDE_IN
            self.position = (self.x_position, int(self.y_position_init * (1 - t) + self.y_position_mid * t))
        elif delay <= self.SLIDE_STILL:
            self.position = (self.x_position, self.y_position_mid)
        elif delay <= self.SLIDE_OUT:
            t = (delay - self.SLIDE_STILL) / (self.SLIDE_OUT - self.SLIDE_STILL)
            self.position = (self.x_position, int(self.y_position_mid * (1 - t) + self.y_position_final * t))

        super().display(surface)


class GameOverSlider(SliderView):
    FILE_NAME = "game_over.png"


class HurryUpSlider(SliderView):
    FILE_NAME = "hurry_up.png"


class ExtraGameSlider(SliderView):
    FILE_NAME = "extra_game.png"


# TODO: Let's observe the maze. And be notify of forward time rather than this
class AnchoredSliderView(view.ImageView):
    """Specific view that slides up over an entity

    Used for scores and some other stuff
    """

    SLIDE_DELAY = 1.0
    SLIDE_DISTANCE = 2.0  # In tiles

    def __init__(self, image_name: str, anchor: entity.Entity) -> None:
        super().__init__(view.load_image(image_name), (0, 0))
        self.start_time = time.time()

        position = inflate_to_reality(anchor.position + (1, 1))
        size = inflate_to_reality(anchor.size)

        self.x_position = int(position[0] + size[0] / 2 - self.size[0] / 2)
        self.y_position_init = int(position[1] + size[1] / 2 - self.size[1] / 2)
        self.y_position_final = self.y_position_init - int(self.SLIDE_DISTANCE * TILE_SIZE[1])

        self.position = (self.x_position, self.y_position_init)

    def display(self, surface: pygame.surface.Surface) -> None:
        delay = time.time() - self.start_time

        if delay > self.SLIDE_DELAY:
            return

        t = delay / self.SLIDE_DELAY
        self.position = (self.x_position, int(self.y_position_init * (1 - t) + self.y_position_final * t))

        super().display(surface)
