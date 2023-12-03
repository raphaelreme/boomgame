"""All the events used by the model based on the observer/observable event."""

from __future__ import annotations

from . import entity
from ..designpattern.event import Event


class MazeStartEvent(Event):
    """At each new maze"""


class MazeEndEvent(Event):
    """When a maze is released"""


class GameEndEvent(Event):
    """When the game is done"""


class StartScreenEvent(Event):
    """At the beginning of each start screen"""


class ForwardStartScreenEvent(Event):
    "Could be used to update the start scren"


class BonusScreenEvent(Event):
    """At the begining of each bonus screen"""


class ForwardBonusScreenEvent(Event):
    """Could be used to update the bonus screen (animation ?)"""


class MazeFailedEvent(Event):
    """When the maze is detected as failed"""


class MazeSolvedEvent(Event):
    """When the maze is detected as solved"""


class MazeEndingEvent(Event):
    """Each update of the maze, when it is ending"""


class ExtraGameEvent(Event):
    """At the beginning of the extra game"""


class HurryUpEvent(Event):
    """30s before time's up"""


class ForwardTimeEvent(Event):
    """Notify the view of a progress in time"""

    def __init__(self, delay: float) -> None:
        super().__init__()
        self.delay = delay


class EntityEvent(Event):
    def __init__(self, entity_: entity.Entity):
        super().__init__()
        self.entity = entity_


class NewEntityEvent(EntityEvent):
    pass


class MovedEntityEvent(EntityEvent):
    pass


class HitEntityEvent(EntityEvent):
    pass


class RemovingEntityEvent(EntityEvent):
    """Each time the entity is removing"""


class RemovedEntityEvent(EntityEvent):
    pass


class LifeLossEvent(EntityEvent):
    """When a player loses a life (after its removing delay)"""


class PlayerDetailsEvent(EntityEvent):
    """When a player details has to be updated"""


class NoiseEvent(EntityEvent):
    """At each entity noise (Not all sounds)"""


class StartRemovingEvent(EntityEvent):
    """when the entity reaches removing state"""


class ScoreEvent(EntityEvent):
    """When score is earned

    Will trigger a score slider (Notify by the entity as a change of the maze)
    """


class ExtraLifeEvent(EntityEvent):
    """When a player completed EXTRA letters

    Will trigger a slider (Notify by the player as a change of the maze)
    """

    def __init__(self, entity_: entity.Entity):
        super().__init__(entity_)
        self.entity: entity.Player
