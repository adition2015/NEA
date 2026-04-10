import pygame, os, random
from player import Player
from enemy import Enemy
from settings import settings, BASE_LEVEL_RES
from utils import draw_debug, resource_path
from grid_waypoint import WaypointGraph
from pathfinding import distance, a_star
from noise import NoiseEvent

DETECTABLE_THRESHOLD = 1.0
DIRECTABLE_THRESHOLD = 2.0
SUSPICION_CONVERSION_CONSTANT = 0.5
SUSPICION_DECAY_CONSTANT = 5  # per second
SUSPICION_THRESHOLD = 50      # must be reached for directable noise to alert
SUSPICION_CAP = 100.0
SUSPICION_MULTIPLIER_CAP = 3.0
 # pixel conversion factor for isq in noise propagation.

LEVEL_COLOUR = (40, 40, 40)

class Level:
    def __init__(self, ID, data):
        self.ID = ID

        self.surface = pygame.Surface(settings.true_level_res, pygame.SRCALPHA)
        self.walls        = []
        self.doors        = []
        self.hiding_spots = []
        self.enemies      = []
        self.dead_enemies = []
        self._load_level(data)

        # All rects are now in BASE coords.
        self.collision_rects = [wall.rect for wall in self.walls]
        self.static_rects    = self.collision_rects.copy()
        self.door_rects      = [door.rect for door in self.doors]
        self.interactables   = list(self.doors) + list(self.hiding_spots)

        # WaypointGraph works in BASE coords — pass base-space rects directly.
        self.graph = WaypointGraph(
            BASE_LEVEL_RES,
            self.static_rects,
            50,     # cell size in base units
            10,     # buffer in base units
            self.door_rects,
        )

        connected = [wp for wp in self.graph.waypoints if wp.neighbours]
        print(f"Waypoints with neighbours: {len(connected)} / {len(self.graph.waypoints)}")
        
        # Open all doors at level start (adds them back to collision once closed).
        for door in self.doors:
            door.interact(self.collision_rects)

        # migrated player data to level_n.json
        player_data = data.get("player", {})
        spawn_pos = pygame.Vector2(player_data.get("position", 
                           [BASE_LEVEL_RES[0]//2, BASE_LEVEL_RES[1]//2]))
        spawn_dir = pygame.Vector2(player_data.get("direction", [0, -1]))
        self.player = Player(position=spawn_pos, direction=spawn_dir)

        self.precalculate_patrol_path()
        print(f'{self.graph.scan_rect_count}/{self.graph.fall_back_count}/{self.graph.ultra_fall_back_count}')

        self.cone_surface = pygame.Surface(settings.true_level_res).convert()
        self.cone_temp    = pygame.Surface(settings.true_level_res).convert()
        self.cone_update_interval = 50   # ms between cone redraws
        self.cone_timer   = 0

        self.noise_events = []
        self.noise_surface = pygame.Surface(settings.true_level_res).convert()
        self.noise_temp = pygame.Surface(settings.true_level_res).convert()

        self.shot_surface = pygame.Surface(settings.true_level_res).convert()
        self.shot_timer = 0.25

        self.level_failed = False
        self.level_completed = False

    # ------------------------------------------------------------------
    # Core loop
    # ------------------------------------------------------------------

    def update(self, dt):
        if not self.player.dead:
            self.cone_timer += dt * 1000
            self.shot_timer -= dt
            self.player.update(dt)
            self._resolve_collisions()
            self.handle_interaction()
            self.check_enemy_interactions()
            self.handle_attack()
            self.handle_enemy_attack()
            self.update_vision_cones(dt)  
            self._process_noise(dt)  
            for enemy in self.enemies:
                enemy.update(dt)
            for dead_enemy in self.dead_enemies:
                dead_enemy.update(dt)
                if dead_enemy.carried:
                    dead_enemy.position = pygame.Vector2(self.player.position)
                    dead_enemy.rect.center = (int(dead_enemy.position.x), int(dead_enemy.position.y))
            if self.dead_enemies and not self.enemies:
                self.level_completed = True
        else:
            self.level_failed = True
                    

    def draw(self, screen, fps):
        self.surface.fill(LEVEL_COLOUR)

        for door in self.doors:
            door.draw(self.surface)

        # Debug waypoints — convert base pos to screen for drawing.
        for wp in self.graph.waypoints:
            sx = int(wp.pos.x * settings.scale_total_x)
            sy = int(wp.pos.y * settings.scale_total_y)
            # pygame.draw.rect(self.surface, (255, 255, 0), pygame.Rect(sx, sy, 1, 1)) # debug

        # self.draw_enemy_paths() # debug
        self.draw_noise_circles()
        self.surface.blit(self.noise_surface, (0, 0), special_flags=pygame.BLEND_ADD)

        for wall in self.walls:
            wall.draw(self.surface)
        for spot in self.hiding_spots:
            spot.draw(self.surface)
        for dead_enemy in self.dead_enemies: # static object: drawn below players and enemies
            dead_enemy.draw(self.surface)

        self.player.draw(self.surface)

        for enemy in self.enemies:
            enemy.draw(self.surface)


        if self.cone_timer >= self.cone_update_interval:
            self.draw_vision_cones()
            self.cone_timer = 0
        self.surface.blit(self.cone_surface, (0, 0), special_flags=pygame.BLEND_ADD)

        self.draw_icons() 
        self.draw_shots(self.shot_surface)
        self.surface.blit(self.shot_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        draw_debug(screen, {
            "Level":f'{self.ID}'
        }, pos=(settings.res[0] // 2 - 60, settings.res[1] - 25))
        draw_debug(screen, 
            {"Health": f"{self.player.health}"},
            pos=(settings.res[0] - 120, 10))
        screen.blit(self.surface, settings.true_level_offset)

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------


    def _load_level(self, data: dict):
        """All objects are created in BASE coords — no scaling at load time."""
        for (x, y, w, h) in data.get("walls", []):
            self.walls.append(Wall(x, y, w, h))

        for (x, y, o) in data.get("doors", []):
            self.doors.append(Door(x, y, o))

        for (x, y) in data.get("hiding_spots", []):
            self.hiding_spots.append(HidingSpot(x, y))

        for (position, direction, patrol_points) in data.get("enemies", []):
            # position and patrol_points come from JSON already in base coords
            self.enemies.append(Enemy(position, direction, patrol_points))

    # ------------------------------------------------------------------
    # Cursor
    # ------------------------------------------------------------------

    def relative_cursor_pos(self):
        """Returns cursor position in BASE coords for debug display."""
        mouse_screen = pygame.Vector2(pygame.mouse.get_pos())
        mouse_level  = mouse_screen - pygame.Vector2(settings.level_offset)
        return settings.from_screen(mouse_level)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def check_interaction(self):
        if self.player.interact_signal:
            target_candidates = {}
            for i in self.interactables:
                if i != self.player.body:
                    distance_vec = self.player.position - pygame.Vector2(i.rect.center)
                    if distance_vec.magnitude() <= 50:   # base units
                        if isinstance(i, Door) or not self.graph.line_blocked(self.player.position,
                                                        pygame.Vector2(i.rect.center)):
                            target_candidates[i] = distance_vec.magnitude()
            if target_candidates:
                key = min(target_candidates, key=target_candidates.get)
                self.player.interact_signal = False
                return key
        self.player.interact_signal = False
        return False

    def check_enemy_interactions(self):
        for enemy in self.enemies:
            for door in self.doors:
                dist = pygame.Vector2(door.rect.center).distance_to(enemy.position)
                if dist < 40 and not door.is_open:        # base units
                    door.interact(self.collision_rects)
                elif 50 < dist < 60 and door.is_open:     # base units
                    door.interact(self.collision_rects)

    def handle_interaction(self):
        interactable = self.check_interaction()
        if interactable:
            if isinstance(interactable, Door):
                interactable.interact(self.collision_rects)
            elif isinstance(interactable, HidingSpot):
                if self.player.hidden:
                    self._player_unhide()
                elif self.player.carrying_body:
                    self._deposit_body(interactable)
                elif interactable.in_use:
                    self._retrieve_body(interactable)
                else:
                    self._player_hide(interactable)
            elif isinstance(interactable, Enemy):
                if not self.player.carrying_body:
                    self._pick_up_body(interactable)

        if self.player.drop_signal:
            self._drop_body()
            self.player.drop_signal = False

    def _pick_up_body(self, enemy): 
        self.player.body = enemy
        self.player.carrying_body = True
        self.player.colour = (150, 100, 100)
        enemy.carried = True

    def _deposit_body(self, hiding_spot):
        if not hiding_spot.in_use:
            hiding_spot.body = self.player.body
            self.player.body.carried = False
            hiding_spot.body.move_condition = False
            hiding_spot.body.position = pygame.Vector2(hiding_spot.rect.center)
            hiding_spot.body.rect.center = hiding_spot.rect.center                
            hiding_spot.body.colour = (50, 30, 30) 
            hiding_spot.interact()
            self.player.body = None
            self.player.carrying_body = False
            self.player.colour = (60, 120, 220)

    def _retrieve_body(self, hiding_spot):
        self.player.body = hiding_spot.body
        self.player.body.carried = True
        self.player.body.colour = (97, 64, 65)
        hiding_spot.body = None
        hiding_spot.interact()
        self.player.carrying_body = True
        self.player.colour = (150, 100, 100)

    def _player_hide(self, hiding_spot):
        self.player.last_pos = pygame.Vector2(self.player.position)
        self.player.speed_mult = 0
        self.player.colour = (255, 255, 255)
        self.player.position = pygame.Vector2(hiding_spot.rect.center)
        self.player.hidden = True

    def _player_unhide(self):
        self.player.speed_mult = 1
        self.player.colour = (60, 120, 220)
        self.player.position = self.player.last_pos
        self.player.last_pos = None
        self.player.hidden = False
        

    def _drop_body(self):
        if self.player.body:
            self.player.body.carried = False
            self.player.body = None
            self.player.carrying_body = False
            self.player.colour = (60, 120, 220)


    def handle_input(self, event):
        self.player.handle_input(event)

    def handle_attack(self):
        # Handles Player Attack
        if self.player.attack_signal:
            for enemy in self.enemies:
                if self.player.position.distance_squared_to(enemy.position) < self.player.attack_range**2: # removes expensive sqrt
                    if not self.check_player_LoS(enemy): # prevents successful attack when enemy has LoS, may remove when enemy attacks created.
                        enemy.transition_death()
                        self.enemies.remove(enemy)
                        self.dead_enemies.append(enemy)
                        self.interactables.append(enemy) # for player interactions
                        break
        self.player.attack_signal = False # reset to false after handling loop

    def handle_enemy_attack(self):
        for enemy in self.enemies:
            if enemy.shot_target != None:
                if self.player.rect.collidepoint(enemy.shot_target) and not self.graph.line_blocked(enemy.shot_target, enemy.position):
                    self.player.health -= 20
                
        

    # ------------------------------------------------------------------
    # Collision  (everything in BASE coords)
    # ------------------------------------------------------------------

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

    def _calculate_pushout(self, mover_rect: pygame.Rect, wall_rect: pygame.Rect):
        overlap_left   = wall_rect.right   - mover_rect.left
        overlap_right  = mover_rect.right  - wall_rect.left
        overlap_top    = wall_rect.bottom  - mover_rect.top
        overlap_bottom = mover_rect.bottom - wall_rect.top

        min_x = overlap_left  if overlap_left  < overlap_right  else -overlap_right
        min_y = overlap_top   if overlap_top   < overlap_bottom else -overlap_bottom

        return pygame.Vector2(min_x, 0) if abs(min_x) < abs(min_y) else pygame.Vector2(0, min_y)

    # ------------------------------------------------------------------
    # Noise Processing
    # ------------------------------------------------------------------
    def _process_noise(self, dt):
        self.noise_events = []
        if self.player.noise_signal > 0:
            self.noise_events.append(NoiseEvent(self.player.position, self.player.noise_signal))

        for enemy in self.enemies:
            candidate_noise = []
            for event in self.noise_events:
                distance_sq = enemy.position.distance_squared_to(event.position)
                perceived = float('inf') if distance_sq == 0 else event.intensity / distance_sq
                candidate_noise.append(NoiseEvent(event.position, perceived))

            if not candidate_noise:
                self.update_suspicion(enemy, 0, dt)  # still decay
                continue

            target = max(candidate_noise, key=lambda n: n.intensity)
            self.update_suspicion(enemy, target.intensity, dt)

            if target.intensity > DIRECTABLE_THRESHOLD:
                if enemy.suspicion >= SUSPICION_THRESHOLD:  # ← the gate
                    if enemy.last_heard.intensity < target.intensity:
                        enemy.last_heard = target
                        alerted_path = self._compute_alerted_path(enemy)
                        enemy.transition_alerted(target, alerted_path)
            elif target.intensity > DETECTABLE_THRESHOLD and enemy.state != "alerted":
                if not self.graph.line_blocked(target.position, enemy.position): # if the sound is blocked, investigation is not conducted.
                    enemy.transition_investigate(target)

    def update_suspicion(self, enemy, intensity, dt):
        # Decay every frame regardless of noise
        enemy.suspicion = max(0, enemy.suspicion - SUSPICION_DECAY_CONSTANT * dt)

        # Accrue if above detectable threshold
        if intensity > DETECTABLE_THRESHOLD:
            gain = (intensity - DETECTABLE_THRESHOLD) * SUSPICION_CONVERSION_CONSTANT * enemy.suspicion_multiplier
            enemy.suspicion = min(SUSPICION_CAP, enemy.suspicion + gain)
                    
                

    # ------------------------------------------------------------------
    # Patrol path pre-calculation
    # ------------------------------------------------------------------

    def precalculate_patrol_path(self):
        for enemy in self.enemies:
            enemy.waypoints = []
            for pt in enemy.patrol_points:   # base coords from JSON
                enemy.waypoints.append(self.graph.nearest_waypoint(pt))
            enemy.precalculate_patrol_path()
            # patrol_path is already in BASE coords — no scaling needed
            if enemy.patrol_path:
                enemy.set_direction(enemy.patrol_path[enemy.patrol_ID])

    # ------------------------------------------------------------------
    # Vision cones
    # ------------------------------------------------------------------

    def check_player_LoS(self, enemy):
        if not self.player.hidden:
            if len(enemy.vision_points) < 3:
                return False
            return self._point_in_polygon(self.player.position, enemy.vision_points)

    def _point_in_polygon(self, point: pygame.Vector2, polygon: list) -> bool:
        """
        Determines if a point lies inside a polygon using the Ray Casting algorithm.

        Algorithm adapted from W. Randolph Franklin's Point In Polygon implementation:
        https://wrfranklin.org/Research/Short_Notes/pnpoly.html

        The algorithm fires a ray from the test point in one direction and counts
        how many times it intersects with the polygon's edges. An odd number of
        intersections means the point is inside; even means outside.
        """
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

    def update_vision_cones(self, dt):
        for enemy in self.enemies:
            if self.check_player_LoS(enemy):
                enemy.transition_chase(self.player.position)
                enemy.LoS_timer = 0.5
            elif enemy.state == "chase":
                if enemy.LoS_timer <= 0 or self.graph.line_blocked(enemy.position,
                                                                     self.player.position):
                    search_path = self._compute_search_path(enemy)
                    enemy.transition_search(search_path)
                else:
                    enemy.transition_chase(self.player.position)
                enemy.LoS_timer -= dt
            elif enemy.state == "returning_to_patrol":
                if not enemy.return_path:
                    return_path = self._compute_return_path(enemy)
                    enemy.set_return_path(return_path)
            for dead_enemy in self.dead_enemies:
                if self._point_in_polygon(dead_enemy.position, enemy.vision_points):
                    enemy.suspicion_multiplier = min(SUSPICION_MULTIPLIER_CAP, enemy.suspicion_multiplier + 1.0)
                    enemy.suspicion = min(SUSPICION_CAP, enemy.suspicion + 30)  # immediate spike

    def draw_vision_cones(self):
        """Build and draw cones; vision_points stay in BASE coords for LoS tests."""
        self.cone_surface.fill((0, 0, 0))
        for enemy in self.enemies:
            enemy.vision_points = enemy.build_vision_cone(self.collision_rects)
            if len(enemy.vision_points) >= 3:
                # Scale to level-surface pixels only here, for drawing.
                scaled = [
                    (p[0] * settings.scale_total_x, p[1] * settings.scale_total_y)
                    for p in enemy.vision_points
                ]
                colour = enemy.get_vision_cone_colour()
                self.cone_temp.fill((0, 0, 0))
                pygame.draw.polygon(self.cone_temp, colour, scaled)
                self.cone_surface.blit(self.cone_temp, (0, 0),
                                       special_flags=pygame.BLEND_ADD)

    # ------------------------------------------------------------------
    # Pathfinding helpers  (all in BASE coords — no conversion needed)
    # ------------------------------------------------------------------

    def _compute_search_path(self, enemy) -> list:
        if enemy.last_seen is None:
            return []
        start_wp = self.graph.nearest_waypoint(enemy.position)
        end_wp   = self.graph.nearest_waypoint(enemy.last_seen)
        path = a_star(start_wp, end_wp)
        return path if path != None else []   # list[Vector2] in BASE coords
    
    def _compute_alerted_path(self, enemy) -> list:
        if enemy.last_heard is None:
            return []
        start_wp = self.graph.nearest_waypoint(enemy.position)
        end_wp  = self.graph.nearest_waypoint(enemy.last_heard.position)
        path = a_star(start_wp, end_wp)
        return path if path != None else []

    def _compute_return_path(self, enemy) -> list:
        if not enemy.patrol_path:
            return []
        nearest_pt = min(enemy.patrol_path,
                         key=lambda pt: enemy.position.distance_to(pt),
                         default=None)
        if nearest_pt is None:
            return []
        start_wp = self.graph.nearest_waypoint(enemy.position)
        end_wp   = self.graph.nearest_waypoint(nearest_pt)
        path = a_star(start_wp, end_wp)
        return path if path != None else []   # list[Vector2] in BASE coords

    # ------------------------------------------------------------------
    # Debug drawing helpers
    # ------------------------------------------------------------------

    def draw_enemy_paths(self):
        def _scaled_pts(path):
            return [(int(p.x * settings.scale_total_x),
                     int(p.y * settings.scale_total_y)) for p in path]

        for enemy in self.enemies:
            if len(enemy.patrol_path) > 1:
                pts = _scaled_pts(enemy.patrol_path)
                pygame.draw.lines(self.surface, (0, 255, 0), False, pts, 3)
                for p in pts:
                    pygame.draw.circle(self.surface, (0, 255, 0), p, 4)

            if len(enemy.search_path) > 1:
                pts = _scaled_pts(enemy.search_path)
                pygame.draw.lines(self.surface, (255, 255, 0), False, pts, 3)
                for p in pts:
                    pygame.draw.circle(self.surface, (255, 255, 0), p, 4)

            if len(enemy.return_path) > 1:
                pts = _scaled_pts(enemy.return_path)
                pygame.draw.lines(self.surface, (0, 0, 255), False, pts, 3)
                for p in pts:
                    pygame.draw.circle(self.surface, (0, 0, 255), p, 4)
            
            if len(enemy.alerted_path) > 1:
                pts = _scaled_pts(enemy.alerted_path)
                pygame.draw.lines(self.surface, (255, 0, 255), False, pts, 3)
                for p in pts:
                    pygame.draw.circle(self.surface, (255, 0, 255), p, 4)
            

    def draw_icons(self):
        player_states = ["sneak", "walk", "run"]
        state = player_states[self.player.movement_mode - 1]
        icon = pygame.image.load(resource_path(os.path.join("assets", "icons", f"{state}.png"))).convert_alpha()
        icon = pygame.transform.scale(icon, settings.to_screen((32, 32)))
        self.player.movement_icon_alpha = (self.player.movement_icon_alpha - 5) % 255
        icon.set_alpha(self.player.movement_icon_alpha)
        self.surface.blit(icon, (settings.true_level_res[0] - icon.get_width() * 1.5,
                                  icon.get_height() * 0.5))

    def draw_noise_circles(self):
        self.noise_surface.fill((0, 0, 0))
        for event in self.noise_events:
            self.noise_temp.fill((0, 0, 0))
            event.draw_noise_circles(self.noise_temp, DETECTABLE_THRESHOLD, DIRECTABLE_THRESHOLD)
            self.noise_surface.blit(self.noise_temp, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def draw_shots(self, surface):
        if self.shot_timer <= 0:
            self.shot_surface.fill((0, 0, 0))
            self.shot_timer = 0.25
        for enemy in self.enemies:
            if enemy.shot_target != None:
                enemy_screen_pos = settings.to_screen(enemy.position)
                target_screen_pos = settings.to_screen(enemy.shot_target)
                pygame.draw.line(surface, (255, 0, 0), enemy_screen_pos, target_screen_pos, 3)
# ===========================================================================
# Level objects  —  rects stored in BASE coords, scaled only in draw()
# ===========================================================================

class Wall:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)   # BASE coords

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), settings.scale_rect(self.rect))


class Door:
    def __init__(self, x, y, o: int):
        self.is_open = True
        w = 5  if o == 0 else 50
        h = 50 if o == 0 else 5
        self.rect = pygame.Rect(x, y, w, h)            # BASE coords

    def open(self, collision_rects):
        if not self.is_open:
            self.is_open = True
            try:
                collision_rects.remove(self.rect)
            except ValueError:
                print("Door rect not found in collision_rects")

    def close(self, collision_rects):
        if self.is_open:
            self.is_open = False
            collision_rects.append(self.rect)

    def interact(self, collision_rects):
        if self.is_open:
            self.close(collision_rects)
        else:
            self.open(collision_rects)

    def draw(self, surface):
        colour = (113, 93, 76) if self.is_open else (75, 57, 41)
        pygame.draw.rect(surface, colour, settings.scale_rect(self.rect))


class HidingSpot:
    def __init__(self, x, y):
        self.rect    = pygame.Rect(x, y, 32, 32)       # BASE coords
        self.in_use  = False
        self.body = None

    def draw(self, surface):
        colour = (0, 128, 128) if self.in_use else (102, 178, 178)
        pygame.draw.rect(surface, colour, settings.scale_rect(self.rect))

    def interact(self):
        self.in_use = not self.in_use