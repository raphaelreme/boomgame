"""Main part of the model: class Maze.

It holds all the data of current level.
"""

from __future__ import annotations

import enum
from typing import Callable, Dict, List, Optional, Set, Tuple

from ..designpattern import observable
from . import entity
from . import events
from . import timer
from . import vector


class MazeException(Exception):
    pass


class OutOfMazeError(MazeException):
    pass


class MazeDescriptionError(MazeException):
    pass


class Maze(observable.Observable):
    """Handle all entities in the maze.

    The maze can be observed in order to know which object it contains.

    Attrs:
        size (Tuple[int, int]): Number of boxes of the maze. (row, columns)
        state (Maze.State): Current state of the maze.
        entities (List[Entity]): All the entity in the maze.
        player_spawns (Dict[int, entity.Position]): Spawn position for each player
        end_timer (timer.Timer): Timer of the end of the maze
        extra_game_timer (timer.Timer): Timer for the extra game
        hurry_up_timer (timer.Timer): Timer in hurry up
    """

    class State(enum.Enum):
        RUNNING = 0
        FAILED = 1
        SOLVED = 2

    SEP = "|"
    VOID = " "
    PLAYER_SPAWNS = {"X": 1, "Y": 2}
    END_DELAY = 2.0
    GAME_OVER_DELAY = 4.0
    EXTRA_GAME_DELAY = 30.0
    HURRY_UP_DELAY = 30.0

    def __init__(self, size: Tuple[int, int]) -> None:
        super().__init__()
        self.size = size
        self.state = Maze.State.RUNNING
        self.entities: Set[entity.Entity] = set()
        self.player_spawns: Dict[int, vector.Vector] = {}
        self.end_timer = timer.Timer()
        self.extra_game_timer = timer.Timer()
        self.hurry_up_timer = timer.Timer()

    def add_entity(self, entity_: entity.Entity) -> None:
        """Register a new entity in the maze.

        Will check that the entity is in the maze.

        Args:
            entity_ (entity.Entity): The entity to register.
        """
        if not self.is_inside(entity_.colliding_rect):
            print(f"Warning: Try to add {entity_}. Out of boundaries: {self.size}")

        self.entities.add(entity_)
        self.changed(events.NewEntityEvent(entity_))

    def remove_entity(self, entity_: entity.Entity) -> None:
        """Remove an entity from the maze

        Args:
            entity_ (entity.Entity): The entity to remove
        """
        self.entities.remove(entity_)
        self.changed(events.RemovedEntityEvent(entity_))

    def add_player(self, player: entity.Player) -> None:
        """Add a player to the maze.

        Cannot add twice the same player.

        Args:
            player (entity.Player): The player to add
        """
        position = self.player_spawns.pop(player.identifier)

        player.register_new_maze(self, position)
        self.add_entity(player)
        self.add_entity(entity.Flash(self, player.position))

    def get_collision(
        self, rect: vector.Rect, condition: Optional[Callable[[entity.Entity], bool]] = None
    ) -> Set[entity.Entity]:
        """Get the overlapping entities

        Args:
            entity_ (vector.Rect): A rect to look at
            condition (Callable): A filter to apply on each entity

        Returns:
            Set[entity.Entity]: All the other entities in collision with the given rect
        """
        colliding_entities = set()

        for entity_ in filter(condition, self.entities):
            if rect.collide_with(entity_.colliding_rect):
                colliding_entities.add(entity_)

        return colliding_entities

    def is_inside(self, rect: vector.Rect) -> bool:
        """Check that the rect belongs to the maze

        Args:
            rect (vector.Rect): Rect in the maze

        Returns:
            bool
        """
        return vector.Rect(vector.Vector((0.0, 0.0)), vector.Vector(self.size)).contains(rect)

    def get_player_count(self) -> int:
        """Number of player in current maze.

        Returns:
            int: The number of player
        """
        return len(list(filter(lambda entity_: isinstance(entity_, entity.Player), self.entities)))

    def hurry_up(self) -> None:
        """Called by the game when the time is almost up"""
        if not self.hurry_up_timer.is_active:
            self.hurry_up_timer.start(self.HURRY_UP_DELAY)
            self.changed(events.HurryUpEvent())

    def update(self, delay: float) -> None:  # pylint: disable=too-many-branches
        """Handle time forwarding.

        Args:
            delay (float): Seconds spent since last call.
        """
        # Forward to entity
        for entity_ in self.entities.copy():
            entity_.update(delay)

        self.changed(events.ForwardTimeEvent(delay))

        if self.extra_game_timer.update(delay):
            self.extra_game_timer.reset()
            self.extra_game_timer.start(float("inf"))  # Block extra game timer
            for entity_ in self.entities.copy():
                if isinstance(entity_, entity.Enemy):
                    entity_.extra_game(False)
                if isinstance(entity_, entity.ExtraLetter):
                    entity_.remove()

        if self.hurry_up_timer.update(delay):
            for entity_ in self.entities:
                if isinstance(entity_, entity.Enemy):
                    entity_.enraged()

        # XXX: The state cannot change even if a player bombs itself during the end timer
        if self.end_timer.is_active:
            self.end_timer.update(delay)
            # self.changed(events.MazeEndingEvent())
            return

        players, enemies, coins = 0, 0, 0
        for entity_ in self.entities:
            if isinstance(entity_, entity.Player):
                players += 1
            if isinstance(entity_, entity.Enemy):
                enemies += 1
            if isinstance(entity_, entity.Coin):
                if not entity_.removing_timer.is_active:
                    coins += 1

        if not players:
            self.state = Maze.State.FAILED
            self.end_timer.start(self.GAME_OVER_DELAY)
            self.changed(events.MazeFailedEvent())
            return

        if not enemies:
            self.state = Maze.State.SOLVED
            self.end_timer.start(Maze.END_DELAY)
            self.changed(events.MazeSolvedEvent())
            return

        if not coins:
            if not self.extra_game_timer.is_active:
                self.extra_game_timer.start(self.EXTRA_GAME_DELAY)
                self.changed(events.ExtraGameEvent())
                for entity_ in self.entities:
                    if isinstance(entity_, entity.Enemy):
                        if not entity_.removing_timer.is_active:
                            entity_.extra_game(True)

    def __str__(self) -> str:
        identifier_to_repr = {i: r for r, i in Maze.PLAYER_SPAWNS.items()}

        static_repr = [[Maze.VOID for _ in range(self.size[1])] for _ in range(self.size[0])]

        for entity_ in self.entities:
            representation = entity_.REPR
            if isinstance(entity_, entity.Player):
                representation = identifier_to_repr[entity_.identifier]

            if not representation:
                continue

            i, j = entity_.position
            static_repr[int(i)][int(j)] = representation

        # If not all players, some spawn points will still be there
        for identifier, position in self.player_spawns.items():
            representation = identifier_to_repr[identifier]

            i, j = position
            static_repr[int(i)][int(j)] = representation

        return "\n".join(map(Maze.SEP.join, static_repr))

    def serialize(self) -> str:
        return str(self)

    @staticmethod
    def unserialize(string: str) -> Maze:  # pylint: disable=too-many-locals
        lines = string.split("\n")
        matrix = list(map(lambda line: line.split(Maze.SEP), lines))

        rows = len(matrix)
        columns = len(matrix[0])
        maze = Maze((rows, columns))
        has_coin = False

        teleporters: List[entity.Teleporter] = []

        for i, line in enumerate(matrix):
            if len(line) != columns:
                raise MazeDescriptionError(f"Line {i} has not the same shape as the first line.")

            for j, char in enumerate(line):
                if char == Maze.VOID:
                    continue

                if char in maze.PLAYER_SPAWNS:
                    identifier = maze.PLAYER_SPAWNS[char]
                    maze.player_spawns[identifier] = vector.Vector((float(i), float(j)))
                    continue

                klass: Optional[entity.EntityClass] = entity.EntityClass.representation_to_entity_class.get(char)

                if not klass:
                    raise MazeDescriptionError(f"Unknown identifier: '{char}' at {(i, j)}")

                if klass is entity.Coin:
                    has_coin = True

                entity_ = klass(maze, vector.Vector((float(i), float(j))))
                maze.entities.add(entity_)

                if isinstance(entity_, entity.Teleporter):
                    teleporters.append(entity_)

        for i, teleporter in enumerate(teleporters):
            teleporter.next_teleporter = teleporters[(i + 1) % len(teleporters)]

        if not has_coin:
            maze.extra_game_timer.start(float("inf"))  # Prevent Extra Game

        return maze

    def save(self, file_name: str) -> None:
        with open(file_name, "w") as file:
            file.write(self.serialize())

    @staticmethod
    def read(file_name: str) -> Maze:
        with open(file_name, "r") as file:
            return Maze.unserialize(file.read())
