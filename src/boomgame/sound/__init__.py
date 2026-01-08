"""Handle the music and sound of the game"""

import pygame.mixer

from .. import resources


def load_sound(file_name: str) -> pygame.mixer.Sound:
    """Load a sound from the sound folder (boomgame/data/sound).

    Args:
        file_name (str): sound file

    Return:
        pygame.mixer.Sound: The sound loaded.
    """
    resource = resources.joinpath("sound").joinpath(file_name)

    return pygame.mixer.Sound(resource)


def load_music(file_name: str) -> None:
    """Load a music from the music folder (boomgame/data/music).

    Args:
        file_name (str): music file
    """
    resource = resources.joinpath("music").joinpath(file_name)

    pygame.mixer.music.load(resource)
