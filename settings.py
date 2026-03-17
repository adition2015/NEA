from utils import *


# --- default window settings ---
DEF_WIDTH, DEF_HEIGHT = 1200, 800
BASE_LEVEL_RES = (1080, 720)


# --- settings class ---

class Settings:
    def __init__(self):
        self.width, self.height = DEF_WIDTH, DEF_HEIGHT
        self.res = (self.width, self.height)
        self.is_fullscreen = True
        self.levelScalar = 0.9
        self.FPS = 120
        self.flags = 0

    def calc_level_res(self):
        self.level_res = level_res(self.levelScalar, (DEF_WIDTH, DEF_HEIGHT))
        self.level_offset = level_offset(self.levelScalar, (DEF_WIDTH, DEF_HEIGHT))
        self.scale_x = self.level_res[0] / BASE_LEVEL_RES[0]
        self.scale_y = self.level_res[1] / BASE_LEVEL_RES[1]
        self.true_level_res = level_res(self.levelScalar, self.res)

        import math
        base_diagonal = math.sqrt(BASE_LEVEL_RES[0]**2 + BASE_LEVEL_RES[1]**2)
        current_diagonal = math.sqrt(self.true_level_res[0]**2 + self.true_level_res[1]**2)
        self.scale_diagonal = current_diagonal / base_diagonal

        self.scale_total_x = self.true_level_res[0] / BASE_LEVEL_RES[0]
        self.scale_total_y = self.true_level_res[1] / BASE_LEVEL_RES[1]

        print(f"scale_x: {self.scale_total_x}, scale_y: {self.scale_total_y}, scale_diagonal: {self.scale_diagonal}")

    def init_resolution(self):
        if self.is_fullscreen:
            self.flags = pygame.FULLSCREEN
            self.res = pygame.display.get_desktop_sizes()[0]
        self.calc_level_res()

    # ------------------------------------------------------------------
    # Render helpers  (base coords  ↔  level-surface pixel coords)
    # Only call these inside draw() methods — never in game logic.
    # ------------------------------------------------------------------

    def to_screen(self, pos) -> pygame.Vector2:
        """Base-res position  →  level-surface pixel coords."""
        return pygame.Vector2(pos[0] * self.scale_total_x,
                              pos[1] * self.scale_total_y)

    def scale_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Base-res Rect  →  level-surface pixel Rect."""
        return pygame.Rect(
            round(rect.x      * self.scale_total_x),
            round(rect.y      * self.scale_total_y),
            round(rect.width  * self.scale_total_x),
            round(rect.height * self.scale_total_y,)
        )

    def from_screen(self, screen_pos) -> pygame.Vector2:
        """Level-surface pixel position  →  base-res coords."""
        return pygame.Vector2(screen_pos[0] / self.scale_total_x,
                              screen_pos[1] / self.scale_total_y)


# --- singleton ---
settings = Settings()
