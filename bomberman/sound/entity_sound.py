"""Sound of all entities"""

from __future__ import annotations

import os
from typing import Dict, cast

import pygame.mixer

from ..designpattern import event, observer
from ..model import entity, events


class EntitySound(observer.Observer):
    """Sound for entities

    Sound at spawn, hit and removing
    """

    sound_loaded: Dict[str, Dict[str, pygame.mixer.Sound]] = {}
    sounds = ["Noise", "Removing", "Spawn"]

    def __init__(self, entity_: entity.Entity) -> None:
        super().__init__()
        self.entity = entity_
        self.entity.add_observer(self)
        self.sound_name = self._build_sound_name()

        sounds = self.get_sounds()
        if "Spawn" in sounds:
            sounds["Spawn"].play()

    def _build_sound_name(self) -> str:
        return self.entity.__class__.__name__

    def get_sounds(self) -> Dict[str, pygame.mixer.Sound]:
        """Lazy sound loader"""
        if self.sound_name in self.sound_loaded:
            return self.sound_loaded[self.sound_name]

        sounds = {}
        for sound in self.sounds:
            path = os.path.join(os.path.dirname(__file__), "..", "data", "sound", f"{self.sound_name}{sound}.wav")
            try:
                sounds[sound] = pygame.mixer.Sound(path)
            except:
                pass

        self.sound_loaded[self.sound_name] = sounds
        return sounds

    def notify(self, event_: event.Event) -> None:
        if isinstance(event_, events.StartRemovingEvent):
            sounds = self.get_sounds()
            if "Removing" in sounds:
                sounds["Removing"].play()
                return

        if isinstance(event_, events.NoiseEvent):
            sounds = self.get_sounds()
            if "Noise" in sounds:
                sounds["Noise"].play()
                return

    @staticmethod
    def from_entity(entity_: entity.Entity) -> EntitySound:
        if isinstance(entity_, entity.Player):
            return PlayerSound(entity_)

        if isinstance(entity_, entity.Bonus):
            return BonusSound(entity_)

        return EntitySound(entity_)


class PlayerSound(EntitySound):
    sounds = EntitySound.sounds + ["Success"]

    def _build_sound_name(self) -> str:
        player = cast(entity.Player, self.entity)
        return f"Player{player.identifier}"

    def notify(self, event_: event.Event) -> None:
        super().notify(event_)
        # TODO: Success sound


class BonusSound(EntitySound):
    def _build_sound_name(self) -> str:
        return "Bonus"
