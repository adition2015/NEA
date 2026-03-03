import pygame
from player import Player

LVL_WIDTH, LVL_HEIGHT = 1000, 640

class Level:
    def __init__(self, ID):
        self.ID = ID
        self.player = Player(
                             position=pygame.Vector2(LVL_WIDTH // 2, LVL_HEIGHT // 2),
                             direction=pygame.Vector2(0, -1)
                             )
        self.surface = pygame.Surface((LVL_WIDTH, LVL_HEIGHT), pygame.SRCALPHA)
        self.walls = [] # all walls have a rect attribute - this will be called for collisions
    
    def update(self, dt):
        self.player.update(dt)

    def draw(self, screen):
        #clear surface every frame:
        self.surface.fill((0, 0, 0))

        # draw player and other dynamic level objects
        self.player.draw(self.surface)

        # draw static level objects
        for i in self.walls:
            i.draw(self.surface)
        screen.blit(self.surface, (40, 40))
        
    def handle_input(self, event):
        self.player.handle_input(event)



class Wall:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = self.build_wall()
        
    def build_wall(self):
        return pygame.rect.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), self.rect)

# level dictionary: type of obj: Wall, for every attribute of wall, contains data.
# should be able to create a level object from a dictionary.




