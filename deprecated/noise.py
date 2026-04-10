import math, pygame
from settings import settings

class NoiseEvent:
    def __init__(self, position, intensity, type=None):
        self.position = position # base coords
        self.intensity = intensity
        self.type = type # describes source / useful for informing enemy actions based on sound types
    
    def draw_noise_circles(self, surface, detectable_threshold, directable_threshold):
        detectable_radius = math.sqrt(self.intensity / detectable_threshold) * settings.scale_total_x
        directable_radius = math.sqrt(self.intensity / directable_threshold) * settings.scale_total_y
        screen_pos = settings.to_screen(self.position)
        pygame.draw.circle(surface, (255, 255, 255), screen_pos, int(detectable_radius), 2)
        pygame.draw.circle(surface, (255, 255, 255), screen_pos, int(directable_radius), 2)
        

        