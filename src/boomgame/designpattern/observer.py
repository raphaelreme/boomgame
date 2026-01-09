"""Provides the Observer class of the design pattern observer/observable."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from boomgame.designpattern import event


class Observer:
    """An observer can be registered in an observable object and will be notify when needed."""

    def notify(self, event_: event.Event) -> None:
        """Handle event on the observable."""
        raise NotImplementedError
