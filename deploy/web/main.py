import asyncio

import pygame

from boomgame.main import BoomGame


if __name__ == "__main__":
    pygame.init()
    game = BoomGame()
    asyncio.run(game.async_main())
