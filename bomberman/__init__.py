"""Bomberman game using pygame."""

import pathlib


__version__ = "0.3.0dev"


DATA_FOLDER = pathlib.Path(__file__).parent.parent / "data"


def display_version() -> None:
    """Entry point of boom_version command

    Print the version on stdout
    """
    print(__version__)
