import pygame
from level import Level, Wall
from menus import *
from settings import settings
from utils import *

class GameStateManager:
    def __init__(self): # initialises full game
        self._game_state = None
        self.init_pygame()
        self.init_window()
        self.init_game_state()

    # initialisation functions
    def init_pygame(self):
        pygame.init()
        self.clock = pygame.time.Clock()

    def init_window(self):
        settings.init_resolution() # dependent on pygame initialisation
        self.screen = pygame.display.set_mode(settings.res, settings.flags)

    def init_game_state(self):
        self.running = True
        self.paused = False
        self.game_state = "menus"

    def load_state(self):
        if self.game_state == "playing":
            if not hasattr(self, 'level') or self.level is None:  # <-- guard
                self.init_load_level()
        elif self.game_state == "menus":
            self.init_menus()
        elif self.game_state == "failed" or self.game_state == "completed":
            self.init_pop_up_menu()


    @property
    def game_state(self):
        return self._game_state
    
    @game_state.setter
    def game_state(self, value):
        self._game_state = value
        self.load_state()


    # runtime functions
    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000 
            fps = self.clock.get_fps()   
            self.handle_events()
            self.update(dt)
            self.draw(fps)
   

    def draw(self, fps):
        self.screen.fill((0, 0, 0))
        if self.game_state in ("playing", "paused"):
            self.level.draw(self.screen, fps)   # game renders first
        if self.game_state in ("playing", "paused", "menus"):
            self.menus.draw(self.screen)        # pop-ups sit on top of whatever is there
        draw_debug(self.screen, {
            "FPS": f'{round(fps)}',
        })
        pygame.display.flip()

    def update(self, dt):
        if self.game_state == "playing":
            self.level.update(dt)
            if self.level.level_failed:
                self.menus.show_popup(LevelMenu("failed"))
            if self.level.level_completed:
                self.menus.show_popup(LevelMenu("completed"))
        self.menus.update(dt)
        if self.menus.transition:
            self._handle_menu_transition(self.menus.transition)
            self.menus.transition = None

    def _handle_menu_transition(self, t: str):
        if t == "playing":
            self.game_state = "playing"
            self.init_load_level()
            self.menus.static_menu = None
        elif t == "resume":
            self.paused = not self.paused
            self.game_state = "playing" # pop-up already dismissed by Menus
        elif t == "retry":
            self.level = None          # force reload on retry
            self.game_state = "playing"
        elif t == "menus":
            self.game_state = "menus"
            self.menus.go_to(StartMenu())
        elif t == "exit":
            self.running = False
                
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p and self.game_state in ("playing", "paused"):
                self.paused = not self.paused
                if self.paused:
                    self.game_state = "paused"
                    self.menus.show_popup(PauseMenu())   # <-- actually create the popup
                else:
                    self.game_state = "playing"
                    self.menus.dismiss_popup()
            elif event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
                self.menus.click_signal = True
            if self.game_state == "playing":
                self.level.handle_input(event) # handle level input
            
    def init_load_level(self):
        # test level
        data = load_level(1)
        self.level = Level(1, data)

    def init_menus(self):
        self.menus = Menus()

    def init_pop_up_menu(self):
        self.pop_up_menu = PopUpMenu(self.game_state)
    
        


