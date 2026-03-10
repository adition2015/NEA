import pygame, numpy as np, math

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position: tuple, direction: tuple, patrol_points: list):
        super().__init__()
        self.position = pygame.Vector2(position)
        self.direction = pygame.Vector2(direction)
        self.speed = 100
        self.patrol_points = patrol_points
        self.current_waypoint_index = 0

        # -- visual setup --
        self.base_image = self._build_image()
        self.rect = self.base_image.get_rect(center=(int(self.position.x), int(self.position.y)))
        self.angle = 0

        self.state = "patrol"

    def _build_image(self) -> pygame.Surface:
        """Build the player's base sprite surface (facing right = 0 degrees)."""
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)  # SRCALPHA = transparent background

        # Body
        pygame.draw.circle(surface, (240, 10, 20), (16, 16), 16)
        # Direction indicator (nose) — points RIGHT by default (angle 0)
        pygame.draw.polygon(surface, (255, 255, 255), [(24, 16), (16, 7), (16, 23)])
        return surface
    
    def patrol(self):
        """Simple waypoint-based patrol - move to next waypoint when close enough."""
        if not self.patrol_points:
            return
        
        target = pygame.Vector2(self.patrol_points[self.current_waypoint_index])
        
        if self.position.distance_to(target) < 5:
            # Move to next waypoint
            self.current_waypoint_index = (self.current_waypoint_index + 1) % len(self.patrol_points)
            target = pygame.Vector2(self.patrol_points[self.current_waypoint_index])
        
        self.direction = (target - self.position).normalize()
    
    def move(self, dt):
        self.position += dt*self.speed*self.direction
        # update angle
        rad = -math.acos(np.dot(tuple(self.direction), (1, 0)))
        self.angle = math.degrees(rad)
    
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


