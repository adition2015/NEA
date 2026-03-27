import pygame
from settings import settings


# ===========================================================================
# MENUS ARCHITECTURE OVERVIEW
#
# There are three layers, rendered in this order each frame:
#   1. Level (game world) — drawn by GameStateManager before menus
#   2. StaticMenu — full-screen surface that completely covers the game view
#   3. PopUpMenu  — small panel + dim overlay sitting on top of whatever is below
#
# The Menus coordinator owns one static + one popup at a time.
# Clicks flow: GameStateManager → Menus → active menu → .clicked string
# State changes flow back: active menu → Menus.transition → GameStateManager
#
# ===========================================================================


# ===========================================================================
# Base classes
# ===========================================================================

class Menu:
    """
    Shared interface for all menu types.
    Subclasses override update(), draw(), handle_input() as needed.
    """
    def update(self, dt: float): pass
    def draw(self, screen: pygame.Surface): pass
    def handle_input(self, event): pass


class StaticMenu(Menu):
    """
    Full-screen menus that replace the game view entirely.

    HOW RENDERING WORKS:
    - Owns its own pygame.Surface (self.surface) the size of the full window.
    - _draw_content() paints everything onto self.surface each frame.
    - draw() blits self.surface to the real screen at (0, 0), covering whatever
      was drawn before (the game world, previous menus, etc.).
    - This means the game loop never needs to stop drawing the level —
      the static menu just paints over it.

    HOW CLICKS WORK:
    - self.buttons is a dict mapping an id string → absolute screen pygame.Rect.
    - GameStateManager sets menus.click_signal = True on mouse down.
    - Menus.update() forwards click_signal to this menu.
    - update() checks every button rect against the current mouse position.
    - The first matching button id is written to self.clicked.
    - Menus.update() reads self.clicked next frame and converts it to a transition.
    """
    BG_COLOUR = (59, 91, 71)

    def __init__(self):
        self.surface = pygame.Surface(settings.res)
        self.buttons: dict[str, pygame.Rect] = {}  # id → absolute screen rect
        self.clicked: str | None = None             # set when a button is clicked; read by Menus
        self.click_signal = False                   # set by Menus; cleared after processing
        self._build()

    def _build(self):
        """Override to define self.buttons and any layout geometry."""
        pass

    def _check_hover(self, rect: pygame.Rect) -> bool:
        """Returns True if the mouse is currently over rect."""
        return rect.collidepoint(pygame.mouse.get_pos())

    def update(self, dt):
        """
        On a click frame, iterate every registered button.
        The first one the mouse is over wins — its id goes to self.clicked.
        click_signal is cleared so we only process one click per frame.
        """
        if self.click_signal:
            for id, rect in self.buttons.items():
                if self._check_hover(rect):
                    self.clicked = id
            self.click_signal = False

    def draw(self, screen):
        """
        Fill self.surface with the background colour, call _draw_content()
        to paint buttons/labels onto it, then blit the whole thing to screen.
        Because we blit at (0,0) with a fully opaque surface, anything drawn
        before this call (e.g. the game world) is completely hidden.
        """
        self.surface.fill(self.BG_COLOUR)
        self._draw_content(self.surface)
        screen.blit(self.surface, (0, 0))

    def _draw_content(self, surface):
        """Override to draw buttons and labels onto the given surface."""
        pass


class PopUpMenu(Menu):
    """
    Overlay menus drawn on top of the current frame.

    HOW RENDERING WORKS:
    - Does NOT own a full-screen surface. Instead it draws directly onto
      the screen surface that is passed into draw().
    - Step 1: Fill a full-window SRCALPHA surface with semi-transparent black
              and blit it onto the screen → dims whatever was drawn beneath.
    - Step 2: Fill a small panel surface and draw buttons/labels onto it.
    - Step 3: Blit the panel centred on screen.
    - This preserves the game world (or static menu) visible but darkened
      behind the panel — the classic "pause screen" look.

    HOW BUTTONS WORK:
    - _add_button() stores drawing params (for rendering) AND registers an
      absolute screen rect in self.buttons (for click detection).
    - Absolute rects are computed using _panel_rect(), which centres the panel
      each time — so buttons always track with the panel position.
    """
    OVERLAY_ALPHA = 160          # 0 = invisible, 255 = solid black
    PANEL_COLOUR  = (30, 30, 35)
    PANEL_SIZE    = (360, 220)
    BORDER_COLOUR = (80, 80, 90)

    def __init__(self):
        # Full-window overlay used only for the dim effect.
        self.overlay = pygame.Surface(settings.res, pygame.SRCALPHA)
        # Small panel surface; buttons are drawn onto this.
        self.panel   = pygame.Surface(self.PANEL_SIZE, pygame.SRCALPHA)
        self.font_lg = pygame.font.SysFont("monospace", 28)
        self.font_sm = pygame.font.SysFont("monospace", 16)
        self.buttons: dict[str, pygame.Rect] = {}  # id → absolute screen rect
        self.clicked: str | None = None
        self.click_signal = False
        self._build()

    def _build(self):
        """Override to call _add_button() for each button this menu needs."""
        pass

    def _panel_rect(self) -> pygame.Rect:
        """Returns the absolute screen rect of the centred panel."""
        r = self.panel.get_rect()
        r.center = (settings.res[0] // 2, settings.res[1] // 2)
        return r

    def _check_hover(self, rect: pygame.Rect) -> bool:
        return rect.collidepoint(pygame.mouse.get_pos())

    def update(self, dt):
        if self.click_signal:
            for id, rect in self.buttons.items():
                if self._check_hover(rect):
                    self.clicked = id
            self.click_signal = False

    def draw(self, screen):
        # 1. Semi-transparent black over whatever is currently on screen.
        #    SRCALPHA lets us set per-pixel alpha; OVERLAY_ALPHA controls darkness.
        self.overlay.fill((0, 0, 0, self.OVERLAY_ALPHA))
        screen.blit(self.overlay, (0, 0))

        # 2. Panel background + rounded border.
        self.panel.fill(self.PANEL_COLOUR)
        pygame.draw.rect(self.panel, self.BORDER_COLOUR,
                         self.panel.get_rect(), width=2, border_radius=8)

        # 3. Subclass draws title, message, and buttons onto the panel surface.
        self._draw_content(self.panel)

        # 4. Blit the finished panel centred on screen.
        screen.blit(self.panel, self._panel_rect())

    def _draw_content(self, surface):
        """Override to draw title, message, and buttons onto the panel surface."""
        pass

    def _add_button(self, id: str, label: str, y: int,
                    colour=(60, 140, 100), text_colour=(220, 220, 220)):
        """
        Register a centred button on this popup.

        y         — vertical position in panel-local coords
        id        — string key used both in self.buttons and by Menus to
                    identify which button was clicked
        label     — text drawn on the button face

        Two rects are created:
          btn_surface_rect — panel-local, used by _render_buttons() for drawing
          abs_rect         — absolute screen coords, used by update() for clicks
        """
        w, h = 160, 40
        panel_rect = self._panel_rect()
        x = (self.PANEL_SIZE[0] - w) // 2              # centre horizontally in panel
        btn_surface_rect = pygame.Rect(x, y, w, h)

        # Offset by the panel's top-left screen position to get absolute coords.
        abs_rect = pygame.Rect(panel_rect.x + x, panel_rect.y + y, w, h)
        self.buttons[id] = abs_rect

        # Cache drawing params so _render_buttons() can paint them each frame.
        if not hasattr(self, '_button_defs'):
            self._button_defs = {}
        self._button_defs[id] = (btn_surface_rect, label, colour, text_colour)

    def _render_buttons(self, surface):
        """Draw all registered buttons onto the panel surface."""
        if not hasattr(self, '_button_defs'):
            return
        for id, (rect, label, colour, text_colour) in self._button_defs.items():
            pygame.draw.rect(surface, colour, rect, border_radius=6)
            text = self.font_sm.render(label, True, text_colour)
            surface.blit(text, text.get_rect(center=rect.center))


# ===========================================================================
# Static menus
# ===========================================================================

class StartMenu(StaticMenu):
    def _build(self):
        self.title_font = pygame.font.SysFont("monospace", 36)

        # to_true_screen() converts from the base 1080×720 coordinate space to
        # actual window pixels, so buttons stay proportionally placed at any resolution.
        btn_w, btn_h = 150, 50
        pos = settings.to_true_screen(pygame.Vector2(540, 360))
        self.play_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self.play_rect.center = (int(pos.x), int(pos.y))
        self.buttons["play"] = self.play_rect

        pos2 = settings.to_true_screen(pygame.Vector2(540, 430))
        self.settings_rect = pygame.Rect(0, 0, 150, 50)
        self.settings_rect.center = (int(pos2.x), int(pos2.y))
        self.buttons["settings"] = self.settings_rect

    def _draw_content(self, surface):
        title = self.title_font.render("GAME", True, (220, 220, 200))
        surface.blit(title, title.get_rect(center=(settings.res[0] // 2,
                                                    settings.res[1] // 3)))
        pygame.draw.rect(surface, (60, 140, 100), self.play_rect, border_radius=8)
        pygame.draw.rect(surface, (80, 100, 120), self.settings_rect, border_radius=8)

        font = pygame.font.SysFont("monospace", 18)
        surface.blit(font.render("Play", True, (220, 220, 220)),
                     font.render("Play", True, (0,0,0)).get_rect(center=self.play_rect.center))
        surface.blit(font.render("Settings", True, (220, 220, 220)),
                     font.render("Settings", True, (0,0,0)).get_rect(center=self.settings_rect.center))


class SettingsMenu(StaticMenu):
    """
    Settings menu with resolution, FPS cap, and fullscreen toggle.

    STAGED VS APPLIED SETTINGS:
    Changes made here are "staged" (stored in _staged_* attributes) and do
    not take effect until "Apply" is clicked. This prevents a half-changed
    resolution from breaking the running game mid-interaction.
    _apply() writes staged values to settings and reinitialises the display.

    ADDING A NEW SETTING ROW:
    1. Add _staged_<name> in _build(), initialised from current settings.
    2. Add prev/next (or toggle) button rects in _build(), keyed by unique ids.
    3. Handle those ids in _handle_click().
    4. Draw the row in _draw_content().
    5. Apply the value in _apply().
    """
    BG_COLOUR = (40, 55, 65)

    RESOLUTIONS = [
        (1280, 720),
        (1600, 900),
        (1920, 1080),
        (2560, 1440),
        (720, 480),
        (480, 720)
    ]

    FPS_OPTIONS = [
        240,
        180,
        144,
        120,
        60,
        30
    ]

    def _build(self):
        self.title_font  = pygame.font.SysFont("monospace", 28)
        self.label_font  = pygame.font.SysFont("monospace", 18)
        self.button_font = pygame.font.SysFont("monospace", 18)

        # Staged (not-yet-applied) copies of the settings we can change.
        # These are separate from the live settings so the user can cancel.
        self._staged_res_index  = self._current_res_index()
        self._staged_fps_index  = self._current_fps_index()
        self._staged_fullscreen = settings.is_fullscreen

        cx = settings.res[0] // 2
        btn_w = 36

        # --- Resolution row ---
        self._res_y = settings.res[1] // 2 - 60
        # Each button gets a unique string key so _handle_click can route correctly.
        self.buttons["res_prev"] = pygame.Rect(cx - 170, self._res_y - 14, btn_w, 30)
        self.buttons["res_next"] = pygame.Rect(cx + 134, self._res_y - 14, btn_w, 30)

        # --- FPS row ---
        # Positioned below the resolution row.
        self._fps_y = self._res_y + 60
        # Note: these use DIFFERENT keys ("fps_prev"/"fps_next") from the
        # resolution buttons — this is what lets _handle_click tell them apart.
        self.buttons["fps_prev"] = pygame.Rect(cx - 170, self._fps_y - 14, btn_w, 30)
        self.buttons["fps_next"] = pygame.Rect(cx + 134, self._fps_y - 14, btn_w, 30)

        # --- Fullscreen toggle row ---
        self._fs_y = self._res_y + 120
        toggle_w, toggle_h = 52, 26
        self.buttons["fullscreen"] = pygame.Rect(cx - toggle_w // 2,
                                                  self._fs_y - toggle_h // 2,
                                                  toggle_w, toggle_h)

        # --- Apply / Back ---
        self._apply_y = self._res_y + 180
        self._back_y  = self._apply_y + 55
        self.buttons["apply"] = pygame.Rect(cx - 80, self._apply_y, 160, 42)
        self.buttons["back"]  = pygame.Rect(cx - 80, self._back_y,  160, 42)

    def _current_res_index(self) -> int:
        """Find where the current resolution sits in the RESOLUTIONS list."""
        current = (settings.width, settings.height)
        if current in self.RESOLUTIONS:
            return self.RESOLUTIONS.index(current)
        return 0

    def _current_fps_index(self) -> int:
        """Find where the current FPS cap sits in the FPS_OPTIONS list."""
        current = settings.FPS
        if current in self.FPS_OPTIONS:
            return self.FPS_OPTIONS.index(current)
        return 0

    def update(self, dt):
        """
        SettingsMenu overrides update() so it can call _handle_click() instead
        of just setting self.clicked — most clicks change internal staged state
        rather than triggering a transition, so they need custom handling.
        """
        if self.click_signal:
            for id, rect in self.buttons.items():
                if self._check_hover(rect):
                    self._handle_click(id)
            self.click_signal = False

    def _handle_click(self, id: str):
        """
        Route a button click to the appropriate staged-state change.
        The % len(...) wrapping makes the lists circular — stepping past the
        last item wraps back to the first.
        """
        if id == "res_prev":
            self._staged_res_index = (self._staged_res_index - 1) % len(self.RESOLUTIONS)
        elif id == "res_next":
            self._staged_res_index = (self._staged_res_index + 1) % len(self.RESOLUTIONS)
        elif id == "fps_prev":
            self._staged_fps_index = (self._staged_fps_index - 1) % len(self.FPS_OPTIONS)
        elif id == "fps_next":
            self._staged_fps_index = (self._staged_fps_index + 1) % len(self.FPS_OPTIONS)
        elif id == "fullscreen":
            self._staged_fullscreen = not self._staged_fullscreen
        elif id == "apply":
            self._apply()
        elif id == "back":
            # "back" is the one click that needs to reach GameStateManager,
            # so we set self.clicked here and let Menus handle the transition.
            self.clicked = "back"

    def _apply(self):
        """
        Write all staged values to the live settings object and reinitialise
        the display. Calling settings.init_resolution() recalculates all the
        scale factors used by the rest of the game.
        After applying, rebuild the menu surfaces and button positions at the
        new resolution so everything lines up correctly.
        """
        w, h = self.RESOLUTIONS[self._staged_res_index]
        settings.width         = w
        settings.height        = h
        settings.is_fullscreen = self._staged_fullscreen
        settings.FPS           = self.FPS_OPTIONS[self._staged_fps_index]
        settings.init_resolution()

        import pygame as pg
        flags = pg.FULLSCREEN if settings.is_fullscreen else 0
        pg.display.set_mode(settings.res, flags)

        # Rebuild menu surfaces at the new resolution, otherwise buttons will
        # be positioned for the old resolution.
        self.surface = pygame.Surface(settings.res)
        self._build()

    def _draw_content(self, surface):
        cx = settings.res[0] // 2

        # Title
        title = self.title_font.render("Settings", True, (200, 210, 215))
        surface.blit(title, title.get_rect(centerx=cx, y=settings.res[1] // 4))

        # --- Resolution row ---
        res_label = self.label_font.render("Resolution", True, (160, 170, 175))
        surface.blit(res_label, res_label.get_rect(centerx=cx, y=self._res_y - 40))

        pygame.draw.rect(surface, (70, 90, 110), self.buttons["res_prev"], border_radius=4)
        surface.blit(self.label_font.render("<", True, (210, 220, 225)),
                     self.label_font.render("<", True, (0,0,0)).get_rect(
                         center=self.buttons["res_prev"].center))

        # Show the currently staged resolution (not necessarily the live one yet).
        w, h = self.RESOLUTIONS[self._staged_res_index]
        res_str = self.label_font.render(f"{w} × {h}", True, (230, 235, 240))
        surface.blit(res_str, res_str.get_rect(centerx=cx, centery=self._res_y))

        pygame.draw.rect(surface, (70, 90, 110), self.buttons["res_next"], border_radius=4)
        surface.blit(self.label_font.render(">", True, (210, 220, 225)),
                     self.label_font.render(">", True, (0,0,0)).get_rect(
                         center=self.buttons["res_next"].center))

        # --- FPS row ---
        fps_label = self.label_font.render("Max FPS", True, (160, 170, 175))
        surface.blit(fps_label, fps_label.get_rect(centerx=cx, y=self._fps_y - 40))

        pygame.draw.rect(surface, (70, 90, 110), self.buttons["fps_prev"], border_radius=4)
        surface.blit(self.label_font.render("<", True, (210, 220, 225)),
                     self.label_font.render("<", True, (0,0,0)).get_rect(
                         center=self.buttons["fps_prev"].center))

        # Show the currently staged FPS value.
        fps = self.FPS_OPTIONS[self._staged_fps_index]
        fps_str = self.label_font.render(str(fps), True, (230, 235, 240))
        surface.blit(fps_str, fps_str.get_rect(centerx=cx, centery=self._fps_y))

        pygame.draw.rect(surface, (70, 90, 110), self.buttons["fps_next"], border_radius=4)
        surface.blit(self.label_font.render(">", True, (210, 220, 225)),
                     self.label_font.render(">", True, (0,0,0)).get_rect(
                         center=self.buttons["fps_next"].center))

        # --- Fullscreen toggle ---
        fs_label = self.label_font.render("Fullscreen", True, (160, 170, 175))
        surface.blit(fs_label, fs_label.get_rect(
            right=self.buttons["fullscreen"].left - 12,
            centery=self._fs_y))

        # The track changes colour based on the staged (not live) value.
        track_colour = (60, 140, 100) if self._staged_fullscreen else (80, 80, 90)
        pygame.draw.rect(surface, track_colour, self.buttons["fullscreen"], border_radius=13)
        knob_x = (self.buttons["fullscreen"].right - 15
                  if self._staged_fullscreen
                  else self.buttons["fullscreen"].left + 3)
        pygame.draw.circle(surface, (220, 225, 230), (knob_x, self._fs_y), 10)

        # "Unapplied changes" hint — shown if anything staged differs from live.
        res_changed = self.RESOLUTIONS[self._staged_res_index] != (settings.width, settings.height)
        fps_changed = self.FPS_OPTIONS[self._staged_fps_index] != settings.FPS
        fs_changed  = self._staged_fullscreen != settings.is_fullscreen
        if res_changed or fps_changed or fs_changed:
            note = self.label_font.render("Unapplied changes", True, (200, 170, 80))
            surface.blit(note, note.get_rect(centerx=cx, y=self._apply_y - 28))

        # --- Apply / Back ---
        pygame.draw.rect(surface, (60, 130, 90),  self.buttons["apply"], border_radius=7)
        surface.blit(self.button_font.render("Apply", True, (220, 230, 225)),
                     self.button_font.render("Apply", True, (0,0,0)).get_rect(
                         center=self.buttons["apply"].center))

        pygame.draw.rect(surface, (70, 80, 100), self.buttons["back"],  border_radius=7)
        surface.blit(self.button_font.render("Back", True, (210, 215, 220)),
                     self.button_font.render("Back", True, (0,0,0)).get_rect(
                         center=self.buttons["back"].center))


# ===========================================================================
# Pop-up menus
# ===========================================================================

class PauseMenu(PopUpMenu):
    """
    Shown when the player presses P during gameplay.
    Sits on top of the game world (which is still rendered beneath the dim).
    "resume" dismisses the popup and unpauses; "main_menu" exits to the start screen.
    """
    TITLE   = "Paused"
    COLOUR  = (180, 180, 200)

    def _build(self):
        self._add_button("resume",    "Resume",    110, colour=(60, 140, 100))
        self._add_button("main_menu", "Main Menu", 160, colour=(80, 80, 120))

    def _draw_content(self, surface):
        title = self.font_lg.render(self.TITLE, True, self.COLOUR)
        surface.blit(title, title.get_rect(centerx=self.PANEL_SIZE[0] // 2, y=40))
        self._render_buttons(surface)


class LevelMenu(PopUpMenu):
    """
    Shown on level completion or failure.
    result='completed' or result='failed' controls title text and colour.
    Same two actions: retry (reload level) or main_menu (exit to start).
    """
    _CONFIG = {
        "completed": ("Level Complete", (140, 220, 140)),
        "failed":    ("Level Failed",   (220, 100, 100)),
    }

    def __init__(self, result: str):
        self.result = result
        super().__init__()

    def _build(self):
        self._add_button("retry",     "Retry",     110, colour=(80, 80, 120))
        self._add_button("main_menu", "Main Menu", 160, colour=(60, 60, 80))

    def _draw_content(self, surface):
        title_text, title_colour = self._CONFIG.get(self.result, ("?", (200, 200, 200)))
        title = self.font_lg.render(title_text, True, title_colour)
        surface.blit(title, title.get_rect(centerx=self.PANEL_SIZE[0] // 2, y=40))
        self._render_buttons(surface)


# ===========================================================================
# Menus coordinator
# ===========================================================================

class Menus:
    """
    Owns the active static menu and (optionally) a pop-up overlay.
    GameStateManager calls draw() and update() each frame;
    it reads .transition once per frame to check for state changes.

    DRAW ORDER (each frame):
      GameStateManager: level.draw()     ← game world
      GameStateManager: menus.draw()
        Menus.draw():   static_menu.draw()  ← full-screen cover if present
        Menus.draw():   pop_up.draw()        ← dim + panel on top if present

    CLICK ROUTING:
      GameStateManager sets menus.click_signal = True on mouse down.
      Menus.update() forwards it to pop_up first (popup takes priority),
      or to static_menu if no popup is showing.
      The receiving menu sets self.clicked; Menus converts that to self.transition.
      GameStateManager reads self.transition and changes game state.
    """
    def __init__(self):
        self.static_menu: StaticMenu | None = StartMenu()
        self.pop_up:      PopUpMenu  | None = None
        self.transition:  str | None = None  # read by GameStateManager each frame
        self.click_signal = False            # set by GameStateManager on mouse down

    def show_popup(self, popup: PopUpMenu):
        """Display a popup over whatever is currently showing."""
        self.pop_up = popup

    def dismiss_popup(self):
        """Remove the current popup, revealing what's beneath."""
        self.pop_up = None

    def go_to(self, menu: StaticMenu):
        """Switch to a new static menu and clear any popup."""
        self.static_menu = menu
        self.pop_up = None

    def update(self, dt):
        # Forward the click signal to whichever menu is active.
        # Pop-up takes priority: if one is showing, clicks don't reach the static menu.
        if self.click_signal:
            if self.pop_up:
                self.pop_up.click_signal = True
            elif self.static_menu:
                self.static_menu.click_signal = True
            self.click_signal = False

        # Update static menu and check for a clicked button.
        if self.static_menu:
            self.static_menu.update(dt)
            clicked = self.static_menu.clicked
            if clicked:
                self.static_menu.clicked = None
                self._handle_static_click(clicked)

        # Update popup and check for a clicked button.
        if self.pop_up:
            self.pop_up.update(dt)
            clicked = self.pop_up.clicked
            if clicked:
                self.pop_up.clicked = None
                self._handle_popup_click(clicked)

    def draw(self, screen):
        # Static menu first (covers the game world if present).
        if self.static_menu:
            self.static_menu.draw(screen)
        # Popup always last — always on top.
        if self.pop_up:
            self.pop_up.draw(screen)

    def _handle_static_click(self, id: str):
        """Convert a static menu button id into a transition or menu change."""
        if id == "play":
            self.transition = "playing"
        elif id == "settings":
            self.go_to(SettingsMenu())
        elif id == "back":
            self.go_to(StartMenu())

    def _handle_popup_click(self, id: str):
        """Convert a popup button id into a transition."""
        if id == "resume":
            self.dismiss_popup()
            self.transition = "resume"
        elif id == "retry":
            self.dismiss_popup()
            self.transition = "retry"
        elif id == "main_menu":
            self.dismiss_popup()
            self.transition = "menus"
