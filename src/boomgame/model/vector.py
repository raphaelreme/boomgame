"""Extra classes related to 2D computations.

No need of numpy thanks to this, and the model is pygame independent.

(Note that without model/view organization the code would probably be smaller and simpler,
with pygame directly managing everything)
"""

from __future__ import annotations

import enum
import sys
from typing import Callable

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override


class Vector(tuple[float, float]):  # noqa: SLOT001  # TODO: Check slots?
    """Simple 2D vector computations useful for positions and directions."""

    def __add__(self, other: object) -> Vector:
        """Addition of two vectors."""
        if isinstance(other, tuple):
            if len(other) != len(self):
                raise RuntimeError("Sizes do not match")
            return Vector((x + y for x, y in zip(self, other)))
        return NotImplemented

    def __radd__(self, other: object) -> Vector:
        """Addition of two vectors (reversed)."""
        return self + other

    def __mul__(self, other: object) -> Vector:
        """Pointwise multiplication or scalar multiplication."""
        if isinstance(other, (int, float)):
            return Vector(other * x for x in self)
        if isinstance(other, tuple):
            return Vector((x * y for x, y in zip(self, other)))
        return NotImplemented

    def __rmul__(self, other: object) -> Vector:
        """Pointwise multiplication or scalar multiplication (reversed)."""
        return self * other

    def __sub__(self, other: object) -> Vector:
        """Subtraction of two vectors."""
        if isinstance(other, tuple):
            return self + -1 * Vector(other)
        return NotImplemented

    def __rsub__(self, other: object) -> Vector:
        """Subtraction of two vectors (reversed)."""
        return -1 * (self - other)

    def apply(self, func: Callable[[float], float]) -> Vector:
        """Apply a function to all the vector."""
        return Vector(func(x) for x in self)

    def int_part(self) -> Vector:
        """Return the integer part of the vector."""
        return Vector(x // 1 for x in self)

    def frac_part(self) -> Vector:
        """Return the fractionnal part of the vector."""
        return Vector(x % 1 for x in self)


class Rect:
    """Rect for collision detection.

    Could probably use pygame.Rect but it does not supports floats so...
    """

    def __init__(self, position: Vector, size: Vector) -> None:
        self.x = position[0]
        self.y = position[1]
        self.width = size[0]
        self.height = size[1]

    def collide_with(self, other: Rect) -> bool:
        """Check if this rect overlaps with the other."""
        return (
            self.x < other.x + other.width
            and self.x + self.width > other.x
            and self.y < other.y + other.height
            and self.y + self.height > other.y
        )

    def contains(self, other: Rect) -> bool:
        """Check if this rect contains the other."""
        return (
            self.x <= other.x
            and self.y <= other.y
            and self.x + self.width >= other.x + other.width
            and self.y + self.height >= other.y + other.height
        )

    @override
    def __repr__(self) -> str:
        return str((self.x, self.y, self.width, self.height))


class Direction(enum.Enum):
    """Default directions for moving entities in the maze."""

    UP = (-1.0, 0.0)
    DOWN = (1.0, 0.0)
    RIGHT = (0.0, 1.0)
    LEFT = (0.0, -1.0)

    def __init__(self, *args: float) -> None:
        super().__init__()
        self.vector = Vector(args)

    @staticmethod
    def get_opposite_direction(direction: Direction) -> Direction:
        """Return the opposite direction.

        UP <-> DOWN
        RIGHT <-> LEFT
        """
        return {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.RIGHT: Direction.LEFT,
            Direction.LEFT: Direction.RIGHT,
        }[direction]
