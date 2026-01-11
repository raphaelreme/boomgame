"""Handle sounds for a given maze."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import pygame
import pygame.mixer

from boomgame import sound_extension
from boomgame.designpattern import observer
from boomgame.model import events
from boomgame.sound import entity_sound, load_sound

if TYPE_CHECKING:
    from boomgame.designpattern import event
    from boomgame.model import maze


# TODO: Adjust volume of different sounds ?
class MazeSound(observer.Observer):
    """Handle all the sounds of the maze."""

    solved = f"MazeSolved{sound_extension}"
    failed = f"MazeFailed{sound_extension}"
    extra_game = f"ExtraGame{sound_extension}"
    hurry_up = f"HurryUp{sound_extension}"
    extra_life = f"ExtraLife{sound_extension}"

    def __init__(self, maze_: maze.Maze) -> None:
        """Constructor.

        Args:
            maze_ (maze.Maze): The maze to represent
        """
        super().__init__()

        self.maze = maze_
        self.maze.add_observer(self)
        self.running = False
        self.failed_sound = load_sound(self.failed)
        self.solved_sound = load_sound(self.solved)
        self.extra_game_sound = load_sound(self.extra_game)
        self.hurry_up_sound = load_sound(self.hurry_up)
        self.extra_life_sound = load_sound(self.extra_life)

        # Set of all the views for each component of the maze
        self.entity_sounds = {entity_sound.EntitySound.from_entity(entity_) for entity_ in self.maze.entities}

        # Start the music if loaded
        with contextlib.suppress(pygame.error):
            pygame.mixer.music.play(-1)

    def notify(self, event_: event.Event) -> None:
        """Handle Maze events."""
        if isinstance(event_, events.NewEntityEvent):
            self.entity_sounds.add(entity_sound.EntitySound.from_entity(event_.entity))
            return

        if isinstance(event_, events.RemovedEntityEvent):
            for sound in self.entity_sounds:
                if sound.entity == event_.entity:
                    self.entity_sounds.remove(sound)
                    return

        if isinstance(event_, events.MazeFailedEvent):
            pygame.mixer.music.stop()
            self.failed_sound.play()
            return

        if isinstance(event_, events.MazeSolvedEvent):
            pygame.mixer.music.stop()
            self.solved_sound.play()
            return

        if isinstance(event_, events.ExtraGameEvent):
            self.extra_game_sound.play()
            return

        if isinstance(event_, events.HurryUpEvent):
            self.hurry_up_sound.play()
            return

        if isinstance(event_, events.ExtraLifeEvent):
            self.extra_life_sound.play()
