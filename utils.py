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
        elif expected_type == tuple:
            raw = raw.strip("()")
            raw = raw.split(",")
            return tuple([int(i) for i in raw])
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
    if count > 0:
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
    "position": tuple,
    "direction": tuple,
    "patrol_points": list
}

hiding_spot_fields = {
    "x": int,
    "y": int
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
            if os.path.exists(path):
                with open(path, "r") as f:
                    content = f.read().strip()
                    return json.loads(content) if content else []
            return []

        # Load structural data (walls and doors)
        walls_raw = read_json(f"levels/level_{level_id:02d}_walls.json")
        doors_raw = read_json(f"levels/level_{level_id:02d}_doors.json")
        hiding_spots_raw = read_json(f"levels/level_{level_id:02d}_hiding_spots.json")
        enemies_raw = read_json(f"levels/level_{level_id:02d}_enemies.json")

        walls = [(e["x"], e["y"], e["width"], e["height"]) for e in walls_raw] if walls_raw else []
        doors = [(e["x"], e["y"], e["orientation"]) for e in doors_raw] if doors_raw else []
        hiding_spots = [(e["x"], e["y"]) for e in hiding_spots_raw] if hiding_spots_raw else []
        enemies = [(e["position"], e["direction"], e["patrol_points"]) for e in enemies_raw] if enemies_raw else []

        return {
            "walls": walls,
            "doors": doors,
            "enemies": enemies,
            "hiding_spots": hiding_spots
        }

    


#level_creation(wall_fields, "levels/level_01_walls.json")
#level_creation(door_fields, "levels/level_01_doors.json")
#level_creation(enemy_fields, "levels/level_01_enemies.json")
#level_creation(hiding_spot_fields, "levels/level_01_hiding_spots.json")


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


