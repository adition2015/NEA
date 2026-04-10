from utils import *


# --- default window settings ---
DEF_WIDTH, DEF_HEIGHT = 1200, 800
BASE_LEVEL_RES = (1080, 720)
MIN_MARGIN = 40  # minimum gap from any window edge, in screen pixels

# --- settings class ---

class Settings:
    def __init__(self):
        self.width, self.height = DEF_WIDTH, DEF_HEIGHT
        self.res = (self.width, self.height)
        self.is_fullscreen = True
        self.FPS = 120
        self.flags = 0

    def calc_level_res(self): # Changed so that aspect ratio of level is constant across all resolutions.
        # Maximum usable area after subtracting margins on both sides
        available_w = self.res[0] - 2 * MIN_MARGIN
        available_h = self.res[1] - 2 * MIN_MARGIN

        # Uniform scale: whichever axis is tighter wins.
        # This preserves the BASE_LEVEL_RES aspect ratio exactly.
        scale = min(available_w / BASE_LEVEL_RES[0],
                    available_h / BASE_LEVEL_RES[1])

        level_w = BASE_LEVEL_RES[0] * scale
        level_h = BASE_LEVEL_RES[1] * scale

        # Centre the level in the window
        offset_x = (self.res[0] - level_w) / 2
        offset_y = (self.res[1] - level_h) / 2

        self.true_level_res    = (int(level_w), int(level_h))
        self.true_level_offset = (int(offset_x), int(offset_y))

        # Keep the existing names that the rest of the code uses
        self.scale_total_x = scale
        self.scale_total_y = scale  # same value — no stretching

    def calc_true_res(self):
        self.scale_true_x = self.res[0] / BASE_LEVEL_RES[0]
        self.scale_true_y = self.res[1] / BASE_LEVEL_RES[1]

    def init_resolution(self):
        self.res = (self.width, self.height)
        if self.is_fullscreen:
            self.flags = pygame.FULLSCREEN
            self.res = pygame.display.get_desktop_sizes()[0]
        self.calc_level_res()
        self.calc_true_res()

    def to_screen(self, pos) -> pygame.Vector2:
        """Base-res position  →  level-surface pixel coords."""
        return pygame.Vector2(pos[0] * self.scale_total_x,
                              pos[1] * self.scale_total_y)

    def to_true_screen(self, pos):
        """Base-res position  →  level-surface pixel coords."""
        return pygame.Vector2(pos[0] * self.scale_true_x,
                              pos[1] * self.scale_true_y)

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
