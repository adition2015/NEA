import pygame

# create waypoints all along the level:
class Waypoint:
    def __init__(self, pos: tuple):
        self.pos = pygame.Vector2(pos)
        self.neighbours = None

    def draw(self, surface):
        self.rect = pygame.Rect(self.pos.x, self.pos.y, 1, 1)
        pygame.draw.rect(surface, (255, 255, 0), self.rect)
    

class WaypointGraph:
    def __init__(self, level_res: tuple, collision_rects: list, res: int, door_rects: list):
        self.res = res
        self.collision_rects = collision_rects
        self.door_rects = door_rects

        # enemy variables:
        self.sdv = pygame.Vector2(20, 20) # enemy size displacement  at base_level
        
        # initialisation
        self.waypoints = self._gen_waypoints(level_res)
        self.graph = self._build_waypoint_graph()
        
        

    def _gen_waypoints(self, level_res):
        """Generates waypoints with resolution density, i.e. one waypoint every res pixels."""
        # add a buffer of 10 pixels to ignore surrounding walls.
        buffer = 10
        w, h = level_res
        cols = round(w // self.res)
        rows = round(h // self.res)
        wps = []
        self.door_waypoints = []

        for i in range(cols):
            for j in range(rows):
                # create wp_rect, check for collisions, place waypoint in centre if no collision rects
                wp_rect = pygame.Rect((i * self.res) + buffer/2, (j * self.res) + buffer / 2, self.res-buffer, self.res-buffer)
                if wp_rect.collidelist(self.collision_rects) == -1:
                    wps.append(Waypoint(wp_rect.center))
        
        # special door waypoints:
        # if this is the target, we can call for interaction with door when enemy is 50 pixels away.
        for door in self.door_rects:
            # add wp to center of door rect:
            wps.append(Waypoint(door.center))
            self.door_waypoints.append(door.center)

        print(f"Built {len(wps)} waypoints")
        return wps

    def _build_waypoint_graph(self):
        """Builds waypoint graph by connecting neighbouring edges which are up to depth cells apart."""
        # adjacency matrix of waypoints
        wp_dict = {}
        for wp in self.waypoints:
            neighbours = self._check_neighbours(wp.pos, depth=3)
            wp.neighbours = neighbours
            wp_dict[wp] = neighbours
        
        return wp_dict # for storage of waypoints
            

    def _check_neighbours(self, waypoint: pygame.Vector2, depth: int): # depth is how many res cells outward does it consider.
        # check waypoint neighbours by considering adjacent cells - check for waypoints res pixels
        # above, below, left and right
        neighbours = []
        candidates = []
        # draw a square with side length 2 * self.res, collect waypoints:
        # check if line_blocked, if not, add to neighbours
        range_rect = pygame.Rect(waypoint.x - ((depth*self.res)//2), waypoint.y - ((depth*self.res)//2), depth*self.res, depth*self.res)

        # collect waypoints by area:
        for wp in self.waypoints:
            if range_rect.collidepoint(wp.pos):
                candidates.append(wp)
        
        for wp in candidates:
            if not self._line_blocked(waypoint, wp.pos):
                neighbours.append(wp)
        return neighbours

    def _line_blocked(self, p1: pygame.Vector2, p2: pygame.Vector2):
        blocked = False
        # enemy width = 32 but for extra room, self.sdv accounts for 40:
        for rect in self.collision_rects:
            if rect.clipline(p1 - self.sdv, p2 - self.sdv) or rect.clipline(p1 + self.sdv, p2 + self.sdv): # blocks if enemy at centre of one waypoint is obstructed at all.
                blocked = True
        return blocked

    def nearest_waypoint(self, pt):
        # Finds nearest waypoint to a given point
        # waypoints generate from res/2, res/2, incrementing res onwards
        # find nearest x and y coordinate near the arith seq res/2 + n
        x, y = pt
        x_offset, y_offset = x - self.res/2, y - self.res/2
        col, row = x_offset // self.res, y_offset // self.res
        pos = ((col + 0.5) * self.res, (row + 0.5) * self.res)
        # Find waypoint at or near the calculated position
        for wp in self.waypoints:
            if wp.pos == pygame.Vector2(pos):
                return wp
        
        # Fallback: find closest waypoint by distance if exact match not found
        closest_wp = min(self.waypoints, key=lambda wp: wp.pos.distance_to(pt))
        return closest_wp
        
        
        
     


