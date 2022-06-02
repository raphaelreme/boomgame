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


# XXX: Some very ugly stuff with ratio size and position...


def display_with_shadow(
    surface: pygame.surface.Surface,
    image: pygame.surface.Surface,
    position: Tuple[int, int],
    shadow_offset: Tuple[int, int],
) -> None:
    """Blit an image with an underlying shadow.

    Args:
        surface (pygame.surface.Surface): Surface to draw on
        image (pygame.surface.Surface): Image to draw
        position (Tuple[int, int]): Position of the drawing.
            The shadow is displayed 3 pixels right and down.
        shadow_offset (Tuple[int, int]): Offset of the shadow
    """
    # Build the shadow image
    shadow = image.copy()
    shadow.fill((0, 0, 0, 200), special_flags=pygame.BLEND_RGBA_MIN)

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
        self.shadow_offset = inflate_to_reality(PanelView.SHADOW_OFFSET, self.ratio)

        super().__init__(view.load_image("panel.png", inflate_to_reality(self.SIZE, self.ratio)), (0, 0))

        self.font = view.load_font(
            "pf_tempesta_seven_condensed_bold.ttf", inflate_to_reality((PanelView.FONT_SIZE, 1), self.ratio)[1]
        )
        self.positions = {key: inflate_to_reality(pos, self.ratio) for key, pos in self.POSITIONS.items()}

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

        display_with_shadow(surface, time_text, self.positions["time"], self.shadow_offset)

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
        "extra": (2.7, 0.41),
        "bonus": (3.3, 0.45),
        "score_text": (4.0, 0.6),
        "score_value": (4.5, 0.41),
        "game": (1.3, 0.7),
        "over": (1.8, 0.75),
    }

    def __init__(self, player: entity.Player, ratio: float) -> None:
        super().__init__((0, 0), inflate_to_reality(self.SIZE, ratio))

        self.ratio = ratio
        self.shadow_offset = inflate_to_reality(PanelView.SHADOW_OFFSET, self.ratio)

        self.player = player
        self.player.add_observer(self)

        self.font = view.load_font(
            "pf_tempesta_seven_condensed_bold.ttf", inflate_to_reality((PanelView.FONT_SIZE, 1), ratio)[1]
        )
        self.positions = {key: inflate_to_reality(pos, ratio) for key, pos in self.POSITIONS.items()}

        # TODO: Store the size somewhere ?
        self.player_head = view.load_image(
            f"player_head{player.identifier}.png", inflate_to_reality((21 / 32, 1), ratio)
        )
        self.health = HealthView(player, ratio)
        self.health_rect = pygame.rect.Rect(self.positions["health"], self.health.size)

        self.extra = ExtraView(player, ratio)
        self.extra_rect = pygame.rect.Rect(self.positions["extra"], self.extra.size)

        self.bonus = BonusView(player, ratio)
        self.bonus_rect = pygame.rect.Rect(self.positions["bonus"], self.bonus.size)

        self.game_over = self.player.life == 0

    def notify(self, event_: event.Event) -> None:
        if isinstance(event_, events.HitEntityEvent):
            self.health.build_hearts()

        if isinstance(event_, (events.LifeLossEvent, events.PlayerDetailsEvent)):
            self.game_over = self.player.life == 0
            self.health.build_hearts()
            self.extra.build_extra()
            self.bonus.build_bonus()

    def display(self, surface: pygame.surface.Surface) -> None:
        life_text = self.font.render(f" x{self.player.life}", True, (255, 255, 255)).convert_alpha()
        score_text = self.font.render("score", True, (255, 255, 255)).convert_alpha()
        score_value = self.font.render(f"{self.player.score:06d}", True, (255, 255, 255)).convert_alpha()

        display_with_shadow(surface, self.player_head, self.positions["player_head"], self.shadow_offset)
        display_with_shadow(surface, life_text, self.positions["life"], self.shadow_offset)
        display_with_shadow(surface, score_text, self.positions["score_text"], self.shadow_offset)
        display_with_shadow(surface, score_value, self.positions["score_value"], self.shadow_offset)

        if self.game_over:
            game_text = self.font.render("GAME", True, (255, 255, 255)).convert_alpha()
            over_text = self.font.render("OVER", True, (255, 255, 255)).convert_alpha()
            display_with_shadow(surface, game_text, self.positions["game"], self.shadow_offset)
            display_with_shadow(surface, over_text, self.positions["over"], self.shadow_offset)
        else:
            self.health.display(surface.subsurface(self.health_rect))

        self.extra.display(surface.subsurface(self.extra_rect))
        self.bonus.display(surface.subsurface(self.bonus_rect))


class HealthView(view.Sprite):
    """Display the hearts of each player"""

    # Default size in tiles
    SIZE = (1 + PanelView.SHADOW_OFFSET[0], 2 + PanelView.SHADOW_OFFSET[1])

    SPRITE_SIZE = (TILE_SIZE[0] // 2, TILE_SIZE[1] // 2)
    ROWS = 1
    COLUMNS = 3
    FILE_NAME = "heart.png"

    def __init__(self, player: entity.Player, ratio: float) -> None:
        self.SPRITE_SIZE = (  # pylint: disable=invalid-name
            int(self.SPRITE_SIZE[0] * ratio),
            int(self.SPRITE_SIZE[1] * ratio),
        )

        image_total_size = (self.SPRITE_SIZE[0] * self.COLUMNS, self.SPRITE_SIZE[1] * self.ROWS)
        super().__init__(
            view.load_image(self.FILE_NAME, image_total_size),
            (0, 0),
        )

        self.player = player
        self.ratio = ratio
        self.shadow_offset = inflate_to_reality(PanelView.SHADOW_OFFSET, self.ratio)

        # This view does not have the size of the sprite but of several sprites
        self.size = inflate_to_reality(self.SIZE, ratio)
        self.hearts = pygame.surface.Surface(self.size).convert_alpha()
        self.build_hearts()

    def build_hearts(self) -> None:
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
                            self.hearts, heart, (self.SPRITE_SIZE[0] * j, self.SPRITE_SIZE[1] * i), self.shadow_offset
                        )
                        self.select_sprite(0, 0)
                        heart = self.sprite_image.subsurface(self.current_sprite)
                        continue

                    self.select_sprite(0, 0)
                    heart = self.sprite_image.subsurface(self.current_sprite)

                display_with_shadow(
                    self.hearts, heart, (self.SPRITE_SIZE[0] * j, self.SPRITE_SIZE[1] * i), self.shadow_offset
                )

    def display(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.hearts, self.position)


class ExtraView(view.Sprite):
    """Display the extra of each player"""

    # Default size in tiles
    SIZE = (13 / 32 + PanelView.SHADOW_OFFSET[0], 5 * 15 / 32 + PanelView.SHADOW_OFFSET[1])

    SPRITE_SIZE = (int(13 / 32 * TILE_SIZE[0]), int(13 / 32 * TILE_SIZE[1]))
    ROWS = 1
    COLUMNS = 6
    FILE_NAME = "extra_icons.png"

    def __init__(self, player: entity.Player, ratio: float) -> None:
        self.SPRITE_SIZE = (  # pylint: disable=invalid-name
            int(self.SPRITE_SIZE[0] * ratio),
            int(self.SPRITE_SIZE[1] * ratio),
        )

        image_total_size = (self.SPRITE_SIZE[0] * self.COLUMNS, self.SPRITE_SIZE[1] * self.ROWS)
        super().__init__(
            view.load_image(self.FILE_NAME, image_total_size),
            (0, 0),
        )

        self.player = player
        self.ratio = ratio
        self.shadow_offset = inflate_to_reality(PanelView.SHADOW_OFFSET, self.ratio)

        # This view does not have the size of the sprite but of several sprites
        self.size = inflate_to_reality(self.SIZE, ratio)

        self.extra = pygame.surface.Surface(self.size).convert_alpha()
        self.build_extra()

    def build_extra(self) -> None:
        self.extra.fill((0, 0, 0, 0))  # Full transparency

        for i, has_letter in enumerate(self.player.extra):
            if has_letter:
                self.select_sprite(0, i + 1)
            else:
                self.select_sprite(0, 0)

            icon = self.sprite_image.subsurface(self.current_sprite)
            display_with_shadow(self.extra, icon, (i * (self.SPRITE_SIZE[0] + 2), 0), self.shadow_offset)

    def display(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.extra, self.position)


class BonusView(view.Sprite):
    """Display the bonus of each player"""

    # Default size in tiles
    SIZE = (1 + 13 / 32 + PanelView.SHADOW_OFFSET[0], 5 * 14 / 32 + PanelView.SHADOW_OFFSET[1])

    SPRITE_SIZE = (int(13 / 32 * TILE_SIZE[0]), int(13 / 32 * TILE_SIZE[1]))
    ROWS = 2
    COLUMNS = 5
    FILE_NAME = "bonus_icons.png"

    def __init__(self, player: entity.Player, ratio: float) -> None:
        self.SPRITE_SIZE = (  # pylint: disable=invalid-name
            int(self.SPRITE_SIZE[0] * ratio),
            int(self.SPRITE_SIZE[1] * ratio),
        )

        image_total_size = (self.SPRITE_SIZE[0] * self.COLUMNS, self.SPRITE_SIZE[1] * self.ROWS)
        super().__init__(
            view.load_image(self.FILE_NAME, image_total_size),
            (0, 0),
        )

        self.font = view.load_font("pf_tempesta_seven_condensed_bold.ttf", self.SPRITE_SIZE[1] // 2)

        self.player = player
        self.ratio = ratio
        self.shadow_offset = inflate_to_reality(PanelView.SHADOW_OFFSET, self.ratio)

        # This view does not have the size of the sprite but of several sprites
        self.size = inflate_to_reality(self.SIZE, ratio)
        self.bonus = pygame.surface.Surface(self.size).convert_alpha()
        self.build_bonus()

    def build_bonus(self) -> None:
        self.bonus.fill((0, 0, 0, 0))  # Full transparency

        # Bomb capacity
        self.select_sprite(0, 0)
        icon = self.sprite_image.subsurface(self.current_sprite)
        display_with_shadow(self.bonus, icon, (0, 0), self.shadow_offset)

        capacity_text = self.font.render(f" x{self.player.bomb_capacity}", True, (255, 255, 255)).convert_alpha()
        display_with_shadow(self.bonus, capacity_text, (0, self.SPRITE_SIZE[1]), self.shadow_offset)

        # Fast bomb
        self.select_sprite(int(not self.player.fast_bomb), 1)
        icon = self.sprite_image.subsurface(self.current_sprite)
        display_with_shadow(self.bonus, icon, (self.SPRITE_SIZE[0] + 1, 0), self.shadow_offset)

        # Laser
        self.select_sprite(0, 2)
        icon = self.sprite_image.subsurface(self.current_sprite)
        display_with_shadow(self.bonus, icon, (2 * (self.SPRITE_SIZE[0] + 1), 0), self.shadow_offset)

        laser_text = self.font.render(f" x{self.player.bomb_radius}", True, (255, 255, 255)).convert_alpha()
        display_with_shadow(
            self.bonus, laser_text, (2 * (self.SPRITE_SIZE[1] + 1), self.SPRITE_SIZE[1]), self.shadow_offset
        )

        # Shield
        self.select_sprite(int(not self.player.shield.is_active), 3)
        icon = self.sprite_image.subsurface(self.current_sprite)
        display_with_shadow(self.bonus, icon, (3 * (self.SPRITE_SIZE[0] + 1), 0), self.shadow_offset)

        # Fast
        self.select_sprite(int(not self.player.fast.is_active), 4)
        icon = self.sprite_image.subsurface(self.current_sprite)
        display_with_shadow(self.bonus, icon, (4 * (self.SPRITE_SIZE[0] + 1), 0), self.shadow_offset)

    def display(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.bonus, self.position)
