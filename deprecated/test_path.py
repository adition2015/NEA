import sys
sys.path.insert(0, '.')
from level import Level
from utils import load_level
from deprecated.navmesh import find_path
import pygame

data = load_level(1)
level = Level(1, data)
nav = level.navmesh
start=(100,100)
end=(300,400)
path=find_path(nav,start,end)
print('Path length:', len(path) if path else None)
print('First points:', path[:5] if path else None)
