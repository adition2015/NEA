import pygame
from settings import settings

# All speeds are in base units per second (base res = 1080×720).
SPEED = {1: 75, 2: 125, 3: 175}

MOVEMENT_TRANSITIONS = {
    1: (3, 2),
    2: (3, 1),
    3: (2, 1),
}

NOISE_LEVELS = {
    1: 80,      # sneak:  sqrt(80/1)   ≈ 89px detectable, never directable
    2: 40000,   # walk:   sqrt(40000/1) = 200px detectable, sqrt(40000/2) ≈ 141px directable
    3: 160000   # run:    sqrt(160000/1) = 400px detectable, sqrt(160000/2) ≈ 283px directable
}


class Player(pygame.sprite.Sprite):
    def __init__(self, position: pygame.Vector2, direction: pygame.Vector2):
        super().__init__()
        self.position  = pygame.Vector2(position)   # BASE coords
        self.direction = pygame.Vector2(direction)
        self.movement_mode = 2
        self.speed_mult = 1
        self.speed = 0


        # --- combat ---
        self.health = 100
        self.attack_range = 25 # BASE coords
        self.attack_cooldown = 0.5 # seconds
        self.dead = False

        # --- hiding ---
        self.last_pos = None
        self.hidden = False
        self.carrying_body = False
        self._body = None # stores interactable object

        # --- visual ---
        self._colour = (60, 120, 220)
        self.base_image = self._build_image()

        
        self.angle = 0
        self.movement_icon_alpha = 255

        # --- flags / signals ---
        self.move_condition  = False
        self.interact_signal = False
        self.attack_signal = False
        self.drop_signal = False
        self.noise_signal = 0


    def _build_image(self) -> pygame.Surface:
        # Image is built at screen pixel size so it looks correct on the
        # level surface — this is the ONE place scale touches player setup.
        self.collision_radius = 10
        size = max(1, int(self.collision_radius * 2 * settings.scale_total_x))
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, self.colour, (size // 2, size // 2), size // 2)
        self.rect = pygame.Rect(0, 0, self.collision_radius * 2, self.collision_radius * 2)
        self.rect.center = (int(self.position.x), int(self.position.y))
        return surface

    def _rotate_to_mouse(self):
        # mouse → screen → level surface → base coords
        mouse_screen = pygame.Vector2(pygame.mouse.get_pos())
        mouse_level  = mouse_screen - pygame.Vector2(settings.true_level_offset)
        mouse_base   = settings.from_screen(mouse_level)

        diff = mouse_base - self.position
        if diff.length() > 0:
            self.direction = diff.normalize()
            self.angle = pygame.Vector2(1, 0).angle_to(self.direction)

    def handle_input(self, event):
        self.handle_movement_mode(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_w: # confirms movement - have to hold to move
            self.move_condition = True
        if event.type == pygame.KEYUP and event.key == pygame.K_w: # confirms stopping movement - have to release to stop
            self.move_condition = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.interact_signal = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            self.drop_signal = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.mouse.get_pressed()[0]:
                self.attack()
        

    def handle_movement_mode(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LSHIFT, pygame.K_LCTRL):
                transitions = MOVEMENT_TRANSITIONS[self.movement_mode]
                self.movement_mode = transitions[0] if event.key == pygame.K_LSHIFT else transitions[1]
            if self.carrying_body and self.movement_mode == 3:
                self.movement_mode = 2
    

    def move(self, dt: float):
        self.noise_signal = NOISE_LEVELS[self.movement_mode] if self.move_condition else 0
        if self.move_condition:
            # All arithmetic in base coords — no scale needed here.
            self.speed = SPEED[self.movement_mode]
            self.position += self.direction * self.speed * dt * self.speed_mult
            self.rect.center = (int(self.position.x), int(self.position.y))


    def attack(self):
        # produces attack signal
        if not self.carrying_body and self.attack_cooldown <= 0:
            self.attack_signal = True
            self.attack_cooldown = 0.5
        # level reads this in handle_player_attacks and verifies whether attack is successful        
    

    def resolve_collision(self, offset: pygame.Vector2):
        self.position += offset
        self.rect.center = (int(self.position.x), int(self.position.y))

    @property   
    def colour(self):
        return self._colour

    @colour.setter
    def colour(self, value):
        self._colour = value
        if hasattr(self, 'base_image'):  # guard for __init__ order
            self.base_image = self._build_image()

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        self._body = value
        if hasattr(self, 'base_image'):
            self.base_image = self._build_image()
    def draw(self, surface: pygame.Surface):
        rotated = pygame.transform.rotate(self.base_image, -self.angle)
        # Only here do we scale: convert base position → level-surface pixels.
        screen_pos = settings.to_screen(self.position)
        rect = rotated.get_rect(center=(int(screen_pos.x), int(screen_pos.y)))
        surface.blit(rotated, rect)

    def update(self, dt: float):
        if self.health > 0:
            self._rotate_to_mouse()
            self.move(dt)
            self.attack_cooldown = min(0, self.attack_cooldown - dt)
        else:
            self.dead = True
            self.colour = (20, 20, 20)
        
