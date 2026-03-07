from shapely.geometry import box, Point
from shapely.ops import unary_union, triangulate
from settings import *
import math
import heapq

class NavPoly:
    def __init__(self, polygon):
        self.poly = polygon
        self.neighbours = []
        self.center = (polygon.centroid.x, polygon.centroid.y)
    


class NavMesh:
    def __init__(self, level_size: tuple, collision_rects: list):
        level_w, level_h = level_size

        # level polygon to calculate the polygon walkable:
        level_poly = box(0, 0, level_w, level_h)
        # all level walls into polygons to subtract
        obstacles = [
            box(r.left, r.top, r.right, r.bottom)
            for r in collision_rects
        ]

        obstacle_union = unary_union(obstacles)

        # walkable polygon
        walkable = level_poly.difference(obstacle_union)

        triangles = triangulate(walkable) # splits walkable area into triangles

        self.polys = [NavPoly(p) for p in triangles]
        
        self._build_neighbours()

    
    def _build_neighbours(self):
        for p1 in self.polys:
            for p2 in self.polys:

                if p1 == p2:
                    continue

                if p1.poly.touches(p2.poly):
                    p1.neighbours.append(p2)
    
    def find_poly(self, pos):

        point = Point(pos)

        for poly in self.polys:
            if poly.poly.contains(point):
                return poly
        
        return None
    

def distance(a, b):
     
    return math.hypot(a[0] - b[0], a[1] - b[1])

def astar(start_poly, goal_poly):

    open_set = []
    heapq.heappush(open_set, (0, start_poly))

    came_from = {}

    g_score = {start_poly: 0}

    while open_set:

        current = heapq.heappop(open_set)[1]

        if current == goal_poly:

            path = []

            while current in came_from:
                path.append(current)
                current = came_from[current]

            path.append(start_poly)

            path.reverse()

            return path

        for neighbour in current.neighbours:
            
            # calculating travel cost

            tentative = g_score[current] + distance(
                current.center, neighbour.center
            )

            # euclidean distance heuristic

            if neighbour not in g_score or tentative < g_score[neighbour]:

                came_from[neighbour] = current
                g_score[neighbour] = tentative

                f = tentative + distance(
                    neighbour.center, goal_poly.center
                ) # cost of a specific node


                heapq.heappush(open_set, (f, neighbour))

    return None

def find_path(self, nav_mesh, start_pos, end_pos):

    start_poly = nav_mesh.find_poly(start_pos)
    end_poly = nav_mesh.find_poly(end_pos)

    if not start_poly or not end_poly:
        return None
    
    poly_path = astar(start_poly, end_poly)

    if not poly_path:
        return None
    
    return [p.center for p in poly_path]

