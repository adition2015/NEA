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
    def __init__(self, level_res: tuple, collision_rects: list, res: int, buffer: int, door_rects: list, collision_radius=10):
        self.collision_radius = collision_radius
        self.res = res
        self.buffer = buffer
        self.collision_rects = collision_rects
        self.door_rects = door_rects


        # enemy variables:
        # enemy size displacement vector at base_level
        self.sdv= pygame.Vector2()
        
        # initialisation
        self.waypoints = self._gen_waypoints(level_res)
        self.graph = self._build_waypoint_graph()
        
        # debug
        self.scan_rect_count = 0
        self.fall_back_count = 0
        self.ultra_fall_back_count = 0
        

    def _gen_waypoints(self, level_res):
        """Generates waypoints with resolution density, i.e. one waypoint every res pixels."""
        # add a buffer of 10 pixels to ignore surrounding walls.
        w, h = level_res
        cols = round(w // self.res)
        rows = round(h // self.res)
        wps = []
        self.door_waypoints = []

        for i in range(cols):
            for j in range(rows):
                # create wp_rect, check for collisions, place waypoint in centre if no collision rects
                wp_rect = pygame.Rect((i * self.res) + self.buffer/2, (j * self.res) + self.buffer / 2, self.res-self.buffer, self.res-self.buffer)
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
            if wp.neighbours:
                wp_dict[wp] = neighbours
            else:
                self.waypoints.remove(wp)
        
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
            if not self.line_blocked(waypoint, wp.pos):
                neighbours.append(wp)
        return neighbours

    def line_blocked(self, p1: pygame.Vector2, p2: pygame.Vector2):
        p1 = pygame.Vector2(p1)
        p2 = pygame.Vector2(p2)
        diff = p2 - p1

        # Compute perpendicular offset to the travel direction
        if diff.length() > 0:
            perp = pygame.Vector2(-diff.y, diff.x).normalize() * self.collision_radius
        else:
            perp = pygame.Vector2(0, 0)

        # Cast three parallel rays: left edge, centre, right edge
        rays = [
            (p1, p2),
            (p1 + perp, p2 + perp),
            (p1 - perp, p2 - perp),
        ]

        for rect in self.collision_rects:
            for ray_start, ray_end in rays:
                if rect.clipline(ray_start, ray_end):
                    return True
        return False

    def nearest_waypoint(self, pt):
        x, y = pt
        # draw a square rect with 4 * self.res length with center, x, y
        pt_vec = pygame.Vector2(pt)
        scan_rect = pygame.Rect(x - 2*self.res, y - 2*self.res, 4*self.res, 4*self.res)
        candidates = [wp for wp in self.waypoints if (scan_rect.collidepoint(wp.pos) and not self.line_blocked(pt_vec, wp.pos))]
        if candidates:
            self.scan_rect_count += 1
            n_wp = min(candidates, key = lambda wp: wp.pos.distance_to(pt_vec))
            #print(f'{pt_vec}:{n_wp.pos}')
            return n_wp
        self.ultra_fall_back_count += 1
        # Last resort: closest by distance if nothing has LoS (shouldn't normally happen)
        n_wp = min(self.waypoints, key=lambda wp: wp.pos.distance_to(pt_vec))
        #print(f'Last Resort: {pt_vec}:{n_wp.pos}')
        return n_wp
            
        
        
     


