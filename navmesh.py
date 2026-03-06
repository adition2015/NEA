from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from settings import *

def rect_to_polygon(rect):
    return box(rect.left, rect.top, rect.right, rect.bottom)

def navmesh(collision_rects):
    w, h = level_res
    margin = 10
    level_poly = box(0, 0, w, h)
    obstacles = [rect_to_polygon(r) for r in collision_rects]
    inflated_obstacles = [o.buffer(margin) for o in obstacles]
    obstacle_union = unary_union(inflated_obstacles)
    walkable = level_poly.difference(obstacle_union)

    navmesh_polys = []

    if walkable.geom_type == "Polygon":
        navmesh_polys.append(list(walkable.exterior.coords))

    elif walkable.geom_type == "MultiPolygon":
        for poly in walkable.geoms:
            navmesh_polys.append(list(poly.exterior.coords))
    
    return navmesh_polys