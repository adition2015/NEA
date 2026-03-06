import pygame

SPEED = 100

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, direction):
        super().__init__()
        self.position = pygame.Vector2(position)
        self.direction = pygame.Vector2(direction)
        self.state = "patrol"

        self.patrol_points = []
        self.current_wp = 0

        # -- visual setup --
        self.base_image = self._build_image()
        self.rect = self.base_image.get_rect(center=(int(self.position.x), int(self.position.y)))
        self.angle = 0

    def _patrol(self, dt):
        if not self.patrol_points:
            return
        
        target = self.patrol_points[0]
        to_target = target - self.position
        dist = to_target.length()

        if dist < 8:
            self.current_wp = (self.current_wp + 1) % len(self.patrol_points)
            return
        
        self.position += to_target.normalize() * SPEED * dt

    def _build_image(self) -> pygame.Surface:
        """Build the player's base sprite surface (facing right = 0 degrees)."""
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)  # SRCALPHA = transparent background

        # Body
        pygame.draw.circle(surface, (60, 120, 220), (16, 16), 16)
        # Direction indicator (nose) — points RIGHT by default (angle 0)
        pygame.draw.polygon(surface, (255, 255, 255), [(24, 16), (16, 7), (16, 23)])
        return surface
    
    
    def move(self, dt):
        pass
    
    def draw(self, surface: pygame.Surface):
        """Rotate fresh from base_image every draw call — no cumulative degradation."""
        rotated = pygame.transform.rotate(self.base_image, -self.angle)
        rect = rotated.get_rect(center=(int(self.position.x), int(self.position.y)))
        surface.blit(rotated, rect)
    
    def update(self, dt: float):
        self.move(dt)

    


