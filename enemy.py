import pygame, math, os
from grid_waypoint import *
from pathfinding import *
from settings import settings
from noise import NoiseEvent


# All speeds are in base units per second (base res = 1080×720).
PATROL_SPEED        = 50
CHASE_SPEED         = 100
SEARCH_SPEED        = 75
RETURN_SPEED        = 50
INVESTIGATE_SPEED   = 30

SUSPICION_CAP = 100.0
SUSPICION_MULTIPLIER_CAP = 3.0

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position: tuple, direction: tuple, patrol_points: list):
        super().__init__()
        self.position = pygame.Vector2(position)        # BASE coords
        self.direction = pygame.Vector2(direction)
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        self.speed = PATROL_SPEED
        self.patrol_points = patrol_points              # BASE coords (straight from JSON)
        self.waypoints = []
        self.patrol_path = []                           # BASE coords (set by Level)
        self.current_waypoint_index = 0

        # --- visual ---
        self._colour = (240, 10, 20)
        self._icon = None
        self.base_image = self._build_image()
        # rect tracks BASE coords for collision / LoS polygon test
        self.rect = self.base_image.get_rect(center=(int(self.position.x),
                                                      int(self.position.y)))
        self.angle = 0
        self._vision_dirty  = True
        self.vision_points  = []                        # BASE coords
        self.vision_cone_colour = (64, 64, 0)
        self.last_seen  = None
        self.player_obs = None
        self.LoS_timer  = 0.5
        self.target_angle = None


        # vision — all distances in base units
        self.FOV           = 100
        self.cone_res      = 0.5
        self.view_distance = 200        # base units

        self.turn_speed = 360           # degrees / second

        self.state     = "patrol"
        self.carried = False
        self.hidden = False
        self.move_condition = True
        self.patrol_ID = 0

        self.search_path  = []
        self.search_id    = 0
        self.return_path  = []
        self.return_id    = 0
        self.alerted_path = []
        self.alerted_id   = 0
        self.suspicion = 0.0
        self.suspicion_multiplier = 1.0
        self.last_heard = NoiseEvent(self.position, 0)

    # ------------------------------------------------------------------
    # Visual
    # ------------------------------------------------------------------

    def _build_image(self) -> pygame.Surface:
        # Image pixel size is a rendering concern — scale is fine here.
        size = max(1, int(20 * settings.scale_total_x))
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, self.colour, (size / 2, size / 2), size / 2)
        if self.icon != None:
            self.icon_surface = pygame.image.load(f"assets/icons/{self.icon}.png")
            self.icon_surface = pygame.transform.scale(self.icon_surface, (size, size))
        return surface
    
    # ------------------------------------------------------------------
    # Death
    # ------------------------------------------------------------------
    def transition_death(self):
        self.state = "dead"  # enters dead state
        self.colour = (97, 64, 65)
        self.icon = "cross"
        self.patrol_path = []
        self.return_path = []
        self.search_path = []
        self.direction = pygame.Vector2(0, 0)

    
        

    # ------------------------------------------------------------------
    # Patrol
    # ------------------------------------------------------------------

    def precalculate_patrol_path(self):
        self.patrol_path = []
        for i in range(len(self.waypoints) - 1):
            path_between_pts = a_star(self.waypoints[i], self.waypoints[i + 1])
            if path_between_pts is None:
                print(f"Warning: no path between waypoint {i} and {i+1} — skipping segment")
                continue
            self.patrol_path.extend(path_between_pts)

        if len(self.waypoints) >= 2:
            return_path = a_star(self.waypoints[-1], self.waypoints[0])
            if return_path:
                self.patrol_path.extend(return_path)

    def patrol(self):
        if not self.patrol_path:
            print("Enemy has no patrol path associated.")
            return
        self.follow_patrol_path()

    def follow_patrol_path(self):
        self.target_pos = self.patrol_path[self.patrol_ID]
        if self.position.distance_to(self.target_pos) < 5:
            self.patrol_ID = (self.patrol_ID + 1) % len(self.patrol_path)
            self.set_direction(self.patrol_path[self.patrol_ID])

    # ------------------------------------------------------------------
    # Chase
    # ------------------------------------------------------------------

    def transition_chase(self, player_obs: pygame.Vector2):
        self.state = "chase"
        self.turn_speed = 360
        self.FOV = 100
        self.vision_cone_colour = (64, 0, 0)
        self.target_angle = None
        self.player_obs   = player_obs
        self.last_seen    = pygame.Vector2(player_obs)
        self.icon = "exclamation"

    def chase(self):
        dist_to_player = self.position.distance_to(self.player_obs)
        min_dist = 30   # base units
        if dist_to_player < min_dist:
            self.speed = 0
            self.set_direction(self.player_obs)
        else:
            self.speed = CHASE_SPEED
            self.set_direction(self.player_obs)

    # ------------------------------------------------------------------
    # Investigate
    # ------------------------------------------------------------------

    def transition_investigate(self, noise):
        if self.state == "chase":
            return
        self.last_heard = noise
        self.state = "investigate"
        self.investigation_timer = 10 # seconds
        self.vision_cone_colour = (64, 32, 0)
        self.set_direction(self.last_heard.position)
    
    def investigate(self, dt):
        if self.investigation_timer < 0 or self.position.distance_to(self.last_heard.position) < 50:
            self.transition_scout()
        
        self.investigation_timer -= dt    
    
    # ------------------------------------------------------------------
    # Alerted
    # ------------------------------------------------------------------

    def transition_alerted(self, noise, alerted_path: list):
        if self.state == "chase":
            return
        if self.state == "alerted" and noise.intensity < self.last_heard.intensity:
            return
        self.state = "alerted"
        self.vision_cone_colour = (64, 0, 0)
        self.alerted_id = 0 
        self.alerted_path = alerted_path or []
    
    def alerted(self):
        if not self.alerted_path:
            self.transition_returning_to_patrol() # could be mid investigation
            return
        target = self.alerted_path[self.alerted_id]
        self.set_direction(target)

        if self.position.distance_to(target) < 5:
            self.alerted_id += 1
            if self.alerted_id >= len(self.alerted_path):
                self.transition_scout() # easy return to patrol
                return
            self.set_direction(self.alerted_path[self.alerted_id])


    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def transition_search(self, search_path: list):
        if self.state == "search":
            return
        self.state = "search"
        self.icon = "question"
        self.vision_cone_colour = (64, 32, 0)
        self.target_angle = None
        self.player_obs   = None
        self.search_path  = search_path or []
        self.search_id    = 0
        self.suspicion_multiplier = min(SUSPICION_MULTIPLIER_CAP, self.suspicion_multiplier + 1.0)
        if self.search_path:
            self.set_direction(self.search_path[0])

    def search(self):
        if not self.search_path:
            self.transition_patrol()
            return

        target = self.search_path[self.search_id]
        self.set_direction(target)

        if self.position.distance_to(target) < 5:
            self.search_id += 1
            if self.search_id >= len(self.search_path):
                self.transition_scout()
                return
            self.set_direction(self.search_path[self.search_id])

    # ------------------------------------------------------------------
    # Scout
    # ------------------------------------------------------------------

    def transition_scout(self):
        if self.state != "scout":
            self.state = "scout"
            self.scout_angles = [self.angle + 180, self.angle + 360]
            self.scout_id    = 0
            self.search_path = []
            self.search_id   = 0
            self.alerted_path = []
            self.alerted_id  = 0
    def scout(self):
        if self.scout_id >= len(self.scout_angles) or self.state != "scout":
            self.target_angle = None
            self.transition_returning_to_patrol()
            return

        self.target_angle = self.scout_angles[self.scout_id]
        if abs(self.angle - self.target_angle) < 1.0:
            self.scout_id += 1

    # ------------------------------------------------------------------
    # Return to patrol
    # ------------------------------------------------------------------

    def transition_returning_to_patrol(self):
        if self.state != "returning_to_patrol":
            self.state = "returning_to_patrol"
            self.icon = None
            self.vision_cone_colour = (64, 64, 0)
            self.target_angle = None
            self.player_obs   = None
            self.return_path  = []
            self.return_id    = 0

    def returning_to_patrol(self):
        if not self.return_path:
            self.transition_patrol()
            return

        target = self.return_path[self.return_id]
        self.set_direction(target)

        if self.position.distance_to(target) < 5:
            self.return_id += 1
            if self.return_id >= len(self.return_path):
                self.transition_patrol()
                return
            self.set_direction(self.return_path[self.return_id])

    def transition_patrol(self):
        self.state = "patrol"
        self.vision_cone_colour = (64, 64, 0)
        self.icon = None
        self.target_angle = None
        self.player_obs   = None
        self.last_seen    = None
        self.return_path  = []
        self.return_id    = 0
        if self.patrol_path:
            min_dist   = float('inf')
            closest_id = 0
            for i, pt in enumerate(self.patrol_path):
                dist = self.position.distance_to(pt)
                if dist < min_dist:
                    min_dist   = dist
                    closest_id = i
            self.patrol_ID = closest_id
            self.set_direction(self.patrol_path[self.patrol_ID])

    # ------------------------------------------------------------------
    # Movement helpers
    # ------------------------------------------------------------------

    def set_return_path(self, path: list):
        self.return_path = path or []
        self.return_id   = 0
        if self.return_path:
            self.set_direction(self.return_path[0])

    def set_direction(self, target: pygame.Vector2):
        vec = pygame.Vector2(target) - self.position
        if vec.length() > 0:
            self.direction = vec.normalize()
        else:
            self.direction = pygame.Vector2(0, 0)

    def resolve_collision(self, offset: pygame.Vector2):
        self.position += offset
        self.rect.center = (int(self.position.x), int(self.position.y))
        if self.patrol_path:
            self.set_direction(self.patrol_path[self.patrol_ID])

    def rotate(self, dt, desired_angle=None):
        if desired_angle is None:
            desired_angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))

        angle_diff = (desired_angle - self.angle + 180) % 360 - 180

        if abs(angle_diff) < 0.01:
            self.angle = desired_angle
            return True

        rotation_amount = dt * self.turn_speed
        if abs(rotation_amount) >= abs(angle_diff):
            self.angle = desired_angle
        else:
            self.angle += rotation_amount if angle_diff > 0 else -rotation_amount

    def move(self, dt, desired_angle=None):
        if self.move_condition:
            self.position += dt * self.speed * self.direction
            self.rect.center = (int(self.position.x), int(self.position.y))
            if desired_angle is not None or self.direction.length() > 0:
                self.rotate(dt, desired_angle)

    # ------------------------------------------------------------------
    # Vision  (ray casting in BASE coords)
    # ------------------------------------------------------------------

    def update_vision(self):
        old_pos   = pygame.Vector2(self.position)
        old_angle = self.angle
        self._vision_dirty = (
            self.position.distance_to(old_pos) > 0.5 or
            abs(self.angle - old_angle) > 2.0
        )

    def build_vision_cone(self, collision_rects):
        """Returns a list of (x, y) tuples in BASE coords."""
        self.angles = self.get_vision_angles()
        points = [(self.position.x, self.position.y)]
        for angle in self.angles:
            points.append(self.cast_ray(angle, collision_rects))
        return points

    def get_vision_angles(self):
        self.ray_count = int(self.FOV * self.cone_res)
        half = self.FOV / 2
        return [
            self.angle - half + i * (1 / self.cone_res)
            for i in range(self.ray_count)
        ]

    def cast_ray(self, angle, collision_rects):
        """Cast a ray in BASE space; collision_rects must be in BASE coords."""
        rad       = math.radians(angle)
        direction = pygame.Vector2(math.cos(rad), -math.sin(rad))
        start     = pygame.Vector2(self.position)
        end       = start + direction * self.view_distance   # view_distance in base units

        hit_point = end
        for wall in collision_rects:
            clipped = wall.clipline(start, end)
            if clipped:
                from pathfinding import distance
                if distance(self.rect.center, clipped[0]) < distance(self.rect.center, hit_point):
                    hit_point = clipped[0]
        return hit_point

    # draw_vision_cone is intentionally removed from Enemy.
    # Level.draw_vision_cones() handles scaling + blending centrally.

    # ------------------------------------------------------------------
    # Draw / Update
    # ------------------------------------------------------------------

    @property   
    def colour(self):
        return self._colour

    @colour.setter
    def colour(self, value):
        self._colour = value
        if hasattr(self, 'base_image'):  # guard for __init__ order
            self.base_image = self._build_image()

    @property   
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, value):
        self._icon = value
        if hasattr(self, 'base_image'):  # guard for __init__ order
            self.base_image = self._build_image()

    def draw(self, surface: pygame.Surface):
        rotated = pygame.transform.rotate(self.base_image, self.angle)
        # Only here: convert base position → level-surface pixels.
        screen_pos = settings.to_screen(self.position)
        icon_screen_pos = settings.to_screen(self.position)
        rect = rotated.get_rect(center=(int(screen_pos.x), int(screen_pos.y)))
        surface.blit(rotated, rect)
        if self.icon != None:
            icon_rect = self.icon_surface.get_rect(center=(int(icon_screen_pos.x), int(icon_screen_pos.y)))
            surface.blit(self.icon_surface, icon_rect)

    def update(self, dt: float):
        if self.state == "patrol":
            self.speed = PATROL_SPEED
            self.patrol()
        elif self.state == "chase":
            self.speed = CHASE_SPEED
            self.chase()
        elif self.state == "search":
            self.speed = SEARCH_SPEED
            self.search()
        elif self.state == "returning_to_patrol":
            self.speed = RETURN_SPEED
            self.returning_to_patrol()
        elif self.state == "scout":
            self.speed = 0
            self.scout()
        elif self.state == "investigate":
            self.speed = INVESTIGATE_SPEED
            self.investigate(dt)
        elif self.state == "alerted":
            self.speed = CHASE_SPEED
            self.alerted()
        if self.state != "dead": 
            self.move(dt, self.target_angle)
            self.update_vision()
