"""Provides the basic classes for simple views."""

from __future__ import annotations

from typing import Optional, Tuple

import pygame
import pygame.display
import pygame.image
import pygame.font
import pygame.rect
import pygame.surface
import pygame.transform

from .. import resources
from . import TILE_SIZE


def load_image(file_name: str, size: Optional[Tuple[int, int]] = None) -> pygame.surface.Surface:
    """Load an image from the image folder (boomgame/data/image).

    Should only be called when the main window (mode) has been set.

    Args:
        file_name (str): image file
        size (Optional, Tuple[int, int]): Convert the image to this size. (in pixels)

    Return:
        pygame.surface.Surface: The image loaded.
    """
    resource = resources.joinpath("image").joinpath(file_name)

    if size:
        return pygame.transform.scale(pygame.image.load(resource).convert_alpha(), size)
    return pygame.image.load(resource).convert_alpha()


def load_font(file_name: str, size: int) -> pygame.font.Font:
    """Load a font from the font folder (boomgame/data/font).

    Args:
        file_name (str): font file (.ttf)
        size (int): Size in pixel of the font

    Return:
        pygame.font.Font: The font loaded.
    """
    resource = resources.joinpath("font").joinpath(file_name)

    return pygame.font.Font(resource, size)


class View:
    """Base class for anything that is displayed on the screen.

    Attrs:
        position (Tuple[int, int]): position of the view when displayed
        size (Tuple[int, int]): Size that is taken by the view
    """

    def __init__(self, position: Tuple[int, int], size: Tuple[int, int]) -> None:
        self.position = position
        self.size = size

    def display(self, surface: pygame.surface.Surface) -> None:
        """Display the view on the given surface

        Args:
            surface (pygame.surface.Surface): Surface that is written by the view
        """
        raise NotImplementedError


class ImageView(View):
    """View of an image

    Attrs: (See View for additional ones)
        image (pygame.surface.Surface): The pygame surface to display.
    """

    def __init__(self, image: pygame.surface.Surface, position: Tuple[int, int]) -> None:
        super().__init__(position, image.get_size())
        self.image = image

    def display(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.image, self.position)


class Sprite(View):
    """Handle a sprite image to animate a view

    Sprite image should be a 2D matrix of sprites of the same size.

    Attr: (See View for additional ones)
        SPRITE_SIZE (Tuple[int, int]): Size of all the sprites. (Same size)
        ROWS (int): Number of sprite rows in the image.
        COLUMNS (int): Number of sprite columns in the image.
        sprite_image (pygame.surface.Surface): The image of sprites
        current_sprite (pygame.rect.Rect): Rect around the current sprite
    """

    SPRITE_SIZE = TILE_SIZE
    ROWS = 1
    COLUMNS = 1

    def __init__(self, sprite_image: pygame.surface.Surface, position: Tuple[int, int]) -> None:
        super().__init__(position, self.SPRITE_SIZE)
        self.sprite_image = sprite_image
        self.current_sprite = pygame.rect.Rect((0, 0), self.SPRITE_SIZE)

    def select_sprite(self, row: int, column: int) -> None:
        """Select which sprite to use from the sprite image

        Args:
            row (int), column (int): Position of the sprite to select.
        """
        assert row < self.ROWS and column < self.COLUMNS
        self.current_sprite = pygame.rect.Rect(
            (column * self.SPRITE_SIZE[0], row * self.SPRITE_SIZE[1]), self.SPRITE_SIZE
        )

    def display(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.sprite_image, self.position, self.current_sprite)
