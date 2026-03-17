## Overview

This is a **top-down 2D game** built with Pygame. It follows a clean, modular architecture split across several files. Here's a breakdown of each system:

---

### Entry Point — `main.py`

Creates a `GameStateManager` instance and calls `run()`. Simple and clean — all logic is delegated elsewhere.

---

### Game Loop — `game_state_manager.py`

The central coordinator. On initialisation it sets up Pygame, the window, game state, and loads the first level. The `run()` loop does three things every frame:

- **`handle_events()`** — processes the Pygame event queue (quit, escape key, and passes input down to the level)
- **`update(dt)`** — advances game logic using delta time (time since last frame in seconds), so movement is framerate-independent
- **`draw(fps)`** — clears the screen and renders the current frame

The `game_state` string (`"playing"`, and presumably future states like `"menu"` or `"paused"`) gates which systems are active each frame.

---

### Level — `level.py`

Owns and coordinates all level objects. On load, it reads wall and door data from `_load_level()` and constructs `Wall` and `Door` objects, scaling their coordinates from a base resolution to the actual window size via `scale_rect()`.

**Collision resolution** is a two-step process:
1. `_resolve_collisions()` iterates every wall and checks if the player's rect overlaps it
2. `_calculate_pushout()` computes the **minimum overlap axis** — it checks all four overlap distances (left, right, top, bottom) and pushes the player out along whichever axis requires the smallest correction. This prevents the player from getting stuck in corners.

`Wall` and `Door` are simple data classes with a `rect` for collision and a `draw()` method. Doors additionally track open/closed state and can be added/removed from the collidable set.

---

### Player — `player.py`

The player is a circular sprite with a directional indicator. Key behaviours:

**Mouse aiming** — `_rotate_to_mouse()` computes the vector from the player's position to the mouse, normalises it to get a direction, then uses `pygame.Vector2.angle_to()` to find the rotation angle. The sprite is re-rotated from the original `base_image` every frame (rather than rotating the already-rotated image) to prevent cumulative pixel degradation.

**Movement modes** — there are three speed tiers (75 / 200 / 350 px/s). `MOVEMENT_TRANSITIONS` is a lookup table that maps the *current* mode to the two modes reachable from it via Shift/Ctrl, so transitions are always valid without any if/else chains.

**Movement** itself only triggers while `W` is held (`move_condition` flag), moving the player along their current direction vector scaled by speed and `dt`.

---

### Settings — `settings.py`

Defines all global constants: window size, FPS cap, and the `levelScalar` (0–1) that controls how much of the window the level surface occupies. It derives `level_res`, `level_offset`, and the `scale_x`/`scale_y` factors used to map base-resolution level data to the actual display size.

---

### Utilities — `utils.py`

Contains helper functions:

- **`level_res` / `level_offset`** — calculate the level surface dimensions and its centred position within the window based on `levelScalar`
- **`load_level()`** — reads wall and door data from two JSON files (`level_01_walls.json`, etc.) and returns a dict that `Level._load_level()` consumes
- **`level_creation()`** — a CLI tool for authoring level JSON files interactively, with typed field validation
- **`draw_debug()`** — renders a dict of key/value pairs to the screen using a monospace font, used for the live position/mode/FPS overlay