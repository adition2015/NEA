import pygame, json
from player import Player
from settings import *
from utils import draw_debug

def scale_rect(x, y, w, h):
    return (
        int(x * scale_x),
        int(y * scale_y),
        int(w * scale_x),
        int(h * scale_y)
    )

class Level:
    def __init__(self, ID, data):
        self.ID = ID
        self.player = Player(
                             position=pygame.Vector2(player_pos),
                             direction=pygame.Vector2(0, -1)
                             )
        self.surface = pygame.Surface(level_res, pygame.SRCALPHA)
        self.walls = [] # all walls have a rect attribute - this will be called for collisions
        self.doors = []# all doors have a rect attribute - if closed, will be called for collisions
        self._load_level(data)


    
    def update(self, dt):
        self.player.update(dt)
        self._resolve_collisions()

    def draw(self, screen, fps):
        #clear surface every frame:
        self.surface.fill((20, 20, 20))

        # draw player and other dynamic level objects
        self.player.draw(self.surface)

        # draw static level objects
        for i in self.walls:
            i.draw(self.surface)
        screen.blit(self.surface, level_offset)

        # debug:
        draw_debug(screen, {
            "pos":   self.player.position,
            "movement_mode": self.player.movement_mode,
            "fps": round(fps)
        })

    def _load_level(self, data: dict):
        for (x, y, w, h) in data.get("walls", []):
            self.walls.append(Wall(*scale_rect(x, y, w, h)))

        for (x, y, o) in data.get("doors", []):
            sx, sy = int(x * scale_x), int(y * scale_y)
            self.doors.append(Door(sx, sy, o))
    

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

class Door:
    def __init__(self, x, y, o: int): # o is orientation: 0 - vertical, 1 - horizontal
        self.is_open = False

        self.width = 5 if o == 0 else 50
        self.height = 50 if o == 0 else 5
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def open(self, collision_rects):
        if not self.is_open:
            self.is_open = True
            if self.rect in collision_rects:
                collision_rects.remove(self.rect)
    
    def close(self, collidable_rects):
        if self.is_open:
            self.is_open = False
            if self.rect not in collidable_rects:
                collidable_rects.append(self.rect)

    def interact(self, collidable_rects):
        if self.is_open:
            self.close(collidable_rects)
        else:
            self.open(collidable_rects)

    def draw(self, surface):
        pygame.draw.rect(surface, (149, 69, 53), self.rect) # change colour on open
    
    


# level dictionary: type of obj: Wall, for every attribute of wall, contains data.
# should be able to create a level object from a dictionary.





