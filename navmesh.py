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
        self.walkable = level_poly.difference(obstacle_union)

        # Use mapbox_earcut for proper triangulation with holes
        import mapbox_earcut as earcut
        import numpy as np
        from shapely.geometry import Polygon
        
        # Prepare coordinates for earcut
        exterior_coords = np.array(list(self.walkable.exterior.coords)[:-1])  # Remove closing duplicate
        hole_coords = []
        hole_indices = []
        index_offset = len(exterior_coords)
        
        for interior in self.walkable.interiors:
            coords = np.array(list(interior.coords)[:-1])
            hole_coords.append(coords)
            hole_indices.append(index_offset)
            index_offset += len(coords)
        
        # Combine all vertices
        all_vertices = np.vstack([exterior_coords] + hole_coords)
        hole_indices = np.array(hole_indices + [len(all_vertices)], dtype=np.uint32)
        
        # Triangulate
        triangles_indices = earcut.triangulate_float64(all_vertices, hole_indices)
        
        # Convert indices back to triangles
        triangles = []
        for i in range(0, len(triangles_indices), 3):
            p1 = tuple(all_vertices[triangles_indices[i]])
            p2 = tuple(all_vertices[triangles_indices[i+1]])
            p3 = tuple(all_vertices[triangles_indices[i+2]])
            triangle = Polygon([p1, p2, p3])
            triangles.append(triangle)

        clean_tris = []

        self.polys = [NavPoly(p) for p in clean_tris]
        
        self._build_neighbours()

    
    def _build_neighbours(self):
        """Populate each polygon's neighbour list.

        The original implementation treated any two triangles whose borders
        touched as neighbours.  Shapely's ``touches`` returns true for a
        shared *point* as well as a shared edge.  When two triangles only
        meet at a single vertex the straight line between their centres can
        cut straight through a wall or obstacle, which is exactly the bug
        reported by the player - enemies were able to walk through corners
        when the path was calculated via those spurious links.

        To fix this we only create a connection if the intersection of the
        two polygons is a line segment (or collection of segments) with
        positive length.  That guarantees that the navigation graph only
        links polygons that share a real edge, not merely a corner.
        """

        for i, p1 in enumerate(self.polys):
            for p2 in self.polys[i+1:]:
                # skip self and already-checked pairs
                if p1 is p2:
                    continue

                if p1.poly.touches(p2.poly):
                    inter = p1.poly.intersection(p2.poly)
                    # ``inter`` will be a Point when shapes only share a
                    # corner.  we want a LineString/MultiLineString with
                    # non‑zero length.
                    if hasattr(inter, "length") and inter.length > 0:
                        p1.neighbours.append(p2)
                        p2.neighbours.append(p1)

    
    def find_poly(self, pos):

        point = Point(pos)

        # ``contains`` is false if the point lies exactly on the boundary.
        # ``covers`` treats boundary points as part of the polygon, which is
        # generally what we want for pathfinding.
        for poly in self.polys:
            if poly.poly.covers(point):
                return poly
        
        return None
    

def distance(a, b):
     
    return math.hypot(a[0] - b[0], a[1] - b[1])

def astar(nav_mesh, start_poly, goal_poly):

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

def find_path(nav_mesh, start_pos, end_pos):

    start_poly = nav_mesh.find_poly(start_pos)
    end_poly = nav_mesh.find_poly(end_pos)

    if not start_poly or not end_poly:
        # print("No path: start or end position is outside the navmesh.")
        return None
    
    poly_path = astar(nav_mesh, start_poly, end_poly)

    if not poly_path:
        return None
    
    return [pygame.Vector2(p.center) for p in poly_path]

