import pygame, json
from player import Player
from settings import *
from utils import draw_debug
from enemy import Enemy

# Links:
"https://www.youtube.com/watch?v=UT_tKPLejyU" # pygame layers for drawing on screen

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
        self.enemies = []
        self._load_level(data)
        

        # -- initialise collision rects -- 
        self.collision_rects = [wall.rect for wall in self.walls]
        self.interactables = [door for door in self.doors]
        # initialises door rects
        for i in self.doors:
            i.interact(self.collision_rects)


    def update(self, dt):
        self.player.update(dt)
        for enemy in self.enemies:
            enemy.update(dt, self.player.position)   # chase the player
        self._resolve_collisions()
        self.handle_interaction()

    def draw(self, screen, fps):
        #clear surface every frame:
        self.surface.fill((20, 20, 20))
        self.graph.draw_debug(self.surface)
        # draw player and other dynamic level objects
       
        # -- doors --
        for i in self.doors:
            i.draw(self.surface)

        # -- player --
        self.player.draw(self.surface)

        for enemy in self.enemies:
            enemy.draw(self.surface)

        # draw static level objects
        for i in self.walls:
            i.draw(self.surface)
        

        # debug:
        draw_debug(screen, {
            "pos":   self.player.position,
            "movement_mode": self.player.movement_mode,
            "fps": round(fps)
        })

        # self.draw_grid(50)

        # nav polygon

        screen.blit(self.surface, level_offset)

    def _load_level(self, data: dict):
        for (x, y, w, h) in data.get("walls", []):
            self.walls.append(Wall(*scale_rect(x, y, w, h)))

        for (x, y, o) in data.get("doors", []):
            sx, sy = int(x * scale_x), int(y * scale_y)
            self.doors.append(Door(sx, sy, o))
            
    
    def check_interaction(self):
        if self.player.interact_signal == True:
            # distance check:
            # if any interactable within range, e.g. doors, hiding spots, then interact with the closest one
            target_candidates = {}
            for i in self.interactables:
                distance_vec = self.player.position - i.rect.center # distance_vec will be type pygame.Vector2
                if distance_vec.magnitude() <= 50:
                    target_candidates[i] = distance_vec.magnitude()
            if len(target_candidates) > 0:
                key = min(target_candidates, key = target_candidates.get) # returns the interactable object with shortest dist. to player
                self.player.interact_signal = False
                return key
        

    def handle_interaction(self):
        interactable = self.check_interaction()
        if interactable:
            interactable.interact(self.collision_rects)

    def handle_input(self, event):
        self.player.handle_input(event)

    def _resolve_collisions(self):
        player_rect = self.player.get_collision_rect()

        for rect in self.collision_rects:
            if player_rect.colliderect(rect):
                offset = self._calculate_pushout(player_rect, rect)
                self.player.resolve_collision(offset)
        
        for enemy in self.enemies:
            enemy_rect = enemy.get_collision_rect()
            for wall in self.walls:
                if enemy_rect.colliderect(wall.rect):
                    offset = self._calculate_pushout(enemy_rect, wall.rect)
                    enemy.resolve_collision(offset)
        
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
    
    def draw_grid(self, cell_size):
        cols, rows = level_res[0] // cell_size, level_res[1] // cell_size
        for i in range(round(cols)):
            for j in range(round(rows)):
                pygame.draw.line(self.surface, (0, 0, 255), (0, cell_size*j), (level_res[0], cell_size*j))
                pygame.draw.line(self.surface, (0, 0, 255), (cell_size*i, 0), (cell_size*i, level_res[1]))
    

# fix nav polygon so that it takes points in order that are connected then form a polygon

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
        self.is_open = True
        self.width = 5 if o == 0 else 50
        self.height = 50 if o == 0 else 5
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def open(self, collision_rects):
        if not self.is_open:
            self.is_open = True
            try:
                collision_rects.remove(self.rect)
            except ValueError:
                print("Door not added to collision_rects")
            return collision_rects
             
    
    def close(self, collision_rects):
        if self.is_open:
            self.is_open = False
            collision_rects.append(self.rect)
            return collision_rects

    def interact(self, collision_rects):
        if self.is_open:
            self.close(collision_rects)
        else:
            self.open(collision_rects)

    def draw(self, surface):
        if self.is_open:
            colour = (113, 93, 76)
        else:
            colour = (75, 57, 41)
        pygame.draw.rect(surface, colour, self.rect) # change colour on open
    
# creating a level polygon
# we can consider all corners of each rect, then consider a polygon of those rects. The border rects are uniform for all levels, so we can start with points (5, 5), (5, 715), (1075, 5), (1075, 715) in our polygon points. Consider all corners of rects within this polygon and add it to the points.


# level dictionary: type of obj: Wall, for every attribute of wall, contains data.
# should be able to create a level object from a dictionary.





