import pygame
from settings import settings


# ===========================================================================
# Base classes
# ===========================================================================

class Menu:
    """Shared interface for all menu types."""
    def update(self, dt: float): pass
    def draw(self, screen: pygame.Surface): pass
    def handle_input(self, event): pass


class StaticMenu(Menu):
    """
    Full-screen menus that replace the game view entirely.
    Draws to its own surface, then blits to screen at (0, 0).
    """
    BG_COLOUR = (59, 91, 71)

    def __init__(self):
        self.surface = pygame.Surface(settings.res)
        self.buttons: dict[str, pygame.Rect] = {}
        self.clicked: str | None = None
        self.click_signal = False
        self._build()

    def _build(self):
        """Override to add buttons and other elements."""
        pass

    def _check_hover(self, rect: pygame.Rect) -> bool:
        return rect.collidepoint(pygame.mouse.get_pos())

    def update(self, dt):
        if self.click_signal:
            for id, rect in self.buttons.items():
                if self._check_hover(rect):
                    self.clicked = id
            self.click_signal = False

    def draw(self, screen):
        self.surface.fill(self.BG_COLOUR)
        self._draw_content(self.surface)
        screen.blit(self.surface, (0, 0))

    def _draw_content(self, surface):
        """Override to draw buttons and labels."""
        pass


class PopUpMenu(Menu):
    """
    Overlay menus drawn on top of the current frame.
    Dims the background with a semi-transparent overlay,
    then draws a centred panel on top.
    """
    OVERLAY_ALPHA = 160          # 0 = invisible, 255 = solid black
    PANEL_COLOUR  = (30, 30, 35)
    PANEL_SIZE    = (360, 220)
    BORDER_COLOUR = (80, 80, 90)

    def __init__(self):
        self.overlay = pygame.Surface(settings.res, pygame.SRCALPHA)
        self.panel   = pygame.Surface(self.PANEL_SIZE, pygame.SRCALPHA)
        self.font_lg = pygame.font.SysFont("monospace", 28)
        self.font_sm = pygame.font.SysFont("monospace", 16)
        self.buttons: dict[str, pygame.Rect] = {}
        self.clicked: str | None = None
        self.click_signal = False
        self._build()

    def _build(self):
        """Override to populate buttons."""
        pass

    def _panel_rect(self) -> pygame.Rect:
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
        # 1. Semi-transparent dim over whatever is currently on screen
        self.overlay.fill((0, 0, 0, self.OVERLAY_ALPHA))
        screen.blit(self.overlay, (0, 0))

        # 2. Panel background + border
        self.panel.fill(self.PANEL_COLOUR)
        pygame.draw.rect(self.panel, self.BORDER_COLOUR,
                         self.panel.get_rect(), width=2, border_radius=8)

        # 3. Panel content (implemented by subclass)
        self._draw_content(self.panel)

        # 4. Blit centred panel onto screen
        screen.blit(self.panel, self._panel_rect())

    def _draw_content(self, surface):
        """Override to draw title, message, and buttons onto the panel surface."""
        pass

    def _add_button(self, id: str, label: str, y: int,
                    colour=(60, 140, 100), text_colour=(220, 220, 220)):
        """
        Helper: creates a centred button on the panel surface and registers it.
        Returns the absolute screen rect (needed for click detection).
        """
        w, h = 160, 40
        panel_rect = self._panel_rect()
        x = (self.PANEL_SIZE[0] - w) // 2
        btn_surface_rect = pygame.Rect(x, y, w, h)

        # Absolute screen rect for click detection
        abs_rect = pygame.Rect(panel_rect.x + x, panel_rect.y + y, w, h)
        self.buttons[id] = abs_rect

        # Draw onto panel during draw call — store params for _draw_content
        if not hasattr(self, '_button_defs'):
            self._button_defs = {}
        self._button_defs[id] = (btn_surface_rect, label, colour, text_colour)

    def _render_buttons(self, surface):
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

        # Play button — centred at base (540, 360)
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

        # Staged (not yet applied) values — start from current settings
        self._staged_res_index  = self._current_res_index()
        self._staged_fps_index  = self._current_fps_index()
        self._staged_fullscreen = settings.is_fullscreen
        self._staged_fps = settings.FPS

        cx = settings.res[0] // 2
        btn_w = 36

        # Resolution row
        self._res_y = settings.res[1] // 2 - 60
        self.buttons["res_prev"] = pygame.Rect(cx - 170, self._res_y - 14, btn_w, 30)
        self.buttons["res_next"] = pygame.Rect(cx + 134, self._res_y - 14, btn_w, 30)
        
        # FPS row
        self._fps_y = settings.res[1] // 2 + 60
        self.buttons["fps_prev"] = pygame.Rect(cx - 170, self._fps_y - 14, btn_w, 30)
        self.buttons["fps_next"] = pygame.Rect(cx + 134, self._fps_y - 14, btn_w, 30)


        # Fullscreen toggle row
        self._fs_y = self._res_y + 60
        toggle_w, toggle_h = 52, 26
        self.buttons["fullscreen"] = pygame.Rect(cx - toggle_w // 2, 
                                                  self._fs_y - toggle_h // 2,
                                                  toggle_w, toggle_h)

        # Apply / Back buttons
        self._apply_y = self._res_y + 140
        self._back_y  = self._apply_y + 55
        self.buttons["apply"] = pygame.Rect(cx - 80, self._apply_y, 160, 42)
        self.buttons["back"]  = pygame.Rect(cx - 80, self._back_y,  160, 42)

    def _current_res_index(self) -> int:
        current = (settings.width, settings.height)
        if current in self.RESOLUTIONS:
            return self.RESOLUTIONS.index(current)
        return 0

    def _current_fps_index(self) -> int:
        current = settings.FPS
        if current in self.FPS_OPTIONS:
            return self.FPS_OPTIONS.index(current)
        return 0

    def update(self, dt):
        if self.click_signal:
            for id, rect in self.buttons.items():
                if self._check_hover(rect):
                    self._handle_click(id)
            self.click_signal = False

    def _handle_click(self, id: str):
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
            self.clicked = "back"

    def _apply(self):
        w, h = self.RESOLUTIONS[self._staged_res_index]
        settings.width       = w
        settings.height      = h
        settings.is_fullscreen = self._staged_fullscreen
        settings.FPS = self._staged_fps
        settings.init_resolution()

        # Reinitialise the display with the new resolution
        import pygame as pg
        flags = pg.FULLSCREEN if settings.is_fullscreen else 0
        pg.display.set_mode(settings.res, flags)

        # Rebuild the menu surfaces and button positions at the new resolution
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

        # < arrow
        pygame.draw.rect(surface, (70, 90, 110),
                         self.buttons["res_prev"], border_radius=4)
        arrow_l = self.label_font.render("<", True, (210, 220, 225))
        surface.blit(arrow_l, arrow_l.get_rect(center=self.buttons["res_prev"].center))

        # Resolution value
        w, h = self.RESOLUTIONS[self._staged_res_index]
        res_str = self.label_font.render(f"{w} × {h}", True, (230, 235, 240))
        surface.blit(res_str, res_str.get_rect(centerx=cx, centery=self._res_y))

        # > arrow
        pygame.draw.rect(surface, (70, 90, 110),
                         self.buttons["res_next"], border_radius=4)
        arrow_r = self.label_font.render(">", True, (210, 220, 225))
        surface.blit(arrow_r, arrow_r.get_rect(center=self.buttons["res_next"].center))

        # --- Fullscreen toggle ---
        fs_label = self.label_font.render("Fullscreen", True, (160, 170, 175))
        surface.blit(fs_label, fs_label.get_rect(
            right=self.buttons["fullscreen"].left - 12,
            centery=self._fs_y))

        track_colour = (60, 140, 100) if self._staged_fullscreen else (80, 80, 90)
        pygame.draw.rect(surface, track_colour,
                         self.buttons["fullscreen"], border_radius=13)
        knob_x = (self.buttons["fullscreen"].right - 15
                  if self._staged_fullscreen
                  else self.buttons["fullscreen"].left + 3)
        pygame.draw.circle(surface, (220, 225, 230),
                           (knob_x, self._fs_y), 10)

        # --- Maximum FPS Options ---
        fps_label = self.label_font.render("Max FPS", True, (160, 170, 175))
        surface.blit(fps_label, fps_label.get_rect(centerx=cx, y=self._res_y - 40))

        # < arrow
        pygame.draw.rect(surface, (70, 90, 110),
                         self.buttons["fps_prev"], border_radius=4)
        arrow_l = self.label_font.render("<", True, (210, 220, 225))
        surface.blit(arrow_l, arrow_l.get_rect(center=self.buttons["fps_prev"].center))

        # Resolution value
        fps = self.FPS_OPTIONS[self._staged_res_index]
        fps_str = self.label_font.render(f"{fps}", True, (230, 235, 240))
        surface.blit(fps_str, fps_str.get_rect(centerx=cx, centery=self._res_y))

        # > arrow
        pygame.draw.rect(surface, (70, 90, 110),
                         self.buttons["res_next"], border_radius=4)
        arrow_r = self.label_font.render(">", True, (210, 220, 225))
        surface.blit(arrow_r, arrow_r.get_rect(center=self.buttons["res_next"].center))


        # Staged-but-unapplied indicator
        res_changed = self.RESOLUTIONS[self._staged_res_index] != (settings.width, settings.height)
        fs_changed  = self._staged_fullscreen != settings.is_fullscreen
        if res_changed or fs_changed:
            note = self.label_font.render("Unapplied changes", True, (200, 170, 80))
            surface.blit(note, note.get_rect(centerx=cx, y=self._apply_y - 28))

        # --- Apply / Back ---
        pygame.draw.rect(surface, (60, 130, 90),
                         self.buttons["apply"], border_radius=7)
        apply_text = self.button_font.render("Apply", True, (220, 230, 225))
        surface.blit(apply_text, apply_text.get_rect(
            center=self.buttons["apply"].center))

        pygame.draw.rect(surface, (70, 80, 100),
                         self.buttons["back"], border_radius=7)
        back_text = self.button_font.render("Back", True, (210, 215, 220))
        surface.blit(back_text, back_text.get_rect(
            center=self.buttons["back"].center))

# ===========================================================================
# Pop-up menus
# ===========================================================================

class PauseMenu(PopUpMenu):
    TITLE   = "Paused"
    COLOUR  = (180, 180, 200)

    def _build(self):
        self._add_button("resume",   "Resume",      110, colour=(60, 140, 100))
        self._add_button("main_menu","Main Menu",   160, colour=(80, 80, 120))

    def _draw_content(self, surface):
        title = self.font_lg.render(self.TITLE, True, self.COLOUR)
        surface.blit(title, title.get_rect(centerx=self.PANEL_SIZE[0] // 2, y=40))
        self._render_buttons(surface)


class LevelMenu(PopUpMenu):
    """
    Handles both 'completed' and 'failed' outcomes.
    Pass result='completed' or result='failed'.
    """
    _CONFIG = {
        "completed": ("Level Complete", (140, 220, 140)),
        "failed":    ("Level Failed",   (220, 100, 100)),
    }

    def __init__(self, result: str):
        self.result = result
        super().__init__()

    def _build(self):
        self._add_button("retry",     "Retry",       110, colour=(80, 80, 120))
        self._add_button("main_menu", "Main Menu",   160, colour=(60, 60, 80))

    def _draw_content(self, surface):
        title_text, title_colour = self._CONFIG.get(
            self.result, ("?", (200, 200, 200)))
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
    it checks .transition for state changes.
    """
    def __init__(self):
        self.static_menu: StaticMenu | None = StartMenu()
        self.pop_up:      PopUpMenu  | None = None
        self.transition:  str | None = None   # read by GameStateManager
        self.click_signal = False

    def show_popup(self, popup: PopUpMenu):
        self.pop_up = popup

    def dismiss_popup(self):
        self.pop_up = None

    def go_to(self, menu: StaticMenu):
        self.static_menu = menu
        self.pop_up = None

    def update(self, dt):
        if self.click_signal:
            if self.pop_up:
                self.pop_up.click_signal = True
            elif self.static_menu:
                self.static_menu.click_signal = True
            self.click_signal = False

        if self.static_menu:
            self.static_menu.update(dt)
            clicked = self.static_menu.clicked
            if clicked:
                self.static_menu.clicked = None
                self._handle_static_click(clicked)

        if self.pop_up:
            self.pop_up.update(dt)
            clicked = self.pop_up.clicked
            if clicked:
                self.pop_up.clicked = None
                self._handle_popup_click(clicked)

    def draw(self, screen):
        if self.static_menu:
            self.static_menu.draw(screen)
        # Pop-up always draws last — on top of game or static menu
        if self.pop_up:
            self.pop_up.draw(screen)

    def _handle_static_click(self, id: str):
        if id == "play":
            self.transition = "playing"
        elif id == "settings":
            self.go_to(SettingsMenu())
        elif id == "back":
            self.go_to(StartMenu())

    def _handle_popup_click(self, id: str):
        if id == "resume":
            self.dismiss_popup()
            self.transition = "resume"
        elif id == "retry":
            self.dismiss_popup()
            self.transition = "retry"
        elif id == "main_menu":
            self.dismiss_popup()
            self.transition = "menus"