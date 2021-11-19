"""Handle entities of the maze."""

from __future__ import annotations

from typing import List, Tuple, cast

from . import TILE_SIZE, inflate_to_reality
from . import view
from ..designpattern import event
from ..designpattern import observer
from ..model import entity
from ..model import events


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
    REMOVING_STEPS: List[Tuple[int, int]] = []

    def __init__(self, entity_: entity.Entity) -> None:
        image_total_size = (self.SPRITE_SIZE[0] * self.COLUMNS, self.SPRITE_SIZE[1] * self.ROWS)
        super().__init__(
            view.load_image(self.FILE_NAME, image_total_size),
            inflate_to_reality((entity_.position.i, entity_.position.j)),
        )
        self.entity = entity_
        self.entity.add_observer(self)
        self.removing_steps = self.REMOVING_STEPS

    def notify(self, event_: event.Event) -> None:
        """Handle an event from the observed entity

        Args:
            event_ (event.Event): Event received from the observable.
        """
        if event_.handled:
            return

        if isinstance(event_, events.RemovingEntityEvent):
            if not self.entity.removing_timer.is_active:
                print("WARNING: removing event without removing state:", self)
            event_.handled = True

            if not self.entity.REMOVING_DELAY or not self.removing_steps:
                return

            step = 1 - max(self.entity.removing_timer.current, 0) / self.entity.removing_timer.total
            self.select_sprite(*self.removing_steps[int(step * len(self.removing_steps))])

    @staticmethod
    def from_entity(entity_: entity.Entity) -> EntityView:
        class_name = f"{entity_.__class__.__name__}View"
        return globals()[class_name](entity_)

    def __lt__(self, other) -> bool:
        """Entity views are sorted by priority"""
        if isinstance(other, EntityView):
            return self.PRIORITY < other.PRIORITY
        return NotImplemented

    def set_style(self, style: int) -> None:
        """Set the style of an entity.

        Only used for walls for now.
        """
        pass


class SolidWallView(EntityView):
    PRIORITY = 100
    FILE_NAME = "solid_wall.png"
    ROWS = 8
    COLUMNS = 1

    def __init__(self, entity_: entity.SolidWall) -> None:
        super().__init__(entity_)
        self.set_style(0)

    def set_style(self, style: int) -> None:
        self.select_sprite(style, 0)


class BreakableWallView(EntityView):
    PRIORITY = 100
    FILE_NAME = "breakable_wall.png"
    ROWS = 8
    COLUMNS = 4
    REMOVING_STEPS = [(0, 1), (0, 2), (0, 3)]

    def __init__(self, entity_: entity.BreakableWall) -> None:
        super().__init__(entity_)
        self.set_style(0)

    def set_style(self, style: int) -> None:
        self.removing_steps = [(style, index[1]) for index in self.REMOVING_STEPS]
        self.select_sprite(style, 0)


class BombView(EntityView):
    PRIORITY = 10
    FILE_NAME = "bomb.png"
    ROWS = 1
    COLUMNS = 3
    RATE = 0.3
    FAST_RATE = 0.05

    def __init__(self, entity_: entity.Bomb) -> None:
        super().__init__(entity_)
        self.select_sprite(0, 0)

    def notify(self, event_: event.Event) -> None:
        super().notify(event_)
        if event_.handled:
            return

        if isinstance(event_, events.ForwardTimeEvent):
            bomb = cast(entity.Bomb, event_.entity)
            if bomb.timer.current < bomb.FAST_TIMEOUT:
                index = int((bomb.BASE_TIMEOUT - bomb.timer.current) / self.FAST_RATE)
                self.select_sprite(0, 1 + (index % 2))
            else:
                index = int((bomb.BASE_TIMEOUT - bomb.timer.current) / self.RATE)
                self.select_sprite(0, index % 2)


class LaserView(EntityView):
    FILE_NAME = "laser.png"
    ROWS = 3
    COLUMNS = 4
    REMOVING_STEPS = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 2), (0, 1), (0, 0)]

    def __init__(self, entity_: entity.Laser) -> None:
        super().__init__(entity_)
        self.removing_steps = [(entity_.orientation.value, index[1]) for index in self.REMOVING_STEPS]


class MovingEntityView(EntityView):
    """Base view class for all moving entity"""

    RATE = 0.1

    direction_to_column = {
        None: 0,
        entity.Direction.DOWN: 0,
        entity.Direction.UP: 1,
        entity.Direction.RIGHT: 2,
        entity.Direction.LEFT: 3,
    }

    def __init__(self, entity_: entity.MovingEntity) -> None:
        super().__init__(entity_)
        i = self.direction_to_column[entity_.current_direction]
        self.select_sprite(i, 0)

    def notify(self, event_: event.Event) -> None:
        super().notify(event_)
        if event_.handled:
            return

        if isinstance(event_, (events.MovedEntityEvent, events.LifeLossEvent)):  # XXX
            entity_ = cast(entity.MovingEntity, event_.entity)
            self.position = inflate_to_reality((entity_.position.i, entity_.position.j))
            if not entity_.current_direction:  # End of a movement probably
                self.select_sprite(self.direction_to_column[entity_.current_direction], 0)
                return

            i = self.direction_to_column[entity_.current_direction]
            j = int(entity_.try_moving_since / self.RATE) % self.COLUMNS
            self.select_sprite(i, j)

            if entity_.next_position:
                next_position = inflate_to_reality((entity_.next_position.i, entity_.next_position.j))
                self.position = (
                    int((self.position[0] * (100 - entity_.step) + entity_.step * next_position[0]) / 100),
                    int((self.position[1] * (100 - entity_.step) + entity_.step * next_position[1]) / 100),
                )


class PlayerView(MovingEntityView):
    PRIORITY = 20
    ROWS = 5
    COLUMNS = 8
    REMOVING_STEPS = [(4, 0), (4, 1), (4, 2), (4, 1)] * 10 + [(4, 1)] * 5

    def __init__(self, entity_: entity.Player) -> None:
        self.FILE_NAME = f"player{entity_.identifier}.png"  # pylint: disable = invalid-name
        super().__init__(entity_)

    def notify(self, event_: event.Event) -> None:
        super().notify(event_)
        if event_.handled:
            return

        if isinstance(event_, events.LifeLossEvent):
            # In case of a life loss, let's update the sprite like it would be done when moving
            super().notify(events.MovedEntityEvent(event_.entity))


class EnemyView(MovingEntityView):
    """Base view class for enemies"""

    PRIORITY = 15
    ROWS = 6
    COLUMNS = 4
    REMOVING_STEPS = [(5, 0), (5, 1)] * 10

    def __init__(self, entity_: entity.Enemy) -> None:
        self.FILE_NAME = f"{entity_.__class__.__name__.lower()}.png"
        super().__init__(entity_)


class SoldierView(EnemyView):
    pass


class SargeView(EnemyView):
    pass


class LizzyView(EnemyView):
    REMOVING_STEPS = [(5, 0), (5, 1), (5, 2), (5, 3)] * 5


class TaurView(EnemyView):
    pass


class GunnerView(EnemyView):
    pass


class ThingView(EnemyView):
    pass


class GhostView(EnemyView):
    pass


class SmoulderView(EnemyView):
    REMOVING_STEPS = [(5, 0), (5, 1), (5, 2), (5, 3)] * 5


class SkullyView(EnemyView):
    pass


class GigglerView(EnemyView):
    pass