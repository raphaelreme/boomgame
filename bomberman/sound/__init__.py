"""Handle the music and sound of the game"""

import pygame.mixer

from .. import DATA_FOLDER


def load_sound(file_name: str) -> pygame.mixer.Sound:
    """Load a sound from the sound folder (bomberman/data/sound).

    Args:
        file_name (str): sound file

    Return:
        pygame.mixer.Sound: The sound loaded.
    """
    real_location = DATA_FOLDER / "sound" / file_name

    return pygame.mixer.Sound(str(real_location))


def load_music(file_name: str) -> None:
    """Load a music from the music folder (bomberman/data/music).

    Args:
        file_name (str): music file
    """
    real_location = DATA_FOLDER / "music" / file_name

    pygame.mixer.music.load(str(real_location))
