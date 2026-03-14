import pygame, math
from grid_waypoint import *
from pathfinding import *
from functools import lru_cache
from settings import settings

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position: tuple, direction: tuple, patrol_points: list):
        super().__init__()
        self.position = pygame.Vector2(position)
        self.direction = pygame.Vector2(direction)
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
        self.speed = 25 * settings.scale_total_x
        self.patrol_points = patrol_points
        self.waypoints = []
        self.current_waypoint_index = 0

        # -- visual setup --
        self.base_image = self._build_image()
        self.rect = self.base_image.get_rect(center=(int(self.position.x), int(self.position.y)))
        self.angle = 0
        self._vision_dirty = True
        self.vision_points = []
        self.vision_cone_colour = (64, 64, 0)
        self.last_seen = None   # last confirmed player position; never cleared by transition_chase
        self.player_obs = None  # live player pos — only non-None when LoS exists
        self.LoS_timer = 0.5 # seconds
        self.target_angle = None

        # vision
        self.FOV = 60
        self.cone_res = 0.5
        self.view_distance = 300 * settings.scale_total_x

        self.turn_speed = 360  # degrees per second

        self.state = "patrol"
        self.patrol_ID = 0

        # search
        self.search_path = []  # Vector2 positions A* computed to last_seen
        self.search_id = 0     # index along search_path

        # return
        self.return_path = []  # Vector2 positions A* computed back to patrol
        self.return_id = 0


    # ------------------------------------------------------------------
    # Visual
    # ------------------------------------------------------------------

    def _build_image(self) -> pygame.Surface:
        size = max(1, int(16 * settings.scale_total_x)) # this is used to ensure at very small resolutions, no zero error.
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        radius = size / 2
        pygame.draw.circle(surface, (240, 10, 20), (size // 2, size // 2), radius)
        return surface

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
        """Called by Level every frame the enemy has LoS. player_obs is always valid here."""
        self.state = "chase"
        self.vision_cone_colour = (64, 0, 0)
        self.target_angle = None
        self.player_obs = player_obs
        # ONLY update last_seen when we have a real sighting — never overwrite with None
        self.last_seen = pygame.Vector2(player_obs)


    def chase(self):
        dist_to_player = self.position.distance_to(self.player_obs)
        min_dist = 30 * settings.scale_total_x
        if dist_to_player < min_dist:
            # Hold position — just face the player, don't move
            self.speed = 0
            self.set_direction(self.player_obs)
        else:
            self.speed = 100 * settings.scale_total_x
            self.set_direction(self.player_obs)
    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def transition_search(self, search_path: list):
        """
        Called by Level the moment LoS is lost while chasing.
        search_path: list[Vector2] from A* leading to last_seen (computed by Level).
        """
        if self.state == "search":
            return  # don't restart an in-progress search
        self.state = "search"
        self.vision_cone_colour = (64, 32, 0)
        self.target_angle = None
        self.player_obs = None
        self.search_path = search_path or []
        self.search_id = 0
        if self.search_path:
            self.set_direction(self.search_path[0])

    def search(self):
        """
        Walk the pre-computed path toward last_seen, checking for LoS each frame
        (that check lives in Level.update_vision_cones — it will call
        transition_chase if the player is re-spotted).
        Transition to patrol once the end of the path is reached without a sighting.
        """
        if not self.search_path:
            self.transition_patrol()
            return

        target = self.search_path[self.search_id]
        self.set_direction(target)

        if self.position.distance_to(target) < 5:
            self.search_id += 1
            if self.search_id >= len(self.search_path):
                self.transition_scout()
                # Reached last_seen — player not found; start scout: rotate 360 degrees and see if player is visible
                
                return
            self.set_direction(self.search_path[self.search_id])
    
    # ------------------------------------------------------------------
    # Scout
    # ------------------------------------------------------------------


    def transition_scout(self):
        if self.state != "scout":
            self.state = "scout"
            self.scout_angles = [self.angle + 180, self.angle + 360]
            self.scout_id = 0
            self.search_path = []
            self.search_id = 0
    
    def scout(self):
        if self.scout_id >= len(self.scout_angles) or self.state != "scout":
            self.target_angle = None   # ← clear so rotate() uses direction again
            self.transition_returning_to_patrol()
            return

        self.target_angle = self.scout_angles[self.scout_id]

        if abs(self.angle - self.target_angle) < 1.0:   # ← threshold, not ==
            self.scout_id += 1

    # ------------------------------------------------------------------
    # Return to patrol
    # ------------------------------------------------------------------

    def transition_returning_to_patrol(self):
        if self.state != "returning_to_patrol":
            self.state = "returning_to_patrol"
            self.vision_cone_colour = (64, 64, 0)
            self.target_angle = None
            self.player_obs = None
            self.return_path = []   # Level will compute and set this via update_vision_cones
            self.return_id = 0



    def returning_to_patrol(self):
        """
        Walk the pre-computed path back to the patrol path.
        Transition to patrol once the end of the path is reached.
        """
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
        """Called when returning to patrol ends."""
        self.state = "patrol"
        self.vision_cone_colour = (64, 64, 0)
        self.target_angle = None
        self.player_obs = None
        self.last_seen = None
        self.return_path = []
        self.return_id = 0
        if self.patrol_path:
            # Find the closest point in patrol_path and set patrol_ID to it
            min_dist = float('inf')
            closest_id = 0
            for i, pt in enumerate(self.patrol_path):
                dist = self.position.distance_to(pt)
                if dist < min_dist:
                    min_dist = dist
                    closest_id = i
            self.patrol_ID = closest_id
            self.set_direction(self.patrol_path[self.patrol_ID])

    # ------------------------------------------------------------------
    # Movement helpers
    # ------------------------------------------------------------------

    def set_return_path(self, path: list):
        self.return_path = path or []
        self.return_id = 0
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

    def rotate(self, dt, desired_angle = None):
        if desired_angle is None:                        # ← was `if not desired_angle`
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

    def move(self, dt, desired_angle = None):
        self.position += dt * self.speed * self.direction
        self.rect.center = (int(self.position.x), int(self.position.y))
        if desired_angle is not None or self.direction.length() > 0:  # ← allow rotate when stopped
            self.rotate(dt, desired_angle)

    # ------------------------------------------------------------------
    # Vision
    # ------------------------------------------------------------------

    def update_vision(self):
        old_pos = pygame.Vector2(self.position)
        old_angle = self.angle
        self._vision_dirty = (
            self.position.distance_to(old_pos) > 0.5 or
            abs(self.angle - old_angle) > 2.0
        )

    def build_vision_cone(self, walls):
        self.angles = self.get_vision_angles()
        points = [(self.position.x, self.position.y)]
        for angle in self.angles:
            points.append(self.cast_ray(angle, walls))
        return points

    def get_vision_angles(self):
        self.ray_count = int(self.FOV * self.cone_res)
        half = self.FOV / 2
        return [
            self.angle - half + i * (1 / self.cone_res)
            for i in range(self.ray_count)
        ]

    def cast_ray(self, angle, collision_rects):
        rad = math.radians(angle)
        direction = pygame.Vector2(math.cos(rad), -math.sin(rad))
        start = pygame.Vector2(self.position)
        end = start + direction * self.view_distance


        hit_point = end
        for wall in collision_rects:
            clipped = wall.clipline(start, end)
            if clipped:
                if distance(self.rect.center, clipped[0]) < distance(self.rect.center, hit_point):
                    hit_point = clipped[0]
        return hit_point

    def draw_vision_cone(self, surface, points):
        if len(points) < 2:
            return
        temp_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        pygame.draw.polygon(temp_surface, (255, 255, 0, 64), points)
        surface.blit(temp_surface, (0, 0))

    # ------------------------------------------------------------------
    # Draw / Update
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        rotated = pygame.transform.rotate(self.base_image, self.angle)
        rect = rotated.get_rect(center=(int(self.position.x), int(self.position.y)))
        surface.blit(rotated, rect)

    def update(self, dt: float):
        if self.state == "patrol":
            self.speed = 50 * settings.scale_total_x
            self.patrol()
        elif self.state == "chase":
            self.speed = 100 * settings.scale_total_x
            self.chase()
        elif self.state == "search":
            self.speed = 75 * settings.scale_total_x
            self.search()
        elif self.state == "returning_to_patrol":
            self.speed = 50 * settings.scale_total_x
            self.returning_to_patrol()
        elif self.state == "scout":
            self.speed = 0
            self.scout()

        self.move(dt, self.target_angle)
        self.update_vision()
