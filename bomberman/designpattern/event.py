"""Provides the base Event class, used in our Observer/Observable pattern."""


class MetaEvent(type):
    """Metaclass of all the events.

    Use to auto_increment the event ID.
    """
    id_counter = 0

    def __init__(cls, cls_name, bases, attributes):  # pylint: disable = unused-argument
        cls.ID = MetaEvent.id_counter
        MetaEvent.id_counter += 1


class Event(metaclass=MetaEvent):
    ID: int
