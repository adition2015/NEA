import pygame
from level import Level, Wall

WIDTH, HEIGHT = 1080, 720
FPS = 60

class GameStateManager:
    def __init__(self): # initialises full game
        self.init_pygame()
        self.init_window()
        self.init_game_state()
        
        if self.game_state == "playing":
            self.load_level()

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
            self.handle_events()
            self.update(dt)
            self.draw()
          

    def update(self, dt):
        if self.game_state == "playing":
            self.level.update(dt)

    def draw(self):
        self.screen.fill((0, 0, 0))

        if self.game_state == "playing":
            self.level.draw(self.screen)

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

            
    def load_level(self):
        # test instance
        self.level = Level(0)
        borders = [Wall(0, 0, 1000, 5), 
           Wall(0, 0, 5, 640),
           Wall(0, 635, 1000, 5),
           Wall(995, 0, 5, 640)]
        self.level.walls += borders
        


