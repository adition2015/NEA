import pygame
from level import Level, Wall
from settings import settings
from utils import *

class GameStateManager:
    def __init__(self): # initialises full game
        self.init_pygame()
        self.init_window()
        self.init_game_state()
        
        if self.game_state == "playing":
            self.init_load_level()

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
        self.game_state = "playing"
        self.paused = False


    # runtime functions
    def run(self):
        while self.running:
            self.game_state = "playing" if not self.paused else "paused"
            self.game_state = "playing" if not self.paused else "paused"
            dt = self.clock.tick(settings.FPS) / 1000 
            fps = self.clock.get_fps()   
            self.handle_events()
            self.update(dt)
            self.draw(fps)
          

    def update(self, dt):
        if self.game_state == "playing":
            self.level.update(dt)

    def draw(self, fps):
        if self.game_state == "playing":
            self.screen.fill((0, 0, 0))
            self.screen.fill((0, 0, 0))
            self.level.draw(self.screen, fps)
            pygame.display.flip()
            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            # -- temp -- 
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.paused = not self.paused
            
            if self.game_state == "playing":
                self.level.handle_input(event) # handle level input
            
    def init_load_level(self):
        # test level
        data = load_level(1)
        self.level = Level(1, data)
        

