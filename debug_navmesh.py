from shapely.geometry import box
from shapely.ops import unary_union, triangulate
from settings import *
from utils import load_level

lvl = load_level(1)

scale_x = level_res[0] / BASE_LEVEL_RES[0]
scale_y = level_res[1] / BASE_LEVEL_RES[1]

# load collision rects
# create pygame.Rect-like objects for NavMesh
import pygame
collision_rects=[pygame.Rect(
        int(x * scale_x),
        int(y * scale_y),
        int(w * scale_x),
        int(h * scale_y)
    ) for x,y,w,h in lvl['walls']]

# also make shapely versions for geometry testing
collision_boxes=[box(r.left, r.top, r.right, r.bottom) for r in collision_rects]

level_w, level_h = level_res
level_poly = box(0,0,level_w,level_h)
obstacle_union=unary_union(collision_boxes)
walkable = level_poly.difference(obstacle_union)
triangles=triangulate(walkable)
print('raw triangles count', len(triangles))
for i,t in enumerate(triangles):
    if t.intersection(obstacle_union).area > 1e-6:
        print('triangle overlaps obstacle area', i)

# now use NavMesh class
from navmesh import NavMesh
# build mesh from walls only (doors are intentionally ignored)
static_walls = [pygame.Rect(r) for r in collision_rects]  # collision_rects all look like rects
nav = NavMesh(level_res, static_walls)
print('navmesh polygons', len(nav.polys))
for idx,p in enumerate(nav.polys):
    print(f"poly {idx} centre {p.center} neighbours {len(p.neighbours)}")
    for n in p.neighbours:
        print(f"   -> {n.center}")
