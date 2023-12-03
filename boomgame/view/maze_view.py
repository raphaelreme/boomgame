"""Handle the Maze to display it on the screen."""

from __future__ import annotations

from typing import Set

import pygame
import pygame.rect
import pygame.surface

from ..designpattern import event
from ..designpattern import observer
from ..model import events
from ..model import maze
from . import TILE_SIZE, inflate_to_reality
from . import entity_view
from . import animation
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
        self.background = pygame.surface.Surface(self.size).convert_alpha()
        self._build_background(style)

        # Set of all the views for each component of the maze
        self.entity_views = {entity_view.EntityView.from_entity(entity_) for entity_ in self.maze.entities}
        for view_ in self.entity_views:
            view_.set_style(style)

        # Animations
        self.animations: Set[animation.MazeAnimationView] = set()

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

        # Display animations
        for animation_ in sorted(self.animations):
            animation_.display(surface)

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
            self.animations.add(animation.GameOverSlider(self))
            return

        if isinstance(event_, events.ExtraGameEvent):
            self.animations.add(animation.ExtraGameSlider(self))
            return

        if isinstance(event_, events.HurryUpEvent):
            self.animations.add(animation.HurryUpSlider(self))
            return

        if isinstance(event_, events.ScoreEvent):
            self.animations.add(animation.ScoreSliderView(self, event_.entity))
            return

        if isinstance(event_, events.ExtraLifeEvent):
            self.animations.add(animation.ExtraLifeSliderView(self, event_.entity))

        if isinstance(event_, events.ForwardTimeEvent):
            for animation_ in self.animations.copy():
                animation_.forward(event_.delay)
