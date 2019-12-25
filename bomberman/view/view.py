"""Provides the basic class for simple views."""

import os
from typing import Dict, Tuple

import pygame


class View:
    """Basic class for simple views.

    It can be displayed on the main_window, but the image has to be set first.
    Be careful, you have to open a window first.

    Attr:
        window (pygame.Surface): The pygame surface on which the image
            will be displayed.
        image (pygame.Surface): The pygame surface to display.
        images (Dict[str, pygame.Surface]): All the other image that can be used for the view.
        x, y (int): Positions of the image on the window.
    """
    def __init__(self):
        # pylint does not find the pygame.Surface class.
        self.window: pygame.SurfaceType = pygame.display.get_surface()  # pylint: disable = no-member
        self.images: Dict[str, pygame.SurfaceType] = {}  # pylint: disable = no-member
        self.image: pygame.SurfaceType = None  # pylint: disable = no-member

        self.pos = (0, 0)

    def display(self):
        if self.image:
            self.window.blit(self.image, self.pos)

    @staticmethod
    def load_image(file_name: str, size: Tuple[int, int]) -> pygame.SurfaceType:  # pylint: disable = no-member
        """Load an image from the img folder.

        Should only be called when the main window (mode) has been set.

        Args:
            file_name (str): The name of the image with the extension.
            size (Tuple[int, int], optional): The target size.

        Return:
            pygame.Surface: The image loaded.
        """
        real_location = os.path.join(os.path.dirname(__file__), '..', 'data', 'image', file_name)
        return pygame.transform.scale(pygame.image.load(real_location).convert_alpha(), size)
