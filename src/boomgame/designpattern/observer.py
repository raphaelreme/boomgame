"""Provides the Observer class of the design pattern observer/observable."""

from . import event


class Observer:
    """An observer can be registered in an observable object and will be notify when needed"""

    def notify(self, event_: event.Event) -> None:
        raise NotImplementedError
