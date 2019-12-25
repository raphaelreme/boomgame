"""Handle the player's display"""

from ..designpattern import event
from ..designpattern import observer
from ..model import events
from ..model import player
from . import view


class PlayerView(view.View, observer.Observer):
    default_player_location = 'boom.png'

    def __init__(self, player_: player.Player):
        super().__init__()
        self.player = player_
        self.player.add_observer(self)

        self.load_images()
        self.image = self.images['default']

        self.update_pos()

    def load_images(self):
        self.images['default'] = view.View.load_image(self.default_player_location, self.player.size)

    def update_pos(self):
        self.pos = self.player.pos

    def notify(self, event_: event.Event):
        if isinstance(event_, events.PlayerMovedEvent):
            self.update_pos()  # We have access to the player so no need to use the event.
