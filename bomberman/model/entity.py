"""Provides classes for all entities of the game"""

from __future__ import annotations

import enum
import random
from typing import Dict, List, Optional, Set

from ..designpattern import observable
from . import events
from . import maze
from . import timer


# TODO: Fix collision and hit


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


class Position:
    """Position of entities in the maze."""

    def __init__(self, i: int, j: int) -> None:
        self.i = i
        self.j = j

    def __add__(self, other: object) -> Position:
        if isinstance(other, Direction):
            return Position(self.i + other.value[0], self.j + other.value[1])
        return NotImplemented

    def __str__(self) -> str:
        return str((self.i, self.j))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Position):
            return (self.i, self.j) == (other.i, other.j)
        return NotImplemented


class Direction(enum.Enum):
    """Direction to follow."""

    UP = (-1, 0)
    DOWN = (1, 0)
    RIGHT = (0, 1)
    LEFT = (0, -1)


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
        SIZE (Tuple[int, int]): (# row, # columns) of the entity.
            Default to (1, 1) (One tile large)
        VULNERABILIES (List[Damage.Type]): Vulnerabilies of the entity.
            Default to [] (Cannot take damage and is therefore invulnerable)
        REMOVING_DELAY (int): Time in removing state
            Default to 0 (Immediately removed.)
    """

    REPR: str = ""
    BASE_HEALTH = 0
    SIZE = (1, 1)
    VULNERABILITIES: List[Damage.Type] = []
    REMOVING_DELAY: float = 0

    def __init__(self, maze_: maze.Maze, position: Position) -> None:
        """Initialise an entity in the maze.

        Args:
            maze_ (Maze): The maze of the entity.
            position (Tuple[int, int]): Row and column indexes of the entity in the maze.
                If the entity is on several row/columns, it will indicates the top left corner of it.
        """
        super().__init__()
        self.maze = maze_
        self.position = position
        self.health = self.BASE_HEALTH
        self.removing_timer = timer.Timer(increase=False)

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

    def hit(self, damage: Damage) -> None:
        if self.removing_timer.is_active:
            return

        if damage.type in self.VULNERABILITIES:
            self.health = max(0, self.health - damage.damage)
            self.changed(events.HitEntityEvent(self))

            if self.health == 0:
                self.removing()

    def removing(self) -> None:
        self.removing_timer.start(self.REMOVING_DELAY)

    def remove(self) -> None:
        self.maze.remove_entity(self)


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

    def __init__(self, player: Player, position: Position) -> None:
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
        # Bomb explosion

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

    def __init__(self, maze_: maze.Maze, position: Position, strength: float, orientation: Laser.Orientation) -> None:
        super().__init__(maze_, position)
        self.orientation = orientation
        self.removing()

        for entity in self.maze.get_entities_at(self.position):
            entity.hit(Damage(int(Laser.DAMAGE * strength), Damage.Type.BOMBS))

    @staticmethod
    def generate_from_bomb(bomb: Bomb) -> None:
        """Generate laser at the center and then for each direction around the bomb

        Args:
            bomb (Bomb): Exploding bomb.
        """
        maze_ = bomb.maze
        maze_.add_entity(Laser(maze_, bomb.position, 1, Laser.Orientation.CENTER))

        for direction in [Direction.UP, Direction.DOWN, Direction.RIGHT, Direction.LEFT]:
            position = bomb.position
            if direction in {Direction.UP, Direction.DOWN}:
                orientation = Laser.Orientation.VERTICAL
            else:
                orientation = Laser.Orientation.HORIZONTAL
            for dist in range(1, bomb.radius + 1):
                position += direction

                if not maze_.is_inside(position) or maze_.contains((SolidWall,), position):
                    # Stop generating laser for this direction we have reached a solid wall
                    break

                alpha = dist / bomb.radius
                strength = 0.25 * alpha + (1 - alpha)  # The furthest the weakest

                if maze_.contains((BreakableWall,), position):
                    # Lasers can go through breakable wall only if the bomb is close to it
                    if dist == 1:
                        maze_.add_entity(Laser(maze_, position, strength, orientation))
                    break  # Laser will never go beyond though

                maze_.add_entity(Laser(maze_, position, strength, orientation))


class MovingEntity(Entity):
    """Moving entity in the maze.

    Let's split a tile in 100 small steps.
    An entity will move on those step toward another tile.

    Attrs:
        BASE_SPEED (int): Base speed of the entity.
            Default to 3 blocks per second
        BLOCKED_BY (Set[Entity]): Entities that will block thes
    """

    # FIXME: Collision with moving entity does not work

    BASE_SPEED = 300
    BLOCKED_BY: Set[EntityClass] = set()

    def __init__(self, maze_: maze.Maze, position: Position) -> None:
        super().__init__(maze_, position)
        self.speed = self.BASE_SPEED
        self.current_direction: Optional[Direction] = None
        self.next_direction: Optional[Direction] = None  # Could be for the player only ?
        self.next_position: Optional[Position] = None
        self.step = 0
        self.try_moving_since: float = 0

    def set_wanted_direction(self, direction: Optional[Direction]) -> None:
        """Set the direction the entity wants to go.

        If set during a current movement, the movement is first finished. Then the entity can change its direction

        Args:
            direction (Optional, Direction): The next direction to follow. If None, the movement will be stopped
        """
        self.next_direction = direction

    def _update_direction(self) -> None:
        """Update the direction once a movement is done

        Called internally by `update`. The current direction can be updated from the next direction,
        or this can also be ignored and set according to what happens in the maze (for instance for enemies)

        By default the next_direction is used to update the current one
        """
        self.current_direction = self.next_direction

    def update(self, delay: float) -> None:
        """Update the position after a small delay

        Args:
            delay (float): Time delay since last call.
        """
        super().update(delay)
        if self.removing_timer.is_active:
            return

        if not self.next_position:  # There is no current movement, thus the direction can be updated directly
            was_moving = self.current_direction != None
            self._update_direction()
            if not self.current_direction and was_moving:
                self.changed(events.MovedEntityEvent(self))  # Stop trying to move against an obstacle

        if not self.current_direction:  # No direction, nothing to do
            return

        # Let's move or keep moving
        self.try_moving_since += delay

        if not self.next_position:
            next_position = self.position + self.current_direction
            if self.maze.is_inside(next_position) and not self.maze.contains(tuple(self.BLOCKED_BY), next_position):
                self.next_position = next_position

        if not self.next_position:
            self.changed(events.MovedEntityEvent(self))
            return

        self.step += int(delay * self.speed)
        if self.step >= 100:
            step = self.step - 100
            self.position = self.next_position

            # Reset movement
            self.step = 0
            self.next_position = None
            self.try_moving_since = 0
            self._update_direction()

            if self.current_direction:
                next_position = self.position + self.current_direction
                if self.maze.is_inside(next_position) and not self.maze.contains(tuple(self.BLOCKED_BY), next_position):
                    self.next_position = next_position
                    self.step = step

        self.changed(events.MovedEntityEvent(self))


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
        fast (bool): If the player speed is increased
        fast_bomb (bool): Bombs explodes faster
        shield (bool): The player has no vulnerabilities
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

    def __init__(self, identifier: int) -> None:
        super().__init__(maze.Maze((0, 0)), Position(0, 0))  # Not related to any maze at first

        self.identifier = identifier

        # Init bonus
        self.bomb_capacity = self.BASE_BOMB_CAPACITY
        self.bomb_radius = self.BASE_BOMB_RADIUS
        self.fast = False
        self.fast_bomb = False
        self.shield = False

        # Init other import stuff
        self.life = self.BASE_LIFE
        self.bomb_count = 0
        self.score = 0
        # TODO: Invulnerability time with new life, shield bonus, any hit

    def reset(self, keep_observers=False) -> None:
        """Reset the player.

        Useful with the player death or a switch of maze.

        Args:
            keep_observers (bool): If False, observers are dropped.
        """
        if not keep_observers:
            super().reset()  # Drop links to the observers so that they can be garbage collected

        # Player related
        self.fast = False
        self.shield = False
        self.bomb_count = 0

        # Movement related
        self.current_direction = None
        self.next_direction = None
        self.next_position = None
        self.step = 0
        self.try_moving_since = 0

        # Entity related
        self.removing_timer.reset()

    def remove(self) -> None:
        self.life -= 1
        if not self.life:
            super().remove()
        else:
            self.health = self.BASE_HEALTH

        self.reset(True)
        # TODO: Reset bonus
        self.changed(events.LifeLossEvent(self))

    def register_new_maze(self, maze_: maze.Maze, position: Position) -> None:
        """Register the player in a new maze.

        Args:
            maze_ (maze.Maze): The new maze to play in
            position (Position): Starting position in the maze
        """
        self.maze = maze_
        self.position = position

    def bombs(self) -> None:
        if self.removing_timer.is_active:
            return

        if self.bomb_count == self.bomb_capacity:
            return

        if 60 < self.step < 90:
            return  # FIXME: Should have some bombing delay ? to prevent two bombs dropped at the same time (59 and 91 ?)

        bomb_position = self.position
        if self.step >= 80:
            bomb_position += self.current_direction

        if self.maze.contains((Bomb,), bomb_position):
            return
        bomb = Bomb(self, bomb_position)
        self.maze.add_entity(bomb)
        self.bomb_count += 1

    def bomb_explodes(self) -> None:
        self.bomb_count -= 1


# XXX: Ugly
Player.BLOCKED_BY = set([BreakableWall, SolidWall, Player])


class Enemy(MovingEntity):
    """Base class for all enemies."""

    REMOVING_DELAY = 2
    BASE_SPEED = 200
    VULNERABILITIES = [Damage.Type.BOMBS]
    ERRATIC = False  # Can randomly turn around
    # TODO: Special behavior of each entity, like sprint, turn back on the player, following him etc

    def __init__(self, maze_: maze.Maze, position: Position) -> None:
        super().__init__(maze_, position)

    def _update_direction(self) -> None:
        # Could may be be unified in Enemy class
        opposite = {
            None: None,
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.RIGHT: Direction.LEFT,
            Direction.LEFT: Direction.RIGHT,
        }[self.current_direction]

        plausible_directions = []
        for direction in [Direction.DOWN, Direction.UP, Direction.LEFT, Direction.RIGHT]:
            next_position = self.position + direction
            if self.maze.is_inside(next_position) and not self.maze.contains(tuple(self.BLOCKED_BY), next_position):
                plausible_directions.append(direction)

        if not plausible_directions:
            return  # Don't work for now

        if not self.ERRATIC and opposite in plausible_directions and len(plausible_directions) > 1:
            plausible_directions.remove(opposite)

        self.current_direction = random.choice(plausible_directions)


# XXX: Ugly
Enemy.BLOCKED_BY = set([BreakableWall, SolidWall, Enemy])


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
    BASE_SPEED = 300  # TODO: Improve speed estimation for all entities


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
