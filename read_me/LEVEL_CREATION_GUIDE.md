## Level Creation System Documentation

Creating a level involves defining walls, doors, enemies, and optional waypoints in JSON files. This system allows easy level design without modifying Python code.

### File Naming Convention

All level files follow the naming pattern: `level_XX_<type>.json`
- `XX` = 2-digit level ID (e.g., 01, 02, 03)
- `<type>` = walls | doors | enemies | waypoints

Example for Level 1:
```
level_01_walls.json
level_01_doors.json
level_01_enemies.json
level_01_waypoints.json
```

### JSON Structures

#### Walls (`level_XX_walls.json`)
Defines rectangular collision geometry.

```json
[
    {
        "x": 0,
        "y": 0,
        "width": 5,
        "height": 720
    },
    {
        "x": 275,
        "y": 0,
        "width": 5,
        "height": 480
    }
]
```

- **x, y**: Top-left corner in game units
- **width, height**: Dimensions in game units

---

#### Doors (`level_XX_doors.json`)
Defines interactive door objects that enemies can open/close.

```json
[
    {
        "x": 115,
        "y": 475,
        "orientation": 1
    },
    {
        "x": 870,
        "y": 475,
        "orientation": 1
    }
]
```

- **x, y**: Door center position
- **orientation**: 0 = vertical, 1 = horizontal

---

#### Enemies (`level_XX_enemies.json`) ⭐ NEW
Defines enemy spawn points and patrol routes.

```json
[
    {
        "position": [100, 100],
        "direction": [0, 0],
        "patrol_points": [[100, 100], [100, 200], [200, 100], [400, 400]]
    },
    {
        "position": [600, 600],
        "direction": [0, 0],
        "patrol_points": [[600, 600], [400, 600], [800, 100], [400, 100]]
    }
]
```

- **position**: [x, y] - Spawn location
- **direction**: [dx, dy] - Initial direction vector (0,0 for default)
- **patrol_points**: [[x1,y1], [x2,y2], ...] - Path the enemy patrols

---

#### Waypoints (`level_XX_waypoints.json`)
Optional supplementary waypoint markers (not yet integrated).

```json
[
    {
        "title": "entrance",
        "x": 500,
        "y": 300
    },
    {
        "title": "treasure",
        "x": 800,
        "y": 150
    }
]
```

- **title**: Label/name for the waypoint
- **x, y**: Coordinates

---

### How to Create a New Level

1. **Duplicate existing files** for a new level ID:
   ```
   level_01_walls.json → level_02_walls.json
   level_01_doors.json → level_02_doors.json
   level_01_enemies.json → level_02_enemies.json
   ```

2. **Edit the JSON files** with your level geometry and enemy placements

3. **Update game_state_manager.py** to load the new level:
   ```python
   data = load_level(2)  # Load level 02
   self.level = Level(2, data)
   ```

4. **Run the game** - enemies will spawn from JSON automatically!

---

### Using the Interactive Level Creator

Commented out in `utils.py` is an interactive level creation tool:

```python
from utils import level_creation, enemy_fields, door_fields, wall_fields

# To add enemies interactively:
level_creation(enemy_fields, "levels/level_02_enemies.json")

# To add doors interactively:
level_creation(door_fields, "levels/level_02_doors.json")

# To add walls interactively:
level_creation(wall_fields, "levels/level_02_walls.json")
```

This prompts you to enter values for each field and appends them to the JSON file.

---

### Code Changes Summary

#### utils.py
- ✅ Updated `load_level()` to read enemy data from JSON
- ✅ Added `enemy_fields` and `waypoint_fields` definitions
- ✅ Added helpful comments showing level creation workflow

#### level.py
- ✅ Replaced hardcoded `self.enemies = [...]` with `self._load_enemies()`
- ✅ Added `_load_enemies(enemies_data)` method to instantiate enemies from JSON
- ✅ All enemies are now loaded dynamically from level data

#### level_01_enemies.json (NEW)
- ✅ Created with existing enemy spawn configurations

#### level_01_waypoints.json (NEW)
- ✅ Created with example waypoint structure

---

### Benefits of This System

1. **No code changes needed** to adjust enemy positions/patrols
2. **Easy level design** - just edit JSON files
3. **Scalable** - supports unlimited enemies per level
4. **Data-driven** - level content separated from game logic
5. **Easy testing** - quickly iterate level designs

---

### Next Steps (Optional Enhancements)

- [ ] Integrate waypoint data into enemy AI
- [ ] Add spawn time/delay for staggered enemy spawning
- [ ] Add enemy type selection (different enemy classes)
- [ ] Create a visual level editor tool
- [ ] Add level progression system
