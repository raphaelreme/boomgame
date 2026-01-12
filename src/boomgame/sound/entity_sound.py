"""Sounds of all entities."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, ClassVar, cast

from boomgame import sound_extension
from boomgame.designpattern import observer
from boomgame.model import entity, events
from boomgame.sound import load_sound

if TYPE_CHECKING:
    import pygame.mixer

    from boomgame.designpattern import event


# TODO: Stop sound when removed ? (for bombs for example)
class EntitySound(observer.Observer):
    """Sounds for entities.

    Sound at spawn, hit and removing
    """

    sound_loaded: ClassVar[dict[str, dict[str, pygame.mixer.Sound]]] = {}
    sounds: ClassVar[list[str]] = ["Noise", "Removing", "Spawn"]

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

    def get_sounds(self) -> dict[str, pygame.mixer.Sound]:
        """Lazy sound loader."""
        if self.sound_name in self.sound_loaded:
            return self.sound_loaded[self.sound_name]

        sounds = {}
        for sound in self.sounds:
            with contextlib.suppress(FileNotFoundError):
                sounds[sound] = load_sound(f"{self.sound_name}{sound}{sound_extension}")

        self.sound_loaded[self.sound_name] = sounds
        return sounds

    def notify(self, event_: event.Event) -> None:
        """Handle Entity event."""
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
        """Build from Entity."""
        if isinstance(entity_, entity.Enemy):
            return EnemySound(entity_)

        if isinstance(entity_, entity.Player):
            return PlayerSound(entity_)

        if isinstance(entity_, entity.Bonus):
            return BonusSound(entity_)

        return EntitySound(entity_)


class PlayerSound(EntitySound):
    """Sounds for Players."""

    sounds: ClassVar[list[str]] = [*EntitySound.sounds, "Success"]

    def _build_sound_name(self) -> str:
        player = cast("entity.Player", self.entity)
        return f"Player{player.identifier}"

        # TODO: Success sound


class BonusSound(EntitySound):
    """Sounds for Bonuses."""

    def _build_sound_name(self) -> str:
        return "Bonus"


# A bit ugly... Cannot handle spawn sound of alien but there is none
# so let's keep it that way for now
class AlienSound(EntitySound):
    """Sounds for Aliens."""

    def _build_sound_name(self) -> str:
        return "Alien"

    def notify(self, event_: event.Event) -> None:
        """Handle Entity event."""
        # Everything is handled by Enemy Sound


class EnemySound(EntitySound):
    """Sounds for Enemies."""

    def __init__(self, entity_: entity.Entity) -> None:
        super().__init__(entity_)
        self.entity: entity.Enemy
        self.alien_sound = AlienSound(self.entity)

    def notify(self, event_: event.Event) -> None:
        """Handle Entity event."""
        if not self.entity.is_alien:
            super().notify(event_)
            return

        if isinstance(event_, events.StartRemovingEvent):
            sounds = self.alien_sound.get_sounds()
            if "Removing" in sounds:
                sounds["Removing"].play()
                return

        if isinstance(event_, events.NoiseEvent):
            sounds = self.alien_sound.get_sounds()
            if "Noise" in sounds:
                sounds["Noise"].play()
                return
