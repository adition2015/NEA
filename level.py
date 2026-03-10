import pygame, json
from player import Player
from enemy import Enemy
from settings import *
from utils import draw_debug

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
        self._load_level(data)
        
        

        # build lists of collision rectangles.  ``collision_rects`` is the
        # authoritative set used for physics and door interactions; it will be
        # mutated whenever a door opens or closes.  the navigation mesh is
        # constructed from *walls alone* and is never updated because doors are
        # effectively always passable (enemies will open them if necessary).
        self.collision_rects = [wall.rect for wall in self.walls]
        self.interactables = [door for door in self.doors]

        # now initialise door geometry in the physics set; this has no bearing
        # on the mesh and only affects collisions for player/enemies.
        for door in self.doors:
            door.interact(self.collision_rects)


        # initialise enemies
        self.enemies = [
            Enemy((100, 100), (1, 0), [(100, 100), (300, 400)])
        ]

    def update(self, dt):
        self.player.update(dt)
        self._resolve_collisions()
        self.handle_interaction()
        for i in self.enemies:
           i.update(dt)

    def draw(self, screen, fps):
        #clear surface every frame:
        self.surface.fill((20, 20, 20))

        # draw player and other dynamic level objects
       
        # -- doors --
        for i in self.doors:
            i.draw(self.surface)

        # -- player --
        self.player.draw(self.surface)

        # -- enemy --
        for i in self.enemies:
            i.draw(self.surface)

        # draw static level objects
        for i in self.walls:
            i.draw(self.surface)
        


        # debug:
        draw_debug(screen, {
            "pos":   self.enemies[0].position,
            "movement_mode": self.player.movement_mode,
            "fps": round(fps)
        })

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
            # the mesh does not depend on the door state – doors are always
            # passable – so we never rebuild it.  collision_rects will still be
            # updated for physics though.

    def handle_input(self, event):
        self.player.handle_input(event)

    def _resolve_collisions(self):
        player_rect = self.player.get_collision_rect()
        enemy_rects = [enemy.rect for enemy in self.enemies]

        for rect in self.collision_rects:
            if player_rect.colliderect(rect):
                offset = self._calculate_pushout(player_rect, rect)
                self.player.resolve_collision(offset)
            for enemy_rect in enemy_rects:
                if enemy_rect.colliderect(rect):
                    offset = self._calculate_pushout(enemy_rect, rect)
                    enemy_rect.position += offset
                    enemy_rect.center = (int(enemy_rect.position.x), int(enemy_rect.position.y))
        
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

# consider a cell of rects size 



# creating a level polygon
# we can consider all corners of each rect, then consider a polygon of those rects. The border rects are uniform for all levels, so we can start with points (5, 5), (5, 715), (1075, 5), (1075, 715) in our polygon points. Consider all corners of rects within this polygon and add it to the points.


# level dictionary: type of obj: Wall, for every attribute of wall, contains data.
# should be able to create a level object from a dictionary.





