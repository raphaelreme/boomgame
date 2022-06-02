"""Link each element of the model to a view.

The view will be able to display the corresponding image on
the window.
"""

from typing import Tuple


TILE_SIZE = (32, 32)


def inflate_to_reality(base: Tuple[float, float], ratio: float = 1) -> Tuple[int, int]:
    """Inflate size/position to the real world.

    Args:
        base (Tuple[float, float]): Tuple representing a size or a position in the model world.
            Where tile is the unit. And the axis are i and j.
        ratio (float): Optional ratio when some components does not share the same TILE SIZE as others

    Returns:
        x (int), y (int): Inflated tuple in the real world. (In pixels)
    """
    return (int(base[1] * TILE_SIZE[0] * ratio), int(base[0] * TILE_SIZE[1] * ratio))
