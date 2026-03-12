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
        self.speed = 100
        self.patrol_points = patrol_points
        self.waypoints = []
        self.current_waypoint_index = 0

        # -- visual setup --
        self.base_image = self._build_image()
        self.rect = self.base_image.get_rect(center=(int(self.position.x), int(self.position.y)))
        self.angle = 0

        # vision
        self.FOV = 60
        self.cone_res = 0.5 # lines per degree
        self.view_distance = int(300 * settings.scale_diagonal)  # Scale vision range to resolution

        self.turn_speed = 360 # degrees per second

        self.state = "patrol"
        self.patrol_ID = 0

        # -- prerequisites --


    def _build_image(self) -> pygame.Surface:
        """Build the enemy's base sprite surface (facing right = 0 degrees)."""
        BASE_SIZE = 16
        BASE_RADIUS = BASE_SIZE / 2
        size = int(BASE_SIZE * settings.scale_diagonal)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)  # SRCALPHA = transparent background

        # Body
        radius = int(BASE_RADIUS * settings.scale_diagonal)
        pygame.draw.circle(surface, (240, 10, 20), (size // 2, size // 2), radius)
        
        # Direction indicator (nose) — points RIGHT by default (angle 0)
        scale = settings.scale_diagonal
        pygame.draw.polygon(surface, (255, 255, 255), [
            (int(24 * scale), int(16 * scale)), 
            (int(16 * scale), int(7 * scale)), 
            (int(16 * scale), int(23 * scale))
        ])
        return surface
        return surface
    
    def precalculate_patrol_path(self):
        self.patrol_path = []
        for i in range(len(self.waypoints) - 1):
            path_between_pts = a_star(self.waypoints[i], self.waypoints[i+1])
            if path_between_pts is None:
                print(f"Warning: no path between waypoint {i} and {i+1} — skipping segment")
                continue
            self.patrol_path.extend(path_between_pts)
        
        if len(self.waypoints) >= 2:
            return_path = a_star(self.waypoints[-1], self.waypoints[0])
            if return_path:
                self.patrol_path.extend(return_path)
        print(self.patrol_path)
    
    def patrol(self):
        """Simple waypoint-based patrol - move to next waypoint when close enough."""
        if not self.patrol_path:
            print("Enemy has no patrol path associated.")
            return 
        # follow patrol path indefinitely:
        else:
            self.follow_patrol_path()


    def follow_patrol_path(self):
        # patrol_path contains Waypoint objects; compare using their positions
        self.target_pos = self.patrol_path[self.patrol_ID]
        if self.position.distance_to(self.target_pos) < 5:
            self.patrol_ID = (self.patrol_ID + 1) % len(self.patrol_path)
            self.set_direction()
            # print(f"pos: {self.position}, target: {self.target_pos}, dist: {self.position.distance_to(self.target_pos)}")

    def set_direction(self):
        # point towards the current waypoint in the patrol path
        target = self.patrol_path[self.patrol_ID]
        vec = target - self.position
        if vec.length() > 0:
            self.direction = vec.normalize()
        else:
            
            self.direction = pygame.Vector2(0, 0)

    def resolve_collision(self, offset: pygame.Vector2):
        self.position += offset
        self.rect.center = (int(self.position.x), int(self.position.y))
        # reset direction:
        self.set_direction()
    
    def rotate(self, dt):
        # Calculate desired angle from direction vector
        desired_angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))
        
        # Calculate shortest angle difference (-180 to +180)
        angle_diff = (desired_angle - self.angle + 180) % 360 - 180
        
        # If already at the target, stop rotating
        if abs(angle_diff) < 0.01:
            self.angle = desired_angle
            return True
        
        # Calculate rotation amount for this frame
        rotation_amount = dt * self.turn_speed
        
        # OVERSHOOT PREVENTION: If we would rotate past the target, clamp to exact angle
        if abs(rotation_amount) >= abs(angle_diff):
            self.angle = desired_angle
        else:
            # Rotate in the correct direction by the calculated amount
            if angle_diff < 0:
                self.angle -= rotation_amount
            else:
                self.angle += rotation_amount 


    def move(self, dt):
        self.position += dt * self.speed * self.direction
        self.rect.center = (int(self.position.x), int(self.position.y))
        # update angle (if direction is zero this will produce 0)
        if self.direction.length() > 0:
            self.rotate(dt)
        else:
            self.angle = 0

    
    def draw(self, surface: pygame.Surface):
        """Rotate fresh from base_image every draw call — no cumulative degradation."""
        rotated = pygame.transform.rotate(self.base_image, self.angle)
        rect = rotated.get_rect(center=(int(self.position.x), int(self.position.y)))
        surface.blit(rotated, rect)
    
    def update(self, dt: float):
        old_pos = pygame.Vector2(self.position)
        old_angle = self.angle
        if self.state == "patrol":
            self.patrol()
        self.move(dt)
        self._vision_dirty = (self.position != old_pos or self.angle != old_angle)

    def build_vision_cone(self, walls):
        cx, cy = self.rect.center
        half_fov = self.FOV / 2
        ARC_STEP = 10  # degrees between arc fill points — lower = smoother

        # Collect wall corner angles as before
        candidate_angles = [self.angle - half_fov, self.angle + half_fov]
        for rect in walls:
            for corner in [(rect.left, rect.top), (rect.right, rect.top),
                        (rect.left, rect.bottom), (rect.right, rect.bottom)]:
                ex, ey = corner
                raw_angle = math.degrees(math.atan2(-(ey - cy), ex - cx))
                diff = (raw_angle - self.angle + 180) % 360 - 180
                if abs(diff) <= half_fov + 1:
                    for offset in (-0.0001, 0, 0.0001):
                        candidate_angles.append(self.angle + diff + offset)

        candidate_angles = sorted(set(candidate_angles))
        candidate_angles = [a for a in candidate_angles
                            if abs((a - self.angle + 180) % 360 - 180) <= half_fov]

        # Cast rays and tag whether they reached full distance (no wall hit)
        raw_points = []
        for angle in candidate_angles:
            pt = self.cast_ray(angle, walls)
            px, py = pt
            dist = math.hypot(px - cx, py - cy)
            at_max = dist >= self.view_distance - 1
            raw_points.append((angle, pt, at_max))

        # Build final point list, inserting arc fills between open rays
        points = [(cx, cy)]
        for i, (angle, pt, at_max) in enumerate(raw_points):
            points.append(pt)
            if i + 1 < len(raw_points):
                next_angle, next_pt, next_at_max = raw_points[i + 1]
                if at_max and next_at_max:
                    # Both rays hit open air — fill the gap with arc points
                    steps = int((next_angle - angle) / ARC_STEP)
                    for s in range(1, steps):
                        fill_angle = angle + s * ARC_STEP
                        rad = math.radians(fill_angle)
                        arc_pt = (
                            cx + math.cos(rad) * self.view_distance,
                            cy - math.sin(rad) * self.view_distance
                        )
                        points.append(arc_pt)

        return points

    def get_vision_angles(self):
        self.ray_count = int(self.FOV * self.cone_res)
        half = self.FOV / 2
        angles =  [
            self.angle - half + i * (1 / self.cone_res)
            for i in range(self.ray_count)
        ]
        return angles

    def cast_ray(self, angle, collision_rects):
        "Returns the end point of a ray in a vision cone"
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = -math.sin(rad)
        direction = pygame.Vector2(dx, dy)
        start = pygame.Vector2(self.rect.center)
        end = start + direction * self.view_distance
        
        hit_point = end
        for wall in collision_rects:
            clipped = wall.clipline(start, end)
            if clipped:
                #find distance between hitpoint and self.rect.center
                if distance(self.rect.center, clipped[0]) < distance(self.rect.center, hit_point):
                    hit_point = clipped[0]
        return hit_point

    def draw_vision_cone(self, surface, points):
        # TRANSPARENCY FIX: pygame.draw.polygon with alpha doesn't blend properly on SRCALPHA surfaces
        # Solution: Create a temporary surface, draw on it, then blit with proper alpha blending
        if len(points) < 2:
            return  # Need at least 2 points to draw
        
        # Create a temporary transparent surface for the vision cone
        temp_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        
        # Draw the filled polygon on the temporary surface with transparency (RGBA: Yellow with 64/255 alpha)
        pygame.draw.polygon(temp_surface, (255, 255, 0, 64), points)
        
        # Blit the temporary surface onto the main surface using alpha blending
        # This properly composites the transparent polygon with the background
        surface.blit(temp_surface, (0, 0))