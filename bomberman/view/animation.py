from __future__ import annotations

import pygame.surface

from ..model import entity
from . import view
from . import maze_view
from . import inflate_to_reality, TILE_SIZE


class MazeAnimationView(view.ImageView):
    """Simple Animation above the maze.

    Move an image above the maze for a while
    """

    PRIORITY = 0
    DELAY = 0.0

    def __init__(self, image: pygame.surface.Surface, maze_view_: maze_view.MazeView) -> None:
        super().__init__(image, (0, 0))
        self.maze_view = maze_view_
        self.delay = 0.0

    def forward(self, delay: float) -> None:
        """Forward time in the animation"""
        self.delay += delay

        if self.delay > self.DELAY:
            self.maze_view.animations.remove(self)

        self.update()

    def update(self) -> None:
        """Update the position of the view"""

    def __lt__(self, other) -> bool:
        """Animation are sorted by priority"""
        if isinstance(other, MazeAnimationView):
            return self.PRIORITY < other.PRIORITY
        return NotImplemented


class MainSliderView(MazeAnimationView):
    """Specific view that display an image by sliding it from top to bottom

    Used for ExtraGame, GameOver and HurryUp images
    """

    FILE_NAME: str
    SLIDE_IN = 0.7
    SLIDE_STILL = SLIDE_IN + 1.4
    SLIDE_OUT = SLIDE_STILL + 0.7

    PRIORITY = 10
    DELAY = SLIDE_OUT

    def __init__(self, maze_view_: maze_view.MazeView) -> None:
        super().__init__(view.load_image(self.FILE_NAME), maze_view_)
        maze_size = self.maze_view.size

        self.x_position = (maze_size[0] - self.size[0]) // 2
        self.y_position_init = -self.size[1]
        self.y_position_mid = (maze_size[1] - self.size[1]) // 2
        self.y_position_final = maze_size[1]

        self.position = (self.x_position, self.y_position_init)

    def update(self) -> None:
        if self.delay <= self.SLIDE_IN:
            t = self.delay / self.SLIDE_IN
            self.position = (self.x_position, int(self.y_position_init * (1 - t) + self.y_position_mid * t))
        elif self.delay <= self.SLIDE_STILL:
            self.position = (self.x_position, self.y_position_mid)
        elif self.delay <= self.SLIDE_OUT:
            t = (self.delay - self.SLIDE_STILL) / (self.SLIDE_OUT - self.SLIDE_STILL)
            self.position = (self.x_position, int(self.y_position_mid * (1 - t) + self.y_position_final * t))


class GameOverSlider(MainSliderView):
    FILE_NAME = "game_over.png"
    PRIORITY = 13


class HurryUpSlider(MainSliderView):
    FILE_NAME = "hurry_up.png"
    PRIORITY = 12


class ExtraGameSlider(MainSliderView):
    FILE_NAME = "extra_game.png"
    PRIORITY = 11


class AnchoredSliderView(MazeAnimationView):
    """Specific view that slides up over an entity

    Used for scores and some other stuff
    """

    DELAY = 1.0
    SLIDE_DISTANCE = 2.0  # In tiles

    def __init__(self, image: pygame.surface.Surface, maze_view_: maze_view.MazeView, anchor: entity.Entity) -> None:
        super().__init__(image, maze_view_)

        position = inflate_to_reality(anchor.position + (1, 1))
        size = inflate_to_reality(anchor.size)

        self.x_position = int(position[0] + size[0] / 2 - self.size[0] / 2)
        self.y_position_init = int(position[1] + size[1] / 2 - self.size[1] / 2)
        self.y_position_final = self.y_position_init - int(self.SLIDE_DISTANCE * TILE_SIZE[1])

        self.position = (self.x_position, self.y_position_init)

    def update(self) -> None:
        t = self.delay / self.DELAY
        self.position = (self.x_position, int(self.y_position_init * (1 - t) + self.y_position_final * t))


class ScoreSliderView(AnchoredSliderView):
    """Handle all the score sliders"""

    def __init__(self, maze_view_: maze_view.MazeView, anchor: entity.Entity) -> None:
        super().__init__(view.load_image(f"score_{anchor.SCORE.value}.png"), maze_view_, anchor)