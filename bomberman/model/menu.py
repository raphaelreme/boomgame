import enum

from ..designpattern import observable


class Menu(observable.Observable):
    """Menu class"""

    class Page(enum.Enum):
        MAIN = "main"
        OPEN_GAME = "open_game"
        PREFERENCES = "preferences"
        SCORES = "scores"
        INFOS = "infos_{i}"

    def __init__(self) -> None:
        super().__init__()
        self.current_page = Menu.Page.MAIN
