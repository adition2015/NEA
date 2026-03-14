import pygame
from player import Player
from enemy import Enemy
from settings import *
from utils import draw_debug
from grid_waypoint import *
from pathfinding import distance, a_star
# Links:
"https://www.youtube.com/watch?v=UT_tKPLejyU" # pygame layers for drawing on screen


def scale_rect(x, y, w, h):
    return (
        int(x * settings.scale_x),
        int(y * settings.scale_y),
        int(w * settings.scale_x),
        int(h * settings.scale_y)
    )

class Level:
    def __init__(self, ID, data):
        player_pos = (BASE_LEVEL_RES[0] // 2 * settings.scale_total_x, BASE_LEVEL_RES[1] // 2 * settings.scale_total_y)
        self.ID = ID

        self.surface = pygame.Surface(settings.true_level_res, pygame.SRCALPHA)
        self.walls = []
        self.doors = []
        self.hiding_spots = []
        self.enemies = []
        self._load_level(data)

        self.collision_rects = [wall.rect for wall in self.walls]
        self.static_rects = self.collision_rects.copy()
        self.interactables = [door for door in self.doors] + [h for h in self.hiding_spots]
        self.door_rects = [door.rect for door in self.doors]

        # Replace the WaypointGraph line in __init__:
        self.graph = WaypointGraph(
            BASE_LEVEL_RES,
            self.base_static_rects,
            50,   # base-res cell size, no scale factor
            10,   # base-res buffer
            self.base_door_rects    
        )

        connected = [wp for wp in self.graph.waypoints if wp.neighbours]
        print(f"Waypoints with neighbours: {len(connected)} / {len(self.graph.waypoints)}")


        for door in self.doors:
            door.interact(self.collision_rects)

        self.player = Player(
                             position=pygame.Vector2(player_pos),
                             direction=pygame.Vector2(0, -1)
                             )

        """self.enemies = [
            Enemy((100 * settings.scale_total_x, 100 * settings.scale_total_y), (0, 0), [(p[0] * settings.scale_total_x, p[1] * settings.scale_total_y) for p in [(100, 100), (100, 200), (200, 100), (400, 400)]]),
            Enemy((600 * settings.scale_total_x, 600 * settings.scale_total_y), (0, 0), [(p[0] * settings.scale_total_x, p[1] * settings.scale_total_y) for p in [(600, 600), (400, 600), (800, 100), (400, 100)]])
            #Enemy((200, 200), (0, 0), [(200, 200), (300, 200), (200, 600), (900, 400)]),
            #Enemy((500, 600), (0, 0), [(500, 600), (200, 100), (700, 100), (100, 500)])
        ]"""

        self.precalculate_patrol_path()
        print(f'{self.graph.scan_rect_count}/{self.graph.fall_back_count}/{self.graph.ultra_fall_back_count}')
        self.cone_surface = pygame.Surface(settings.true_level_res).convert()
        self.cone_temp = pygame.Surface(settings.true_level_res).convert()
        self.cone_update_interval = 50  # ms between cone redraws (= 20 FPS)
        self.cone_timer = 0

    def update(self, dt):
        self.cone_timer += dt * 1000
        self.player.update(dt)
        self._resolve_collisions()
        self.handle_interaction()
        self.check_enemy_interactions()
        self.update_vision_cones(dt)
        for i in self.enemies:
            i.update(dt)

    def draw(self, screen, fps):
        self.surface.fill((20, 20, 20))

        for i in self.doors:
            i.draw(self.surface)

        # draw debug waypoints
        for wp in self.graph.waypoints:
            wp.draw(self.surface)
        # Draw enemy paths for debugging
        self.draw_enemy_paths()
        # debug collision rects:
        #for rect in self.collision_rects:
        #   pygame.draw.rect(self.surface, (0, 255, 0), rect, 2)

        self.player.draw(self.surface)

        for i in self.enemies:
            i.draw(self.surface)
        if self.cone_timer >= self.cone_update_interval:
            self.draw_vision_cones()
            self.cone_timer = 0
        self.surface.blit(self.cone_surface, (0, 0), special_flags=pygame.BLEND_ADD)

        for i in self.walls:
            i.draw(self.surface)

        

        # draw overlays
        self.draw_icons()
        screen.blit(self.surface, settings.level_offset)

        draw_debug(screen, {
            "cursor_pos":  self.relative_cursor_pos(),
            "movement_mode": self.player.movement_mode,
            "fps": round(fps),
            "enemy_states" : [f"{i}:{enemy.state}" for i, enemy in enumerate(self.enemies)],
            "enemy_directions": [f"{i}:{enemy.direction}" for i, enemy in enumerate(self.enemies)]
        }, size=16)

    # cursor pos relative to level:
    def relative_cursor_pos(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        relative_pos = mouse_pos - settings.level_offset
        return tuple(relative_pos)


    def draw_enemy_paths(self):
        """Draw lines representing the paths enemies are following for debugging."""
        for enemy in self.enemies:
            # Draw patrol path in green
            if len(enemy.patrol_path) > 1:
                points = [(int(p.x), int(p.y)) for p in enemy.patrol_path]
                pygame.draw.lines(self.surface, (0, 255, 0), False, points, 3)
                # Draw small circles at waypoints
                for p in enemy.patrol_path:
                    pygame.draw.circle(self.surface, (0, 255, 0), (int(p.x), int(p.y)), 4)
            
            # Draw search path in yellow
            if len(enemy.search_path) > 1:
                points = [(int(p.x), int(p.y)) for p in enemy.search_path]
                pygame.draw.lines(self.surface, (255, 255, 0), False, points, 3)
                for p in enemy.search_path:
                    pygame.draw.circle(self.surface, (255, 255, 0), (int(p.x), int(p.y)), 4)
            
            # Draw return path in blue
            if len(enemy.return_path) > 1:
                points = [(int(p.x), int(p.y)) for p in enemy.return_path]
                pygame.draw.lines(self.surface, (0, 0, 255), False, points, 3)
                for p in enemy.return_path:
                    pygame.draw.circle(self.surface, (0, 0, 255), (int(p.x), int(p.y)), 4)

    def _load_level(self, data: dict):
        self.base_static_rects = []
        self.base_door_rects   = []

        for (x, y, w, h) in data.get("walls", []):
            self.base_static_rects.append(pygame.Rect(x, y, w, h))
            scaled_x = x * settings.scale_total_x
            scaled_y = y * settings.scale_total_y
            scaled_w = w * settings.scale_total_x
            scaled_h = h * settings.scale_total_y
            self.walls.append(Wall(scaled_x, scaled_y, scaled_w, scaled_h))

        for (x, y, o) in data.get("doors", []):
            bw = 5 if o == 0 else 50
            bh = 50 if o == 0 else 5
            self.base_door_rects.append(pygame.Rect(x, y, bw, bh))
            scaled_x = x * settings.scale_total_x
            scaled_y = y * settings.scale_total_y
            self.doors.append(Door(scaled_x, scaled_y, o))

        for (x, y) in data.get("hiding_spots", []):
            scaled_x = x * settings.scale_total_x
            scaled_y = y * settings.scale_total_y
            self.hiding_spots.append(HidingSpot(scaled_x, scaled_y))

        for (position, direction, patrol_points) in data.get("enemies", []):
            scaled_position = (position[0] * settings.scale_total_x, position[1] * settings.scale_total_y)
            self.enemies.append(Enemy(scaled_position, direction, patrol_points)) 

    

    def check_interaction(self):
        if self.player.interact_signal == True:
            target_candidates = {}
            for i in self.interactables:
                distance_vec = self.player.position - i.rect.center
                if distance_vec.magnitude() <= 50 * settings.scale_total_x:
                    target_candidates[i] = distance_vec.magnitude()
            if len(target_candidates) > 0:
                key = min(target_candidates, key=target_candidates.get)
                self.player.interact_signal = False
                return key


    def check_enemy_interactions(self):
        for enemy in self.enemies:
            for door in self.doors:
                dist = pygame.Vector2(door.rect.center).distance_to(enemy.position)
                if dist < 40 * settings.scale_total_x and not door.is_open:
                    door.interact(self.collision_rects)
                elif dist > 50 * settings.scale_total_x and dist < 60 * settings.scale_total_x and door.is_open:
                    door.interact(self.collision_rects)

    def check_player_LoS(self, enemy):
        if len(enemy.vision_points) < 3:
            return False
        return self._point_in_polygon(self.player.position, enemy.vision_points)


    def _point_in_polygon(self, point: pygame.Vector2, polygon: list) -> bool:
        """Ray casting algorithm — counts how many polygon edges a ray crosses."""
        x, y = point
        inside = False
        n = len(polygon)
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside
    
    def _to_base(self, pos: pygame.Vector2) -> pygame.Vector2:
        """Convert a scaled screen position back to base-res space."""
        return pygame.Vector2(
            pos.x / settings.scale_total_x,
            pos.y / settings.scale_total_y
        )

    def _scale_path(self, path: list) -> list:
        """Scale an A* path (base-res Vector2 list) up to screen space."""
        if not path:
            return []
        return [
            pygame.Vector2(p.x * settings.scale_total_x, p.y * settings.scale_total_y)
            for p in path
        ]

    def update_vision_cones(self, dt):
        for enemy in self.enemies:
            if self.check_player_LoS(enemy):
                # Player is visible — pass the live position; transition_chase
                # updates last_seen only here, so it's always the real sighting.
                enemy.transition_chase(self.player.position)
                enemy.LoS_timer = 0.5
            elif enemy.state == "chase":
                # LoS just broke while chasing — compute A* path to last_seen
                # and hand it to the enemy to begin the search phase.
                # need to add a half second for the enemy to regain sight of the player to stop player avoiding via moving behind enemy.
                # to make enemy feel more responsive and intelligent, the enemy should know the player's position for 0.5 seconds after losing sight.
                if enemy.LoS_timer <= 0 or self.graph.line_blocked(self._to_base(enemy.position), self._to_base(self.player.position)):
                    # this ensures the enemy is not chasing the player through a wall for 0.5 seconds, but still can react to player.
                    search_path = self._compute_search_path(enemy)
                    enemy.transition_search(search_path)
                else:
                    enemy.transition_chase(self.player.position)
                enemy.LoS_timer -= dt
                
            elif enemy.state == "returning_to_patrol":
                # Compute return path if not already set
                if not enemy.return_path:
                    return_path = self._compute_return_path(enemy)
                    enemy.set_return_path(return_path)
            # "patrol" or "search" with no LoS: do nothing.
            # The enemy calls transition_patrol() itself when the search
            # path is exhausted without re-acquiring the player.

    def _compute_search_path(self, enemy) -> list:
        """
        A* from the enemy's current position to its last confirmed player
        sighting. Returns a list[Vector2] or [] if pathfinding fails.
        Lives here because only Level has access to the waypoint graph.
        """
        if enemy.last_seen is None:
            return []
        start_wp = self.graph.nearest_waypoint(self._to_base(enemy.position))
        end_wp   = self.graph.nearest_waypoint(self._to_base(enemy.last_seen))
        path = a_star(start_wp, end_wp)
        return self._scale_path(path) if path else []
    
    def _compute_return_path(self, enemy) -> list:
        """
        A* from the enemy's current position to the nearest point on its patrol path.
        Returns a list[Vector2] or [] if pathfinding fails.
        """
        if not enemy.patrol_path:
            return []
        # patrol_path is already in screen space, so distance comparisons are fine
        nearest_pt = min(enemy.patrol_path, key=lambda pt: enemy.position.distance_to(pt), default=None)
        if nearest_pt is None:
            return []
        start_wp = self.graph.nearest_waypoint(self._to_base(enemy.position))
        end_wp   = self.graph.nearest_waypoint(self._to_base(nearest_pt))
        path = a_star(start_wp, end_wp)
        return self._scale_path(path) if path else []

    def handle_interaction(self):
        interactable = self.check_interaction()
        if interactable:
            interactable.interact(self.collision_rects)

    def handle_input(self, event):
        self.player.handle_input(event)

    def _resolve_collisions(self):
        for rect in self.collision_rects:
            if self.player.rect.colliderect(rect):
                offset = self._calculate_pushout(self.player.rect, rect)
                self.player.resolve_collision(offset)
        for rect in self.collision_rects:
            for enemy in self.enemies:
                if enemy.rect.colliderect(rect):
                    offset = self._calculate_pushout(enemy.rect, rect)
                    enemy.resolve_collision(offset)

    def _calculate_pushout(self, player_rect: pygame.Rect, wall_rect: pygame.Rect):
        overlap_left   = wall_rect.right  - player_rect.left
        overlap_right  = player_rect.right - wall_rect.left
        overlap_top    = wall_rect.bottom - player_rect.top
        overlap_bottom = player_rect.bottom - wall_rect.top

        min_x = overlap_left  if overlap_left  < overlap_right  else -overlap_right
        min_y = overlap_top   if overlap_top   < overlap_bottom else -overlap_bottom

        if abs(min_x) < abs(min_y):
            return pygame.Vector2(min_x, 0)
        else:
            return pygame.Vector2(0, min_y)

    def precalculate_patrol_path(self):
        for enemy in self.enemies:
            enemy.waypoints = []
            for pt in enemy.patrol_points:          # base-res, no conversion needed
                enemy.waypoints.append(self.graph.nearest_waypoint(pt))
            enemy.precalculate_patrol_path()
            enemy.patrol_path = self._scale_path(enemy.patrol_path)   # ← scale once here
            if enemy.patrol_path:
                enemy.set_direction(enemy.patrol_path[enemy.patrol_ID])

    def draw_vision_cones(self):
        self.cone_surface.fill((0, 0, 0))
        for enemy in self.enemies:
            enemy.vision_points = enemy.build_vision_cone(self.collision_rects)
            if len(enemy.vision_points) >= 3:
                self.cone_temp.fill((0, 0, 0))
                pygame.draw.polygon(self.cone_temp, enemy.vision_cone_colour, enemy.vision_points)
                self.cone_surface.blit(self.cone_temp, (0, 0),
                                       special_flags=pygame.BLEND_ADD)
    
    def draw_icons(self):
        player_states = ["sneak", "walk", "run"]
        state = player_states[self.player.movement_mode - 1]
        icon = pygame.image.load(os.path.join("assets", "icons", f"{state}.png")).convert_alpha()
        icon = pygame.transform.scale(icon, (32, 32))
        # draw on top right of surface
        self.player.movement_icon_alpha = ((self.player.movement_icon_alpha - 5) % 255)
        icon.set_alpha(self.player.movement_icon_alpha)
        self.surface.blit(icon, (settings.true_level_res[0] - icon.get_width()*1.5, icon.get_height() * 0.5))
        


# fix nav polygon so that it takes points in order that are connected then form a polygon

class Wall:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = self.build_wall()


    def build_wall(self):
        return pygame.rect.Rect(self.x, self.y, self.width, self.height)


    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), self.rect)

class Door:
    def __init__(self, x, y, o: int):
        self.is_open = True
        self.width = 5 if o == 0 else 50
        self.height = 50 if o == 0 else 5
        self.width *= settings.scale_total_x
        self.height *= settings.scale_total_y
        self.rect = pygame.rect.Rect(x, y, self.width, self.height)

    def open(self, collision_rects):
        if not self.is_open:
            self.is_open = True
            try:
                collision_rects.remove(self.rect)
            except ValueError:
                print("Door not added to collision_rects")
            return collision_rects


    def close(self, collision_rects):
        if self.is_open:
            self.is_open = False
            collision_rects.append(self.rect)
            return collision_rects

    def interact(self, collision_rects):
        if self.is_open:
            self.close(collision_rects)
        else:
            self.open(collision_rects)

    def draw(self, surface):
        colour = (113, 93, 76) if self.is_open else (75, 57, 41)
        pygame.draw.rect(surface, colour, self.rect)

class HidingSpot:
    def __init__(self, x, y):
        self.width, self.height = 32 * settings.scale_total_x, 32 * settings.scale_total_y
        self.rect = pygame.rect.Rect(x, y, self.width, self.height)
        self.in_use = False
    
    def draw(self, surface):
        colour = (0, 128, 128) if not self.in_use else (102, 178, 178)
        pygame.draw.rect(surface, colour, self.rect)

    

    
