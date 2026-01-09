"""Provides the Observable class of the design pattern observer/observable."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from boomgame.designpattern import event, observer


class Observable:
    """Observable objects can be observed.

    Observers can be added and each observer is notify with an event when the observable is changed.
    """

    def __init__(self) -> None:
        self.observers: set[observer.Observer] = set()

    def add_observer(self, observer_: observer.Observer) -> None:
        """Register a new observer."""
        self.observers.add(observer_)

    def remove_observer(self, observer_: observer.Observer) -> None:
        """Remove an observer."""
        self.observers.remove(observer_)

    def reset(self) -> None:
        """Reset the observer set."""
        self.observers = set()

    def changed(self, event_: event.Event) -> None:
        """Notify all observers of a change."""
        for observer_ in self.observers:
            observer_.notify(event_)

    # Sanity check ? if not event_.handled:  print(event_)
