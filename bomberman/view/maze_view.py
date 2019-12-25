"""Handle the Maze to display it on the screen."""

import pygame

from ..designpattern import event
from ..designpattern import observer
from ..model import events
from ..model import obstacle
from ..model import maze
from . import obstacle_view
from . import player_view
from . import view


class MazeView(view.View, observer.Observer):
    background_location = 'background.png'

    def __init__(self, maze_: maze.Maze):
        super().__init__()
        self.maze = maze_
        self.maze.add_observer(self)

        self.bomb_views = []
        self.obstacle_views = []
        self.player_views = []

        for obstacle_ in self.maze.obstacles:
            self.create_obstacle_view(obstacle_)
        for bomb in self.maze.bombs:
            self.create_obstacle_view(bomb)
        for player_ in self.maze.players:
            self.player_views.append(player_view.PlayerView(player_))

        box_size = obstacle.Obstacle.size
        background_box = view.View.load_image(self.background_location, box_size)
        self.image = pygame.surface.Surface(self.maze.size)  # pylint: disable = c-extension-no-member

        for i in range(self.maze.height):
            for j in range(self.maze.width):
                self.image.blit(background_box, (j * box_size[0], i * box_size[1]))

    def display(self):
        super().display()

        for obstacle_ in self.obstacle_views:
            obstacle_.display()
        for bomb_ in self.bomb_views:
            bomb_.display()
        for player in self.player_views:
            player.display()

    def notify(self, event_: event.Event):
        if isinstance(event_, events.NewObstacleEvent):
            self.create_obstacle_view(event_.obstacle)

        elif isinstance(event_, events.NewPlayerEvent):
            self.player_views.append(player_view.PlayerView(event_.player))

        elif isinstance(event_, events.DeleteObstacleEvent):
            obstacle_ = event_.obstacle
            if isinstance(obstacle_, obstacle.Bomb):
                for bomb_view_ in self.bomb_views:
                    if bomb_view_.obstacle == obstacle_:
                        self.bomb_views.remove(bomb_view_)
                        break
            else:
                for obstacle_view_ in self.obstacle_views:
                    if obstacle_view_.obstacle == obstacle_:
                        self.obstacle_views.remove(obstacle_view_)
                        break

        elif isinstance(event_, events.DeletePlayerEvent):
            for player_view_ in self.player_views:
                if player_view_.player == event_.player:
                    self.player_views.remove(player_view_)
                    break

    def create_obstacle_view(self, obstacle_: obstacle.Obstacle):
        if isinstance(obstacle_, obstacle.WoodWall):
            self.obstacle_views.append(obstacle_view.WoodWallView(obstacle_))
        elif isinstance(obstacle_, obstacle.StoneWall):
            self.obstacle_views.append(obstacle_view.StoneWallView(obstacle_))
        elif isinstance(obstacle_, obstacle.Bomb):
            self.bomb_views.append(obstacle_view.BombView(obstacle_))
