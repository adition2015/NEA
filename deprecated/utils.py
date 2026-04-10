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
    path = f"levels/level_{level_id:02d}.json"
    if not os.path.exists(path):
        print(f"Level file not found: {path}")
        return {}
    with open(path, "r") as f:
        data = json.loads(f.read().strip())

    walls = [(e["x"], e["y"], e["width"], e["height"]) 
             for e in data.get("walls", [])]
    doors = [(e["x"], e["y"], e["orientation"]) 
             for e in data.get("doors", [])]
    hiding_spots = [(e["x"], e["y"]) 
                    for e in data.get("hiding_spots", [])]
    enemies = [(e["position"], e["direction"], e["patrol_points"]) 
               for e in data.get("enemies", [])]

    return {
        "meta":         data.get("meta", {}),
        "player":       data.get("player", {"position": [540, 360], "direction": [0, -1]}),
        "walls":        walls,
        "doors":        doors,
        "hiding_spots": hiding_spots,
        "enemies":      enemies,
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


def merge_level(level_id): # copied someone else for this, I wanted to migrate existing level data so that I can more easily create new levels.
    def read(path):
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return []

    n = f"{level_id:02d}"
    merged = {
        "meta": {"id": level_id, "name": f"Level {n}", "objective": ""},
        "player": {"position": [90, 500], "direction": [0, -1]},
        "walls":        read(f"levels/level_{n}_walls.json"),
        "doors":        read(f"levels/level_{n}_doors.json"),
        "hiding_spots": read(f"levels/level_{n}_hiding_spots.json"),
        "enemies":      read(f"levels/level_{n}_enemies.json"),
    }
    with open(f"levels/level_{n}.json", "w") as f:
        json.dump(merged, f, indent=4)
    print(f"Created levels/level_{n}.json")

