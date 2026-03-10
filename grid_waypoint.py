import pygame

# create waypoints all along the level:
class Waypoint:
    def __init__(self, pos: tuple):
        self.pos = pygame.vector2(pos)
        self.neighbours = None
    

class WaypointGraph:
    def __init__(self, level_res: tuple, collision_rects: list, res: int):
        self.waypoints = self._gen_waypoints(level_res, collision_rects, res)
        self.graph = self._build_waypoint_graph()
        self.res = res

    def _gen_waypoints(self, level_res, collision_rects):
        """Generates waypoints with resolution density, i.e. one waypoint every res pixels."""
        # add a buffer of 10 pixels to ignore surrounding walls.
        buffer = 10
        w, h = level_res
        cols = w // self.res
        rows = h // self.res
        wps = []

        for i in range(cols):
            for j in range(rows):
                # create wp_rect, check for collisions, place waypoint in centre if no collision rects
                wp_rect = pygame.Rect((i * self.res) + buffer/2, (j * self.res) + buffer / 2, self.res-buffer, self.res-buffer)
                if wp_rect.collidelist(collision_rects):
                    wps.append(Waypoint(wp_rect.center))
        
        return wps

    def _build_waypoint_graph(self):
        """Builds waypoint graph by connecting neighbouring edges which are up to depth cells apart."""
        # adjacency matrix of waypoints
        wp_dict = {}
        for wp in self.waypoints:
            neighbours = self._check_neighbours(wp)
            wp.neighbours = neighbours
            wp_dict[wp] = neighbours
        return wp_dict # for storage of waypoints
            

    def _check_neighbours(self, waypoint: pygame.Vector2):
        # check waypoint neighbours by considering adjacent cells - check for waypoints res pixels
        # above, below, left and right
        neighbours = []
        # above -> y -= 50
        # below -> y += 50
        # left -> x -= 50
        # right -> x += 50
        # considers diagonals as well
        pts = [waypoint + pygame.Vector2(0, -50), 
               waypoint + pygame.Vector2(0, 50), 
               waypoint + pygame.Vector2(-50, 0), 
               waypoint + pygame.Vector2(50, 0),
               waypoint + pygame.Vector2(50, -50), 
               waypoint + pygame.Vector2(50, 50), 
               waypoint + pygame.Vector2(-50, -50), 
               waypoint + pygame.Vector2(-50, 50),]
        for pt in pts:
            if pt in self.waypoint_points:
                neighbours.append(pt)
        
        return neighbours


    def nearest_waypoint(self, pt):
        # Finds nearest waypoint to a given point
        # waypoints generate from res/2, res/2, incrementing res onwards
        # find nearest x and y coordinate near the arith seq res/2 + n
        x, y = pt.x, pt.y
        x_offset, y_offset = x - self.res/2, y - self.res/2
        col, row = x_offset % self.res, y_offset % self.res
        pos = ((col + 0.5) * self.res, (row + 0.5) * self.res)
        if pos in [wp.pos for wp in self.waypoints]:
            return pos
        
     


