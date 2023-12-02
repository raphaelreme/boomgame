from __future__ import annotations

import enum
import json
from typing import Callable, Dict, List

import pygame.surface

from .. import resources
from ..view import view, inflate_to_reality
from . import actions, element, theme

# TODO: Other pages + settings


class PageEnum(enum.Enum):
    MAIN = "main"
    OPEN_GAME = "open_game"
    PREFERENCES = "preferences"
    SCORES = "scores"
    INFOS = "infos_{i}"
    PAUSE = "pause"
    WIN = "win"


class Menu(view.View):
    """The Menu is a view that wraps a displayed Page with interactive elements"""

    SIZE = (15, 20)

    actions: Dict[PageEnum, Dict[str, Callable[[element.Element], None]]] = {
        PageEnum.MAIN: {
            "new_game": actions.new_game,
            "open_game": actions.open_game,
            "quit": actions.quit_game,
        },
    }

    def __init__(self, start_callback, quit_callback) -> None:
        super().__init__((0, 0), inflate_to_reality(self.SIZE))
        self.lang = "en"
        resource = resources.joinpath("menu").joinpath("lang").joinpath(f"{self.lang}.json")
        self.traductions: Dict[str, str] = json.loads(resource.read_text())
        self.page = Page(PageEnum.MAIN, PageEnum.MAIN, self)

        self.start_callback = start_callback
        self.quit_callback = quit_callback

    def update(self, delay: float):
        self.page.update(delay)

    def handle_event(self, event):
        self.page.handle_event(event)

    def display(self, surface: pygame.surface.Surface) -> None:
        self.page.display(surface)


class Page(view.View):
    """A page of the menu"""

    def __init__(self, page: PageEnum, previous: PageEnum, menu: Menu) -> None:
        super().__init__((0, 0), menu.size)
        self.menu = menu
        self.page = page
        self.previous = previous
        self.actions = self.menu.actions[self.page]

        resource = resources.joinpath("menu").joinpath(f"{page.value}.json")
        page_config = json.loads(resource.read_text())
        self.theme = theme.Theme(page_config["theme"])

        self.interactive_elements: List[element.InteractiveElement] = []
        self.static_elements: List[element.Element] = []
        # Build objects
        for element_dict in page_config["elements"]:
            element_ = element.Element.build(element_dict, self)
            if isinstance(element_, element.InteractiveElement):
                self.interactive_elements.append(element_)
            else:
                self.static_elements.append(element_)

        ## Build the background once for all
        self.background = pygame.surface.Surface(self.size).convert_alpha()
        self._build_background()

    def _build_background(self) -> None:
        """Build the background surface"""
        background_tile = view.load_image(self.theme.background, inflate_to_reality(self.theme.background_size))

        for i in range(0, self.menu.SIZE[0], int(self.theme.background_size[0])):
            for j in range(0, self.menu.SIZE[1], int(self.theme.background_size[1])):
                self.background.blit(background_tile, inflate_to_reality((i, j)))

        for element_ in self.static_elements:
            element_.display(self.background)

    def display(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.background, self.position)

        for element_ in self.interactive_elements:
            element_.display(surface)

    def handle_event(self, event):
        for interactive_element in self.interactive_elements:
            interactive_element.handle_event(event)

    def update(self, delay: float):
        for interactive_element in self.interactive_elements:
            interactive_element.update(delay)
