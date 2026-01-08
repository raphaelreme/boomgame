"""Provides the base Event class, used in our Observer/Observable pattern."""


class MetaEvent(type):
    """Metaclass of all the events.

    Use to auto_increment the event ID.
    """

    id_counter = 0

    def __init__(cls, cls_name: str, bases: tuple, attributes: dict) -> None:
        super().__init__(cls_name, bases, attributes)
        cls.ID = MetaEvent.id_counter
        MetaEvent.id_counter += 1


class Event(metaclass=MetaEvent):
    """Event base class.

    Attr:
        ID (int): Unique class identifier defined by the metaclass
        handled (bool): Set to true when the event is handled.
    """

    ID: int

    def __init__(self) -> None:
        self.handled = False
