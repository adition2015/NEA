import pygame, numpy as np, math
from grid_waypoint import *
from pathfinding import *

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

        self.state = "patrol"
        self.patrol_ID = 0

        # -- prerequisites --


    def _build_image(self) -> pygame.Surface:
        """Build the player's base sprite surface (facing right = 0 degrees)."""
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)  # SRCALPHA = transparent background

        # Body
        pygame.draw.circle(surface, (240, 10, 20), (16, 16), 16)
        # Direction indicator (nose) — points RIGHT by default (angle 0)
        pygame.draw.polygon(surface, (255, 255, 255), [(24, 16), (16, 7), (16, 23)])
        return surface
    
    def precalculate_patrol_path(self):
        self.patrol_path = []
        # construct a path that enemy walks from p1 through path and back to p1:
        print(f'Enemy waypoints: {self.waypoints}')
        for i in range(len(self.waypoints) - 1):
            # compute start and end wps:
            
            path_between_pts = a_star(self.waypoints[i], self.waypoints[i+1])
            self.patrol_path.extend(path_between_pts)
        # calculate path from last to first and extend patrol_path:
        self.patrol_path.extend(a_star(self.waypoints[-1], self.waypoints[0]))
        print(self.patrol_path)
        # ensure we have a valid direction heading toward first waypoint
        if self.patrol_path:
            self.patrol_ID = 0
            self.set_direction()
    
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
        target_pos = self.patrol_path[self.patrol_ID]
        if self.position.distance_to(target_pos) < 5:
            self.patrol_ID = (self.patrol_ID + 1) % len(self.patrol_path)
            self.set_direction()

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

    def move(self, dt):
        self.position += dt * self.speed * self.direction
        self.rect.center = (int(self.position.x), int(self.position.y))
        # update angle (if direction is zero this will produce 0)
        if self.direction.length() > 0:
            rad = -math.acos(np.dot(tuple(self.direction), (1, 0)))
            self.angle = math.degrees(rad)
        else:
            self.angle = 0
    
    def draw(self, surface: pygame.Surface):
        """Rotate fresh from base_image every draw call — no cumulative degradation."""
        rotated = pygame.transform.rotate(self.base_image, -self.angle)
        rect = rotated.get_rect(center=(int(self.position.x), int(self.position.y)))
        surface.blit(rotated, rect)
    
    def update(self, dt: float):
        # handle variable updates
        if self.state == "patrol":
            self.patrol()

        # handle position updates
        self.move(dt)


