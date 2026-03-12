from utils import *


# --- default window settings ---
DEF_WIDTH, DEF_HEIGHT = 1200, 800 # default
BASE_LEVEL_RES = (1080, 720)


# --- settings class ---

class Settings:
    def __init__(self):
        self.width, self.height = DEF_WIDTH, DEF_HEIGHT
        self.res = (self.width, self.height)
        self.is_fullscreen = True
        self.levelScalar = 0.9
        self.FPS = 120
        self.flags = None


    def calc_level_res(self):
        self.level_res = level_res(self.levelScalar, self.res)
        self.level_offset = level_offset(self.levelScalar, self.res)
        self.scale_x = self.level_res[0] / BASE_LEVEL_RES[0]
        self.scale_y = self.level_res[1] / BASE_LEVEL_RES[1]
        
        # Calculate diagonal scale factor for sprites
        # Uses the ratio of diagonals between actual and base resolution
        import math
        base_diagonal = math.sqrt(BASE_LEVEL_RES[0]**2 + BASE_LEVEL_RES[1]**2)
        current_diagonal = math.sqrt(self.level_res[0]**2 + self.level_res[1]**2)
        self.scale_diagonal = current_diagonal / base_diagonal
    
    def init_resolution(self):
        if self.is_fullscreen:
            self.flags = pygame.FULLSCREEN|pygame.HWSURFACE 
            self.res = pygame.display.get_desktop_sizes()[0]
        self.calc_level_res()


# --- settings instance
settings = Settings()

