"""Provides the Observer class of the design pattern observer/observable."""

from . import event


class Observer:
    def notify(self, event_: event.Event):
        raise NotImplementedError
