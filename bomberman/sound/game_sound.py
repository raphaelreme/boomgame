"""Handle the sound of all the game"""


import pygame.mixer

from ..designpattern import event, observer
from ..model import events, game
from . import maze_sound
from . import load_music


class GameSound(observer.Observer):
    """Produces all the sound in the game"""

    def __init__(self, model: game.GameModel) -> None:
        super().__init__()
        self.model = model
        self.model.add_observer(self)
        self.maze_sound = maze_sound.MazeSound(self.model.maze)
        # pygame.mixer.music.set_volume(1.0)

    def notify(self, event_: event.Event) -> None:
        if isinstance(event_, events.MazeStartEvent):
            self.maze_sound = maze_sound.MazeSound(self.model.maze)

        if isinstance(event_, events.StartScreenEvent):
            pygame.mixer.music.unload()
            load_music(f"music{self.model.style + 1}.ogg")

        if isinstance(event_, events.BonusScreenEvent):
            pass  # TODO: Bonus sound ?
