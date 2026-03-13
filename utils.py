import os, json, pygame

_debug_fonts = {}

# --- window resolution calculations ---

def level_offset(levelScalar: float, window_res: tuple) -> tuple:
    """Determines offset from top left of screen of the level surface"""
    level_offset = tuple((dim * (1 - levelScalar))//2 for dim in window_res)
    return level_offset

def level_res(levelScalar: float, window_res: tuple) -> tuple:
    """Determines level resolution"""
    level_res = tuple(dim * levelScalar for dim in window_res)
    return level_res

# --- level editor ---

def level_creation(fields: dict, destination: str):
    """
    fields: {
        "field_name": type   e.g. "x": int, "label": str, "coords": list
    }
    destination: path to a json file
    """
    
    def parse_value(raw: str, expected_type):
        if expected_type == int:
            return int(raw)
        elif expected_type == float:
            return float(raw)
        elif expected_type == list:
            return json.loads(raw)  # e.g. "[1, 2, 3]"
        else:
            return raw  # str fallback

    try:
        count = int(input("How many entries to add? "))
    except ValueError:
        print("Invalid number.")
        return

    new_entries = []

    for i in range(count):
        print(f"\n-- Entry {i + 1} --")
        entry = {}
        for field, expected_type in fields.items():
            while True:
                raw = input(f"  {field} ({expected_type.__name__}): ")
                try:
                    entry[field] = parse_value(raw, expected_type)
                    break
                except (ValueError, json.JSONDecodeError):
                    print(f"  Invalid input, expected {expected_type.__name__}. Try again.")
        new_entries.append(entry)

    # Load existing data if file exists, else create file 
    if not os.path.exists(destination):
        with open(destination, 'w') as f:
            json.dump({}, f, indent=4)
    with open(destination, "r") as f:
        content = f.read().strip()
        existing = json.loads(content) if content else []
    
    existing.extend(new_entries)

    with open(destination, "w") as f:
        json.dump(existing, f, indent=4)

    print(f"\nAdded {count} entries to '{destination}'.")

wall_fields = {
    "x":      int,
    "y":      int,
    "width":  int,
    "height": int,
}

door_fields = {
    "x":           int,
    "y":           int,
    "orientation": int,
}

enemy_fields = {
    "position":         list,    # [x, y] coordinates
    "direction":        list,    # [dx, dy] direction vector
    "patrol_points":    list     # [[x1, y1], [x2, y2], ...] patrol waypoints
}

waypoint_fields = {
    "title":            str,     # Name/description of waypoint
    "x":                int,     # X coordinate
    "y":                int      # Y coordinate
}

def load_level(level_id: int) -> dict:
        """
        Loads wall, door, and enemy data from JSON files for a given level ID.
        Returns a dict compatible with Level._load_level()
        
        Expected JSON files:
        - levels/level_XX_walls.json: Wall geometry
        - levels/level_XX_doors.json: Door positions and orientations
        - levels/level_XX_enemies.json: Enemy spawns and patrol points (optional)
        """
        def read_json(path):
            """Helper to safely read JSON files; returns empty list if file doesn't exist."""
            try:
                with open(path, "r") as f:
                    content = f.read().strip()
                    return json.loads(content) if content else []
            except FileNotFoundError:
                return []

        # Load structural data (walls and doors)
        walls_raw = read_json(f"levels/level_{level_id:02d}_walls.json")
        doors_raw = read_json(f"levels/level_{level_id:02d}_doors.json")
        
        # Load enemy spawn data
        enemies_raw = read_json(f"levels/level_{level_id:02d}_enemies.json")

        # Convert walls to tuples for Level class
        walls = [(e["x"], e["y"], e["width"], e["height"]) for e in walls_raw]
        
        # Convert doors to tuples for Level class
        doors = [(e["x"], e["y"], e["orientation"]) for e in doors_raw]
        
        # Process enemy data: convert lists to tuples for Vector2 creation
        # utils.py — load_level: copy patrol_points so mutation can't affect source data
        enemies = [
            {
            "position": tuple(e["position"]),
            "direction": tuple(e["direction"]),
            "patrol_points": [list(p) for p in e["patrol_points"]]  # deep copy
            }
        for e in enemies_raw
        ]

        return {
            "walls": walls,
            "doors": doors,
            "enemies": enemies,  # New key for enemy data
        }

    


#level_creation(wall_fields, "levels/level_01_walls.json")
#level_creation(door_fields, "levels/level_01_doors.json")
# level_creation(enemy_fields, "levels/level_01_enemies.json")
# level_creation(waypoint_fields, "levels/level_01_waypoints.json")

# --- LEVEL CREATION GUIDE ---
# To create/edit level content, call level_creation with appropriate field definitions:
#
# For new level (e.g., level 02):
#   level_creation(wall_fields, "levels/level_02_walls.json")
#   level_creation(door_fields, "levels/level_02_doors.json")
#   level_creation(enemy_fields, "levels/level_02_enemies.json")
#
# Enemy JSON format:
#   {
#       "position": [x, y],              # Enemy spawn location
#       "direction": [dx, dy],           # Initial direction (0,0 for auto)
#       "patrol_points": [[x1,y1],[x2,y2]...]  # Path to patrol
#   }
#
# Waypoint JSON format (optional, for manual navigation points):
#   {
#       "title": "waypoint_name",
#       "x": 500,
#       "y": 300
#   }

# --- draw debug ---

def draw_debug(surface, data: dict, pos=(10, 10), size=15, colour=(0, 255, 0)):
    """
    data: any dict of label->value pairs you want displayed
    """
    if size not in _debug_fonts:
        _debug_fonts[size] = pygame.font.SysFont("monospace", size)
    font = _debug_fonts[size]
    x, y = pos
    for label, value in data.items():
        text = font.render(f"{label}: {value}", True, colour)
        surface.blit(text, (x, y))
        y += size + 2
