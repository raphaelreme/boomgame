from __future__ import annotations

import json
from typing import Tuple

from .. import resources


class Theme:  # Ugly
    """Load a theme

    A theme is simply a background sprite (name and size) with default properties for elements or class

    Format:
    {
        "background": str,
        "background_size": [float, float],
        "__default": {
            "prop": value
        },
        "<class>": {
            "prop": value
        }
    }
    """

    DEFAULT = "__default"

    def __init__(self, name: str) -> None:
        resource = resources.joinpath("theme").joinpath(f"{name}.json")
        self.data: dict = json.loads(resource.read_text())
        self.background: str = self.data["background"]
        self.background_size: Tuple[float, float] = self.data["background_size"]

    def get(self, klass: str, property_: str, default=None):
        if klass in self.data:
            if property_ in self.data[klass]:
                return self.data[klass][property_]
        if self.DEFAULT in self.data:
            if property_ in self.data[self.DEFAULT]:
                return self.data[self.DEFAULT][property_]

        if default is None:
            raise KeyError(f"Unable to find property {property_} for class {klass}")
        return default
