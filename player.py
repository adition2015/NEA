import pygame
from settings import settings

SPEED = {1: 75, 2: 125, 3: 175}

MOVEMENT_TRANSITIONS = {
    1: (3, 2),
    2: (3, 1),
    3: (2, 1),
}


class Player(pygame.sprite.Sprite):
    def __init__(self, position: pygame.Vector2, direction: pygame.Vector2):
        super().__init__()
        self.position  = pygame.Vector2(position)
        self.direction = pygame.Vector2(direction)
        self.movement_mode = 2

        # --- Visual setup ---
        self.base_image = self._build_image()
        self.rect = self.base_image.get_rect(center=(int(self.position.x), int(self.position.y)))
        self.angle = 0
        self.movement_icon_alpha = 255

        # --- condiitons - accessed by level object --- 
        self.move_condition = False

        # --- signals where conditional logic is performed by level object --- 
        self.interact_signal = False

    def _build_image(self) -> pygame.Surface:
        size = max(1, int(16 * settings.scale_total_x))
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        radius = size / 2
        pygame.draw.circle(surface, (60, 120, 220), (size // 2, size // 2), radius)
        return surface

    def _rotate_to_mouse(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos()) - settings.level_offset
        diff = mouse_pos - self.position

        if diff.length() > 0:
            self.direction = diff.normalize()
            # angle_to measures from self -> target, negate because pygame Y-axis is flipped
            self.angle = pygame.Vector2(1, 0).angle_to(self.direction)

    def handle_input(self, event):
        self.handle_movement_mode(event)  
        if event.type == pygame.KEYDOWN and event.key == pygame.K_w:
            self.move_condition = True
        if event.type == pygame.KEYUP and event.key == pygame.K_w:
            self.move_condition = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            # check for interaction - handled by level:
            # send an interaction signal to the Level object, which checks if a interactable is within the player's reachable radius - e.g. 50 pixels from player.center
            self.interact_signal = True
            # level tries interaction, if condition not met, resets interact signal to False     

    def handle_movement_mode(self, event: pygame.event.Event):
        """Call this from your event loop, passing each KEYDOWN event."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LSHIFT, pygame.K_LCTRL):
                transitions = MOVEMENT_TRANSITIONS[self.movement_mode]
                self.movement_mode = transitions[0] if event.key == pygame.K_LSHIFT else transitions[1]

    def move(self, dt: float):
        if self.move_condition:
            self.position += self.direction * SPEED[self.movement_mode] * dt * settings.scale_diagonal
            self.rect.center = (int(self.position.x), int(self.position.y))

    
    def resolve_collision(self, offset: pygame.Vector2):
        self.position += offset
        self.rect.center = (int(self.position.x), int(self.position.y))


    def draw(self, surface: pygame.Surface):
        """Rotate fresh from base_image every draw call — no cumulative degradation."""
        rotated = pygame.transform.rotate(self.base_image, -self.angle)
        rect = rotated.get_rect(center=(int(self.position.x), int(self.position.y)))
        surface.blit(rotated, rect)

    def update(self, dt: float):
        self._rotate_to_mouse()
        self.move(dt)

