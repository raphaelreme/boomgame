"""Display obstacles."""

from ..designpattern import event
from ..designpattern import observer
from ..model import events
from ..model import obstacle
from . import view


class ObstacleView(view.View, observer.Observer):
    default_location = None

    def __init__(self, obstacle_: obstacle.Obstacle):
        super().__init__()
        self.obstacle = obstacle_
        self.obstacle.add_observer(self)

        self.load_images()
        self.image = self.images['default']

        self.pos = self.obstacle.pos

    def load_images(self):
        self.images['default'] = view.View.load_image(self.default_location, self.obstacle.size)

    def notify(self, event_: event.Event):
        if isinstance(event_, events.ObstacleBombedEvent):
            self.bombed_animation()

    def bombed_animation(self):  # Could do some sprite animation to destroy a tile/bomb.
        pass


class WoodWallView(ObstacleView):
    default_location = 'wood_wall.png'


class StoneWallView(ObstacleView):
    default_location = 'stone_wall.png'


class BombView(ObstacleView):
    default_location = 'bomb.png'
