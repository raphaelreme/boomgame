"""Display the left panel."""

from typing import Dict, Tuple

import pygame
import pygame.font
import pygame.rect
import pygame.surface

from ..designpattern import event
from ..designpattern import observer
from ..model import events
from ..model import game
from ..model import entity
from . import TILE_SIZE, inflate_to_reality
from . import view


def display_with_shadow(
    surface: pygame.surface.Surface, image: pygame.surface.Surface, position: Tuple[int, int], ratio: float
) -> None:
    """Blit an image with an underlying shadow.

    Args:
        surface (pygame.surface.Surface): Surface to draw on
        image (pygame.surface.Surface): Image to draw
        position (Tuple[int, int]): Position of the drawing.
            The shadow is displayed 3 pixels right and di.
    """
    # Build the shadow image
    shadow = image.copy()
    shadow.fill((0, 0, 0, 200), special_flags=pygame.BLEND_RGBA_MIN)

    shadow_offset = inflate_to_reality(PanelView.SHADOW_OFFSET, ratio)

    surface.blit(shadow, (position[0] + shadow_offset[0], position[1] + shadow_offset[1]))
    surface.blit(image, position)


class PanelView(view.ImageView):
    """Panel of the game

    Display the remaining time, the life of the players, the scores and the bonuses.
    """

    SIZE = (15, 3)  # Default size in tiles

    # Default positions of components in tiles
    POSITIONS: Dict[str, Tuple[float, float]] = {
        "player_details_1": (1.5, 0),
        "player_details_2": (8, 0),
        "time": (7, 0.7),
    }

    FONT_SIZE = 0.5  # Default font size in tiles
    SHADOW_OFFSET = (0.07, 0.07)  # Offset of the shadow in tiles

    def __init__(self, model: game.GameModel) -> None:
        self.model = model
        self.ratio = (self.model.maze.size[0] + 2) / self.SIZE[0]

        super().__init__(view.load_image("panel.png", inflate_to_reality(self.SIZE, self.ratio)), (0, 0))

        self.font = view.load_font(
            "pf_tempesta_seven_condensed_bold.ttf", inflate_to_reality((PanelView.FONT_SIZE, 1), self.ratio)[1]
        )
        self.positions = {key: inflate_to_reality(self.POSITIONS[key], self.ratio) for key in self.POSITIONS}

        self.player_details = {i: PlayerDetails(self.model.players[i], self.ratio) for i in self.model.players}

        self.rect_player_details = {
            i: pygame.rect.Rect(self.positions[f"player_details_{i}"], self.player_details[i].size)
            for i in self.player_details
        }

    def display(self, surface: pygame.surface.Surface) -> None:
        super().display(surface)

        time = max(int(self.model.time), 0)

        minutes = time // 60
        seconds = time % 60
        color = (255, 0, 0) if time <= 30 else (255, 255, 255)

        time_text = self.font.render(f"{minutes:02d}:{seconds:02d}", True, color).convert_alpha()

        display_with_shadow(surface, time_text, self.positions["time"], self.ratio)
        for i in self.player_details:
            self.player_details[i].display(surface.subsurface(self.rect_player_details[i]))


class PlayerDetails(view.View, observer.Observer):
    """Display life, scores and bonuses of players"""

    SIZE = (5.5, 3)  # Default size in tiles

    # Default positions of components in tiles
    POSITIONS = {
        "player_head": (0.5, 0.5),
        "life": (0.4, 1.5),
        "health": (1.5, 0.5),
        "score": (4.5, 0.41),
        "game": (1.3, 0.7),
        "over": (1.8, 0.75),
    }

    def __init__(self, player: entity.Player, ratio: float) -> None:
        super().__init__((0, 0), inflate_to_reality(self.SIZE, ratio))

        self.ratio = ratio

        self.player = player
        self.player.add_observer(self)

        self.font = view.load_font(
            "pf_tempesta_seven_condensed_bold.ttf", inflate_to_reality((PanelView.FONT_SIZE, 1), ratio)[1]
        )
        self.positions = {key: inflate_to_reality(self.POSITIONS[key], ratio) for key in self.POSITIONS}

        # TODO: Store the size somewhere ?
        self.player_head = view.load_image(
            f"player_head{player.identifier}.png", inflate_to_reality((21 / 32, 1), ratio)
        )
        self.health = HealthView(player, ratio)
        self.health_rect = pygame.rect.Rect(self.positions["health"], self.health.size)

        self.game_over = self.player.life == 0

    def notify(self, event_: event.Event) -> None:
        if isinstance(event_, events.HitEntityEvent):
            self.health._build_hearts()

        if isinstance(event_, events.LifeLossEvent):
            self.game_over = self.player.life == 0
            self.health._build_hearts()

    def display(self, surface: pygame.surface.Surface) -> None:
        life_text = self.font.render(f" x{self.player.life}", True, (255, 255, 255)).convert_alpha()
        score_text = self.font.render(f"{self.player.score:06d}", True, (255, 255, 255)).convert_alpha()

        display_with_shadow(surface, self.player_head, self.positions["player_head"], self.ratio)
        display_with_shadow(surface, life_text, self.positions["life"], self.ratio)
        display_with_shadow(surface, score_text, self.positions["score"], self.ratio)

        if self.game_over:
            game_text = self.font.render("GAME", True, (255, 255, 255)).convert_alpha()
            over_text = self.font.render("OVER", True, (255, 255, 255)).convert_alpha()
            display_with_shadow(surface, game_text, self.positions["game"], self.ratio)
            display_with_shadow(surface, over_text, self.positions["over"], self.ratio)
        else:
            self.health.display(surface.subsurface(self.health_rect))


class HealthView(view.Sprite):
    """Display the hearts of each player"""

    # Default size in tiles
    SIZE = (1 + PanelView.SHADOW_OFFSET[0], 2 + PanelView.SHADOW_OFFSET[1])

    SPRITE_SIZE = (TILE_SIZE[0] // 2, TILE_SIZE[1] // 2)
    ROWS = 1
    COLUMNS = 3
    FILE_NAME = "heart.png"

    def __init__(self, player: entity.Player, ratio: float) -> None:
        self.SPRITE_SIZE = (int(self.SPRITE_SIZE[0] * ratio), int(self.SPRITE_SIZE[1] * ratio))

        image_total_size = (self.SPRITE_SIZE[0] * self.COLUMNS, self.SPRITE_SIZE[1] * self.ROWS)
        super().__init__(
            view.load_image(self.FILE_NAME, image_total_size),
            (0, 0),
        )

        self.player = player
        self.ratio = ratio

        # This view does not have the size of the sprite but of several sprites
        self.size = inflate_to_reality(self.SIZE, ratio)
        self.hearts = pygame.surface.Surface(self.size).convert_alpha()
        self._build_hearts()

    def _build_hearts(self) -> None:
        self.hearts.fill((0, 0, 0, 0))  # Full transparency

        # Select the heart given the health
        self.select_sprite(0, 2)
        heart = self.sprite_image.subsurface(self.current_sprite)

        for i in range(2):
            for j in range(4):
                if 4 * i + j == self.player.health // 2:
                    if self.player.health % 2:
                        self.select_sprite(0, 1)
                        heart = self.sprite_image.subsurface(self.current_sprite)
                        display_with_shadow(
                            self.hearts, heart, (self.SPRITE_SIZE[0] * j, self.SPRITE_SIZE[1] * i), self.ratio
                        )
                        self.select_sprite(0, 0)
                        heart = self.sprite_image.subsurface(self.current_sprite)
                        continue

                    self.select_sprite(0, 0)
                    heart = self.sprite_image.subsurface(self.current_sprite)

                display_with_shadow(self.hearts, heart, (self.SPRITE_SIZE[0] * j, self.SPRITE_SIZE[1] * i), self.ratio)

    def display(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.hearts, self.position)
