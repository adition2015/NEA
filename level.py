import pygame
from player import Player
from enemy import Enemy
from settings import *
from utils import draw_debug
from grid_waypoint import *
from pathfinding import distance
# Links:
"https://www.youtube.com/watch?v=UT_tKPLejyU" # pygame layers for drawing on screen


def scale_rect(x, y, w, h):
    return (
        int(x * settings.scale_x),
        int(y * settings.scale_y),
        int(w * settings.scale_x),
        int(h * settings.scale_y)
    )

class Level:
    def __init__(self, ID, data):
        player_pos = tuple(x//2 for x in settings.level_res) # encode it into data for level.
        self.ID = ID

        self.surface = pygame.Surface(settings.level_res, pygame.SRCALPHA)
        self.walls = [] # all walls have a rect attribute - this will be called for collisions
        self.doors = []# all doors have a rect attribute - if closed, will be called for collisions
        self._load_level(data)

        # build lists of collision rectangles.  ``collision_rects`` is the
        # authoritative set used for physics and door interactions; it will be
        # mutated whenever a door opens or closes.  the navigation mesh is
        # constructed from *walls alone* and is never updated because doors are
        # effectively always passable (enemies will open them if necessary).
        self.collision_rects = [wall.rect for wall in self.walls]
        self.static_rects = self.collision_rects.copy()
        self.interactables = [door for door in self.doors]
        self.door_rects = [door.rect for door in self.doors]

        self.graph = WaypointGraph(settings.level_res, self.static_rects, 50, self.door_rects)
        connected = [wp for wp in self.graph.waypoints if wp.neighbours]
        print(f"Waypoints with neighbours: {len(connected)} / {len(self.graph.waypoints)}")
        
        # now initialise door geometry in the physics set; this has no bearing
        # on the mesh and only affects collisions for player/enemies.
        for door in self.doors:
            door.interact(self.collision_rects)

        self.player = Player(
                             position=pygame.Vector2(player_pos),
                             direction=pygame.Vector2(0, -1)
                             )

        # initialise enemies
        self.enemies = [
            Enemy((100, 100), (0, 0), [(100, 100), (100, 200), (200, 100), (400, 400)]),
            Enemy((600, 600), (0, 0), [(600, 600), (400, 600), (800, 100), (400, 100)]),
            Enemy((200, 200), (0, 0), [(200, 200), (300, 200), (200, 600), (900, 400)]),
            Enemy((500, 600), (0, 0), [(500, 600), (200, 100), (700, 100), (100, 500)])
        ]

        self.precalculate_patrol_path()


        # preallocated drawing surface for vision cones:
        self.cone_surface = pygame.Surface(settings.level_res).convert()
        self.cone_temp = pygame.Surface(settings.level_res).convert()
        self.cone_update_interval = 50  # ms between cone redraws (= 20 FPS)
        self.cone_timer = 0

    def update(self, dt):
        self.cone_timer += dt * 1000 
        self.player.update(dt)
        self._resolve_collisions()
        self.handle_interaction()
        self.check_enemy_interactions()
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
        if self.cone_timer >= self.cone_update_interval:
            self.draw_vision_cones()
            self.cone_timer = 0
        # always blit the cached cone_surface, even on skipped frames
        self.surface.blit(self.cone_surface, (0, 0), special_flags=pygame.BLEND_ADD)

        # draw static level objects
        for i in self.walls:
            i.draw(self.surface)
        


        # debug:
        draw_debug(screen, {
            "pos":   self.enemies[0].position,
            "movement_mode": self.player.movement_mode,
            "fps": round(fps)
        })

        #debug waypoints
        #for wp in self.graph.waypoints:
        #   wp.draw(self.surface)

        # debug collision rects:
        for rect in self.collision_rects:
            pygame.draw.rect(self.surface, (0, 255, 0), rect, 2)

        screen.blit(self.surface, settings.level_offset)

    def _load_level(self, data: dict):
        for (x, y, w, h) in data.get("walls", []):
            self.walls.append(Wall(*scale_rect(x, y, w, h)))

        for (x, y, o) in data.get("doors", []):
            sx, sy = int(x * settings.scale_x), int(y * settings.scale_y)
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
    
    def check_enemy_interactions(self):
        for enemy in self.enemies:
            for door in self.doors:
                dist = pygame.Vector2(door.rect.center).distance_to(enemy.position)
                if dist < 40 and not door.is_open:
                    door.interact(self.collision_rects)
                elif dist > 50 and dist < 60 and door.is_open: # stops player interaction otherwise
                    door.interact(self.collision_rects) 
                   

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
        for rect in self.collision_rects:
            if abs(rect.centerx - self.player.rect.centerx) > 80:
                continue
            if self.player.rect.colliderect(rect):
                offset = self._calculate_pushout(self.player.rect, rect)
                self.player.resolve_collision(offset)
        for rect in self.collision_rects:
            for enemy in self.enemies:
                if abs(rect.centerx - enemy.rect.centerx) > 80:
                    continue
                if enemy.rect.colliderect(rect):
                    offset = self._calculate_pushout(enemy.rect, rect)
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

    def precalculate_patrol_path(self):
        # compute start and end wps for each enemy, call precalculate_patrol_path for each enemy:
        for enemy in self.enemies:
            # map patrol pts to waypoints:
            enemy.waypoints = []
            for i in enemy.patrol_points:
                enemy.waypoints.append(self.graph.nearest_waypoint(i))
            enemy.precalculate_patrol_path()
            enemy.set_direction()

    def draw_vision_cones(self):
        self.cone_surface.fill((0, 0, 0))
        for enemy in self.enemies:
            points = enemy.build_vision_cone(self.collision_rects)
            if len(points) >= 3:
                self.cone_temp.fill((0, 0, 0))
                pygame.draw.polygon(self.cone_temp, (64, 64, 0), points)
                self.cone_surface.blit(self.cone_temp, (0, 0),
                                    special_flags=pygame.BLEND_ADD)
                

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
        self.width *= settings.scale_x
        self.height *= settings.scale_y
        self.rect = pygame.rect.Rect(x, y, self.width, self.height)
        

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





