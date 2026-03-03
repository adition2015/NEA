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
        self._resolve_collisions()

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

    def _resolve_collisions(self):
        player_rect = self.player.get_collision_rect()

        for wall in self.walls:
            if player_rect.colliderect(wall.rect):
                offset = self._calculate_pushout(player_rect, wall.rect)
                self.player.resolve_collision(offset)
        
    def _calculate_pushout(self, player_rect: pygame.Rect, wall_rect: pygame.Rect):
        overlap_left  = wall_rect.right  - player_rect.left
        overlap_right = player_rect.right - wall_rect.left
        overlap_top   = wall_rect.bottom - player_rect.top
        overlap_bottom= player_rect.bottom - wall_rect.top

        # Pick the smallest overlap — that's the axis to resolve on
        min_x = overlap_left  if overlap_left < overlap_right  else -overlap_right
        min_y = overlap_top   if overlap_top  < overlap_bottom else -overlap_bottom

        if abs(min_x) < abs(min_y):
            return pygame.Vector2(min_x, 0)
        else:
            return pygame.Vector2(0, min_y)


                


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




