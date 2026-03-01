import pygame
import sys
from player import Player

pygame.init()

WIDTH, HEIGHT = 1080, 720
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")
clock = pygame.time.Clock()

player = Player(
    position=pygame.Vector2(WIDTH // 2, HEIGHT // 2),
    direction=pygame.Vector2(0, -1)
)

running = True
while running:
    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        player.handle_movement_mode(event)   # ✅ pass event in, not get_pressed

    player.update(dt)

    screen.fill((20, 20, 20))
    player.draw(screen)                      # ✅ player draws itself
    pygame.display.flip()

pygame.quit()
sys.exit()