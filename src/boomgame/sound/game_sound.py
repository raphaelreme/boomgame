"""Handle the sounds of all the game."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame.mixer

from boomgame.designpattern import observer
from boomgame.model import events
from boomgame.sound import load_music, maze_sound

if TYPE_CHECKING:
    from boomgame.designpattern import event
    from boomgame.model import game


class GameSound(observer.Observer):
    """Produces all the sound in the game."""

    def __init__(self, model: game.GameModel) -> None:
        super().__init__()
        self.model = model
        self.model.add_observer(self)
        self.maze_sound = maze_sound.MazeSound(self.model.maze)
        # Set volume? pygame.mixer.music.set_volume(1.0)

    def notify(self, event_: event.Event) -> None:
        """Handle Game event."""
        if isinstance(event_, events.MazeStartEvent):
            self.maze_sound = maze_sound.MazeSound(self.model.maze)

        if isinstance(event_, events.StartScreenEvent):
            pygame.mixer.music.unload()
            load_music(f"music{self.model.style + 1}.ogg")

        if isinstance(event_, events.BonusScreenEvent):
            pass  # TODO: Bonus sound ?
