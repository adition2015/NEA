import pygame
from level import Level, Wall
from settings import *
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
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Game")

    def init_game_state(self):
        self.running = True
        self.game_state = "playing"

    # runtime functions
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000 
            fps = self.clock.get_fps()   
            self.handle_events()
            self.update(dt)
            self.draw(fps)
          

    def update(self, dt):
        if self.game_state == "playing":
            self.level.update(dt)

    def draw(self, fps):
        self.screen.fill((0, 0, 0))

        if self.game_state == "playing":
            self.level.draw(self.screen, fps)

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            # -- temp -- 
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            
            if self.game_state == "playing":
                self.level.handle_input(event) # handle level input

            
    def init_load_level(self):
        # test level
        data = load_level(1)
        self.level = Level(1, data)
        

