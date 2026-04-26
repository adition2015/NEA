import pygame
import sys
from game_state_manager import GameStateManager

game = GameStateManager()

if __name__ == "__main__":
    game.run()
    pygame.quit()
    sys.exit()