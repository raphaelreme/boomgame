"""Handle entities of the maze."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, ClassVar, cast

import pygame.rect
import pygame.surface
import pygame.transform

from boomgame.designpattern import observer
from boomgame.model import entity, events, vector
from boomgame.view import TILE_SIZE, inflate_to_reality, view

if TYPE_CHECKING:
    from boomgame.designpattern import event

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override


class EntityView(view.Sprite, observer.Observer):
    """Base view for entities. Let's only use Sprite views.

    It observes an entity.

    Attrs: (See view.Sprite for other attributes)
        PRIORITY (int): Priority in display. (The small priorities are displayed first)
        FILE_NAME (str): File in the image folder where the sprite for this view is stored.
        REMOVING_STEPS (List[Tuple[int, int]]): List of the positions of sprites for the removing steps.
    """

    PRIORITY = 0
    FILE_NAME: str
    SPRITE_SIZE = TILE_SIZE
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = []

    def __init__(self, entity_: entity.Entity) -> None:
        image_total_size = (self.SPRITE_SIZE[0] * self.COLUMNS, self.SPRITE_SIZE[1] * self.ROWS)
        super().__init__(view.load_image(self.FILE_NAME, image_total_size), inflate_to_reality(entity_.position))
        self.entity = entity_
        self.entity.add_observer(self)
        self.removing_steps = self.REMOVING_STEPS

    def notify(self, event_: event.Event) -> None:
        """Handle an event from the observed entity.

        Args:
            event_ (event.Event): Event received from the observable.
        """
        if isinstance(event_, events.RemovingEntityEvent):
            if not self.entity.removing_timer.is_active:
                print("WARNING: removing event without removing state:", self)  # noqa: T201
            event_.handled = True

            if not self.entity.REMOVING_DELAY or not self.removing_steps:
                return

            step = 1 - max(self.entity.removing_timer.current, 1e-6) / self.entity.removing_timer.total
            self.select_sprite(*self.removing_steps[int(step * len(self.removing_steps))])

    @staticmethod
    def from_entity(entity_: entity.Entity) -> EntityView:
        """Construct from entity."""
        class_name = f"{entity_.__class__.__name__}View"
        return globals()[class_name](entity_)

    def __lt__(self, other) -> bool:
        """Entity views are sorted by priority."""
        if isinstance(other, EntityView):
            return self.PRIORITY < other.PRIORITY
        return NotImplemented

    def set_style(self, style: int) -> None:
        """Set the style of an entity.

        Only used for walls for now.
        """


class FakeEntityView(EntityView):
    """Base class for Fake Entity.

    Easy to add special entities that only needs to do some stuff without any view
    """

    FILE_NAME = "heart.png"  # Need one but unused

    @override
    def display(self, surface: pygame.surface.Surface) -> None:
        pass


class BreakableWallRemoverView(FakeEntityView):
    """Fake entity view just here for consistency."""


class CoinView(EntityView):
    """Coin."""

    FILE_NAME = "coin.png"
    ROWS = 1
    COLUMNS = 10
    REMOVING_STEPS = [(0, i) for i in range(10)] * 10


class SolidWallView(EntityView):
    """SolidWall."""

    PRIORITY = 100
    FILE_NAME = "solid_wall.png"
    ROWS = 8
    COLUMNS = 1

    def __init__(self, entity_: entity.SolidWall) -> None:
        super().__init__(entity_)
        self.set_style(0)

    @override
    def set_style(self, style: int) -> None:
        self.select_sprite(style, 0)


class BreakableWallView(EntityView):
    """BreakableWall."""

    PRIORITY = 100
    FILE_NAME = "breakable_wall.png"
    ROWS = 8
    COLUMNS = 4
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(0, 1), (0, 2), (0, 3)]

    def __init__(self, entity_: entity.BreakableWall) -> None:
        super().__init__(entity_)
        self.set_style(0)

    @override
    def set_style(self, style: int) -> None:
        self.removing_steps = [(style, index[1]) for index in self.REMOVING_STEPS]
        self.select_sprite(style, 0)


class BombView(EntityView):
    """Bomb."""

    PRIORITY = 10
    FILE_NAME = "bomb.png"
    ROWS = 1
    COLUMNS = 3
    RATE = 0.3
    FAST_RATE = 0.05

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)

        if isinstance(event_, events.ForwardTimeEvent):
            bomb = cast("entity.Bomb", self.entity)
            if bomb.timer.current < bomb.FAST_TIMEOUT:
                index = int((bomb.BASE_TIMEOUT - bomb.timer.current) / self.FAST_RATE)
                self.select_sprite(0, 1 + (index % 2))
            else:
                index = int((bomb.BASE_TIMEOUT - bomb.timer.current) / self.RATE)
                self.select_sprite(0, index % 2)


class LaserView(EntityView):
    """Laser."""

    PRIORITY = 5
    FILE_NAME = "laser.png"
    ROWS = 3
    COLUMNS = 4
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 2), (0, 1), (0, 0)]

    def __init__(self, entity_: entity.Laser) -> None:
        super().__init__(entity_)
        self.removing_steps = [(entity_.orientation.value, index[1]) for index in self.REMOVING_STEPS]


class TeleporterView(EntityView):
    """Teleporter."""

    FILE_NAME = "teleporter.png"
    ROWS = 1
    COLUMNS = 8
    RATE = 0.1

    def __init__(self, entity_: entity.Entity) -> None:
        super().__init__(entity_)
        self.entity: entity.Teleporter

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)

        if isinstance(event_, events.ForwardTimeEvent):
            j = int(self.entity.alive_since.current / self.RATE) % self.COLUMNS
            self.select_sprite(0, j)


class FlashView(EntityView):
    """Flash."""

    FILE_NAME = "flash.png"
    PRIORITY = 30
    ROWS = 1
    COLUMNS = 4
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 2), (0, 1), (0, 0)]


class MovingEntityView(EntityView):
    """Base view class for all moving entity."""

    RATE = 0.1

    direction_to_row: ClassVar[dict[vector.Direction | None, int]] = {
        None: 0,
        vector.Direction.DOWN: 0,
        vector.Direction.UP: 1,
        vector.Direction.RIGHT: 2,
        vector.Direction.LEFT: 3,
    }

    def __init__(self, entity_: entity.MovingEntity) -> None:
        super().__init__(entity_)
        i = self.direction_to_row[entity_.current_direction]
        self.select_sprite(i, 0)

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)

        if isinstance(event_, events.MovedEntityEvent):
            entity_ = cast("entity.MovingEntity", event_.entity)
            self.position = inflate_to_reality(entity_.position)
            if not entity_.current_direction:  # End of a movement probably
                self.select_sprite(self.direction_to_row[entity_.current_direction], 0)
                return

            i = self.direction_to_row[entity_.current_direction]
            j = int(entity_.try_moving_since / self.RATE) % self.COLUMNS
            self.select_sprite(i, j)


class PlayerView(MovingEntityView):
    """Player View."""

    PRIORITY = 15
    ROWS = 5
    COLUMNS = 8
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(4, 0), (4, 1), (4, 2), (4, 1)] * 15 + [(4, 1)] * 40
    SHIELD = "shield.png"
    SHIELD_ROWS = 1
    SHIELD_COLUMNS = 3
    SHIELD_TWINKLE_DELAY = 3.0
    SHIELD_RATE = 0.1

    direction_to_shield: ClassVar[dict[vector.Direction | None, int]] = {
        None: 0,
        vector.Direction.UP: 0,
        vector.Direction.DOWN: 0,
        vector.Direction.RIGHT: 1,
        vector.Direction.LEFT: 2,
    }

    def __init__(self, entity_: entity.Player) -> None:
        self.FILE_NAME = f"player{entity_.identifier}.png"  # pylint: disable = invalid-name
        super().__init__(entity_)
        self.entity: entity.Player

        shield_size = (self.SPRITE_SIZE[0] * self.SHIELD_COLUMNS, self.SPRITE_SIZE[1] * self.SHIELD_ROWS)
        self.shield_sprite = view.load_image(self.SHIELD, shield_size)
        self.shield_sprite.set_alpha(128)

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)

        if isinstance(event_, events.LifeLossEvent):
            # In case of a life loss, let's update the sprite like it would be done when moving
            super().notify(events.MovedEntityEvent(event_.entity))

    @override
    def display(self, surface: pygame.surface.Surface) -> None:
        if not self.entity.shield.is_active:
            super().display(surface)
            return

        if (
            self.entity.shield.current < self.SHIELD_TWINKLE_DELAY
            and int(self.entity.shield.current / self.SHIELD_RATE) % 2
        ):
            super().display(surface)
            return

        # Display shield
        # XXX: Could use the player as a mask for the shield ?
        image = pygame.surface.Surface(self.SPRITE_SIZE).convert_alpha()
        image.fill((0, 0, 0, 0))
        image.blit(self.sprite_image, (0, 0), self.current_sprite)
        shield_rect = pygame.rect.Rect(
            (self.direction_to_shield[self.entity.current_direction] * self.SPRITE_SIZE[0], 0 * self.SPRITE_SIZE[1]),
            self.SPRITE_SIZE,
        )
        image.blit(self.shield_sprite, (0, 0), shield_rect)
        surface.blit(image, self.position)


class AlienView(MovingEntityView):
    """Enemy view for all enemies in extra game."""

    FILE_NAME = "alien.png"
    ROWS = 5
    COLUMNS = 4
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(4, 0), (4, 1)] * 10


class EnemyView(MovingEntityView):
    """Base view class for enemies."""

    PRIORITY = 20
    ROWS = 6
    COLUMNS = 4
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(5, 0), (5, 1)] * 10
    FIRING_ROW = 4

    def __init__(self, entity_: entity.Enemy) -> None:
        self.FILE_NAME = f"{entity_.__class__.__name__.lower()}.png"  # pylint: disable=invalid-name
        super().__init__(entity_)
        self.entity: entity.Enemy
        self.alien_view = AlienView(self.entity)

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)

        if isinstance(event_, events.MovedEntityEvent) and self.entity.firing_timer.is_active:
            self.select_sprite(self.FIRING_ROW, self.direction_to_row[self.entity.current_direction])

    @override
    def display(self, surface: pygame.surface.Surface) -> None:
        if self.entity.is_alien:
            self.alien_view.display(surface)
        else:
            super().display(surface)


class SoldierView(EnemyView):
    """Soldier."""


class SargeView(EnemyView):
    """Sarge."""


class LizzyView(EnemyView):
    """Lizzy."""

    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(5, 0), (5, 1), (5, 2), (5, 3)] * 5


class TaurView(EnemyView):
    """Taur."""


class GunnerView(EnemyView):
    """Gunner."""


class ThingView(EnemyView):
    """Thing."""


class GhostView(EnemyView):
    """Ghost."""


class SmoulderView(EnemyView):
    """Smoulder."""

    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(5, 0), (5, 1), (5, 2), (5, 3)] * 5


class SkullyView(EnemyView):
    """Skully."""


class GigglerView(EnemyView):
    """Giggler."""


class HeadView(EnemyView):
    """Head."""

    SPRITE_SIZE = inflate_to_reality(entity.Head.SIZE)
    ROWS = 1
    COLUMNS = 1
    REMOVING_RATE = 0.1
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = []

    @override
    def display(self, surface: pygame.surface.Surface) -> None:
        if self.entity.removing_timer.is_active and int(self.entity.removing_timer.current / self.REMOVING_RATE) % 2:
            return

        super().display(surface)


class BulletView(EntityView):
    """Base view for bullets."""

    PRIORITY = 150
    ROWS = 1
    COLUMNS = 5
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(0, 1), (0, 2), (0, 3), (0, 4)]

    direction_to_rotation: ClassVar[dict[vector.Direction | None, int]] = {
        None: 0,
        vector.Direction.DOWN: 0,
        vector.Direction.UP: 180,
        vector.Direction.RIGHT: 90,
        vector.Direction.LEFT: 270,
    }

    def __init__(self, entity_: entity.Bullet) -> None:
        self.FILE_NAME = f"{entity_.__class__.__name__.lower()}.png"  # pylint: disable=invalid-name
        super().__init__(entity_)
        self.entity: entity.Bullet
        self.rotation = self.direction_to_rotation[entity_.display_direction]

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)

        if isinstance(event_, events.MovedEntityEvent):
            self.position = inflate_to_reality(event_.entity.position)

    @override
    def display(self, surface: pygame.surface.Surface) -> None:
        image = pygame.surface.Surface(self.SPRITE_SIZE).convert_alpha()
        image.fill((0, 0, 0, 0))
        image.blit(self.sprite_image, (0, 0), self.current_sprite)
        image = pygame.transform.rotate(image, self.rotation)
        surface.blit(image, self.position)


class ShotView(BulletView):
    """Shot."""


class FireballView(BulletView):
    """Fireball."""


class MGShotView(BulletView):
    """MGShot."""

    COLUMNS = 6
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5)]


class LightboltView(BulletView):
    """Lightbolt."""


class FlameView(BulletView):
    """Flame."""

    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
        (0, 4),
        (0, 3),
        (0, 2),
        (0, 1),
        (0, 0),
    ]

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)
        if self.entity.removing_timer.is_active:
            return

        if isinstance(event_, events.MovedEntityEvent) and self.entity.distance < self.entity.RANGE:
            j = int(self.COLUMNS * self.entity.distance / self.entity.RANGE)
            self.select_sprite(0, j)
            self.removing_steps = self.REMOVING_STEPS[j:]

    @override
    def __lt__(self, other) -> bool:
        # Improve Flame visualization by enforcing an order between Flames
        if isinstance(other, FlameView):
            if self.entity.removing_timer.is_active:
                if not other.entity.removing_timer.is_active:
                    return True
                return self.entity.removing_timer.current < other.entity.removing_timer.current
            if other.entity.removing_timer.is_active:
                return False
            return self.entity.distance > other.entity.distance
        return super().__lt__(other)


class PlasmaView(BulletView):
    """Plasma."""


class MagmaView(BulletView):
    """Magma."""


class MissileView(BulletView):
    """Missile."""

    COLUMNS = 7
    REMOVING_STEPS: ClassVar[list[tuple[int, int]]] = [(0, 2), (0, 3), (0, 4), (0, 5), (0, 6)]
    ROTATE_RATE = 0.1

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)

        if self.entity.removing_timer.is_active:
            return

        if isinstance(event_, events.MovedEntityEvent):
            missile = cast("entity.Missile", self.entity)
            self.select_sprite(0, int(missile.alive_since.current / self.ROTATE_RATE) % 2)

    @override
    def display(self, surface: pygame.surface.Surface) -> None:
        EntityView.display(self, surface)


class BonusView(EntityView):
    """Base view for bonuses."""

    FILE_NAME = "bonuses.png"
    PRIORITY = 50
    ROWS = 1
    COLUMNS = 9
    REMOVING_RATE = 0.1

    class_to_column: ClassVar[dict[type[entity.Bonus], int]] = {
        entity.LightboltBonus: 0,
        entity.SkullBonus: 1,
        entity.BombCapacityBonus: 2,
        entity.FastBombBonus: 3,
        entity.BombRadiusBonus: 4,
        entity.HeartBonus: 5,
        entity.FullHeartBonus: 6,
        entity.ShieldBonus: 7,
        entity.FastBonus: 8,
    }

    def __init__(self, entity_: entity.Bonus) -> None:
        super().__init__(entity_)
        self.select_sprite(0, self.class_to_column[type(entity_)])

    @override
    def display(self, surface: pygame.surface.Surface) -> None:
        if self.entity.removing_timer.is_active and int(self.entity.removing_timer.current / self.REMOVING_RATE) % 2:
            return

        super().display(surface)


class LightboltBonusView(BonusView):
    """Lightbolt (Bonus)."""


class SkullBonusView(BonusView):
    """Skull."""


class BombCapacityBonusView(BonusView):
    """BombCapacity."""


class FastBombBonusView(BonusView):
    """FastBomb."""


class BombRadiusBonusView(BonusView):
    """BombRadius."""


class HeartBonusView(BonusView):
    """Heart."""


class FullHeartBonusView(BonusView):
    """FullHeart."""


class ShieldBonusView(BonusView):
    """Shield."""


class FastBonusView(BonusView):
    """Fast."""


class ExtraLetterView(EntityView):
    """View of EXTRA Letter."""

    FILE_NAME = "extra_letters.png"
    PRIORITY = 15
    ROWS = 5
    COLUMNS = 4
    TRANSITION_DELAY = 0.3

    def __init__(self, entity_: entity.Entity) -> None:
        super().__init__(entity_)
        self.entity: entity.ExtraLetter
        self.select_sprite(self.entity.letter_id, 0)

    @override
    def notify(self, event_: event.Event) -> None:
        super().notify(event_)

        if isinstance(event_, events.ForwardTimeEvent):
            if self.entity.letter_timer.current > self.TRANSITION_DELAY:
                self.select_sprite(self.entity.letter_id, 0)
                return

            t = 1 - self.entity.letter_timer.current / self.TRANSITION_DELAY
            self.select_sprite(self.entity.letter_id, int(4 * t))
