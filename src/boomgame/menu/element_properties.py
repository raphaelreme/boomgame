from __future__ import annotations

import dataclasses
from typing import Optional, Tuple

from . import theme


@dataclasses.dataclass
class ElementProperties:
    """Properties for displayed element in a page

    Elements are defined in the page json as:
    {
        "klass": str, // Name of the element
        "style": str, // Optional name of a style (in the theme)
        "property": value,  // Particular properties of this element (pos, z, text, etc..)
        ...
    }

    Properties are read from element data. If not provied, the default value for the element style or class is used

    Attributes:
        pos (Tuple[float, float]): position of the element in tile unit
        z (float): Offset of the shadow (depth) in tile unit
    """

    pos: Tuple[float, float]
    z: float
    align: str

    @classmethod
    def build(cls, page_theme: theme.Theme, element_dict: dict) -> ElementProperties:
        klass = element_dict.get("style", element_dict["element"])

        kwargs = {}
        for property_, field in cls.__dataclass_fields__.items():  # pylint: disable=no-member
            if property_ in element_dict:
                kwargs[property_] = element_dict[property_]
            else:
                default = (
                    None
                    if isinstance(field.default, dataclasses._MISSING_TYPE)  # pylint: disable=protected-access
                    else field.default
                )
                kwargs[property_] = page_theme.get(klass, property_, default)

        return cls(**kwargs)


@dataclasses.dataclass
class TextProperties(ElementProperties):
    """Text properties

    Attributes:
        text (str): Text to display
        font_name (str): Name of the font
        font_size (float): Size of the font in tile unit
        text_color (str): Text color

    """

    text: str
    font_name: str
    font_size: float
    text_color: str


@dataclasses.dataclass
class ImageProperties(ElementProperties):
    """Image properties

    Attributes:
        image_name (str): Image to display
        image_size (Optional[Tuple[float, float]]): Optional resize

    """

    image_name: str
    image_size: Optional[Tuple[float, float]]


@dataclasses.dataclass
class ButtonProperties(TextProperties):
    """Button properties


    Attributes:
        text_color_hovered (str): Text color when hovered
        clicked_delay (float): Delay of the clicked animation
        action (str): Name of the action to perform

    """

    text_color_hovered: str
    clicked_delay: float
    action: str
