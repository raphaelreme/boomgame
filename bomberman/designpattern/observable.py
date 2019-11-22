"""Provides the Observable class of the design pattern observer/observable."""

from . import observer
from . import event


class Observable:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer_: observer.Observer):
        self.observers.append(observer_)

    def changed(self, event_: event.Event):
        for observer_ in self.observers:
            observer_.notify(event_)
