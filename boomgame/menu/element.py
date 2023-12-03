from __future__ import annotations

import pygame

from ..view import panel_view, view, inflate_to_reality, TILE_SIZE
from . import element_properties, menu


class Element(view.ImageView):
    """A basic element on a page with a shadow"""

    def __init__(self, page: menu.Page, properties: element_properties.ElementProperties) -> None:
        super().__init__(pygame.surface.Surface((0, 0)), inflate_to_reality(properties.pos))
        self.properties = properties
        self.page = page
        self.shadow_offset = inflate_to_reality((self.properties.z, self.properties.z))

    def display(self, surface: pygame.surface.Surface) -> None:
        panel_view.display_with_shadow(surface, self.image, self.top_left_position, self.shadow_offset)

    @property
    def top_left_position(self):
        x, y = self.position
        size = self.image.get_size()  # Size without shadow
        align_y, align_x = self.properties.align.split("-")
        if align_x == "left":
            pass
        elif align_x == "center":
            x -= size[0] // 2
        elif align_x == "right":
            x -= size[0]
        else:
            raise ValueError(f"Unknown value of x-align: {align_x}. Should be in [left, center, right]")
        if align_y == "top":
            pass
        elif align_y == "center":
            y -= size[1] // 2
        elif align_y == "bottom":
            y -= size[1]
        else:
            raise ValueError(f"Unknown value of y-align: {align_y}. Should be in [top, center, bottom]")

        return x, y

    @staticmethod
    def build(element_dict: dict, page: menu.Page) -> Element:
        element_class, property_class = {
            "Text": (TextElement, element_properties.TextProperties),
            "Image": (ImageElement, element_properties.ImageProperties),
            "Button": (ButtonElement, element_properties.ButtonProperties),
        }[element_dict["element"]]

        return element_class(page, property_class.build(page.theme, element_dict))  # type: ignore


class InteractiveElement(Element):
    def __init__(self, page: menu.Page, properties: element_properties.ElementProperties) -> None:
        super().__init__(page, properties)
        self.hovered = False
        self._clicked = False
        self.clicked = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.top_left_position, self.size)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            hovered = self.rect.collidepoint(event.pos)
            if hovered and not self.hovered:
                self.hover(True)
            elif self.hovered and not hovered:
                self.hover(False)

        if event.type == pygame.MOUSEBUTTONDOWN:
            hovered = self.rect.collidepoint(event.pos)
            if hovered:
                self._clicked = True

        if event.type == pygame.MOUSEBUTTONUP:
            hovered = self.rect.collidepoint(event.pos)
            self._clicked = False
            if hovered:  # Trigger a real click only if still hovered
                self.click()

    def hover(self, hovered: bool):
        """Called when the state over changes"""
        self.hovered = hovered

    def update(self, delay: float):
        """Update the optional animation of the object"""

    def click(self):
        """Handle a click"""
        self.clicked = True


class ImageElement(Element):
    """Display an image in the page"""

    def __init__(self, page: menu.Page, properties: element_properties.ImageProperties) -> None:
        super().__init__(page, properties)
        self.properties: element_properties.ImageProperties
        self.image = view.load_image(
            properties.image_name, None if properties.image_size is None else inflate_to_reality(properties.image_size)
        )
        w, h = self.image.get_size()
        self.size = (w + self.shadow_offset[0], h + self.shadow_offset[1])


class TextElement(Element):
    """Display text in the page"""

    def __init__(self, page: menu.Page, properties: element_properties.TextProperties) -> None:
        super().__init__(page, properties)
        self.properties: element_properties.TextProperties
        self.font = view.load_font(self.properties.font_name, int(self.properties.font_size * TILE_SIZE[0]))
        self.set_text(self.properties.text)

    def set_text(self, text: str) -> None:
        """Set the text of the Element

        Solves traductions and variables
        """
        if text[0] == "@":
            text = self.page.menu.traductions.get(text[1:], text[1:])
        # TODO: Handle variables
        self.properties.text = text
        self.image = self.font.render(text, True, self.properties.text_color).convert_alpha()
        w, h = self.image.get_size()
        self.size = (w + self.shadow_offset[0], h + self.shadow_offset[1])


class ButtonElement(TextElement, InteractiveElement):
    """Display an interactable button"""

    COLOR_SWITCH_DELAY = 0.1

    def __init__(self, page: menu.Page, properties: element_properties.ButtonProperties) -> None:
        super().__init__(page, properties)
        self.properties: element_properties.ButtonProperties
        self.clicked_delay = self.properties.clicked_delay

    def hover(self, hovered: bool):
        super().hover(hovered)
        text_color = self.properties.text_color_hovered if hovered else self.properties.text_color
        self.image = self.font.render(self.properties.text, True, text_color).convert_alpha()

    def update(self, delay: float):
        if self.clicked:
            self.clicked_delay -= delay
            use_hovered = int(self.clicked_delay / self.COLOR_SWITCH_DELAY) % 2
            text_color = self.properties.text_color_hovered if use_hovered else self.properties.text_color
            self.image = self.font.render(self.properties.text, True, text_color).convert_alpha()
            if self.clicked_delay < 0:
                self.clicked = False
                self.clicked_delay = self.properties.clicked_delay
                action = self.page.actions.get(self.properties.action)
                if action:
                    action(self)
                else:
                    print(f"Warning: {self.properties.action} not found")
