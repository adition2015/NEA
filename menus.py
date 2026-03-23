import pygame
from settings import settings


class Menus:
    def __init__(self):
        self.state = "start"
        self.surface = pygame.Surface(settings.res)
        self.start_menu = StartMenu()
        self.menu = self.start_menu
        self.pop_up_menu = None
        self.click_signal = False
    
    def draw(self, screen):
        if self.menu != None:
            self.menu.draw(self.surface)
            screen.blit(self.surface, (0, 0))
        if self.pop_up_menu != None: 
            self.pop_up_menu.draw(self.surface)
            screen.blit(self.surface, (0, 0))
    
    def update(self, dt):
        if self.menu != None:
            self.menu.update(dt)
            if self.click_signal:
                if self.state == "start":
                    self.start_menu.click_signal = True
            if self.menu.clicked == "play":
                self.state = "play"
                self.menu = None
            if self.state == "start":
                self.menu = self.start_menu

    

        


class StartMenu:
    def __init__(self):
        self.surface = pygame.Surface(settings.res)
        self.click_signal = False
        self.buttons = {}
        self.clicked = None
        self.create_play_button()
        self.create_settings_button()

    def update(self, dt):
        if self.click_signal:
            for id, button in self.buttons.items():
                if self.check_hover(button):
                    self.clicked = id
            

    def calc_button_dims(self): 
        # Play Button
        
        """pb_w, pb_h = 150, 50 # hard coded play button width
        pb_left, pb_top = 540 - (pb_w/2), 360 - (pb_h/2)
        pb_dims = pygame.Vector2(pb_w, pb_h)
        pb_pos = pygame.Vector2(pb_left, pb_top)
        pb_dims = settings.to_true_screen(pb_dims)
        pb_pos = settings.to_true_screen(pb_pos)
        self.play_button = pygame.rect.Rect(pb_pos[0], pb_pos[1], pb_dims[0], pb_dims[1])"""
        pass 
    def create_play_button(self):
        self.play_button = pygame.image.load("assets/play_button.png").convert_alpha()
        self.play_button_rect = self.play_button.get_rect()
        self.play_button_rect.center = settings.to_true_screen(pygame.Vector2(540, 360))
        self.buttons["play"] = self.play_button_rect
    def create_settings_button(self):
        self.settings_button = pygame.image.load("assets/settings_button.png").convert_alpha()
        self.settings_button_rect = self.settings_button.get_rect()
        self.settings_button_rect.center = settings.to_true_screen(pygame.Vector2(540, 400))
        self.buttons["settings"] = self.settings_button_rect


    

    def draw_buttons(self):
        #pygame.draw.rect(self.surface, (0, 76, 76), self.play_button)
        self.surface.blit(self.play_button, self.play_button_rect)
        self.surface.blit(self.settings_button, self.settings_button_rect)

    def check_hover(self, button: pygame.Rect):
        mouse_pos = pygame.mouse.get_pos()
        if button.collidepoint(mouse_pos):
            return True
        return False
    
    def draw(self, screen):
        self.surface.fill((59, 91, 71))
        # draw buttons here
        self.draw_buttons()
        screen.blit(self.surface, (0, 0))


class PopUpMenu:
    def __init__(self, message: str):
        self.message = message
        self.res = (settings.res[0]/3, settings.res[1]/3)
        self.surface = pygame.Surface(self.res)       
        self.size = 24
        self.font = pygame.font.SysFont("monospace", self.size)
    
    def draw(self, screen):
        self.draw_message()
        x = settings.res[0] - (self.res[0] / 2)
        y = settings.res[1] = (self.res[1] / 2)
        screen.blit(self.surface, (x, y))
    
    def draw_message(self):
        self.text = self.font.render(f'Level {self.message}')
        x = self.res[0] / 2 - self.text.get_width()
        y = self.res[1] / 2 - self.text.get_height()
        self.surface.blit(self.text, (x, y))
        