import pygame, numpy as np, math
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
        self.speed = 25
        self.speed = 25
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

        # vision
        self.FOV = 60
        self.cone_res = 0.5
        self.view_distance = int(300 * settings.scale_diagonal)

        self.turn_speed = 360  # degrees per second

        self.state = "patrol"
        self.patrol_ID = 0

        # search
        self.search_path = []  # Vector2 positions A* computed to last_seen
        self.search_id = 0     # index along search_path

        # return to patrol
        self.return_path = []
        self.return_id = 0
        self.returned = True

    # ------------------------------------------------------------------
    # Visual
    # ------------------------------------------------------------------

    def _build_image(self) -> pygame.Surface:
        BASE_SIZE = 16
        BASE_RADIUS = BASE_SIZE / 2
        size = int(BASE_SIZE * settings.scale_diagonal)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        radius = int(BASE_RADIUS * settings.scale_diagonal)
        pygame.draw.circle(surface, (240, 10, 20), (size // 2, size // 2), radius)

        scale = settings.scale_diagonal
        pygame.draw.polygon(surface, (255, 255, 255), [
            (int(24 * scale), int(16 * scale)),
            (int(16 * scale), int(7 * scale)),
            (int(16 * scale), int(23 * scale))
        ])
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
        self.player_obs = player_obs
        # ONLY update last_seen when we have a real sighting — never overwrite with None
        self.last_seen = pygame.Vector2(player_obs)

    def chase(self):
        """Direct pursuit. Level guarantees player_obs is set while state == 'chase'."""
        self.set_direction(self.player_obs)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def transition_search(self, search_path: list, return_path: list):
        """
        Called by Level the moment LoS is lost while chasing.
        search_path: list[Vector2] from A* leading to last_seen (computed by Level).
        """
        if self.state == "search":
            return  # don't restart an in-progress search
        self.state = "search"
        self.vision_cone_colour = (64, 32, 0)
        self.player_obs = None
        self.search_path = search_path or []
        self.search_id = 0
        self.return_path = return_path or []
        print(self.return_path)
        self.return_id = 0
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
                # self.scout()
                # Reached last_seen — player not found; give up and resume patrol
                self.transition_patrol()
                return
            self.set_direction(self.search_path[self.search_id])


    # ------------------------------------------------------------------
    # Return to patrol
    # ------------------------------------------------------------------

    def transition_patrol(self):
        """Called when search ends without re-acquiring the player."""
        if self.state == "patrol": # prevents restarting logic of transitioning patrol
            return
        self.state = "patrol"
        self.vision_cone_colour = (64, 64, 0)
        self.player_obs = None
        self.last_seen = None
        self.search_path = []
        self.search_id = 0
        self.returned = False


    def return_to_patrol(self):
        target = self.return_path[self.return_id]
        self.set_direction(target)

        if self.position.distance_to(target) < 5:
            self.return_id += 1
            if self.return_id >= len(self.return_path):
                self.returned = True
                return
            self.set_direction(self.return_path[self.return_id])
        
                



    # ------------------------------------------------------------------
    # Movement helpers
    # ------------------------------------------------------------------

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

    def rotate(self, dt):
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

    def move(self, dt):
        self.position += dt * self.speed * self.direction * settings.scale_diagonal
        self.position += dt * self.speed * self.direction * settings.scale_diagonal
        self.rect.center = (int(self.position.x), int(self.position.y))
        if self.direction.length() > 0:
            self.rotate(dt)
        else:
            self.angle = 0

    # ------------------------------------------------------------------
    # Vision
    # ------------------------------------------------------------------

    def update_vision(self):
        old_pos = pygame.Vector2(self.position)
        old_angle = self.angle
        self._vision_dirty = (
            self.position.distance_to(old_pos) > 0.5 or
            abs(self.angle - old_angle) > 0.2
        )

    def build_vision_cone(self, walls):
        self.angles = self.get_vision_angles()
        points = [self.rect.center]
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
        start = pygame.Vector2(self.rect.center)
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
            self.speed = 75
            if not self.returned:
                self.return_to_patrol()
            else:    
                self.patrol()
        elif self.state == "chase":
            self.speed = 90
            self.chase()
        elif self.state == "search":
            self.speed = 65
            self.search()

        self.move(dt)
        self.update_vision()
