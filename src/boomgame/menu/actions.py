from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from boomgame.menu import element


def quit_game(source: element.Element) -> None:
    """Quit BOOM game."""
    source.page.menu.quit_callback()


def new_game(source: element.Element) -> None:
    """Start a new BOOM game."""
    source.page.menu.start_callback(True, 0)


def open_game(source: element.Element) -> None:
    """Open a saved game.

    XXX: USED for DEBUG currently
    """
    char = input("Two players (y|n) ? ")
    two_players = char.lower().strip() == "y"
    try:
        maze_solved = int(input("Starting maze ? ")) - 1
    except ValueError:
        maze_solved = 0
    source.page.menu.start_callback(two_players, maze_solved)
