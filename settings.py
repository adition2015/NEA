from utils import *


# --- window settings ---

WIDTH, HEIGHT = 1200, 800
levelScalar = 0.9 # value between zero and 1
FPS = 120

BASE_LEVEL_RES = (1080, 720)

level_res = level_res(levelScalar, (WIDTH, HEIGHT))
level_offset = level_offset(levelScalar, (WIDTH, HEIGHT))
player_pos = tuple(x//2 for x in level_res)

scale_x = level_res[0] / BASE_LEVEL_RES[0]
scale_y = level_res[1] / BASE_LEVEL_RES[1]