import pygame
from navmesh import NavMesh, find_path

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position: tuple, direction: tuple, patrol_points: list):
        super().__init__()
        self.position = pygame.Vector2(position)
        self.direction = pygame.Vector2(direction)
        self.speed = 100
        self.patrol_points = patrol_points
        self.patrol_ID = 0
        self.path = []

        # -- visual setup --
        self.base_image = self._build_image()
        self.rect = self.base_image.get_rect(center=(int(self.position.x), int(self.position.y)))
        self.angle = 0


        
        self.state = "patrol"

    def _build_image(self) -> pygame.Surface:
        """Build the player's base sprite surface (facing right = 0 degrees)."""
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)  # SRCALPHA = transparent background

        # Body
        pygame.draw.circle(surface, (60, 120, 220), (16, 16), 16)
        # Direction indicator (nose) — points RIGHT by default (angle 0)
        pygame.draw.polygon(surface, (255, 255, 255), [(24, 16), (16, 7), (16, 23)])
        return surface
    
    def handle_state_based_updates(self, navmesh):
        if self.state == "patrol":
            self.patrol(navmesh)
    
    def move(self, dt):
        self.position += dt*self.speed*self.direction

    def patrol(self, navmesh):
        self.patrol_ID = (self.patrol_ID + 1) % len(self.patrol_points)
        if not self.path:
            self.path = find_path(navmesh, self.position, self.patrol_points[self.patrol_ID])
            # initialise self.direction to first path:
            self.direction = (self.path[0] - self.position).normalize() if self.path else pygame.Vector2(0, 0)
        if self.path:
            self.follow_path()
    
    def follow_path(self):
        # changes self.direction based on path progress
        # treat self.path as a queue
        if self.position.distance_to(self.path[0]) < 5:
            if len(self.path) == 1:
                self.path = []
            else:
                self.path.pop(0)
                # update direction:
                self.direction = (self.path[0] - self.position).normalize()

        
    def draw(self, surface: pygame.Surface):
        """Rotate fresh from base_image every draw call — no cumulative degradation."""
        rotated = pygame.transform.rotate(self.base_image, -self.angle)
        rect = rotated.get_rect(center=(int(self.position.x), int(self.position.y)))
        surface.blit(rotated, rect)
    
    def update(self, dt: float, navmesh: NavMesh):
        # handle variable updates
        self.handle_state_based_updates(navmesh)

        # handle position updates
        self.move(dt)


