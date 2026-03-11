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

    # Load existing data if file exists
    if os.path.exists(destination):
        with open(destination, "r") as f:
            content = f.read().strip()
            existing = json.loads(content) if content else []
    else:
        existing = []

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

def load_level(level_id: int) -> dict:
        """
        Loads wall and door data from JSON files for a given level ID.
        Returns a dict compatible with Level._load_level()
        """
        def read_json(path):
            with open(path, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else []

        walls_raw = read_json(f"levels/level_{level_id:02d}_walls.json")
        doors_raw = read_json(f"levels/level_{level_id:02d}_doors.json")

        walls = [(e["x"], e["y"], e["width"], e["height"]) for e in walls_raw]
        doors = [(e["x"], e["y"], e["orientation"]) for e in doors_raw]

        return {
            "walls": walls,
            "doors": doors,
        }

#level_creation(wall_fields, "levels/level_01_walls.json")
#level_creation(door_fields, "levels/level_01_doors.json")

# --- draw debug ---

def draw_debug(surface, data: dict, pos=(10, 10), size=10, colour=(0, 255, 0)):
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
