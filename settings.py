from utils import *


# --- default window settings ---
DEF_WIDTH, DEF_HEIGHT = 1200, 800 # default
BASE_LEVEL_RES = (1080, 720)


# --- settings class ---

class Settings:
    def __init__(self):
        self.width, self.height = DEF_WIDTH, DEF_HEIGHT
        self.res = (self.width, self.height)
        self.is_fullscreen = False
        self.levelScalar = 0.9
        self.FPS = 120
        self.flags = 0 # integer needed as error pops up with none.


    def calc_level_res(self):
        self.level_res = level_res(self.levelScalar, (DEF_WIDTH, DEF_HEIGHT))
        self.level_offset = level_offset(self.levelScalar, (DEF_WIDTH, DEF_HEIGHT))
        self.scale_x = self.level_res[0] / BASE_LEVEL_RES[0]
        self.scale_y = self.level_res[1] / BASE_LEVEL_RES[1]
        self.true_level_res = level_res(self.levelScalar, self.res)

        
        
        # Calculate diagonal scale factor for sprites
        # Uses the ratio of diagonals between actual and base resolution
        import math
        base_diagonal = math.sqrt(BASE_LEVEL_RES[0]**2 + BASE_LEVEL_RES[1]**2)
        current_diagonal = math.sqrt(self.true_level_res[0]**2 + self.true_level_res[1]**2)
        self.scale_diagonal = current_diagonal / base_diagonal
        
        self.scale_total_x = self.true_level_res[0] / BASE_LEVEL_RES[0]
        self.scale_total_y = self.true_level_res[1] / BASE_LEVEL_RES[1]
        
        print(f"scale_x: {settings.scale_total_x}, scale_y: {settings.scale_total_y}, scale_diagonal: {settings.scale_diagonal}")

    def init_resolution(self):
        if self.is_fullscreen:
            self.flags = pygame.FULLSCREEN
            self.res = pygame.display.get_desktop_sizes()[0]
            print(self.res)
        self.calc_level_res()


# --- settings instance
settings = Settings()

