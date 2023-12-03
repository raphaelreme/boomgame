"""Provides the Observable class of the design pattern observer/observable."""

from typing import Set

from . import observer
from . import event


class Observable:
    """Observable objects can be observed.

    Observers can be added and each observer is notify with an event when the observable is changed.
    """

    def __init__(self) -> None:
        self.observers: Set[observer.Observer] = set()

    def add_observer(self, observer_: observer.Observer) -> None:
        self.observers.add(observer_)

    def remove_observer(self, observer_: observer.Observer) -> None:
        self.observers.remove(observer_)

    def reset(self) -> None:
        self.observers = set()

    def changed(self, event_: event.Event) -> None:
        for observer_ in self.observers:
            observer_.notify(event_)

        # Sanity check
        # if not event_.handled:
        #     print(event_)
