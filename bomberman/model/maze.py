"""Main part of the model: class Maze.

It holds all the data of the game.
"""

from __future__ import annotations

import enum
from typing import Dict, List, Optional, Set, Tuple

from ..designpattern import observable
from . import entity
from . import events
from . import timer


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
    """

    class State(enum.Enum):
        RUNNING = 0
        FAILED = 1
        SOLVED = 2

    SEP = "|"
    VOID = " "
    PLAYER_SPAWNS = {"X": 1, "Y": 2}
    END_DELAY = 2

    def __init__(self, size: Tuple[int, int]) -> None:
        super().__init__()
        self.size = size
        self.state = Maze.State.RUNNING
        self.entities: Set[entity.Entity] = set()
        self.player_spawns: Dict[int, entity.Position] = {}
        self.end_timer = timer.Timer()

    def add_entity(self, entity_: entity.Entity) -> None:
        """Register a new entity in the maze.

        Will check that the entity is in the maze.

        Args:
            entity_ (entity.Entity): The entity to register.
        """
        if not self.is_inside(entity_.position):
            raise OutOfMazeError(f"Try to add {entity_} at {entity_.position}. Out of boundaries: {self.size}")

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

    def contains(self, entity_classes: Tuple[entity.EntityClass, ...], position: entity.Position) -> bool:
        """Check if any entity present at the given position is of the given classes

        Args:
            entity_classes (Tuple[entity.EntityClass, ...]): Type of entities to look at
            position (entity.Position): Position in the maze

        Returns:
            bool
        """
        for entity_ in self.entities:
            if entity_.position == position and isinstance(entity_, entity_classes):
                return True
        return False

    def get_entities_at(self, position: entity.Position) -> List[entity.Entity]:
        """Return all the entities at a given position

        Args:
            position (entity.Position): The position to look at

        Returns:
            List[entity.Entity]: Entities at the current position
        """
        entites = []
        for entity_ in self.entities:
            if entity_.position == position:
                entites.append(entity_)

        return entites

    def is_inside(self, position: entity.Position) -> bool:
        """Check that the position belongs to the maze

        Args:
            position (entity.Position): Position in the maze

        Returns:
            bool
        """
        return 0 <= position.i < self.size[0] and 0 <= position.j < self.size[1]

    def get_player_count(self) -> int:
        """Number of player in current maze.

        Returns:
            int: The number of player
        """
        return len(list(filter(lambda entity_: isinstance(entity_, entity.Player), self.entities)))

    def update(self, delay: float) -> None:
        """Handle time forwarding.

        Args:
            delay (float): Seconds spent since last call.
        """
        # Forward to entity
        for entity_ in self.entities.copy():
            entity_.update(delay)

        # XXX: The state cannot change even if a player bombs itself during the end timer
        if self.end_timer.is_active:
            self.end_timer.update(delay)
            self.changed(events.MazeEndingEvent())
            return

        players, enemies = 0, 0
        for entity_ in self.entities:
            if isinstance(entity_, entity.Player):
                players += 1
            if isinstance(entity_, entity.Enemy):
                enemies += 1

        if not players:
            self.state = Maze.State.FAILED
            self.end_timer.start(Maze.END_DELAY)
            self.changed(events.MazeFailedEvent())
            return

        if not enemies:
            self.state = Maze.State.SOLVED
            self.end_timer.start(Maze.END_DELAY)
            self.changed(events.MazeSolvedEvent())

    def __str__(self) -> str:
        identifier_to_repr = {i: r for r, i in Maze.PLAYER_SPAWNS.items()}

        static_repr = [[Maze.VOID for _ in range(self.size[1])] for _ in range(self.size[0])]

        for entity_ in self.entities:
            representation = entity_.REPR
            if isinstance(entity_, entity.Player):
                representation = identifier_to_repr[entity_.identifier]

            if not representation:
                continue

            i, j = entity_.position.i, entity_.position.j
            static_repr[i][j] = representation

        # If not all players, some spawn points will still be there
        for identifier, position in self.player_spawns.items():
            representation = identifier_to_repr[identifier]
            static_repr[position.i][position.j] = representation

        return "\n".join(map(Maze.SEP.join, static_repr))

    def serialize(self) -> str:
        return str(self)

    @staticmethod
    def unserialize(string: str) -> Maze:
        lines = string.split("\n")
        matrix = list(map(lambda line: line.split(Maze.SEP), lines))

        rows = len(matrix)
        columns = len(matrix[0])
        maze = Maze((rows, columns))

        for i, line in enumerate(matrix):
            if len(line) != columns:
                raise MazeDescriptionError(f"Line {i} has not the same shape as the first line.")

            for j, char in enumerate(line):
                if char == Maze.VOID:
                    continue

                if char in maze.PLAYER_SPAWNS:
                    identifier = maze.PLAYER_SPAWNS[char]
                    maze.player_spawns[identifier] = entity.Position(i, j)
                    continue

                klass: Optional[entity.EntityClass] = entity.EntityClass.representation_to_entity_class.get(char)

                if not klass:
                    raise MazeDescriptionError(f"Unknown identifier: '{char}' at {(i, j)}")

                maze.entities.add(klass(maze, entity.Position(i, j)))

        return maze

    def save(self, file_name: str) -> None:
        with open(file_name, "w") as file:
            file.write(self.serialize())

    @staticmethod
    def read(file_name: str) -> Maze:
        with open(file_name, "r") as file:
            return Maze.unserialize(file.read())
