"""Link each element of the model to a view.

The view will be able to display the corresponding image on
the window.
"""

from . import obstacle_view
from . import maze_view
from . import player_view
from . import view


__all__ = ['obstacle_view', 'maze_view', 'player_view', 'view']
