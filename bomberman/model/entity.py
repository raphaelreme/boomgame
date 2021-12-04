"""Provides classes for all entities of the game"""

from __future__ import annotations

import enum
import math
import random
from typing import Dict, List, Optional, Tuple

from ..designpattern import observable
from . import events
from . import maze
from . import timer
from . import vector


class Damage:
    """Damage done to entities

    Two types: Damage from bombs. And damage from the enemies.
    """

    class Type(enum.Enum):
        ENEMIES = 0
        BOMBS = 1

    def __init__(self, damage: int, type_: Type) -> None:
        self.damage = damage
        self.type = type_


class EntityClass(type):
    """Entity metaclass.

    Attr:
        REPR (Optional[str]):
        representation_to_entity_class (Dict[str, EntityClass]): Mapping from class.REPR to class for all
            EntityClass that are representable. (<=> define REPR attr)
    """

    REPR: str = ""
    representation_to_entity_class: Dict[str, EntityClass] = {}

    def __init__(cls, cls_name: str, bases: tuple, attributes: dict) -> None:
        super().__init__(cls_name, bases, attributes)

        if cls.REPR:
            if cls.REPR == " " or cls.REPR == "|" or len(cls.REPR) > 1:
                raise ValueError(
                    f"Invalid REPR attribute: {cls.REPR} of {cls}."
                    f"Should be a single char and not '{maze.Maze.VOID}' nor '{maze.Maze.SEP}'"
                )
            type(cls).representation_to_entity_class[cls.REPR] = cls


class Entity(observable.Observable, metaclass=EntityClass):
    """Anything that is inside the maze.

    Class Attrs:
        REPR (str): Static representation of entities in mazes.
            If not provided, the entity will not be represented in a maze represention.
        BASE_HEALTH (int): Hp of the entity. When reaching 0, the entity is removed.
            Default to 0 (Removed at the first damage received)
        SIZE (Tuple[float, float]): (# row, # columns) of the entity.
            Default to (1, 1) (One tile large)
        VULNERABILIES (List[Damage.Type]): Vulnerabilies of the entity.
            Default to [] (Cannot take damage and is therefore invulnerable)
        REMOVING_DELAY (int): Time in removing state
            Default to 0 (Immediately removed.)
    """

    REPR: str = ""
    BASE_HEALTH = 0
    SIZE = (1.0, 1.0)
    VULNERABILITIES: List[Damage.Type] = []
    REMOVING_DELAY: float = 0

    def __init__(self, maze_: maze.Maze, position: vector.Vector) -> None:
        """Initialise an entity in the maze.

        Args:
            maze_ (maze.Maze): The maze of the entity.
            position (vector.Vector): Row and column position of the entity in the maze.
                Always refers to the top left corner of the image of the entity
        """
        super().__init__()
        self.maze = maze_
        self.position = position
        self.health = self.BASE_HEALTH
        self.size = vector.Vector(self.SIZE)
        self.removing_timer = timer.Timer(increase=False)

    def colliding_rect(self) -> vector.Rect:
        """Build the colliding rect of the entity

        Given the current approach, the image size is a tuple of integer.
        Entity with a float size have an int size image centered on the entity.
        And the position of the entity is the top left position of the image.

        Returns:
            vector.Rect: The colliding rect of the entity
        """
        return self._build_colliding_rect(self.position, self.size)

    @staticmethod
    def _build_colliding_rect(position: vector.Vector, size: vector.Vector) -> vector.Rect:
        return vector.Rect(position + (size.apply(math.ceil) - size) * 0.5, size)

    def update(self, delay: float) -> None:
        """Handle time forwarding.

        Args:
            delay (float): Seconds spent since last call.
        """
        if self.removing_timer.is_active:
            if self.removing_timer.update(delay):
                self.remove()
            else:
                self.changed(events.RemovingEntityEvent(self))

    def hit(self, damage: Damage) -> bool:
        if self.removing_timer.is_active:
            return False

        if damage.type not in self.VULNERABILITIES:
            return False

        self.health = max(0, self.health - damage.damage)
        self.changed(events.HitEntityEvent(self))

        if self.health == 0:
            self.removing()

        return True

    def removing(self) -> None:
        self.removing_timer.start(self.REMOVING_DELAY)

    def remove(self) -> None:
        self.maze.remove_entity(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} at {self.colliding_rect()}"


class BreakableWall(Entity):
    REPR = "B"
    VULNERABILITIES = [Damage.Type.BOMBS]
    REMOVING_DELAY = 0.5


class SolidWall(Entity):
    REPR = "S"


class Bomb(Entity):
    VULNERABILITIES = [Damage.Type.BOMBS]
    REMOVING_DELAY = 0
    BASE_TIMEOUT: float = 5
    FAST_TIMEOUT: float = 2

    def __init__(self, player: Player, position: vector.Vector) -> None:
        super().__init__(player.maze, position)
        self.player = player
        self.radius = player.bomb_radius
        self.timer = timer.Timer(increase=False)
        self.timer.start(self.FAST_TIMEOUT if player.fast_bomb else self.BASE_TIMEOUT)

    def update(self, delay: float) -> None:
        if self.removing_timer.is_active:
            super().update(delay)
            return

        if self.timer.update(delay):
            self.removing()
            super().update(-self.timer.current)
            return

        self.changed(events.ForwardTimeEvent(self))

    def removing(self) -> None:
        super().removing()

        self.player.bomb_explodes()
        Laser.generate_from_bomb(self)


class Laser(Entity):
    """Laser entity created by a Bomb explosion"""

    class Orientation(enum.Enum):
        CENTER = 0
        VERTICAL = 1
        HORIZONTAL = 2

    REMOVING_DELAY = 0.3
    DAMAGE = 10

    def __init__(
        self, maze_: maze.Maze, position: vector.Vector, strength: float, orientation: Laser.Orientation
    ) -> None:
        super().__init__(maze_, position)
        self.orientation = orientation
        self.damage = int(self.DAMAGE * strength)
        self.removing()

    def update(self, delay: float) -> None:
        super().update(delay)

        if self.removing_timer.is_done:
            return

        decay = abs(self.removing_timer.current - self.REMOVING_DELAY / 2)
        size = 1 - 2 / self.REMOVING_DELAY * decay

        if self.orientation == Laser.Orientation.CENTER:
            self.size = vector.Vector((size, size))
        elif self.orientation == Laser.Orientation.HORIZONTAL:
            self.size = vector.Vector((size, 1.0))
        else:  # Vertical
            self.size = vector.Vector((1.0, size))

        for entity in self.maze.get_collision(self.colliding_rect()):
            entity.hit(Damage(self.damage, Damage.Type.BOMBS))

    @staticmethod
    def generate_from_bomb(bomb: Bomb) -> None:
        """Generate laser at the center and then for each direction around the bomb

        Args:
            bomb (Bomb): Exploding bomb.
        """
        maze_ = bomb.maze
        maze_.add_entity(Laser(maze_, bomb.position, 1, Laser.Orientation.CENTER))

        for direction in [vector.Direction.UP, vector.Direction.DOWN, vector.Direction.RIGHT, vector.Direction.LEFT]:
            position = bomb.position
            if direction in {vector.Direction.UP, vector.Direction.DOWN}:
                orientation = Laser.Orientation.VERTICAL
            else:
                orientation = Laser.Orientation.HORIZONTAL
            for dist in range(1, bomb.radius + 1):
                position += direction.vector  # Int position
                laser_rect = vector.Rect(position, bomb.size)

                if not maze_.is_inside(laser_rect) or maze_.get_collision(
                    laser_rect, lambda entity: isinstance(entity, SolidWall)
                ):
                    # Stop generating laser for this direction we have reached a solid wall
                    break

                alpha = dist / bomb.radius
                strength = 0.25 * alpha + (1 - alpha)  # The furthest the weakest

                if maze_.get_collision(laser_rect, lambda entity: isinstance(entity, BreakableWall)):
                    # Lasers can go through breakable wall only if the bomb is close to it
                    if dist == 1:
                        maze_.add_entity(Laser(maze_, position, strength, orientation))
                    break  # Laser will never go beyond though

                maze_.add_entity(Laser(maze_, position, strength, orientation))


class MovingEntity(Entity):
    """Moving entity in the maze.

    Can only move according to a valid direction and on a plain column or row

    Attrs:
        BASE_SPEED (int): Base speed of the entity.
            Default to 3 blocks per second
        BLOCKED_BY (Set[EntityClass]): Static entities that will block the entity
        BOUNCE_ON (Set[EntityClass]): Moving entities that will block the entity.
    """

    BASE_SPEED = 3
    BLOCKED_BY: Tuple[EntityClass, ...] = (SolidWall, BreakableWall)
    BOUNCE_ON: Tuple[EntityClass, ...] = ()

    def __init__(self, maze_: maze.Maze, position: vector.Vector) -> None:
        super().__init__(maze_, position)
        self.speed = self.BASE_SPEED
        self.current_direction: Optional[vector.Direction] = None
        self.next_direction: Optional[vector.Direction] = None

        # Helper to keep a clean state
        # Not that position = (1 - step) * prev_position + step * next_position
        self.prev_position = self.position
        self.next_position: Optional[vector.Vector] = None
        self.try_moving_since = 0.0
        self.step = 0.0

    def set_wanted_direction(self, direction: Optional[vector.Direction]) -> None:
        """Set the direction the entity wants to go.

        If set during a current movement, the movement is first finished. Then the entity can change its direction

        Args:
            direction (Optional, Direction): The next direction to follow. If None, the movement will be stopped
        """
        self.next_direction = direction

    def _update_direction(self) -> None:
        """Update the direction once a movement is done

        Called internally by `update`. The current direction can be updated from the next direction,
        or randomly or according to what happens in the maze (for instance for enemies)

        By default the next_direction is used to update the current one
        """
        self.current_direction = self.next_direction

    def update(self, delay: float) -> None:
        super().update(delay)

        if not self.removing_timer.is_active:
            self.move(delay)

    def move(self, delay: float) -> None:
        """Update the position after a small delay

        Args:
            delay (float): Time delay since last call.
        """
        # Not moving yet, can update the position directly
        if not self.next_position:
            self._update_direction()
            if not self.current_direction and self.try_moving_since:
                self.try_moving_since = 0
                self.changed(events.MovedEntityEvent(self))  # Stop trying to move against an obstacle

        if not self.current_direction:  # No direction, nothing to do
            return

        self.try_moving_since += delay

        # Not moving, but try to
        if not self.next_position:
            assert self.position.int_part() == self.position  # Should be a int position
            next_position = self.position + self.current_direction.vector
            if self._valid_next_position(next_position):
                self.next_position = next_position

        if not self.next_position:  # Move against an obstacle
            self.changed(events.MovedEntityEvent(self))
            return

        step = delay * self.speed
        self.position += self.current_direction.vector * step
        self.step += step
        if self.step >= 1:  # Has reached a new tile
            remaining_delay = (self.step - 1) / self.speed

            self.position = self.next_position
            self.step = 0
            self.prev_position = self.position
            self.next_position = None

            self.move(remaining_delay)
            return

        # Collision (Should almost never occurs with step=1, let's see if it is enough)
        colliding_entities = self.maze.get_collision(
            self.colliding_rect(), lambda entity: isinstance(entity, self.BOUNCE_ON) and entity is not self
        )
        if len(colliding_entities) > 1:
            print("WARNING: More than one entites colliding at once")

        if colliding_entities:
            self.position -= self.current_direction.vector * step
            self.step -= step
            if self.next_direction != self.current_direction:  # Stop insisting
                self.current_direction = vector.Direction.get_opposite_direction(self.current_direction)
                self.next_position, self.prev_position = self.prev_position, self.next_position
                self.step = 1 - self.step

        self.changed(events.MovedEntityEvent(self))

    def _valid_next_position(self, next_position: vector.Vector) -> bool:
        rect = self._build_colliding_rect(next_position, self.size)

        return self.maze.is_inside(rect) and not self.maze.get_collision(
            rect, lambda entity: isinstance(entity, self.BLOCKED_BY)
        )


class Player(MovingEntity):
    """Player entity.

    Special entity, it is controlled by the player, it has several lifes,
    credits, and goes through different mazes.

    It moves and drops bombs

    Attrs: (See Entity for more attributes)
        BASE_LIFE, life (int, int): Life of the player.
            When the health reaches 0, the life decreased and health is restored.
        BASE_BOMB_CAPACITY, bomb_capacity (int, int): Number of bombs that can be dropped
            at the same time
        BASE_BOMB_RADIUS, bomb_radius (int, int): Size of the bomb explosion
        NEW_LIFE_SHIELD (float): Shield time when resurrected
        HIT_SHIELD (float): Shield when hit
        fast (bool): If the player speed is increased
        fast_bomb (bool): Bombs explodes faster
        shield (timer.Timer): A timer when the player is invulnerable
        score (int): Current score of the player
    """

    # Has no real REPR. X and Y are used to indicates that a player can spawn here.
    # Players are added to a maze by the game itself

    REMOVING_DELAY = 2
    VULNERABILITIES = [Damage.Type.BOMBS, Damage.Type.ENEMIES]
    BASE_HEALTH = 16
    BASE_LIFE = 3
    BASE_BOMB_CAPACITY = 5
    BASE_BOMB_RADIUS = 4
    NEW_LIFE_SHIELD = 3.0
    HIT_SHIELD = 1.0

    def __init__(self, identifier: int) -> None:
        super().__init__(maze.Maze((0, 0)), vector.Vector((0.0, 0.0)))  # Not related to any maze at first

        self.identifier = identifier

        # Init bonus
        self.bomb_capacity = self.BASE_BOMB_CAPACITY
        self.bomb_radius = self.BASE_BOMB_RADIUS
        self.fast = False
        self.fast_bomb = False
        self.shield = timer.Timer(increase=False)

        # Init other import stuff
        self.life = self.BASE_LIFE
        self.bomb_count = 0
        self.score = 0
        # TODO: Invulnerability time with new life, shield bonus, any hit

    def reset(self) -> None:
        """Reset the player when changing of maze"""
        super().reset()  # Drop links to the observers so that they can be garbage collected

        # Player related
        self.fast = False
        self.shield.reset()
        self.bomb_count = 0

        # Movement related
        self.current_direction = None
        self.next_direction = None
        self.next_position = None
        self.prev_position = self.position
        self.step = 0.0
        self.try_moving_since = 0.0

        # Entity related
        self.removing_timer.reset()

    def new_life(self) -> None:
        """Reset some stuff when a player loses a life"""
        self.fast = False
        self.shield.reset()
        self.shield.start(self.NEW_LIFE_SHIELD)
        # Reset bonus

        self.removing_timer.reset()

    def remove(self) -> None:
        self.life -= 1
        if not self.life:
            super().remove()
        else:
            self.health = self.BASE_HEALTH

        self.new_life()
        # TODO: Reset bonus
        self.changed(events.LifeLossEvent(self))

    def register_new_maze(self, maze_: maze.Maze, position: vector.Vector) -> None:
        """Register the player in a new maze.

        Args:
            maze_ (maze.Maze): The new maze to play in
            position (vector.Vector): Starting position in the maze
        """
        self.maze = maze_
        self.position = position
        self.reset()

    def bombs(self) -> None:
        if self.removing_timer.is_active:
            return

        if self.bomb_count == self.bomb_capacity:
            return

        if 0.6 < self.step < 0.9:
            return  # FIXME: Should have some bombing delay ? to prevent two bombs dropped at the same time (59 and 91 ?)

        bomb_position = self.prev_position
        if self.next_position and self.step >= 0.8:
            bomb_position = self.next_position

        if self.maze.get_collision(
            self._build_colliding_rect(bomb_position, self.size), lambda entity: isinstance(entity, Bomb)
        ):  # Don't drop a bomb if one is already here
            return

        self.maze.add_entity(Bomb(self, bomb_position))
        self.bomb_count += 1

    def bomb_explodes(self) -> None:
        self.bomb_count -= 1

    def hit(self, damage: Damage) -> bool:
        if self.shield.is_active:
            return False

        if not super().hit(damage):
            return False

        if self.health:
            self.shield.start(self.HIT_SHIELD)
        return True

    def update(self, delay: float) -> None:
        super().update(delay)

        if self.shield.update(delay):
            self.shield.reset()


# XXX: Ugly
Player.BOUNCE_ON = (Player,)


class Enemy(MovingEntity):
    """Base class for all enemies."""

    REMOVING_DELAY = 2
    BASE_SPEED = 2
    VULNERABILITIES = [Damage.Type.BOMBS]
    ERRATIC = False  # Can randomly turn around
    COLLISION_DAMAGE = 1
    BULLET_DAMAGE = 1
    # TODO: Special behavior of each entity, like sprint, turn back on the player, following him etc

    def _update_direction(self) -> None:
        if self.next_direction:  # Usually not set for enemies
            self.current_direction = self.next_direction  # Could check direction validity
            self.next_direction = None
            return

        plausible_directions = []
        for direction in [vector.Direction.DOWN, vector.Direction.UP, vector.Direction.LEFT, vector.Direction.RIGHT]:
            next_position = self.position + direction.vector
            if self._valid_next_position(next_position):
                plausible_directions.append(direction)

        if not plausible_directions:
            return  # Don't work for now

        opposite_direction: Optional[vector.Direction]
        if self.current_direction:
            opposite_direction = vector.Direction.get_opposite_direction(self.current_direction)
        else:
            opposite_direction = None

        if not self.ERRATIC and opposite_direction in plausible_directions and len(plausible_directions) > 1:
            plausible_directions.remove(opposite_direction)

        self.current_direction = random.choice(plausible_directions)

    def update(self, delay: float) -> None:
        super().update(delay)

        if self.removing_timer.is_active:
            return

        for entity in self.maze.get_collision(self):
            entity.hit(Damage(self.COLLISION_DAMAGE, Damage.Type.ENEMIES))


# XXX: Ugly
Enemy.BOUNCE_ON = (Enemy,)


class Soldier(Enemy):
    REPR = "0"
    ERRATIC = True


class Sarge(Enemy):
    REPR = "1"
    ERRATIC = True


class Lizzy(Enemy):
    REPR = "2"


class Taur(Enemy):
    REPR = "3"
    BASE_SPEED = 3  # TODO: Improve speed estimation for all entities


class Gunner(Enemy):
    REPR = "4"


class Thing(Enemy):
    REPR = "5"


class Ghost(Enemy):
    REPR = "6"


class Smoulder(Enemy):
    REPR = "7"


class Skully(Enemy):
    REPR = "8"


class Giggler(Enemy):
    REPR = "9"
