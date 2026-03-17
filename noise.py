import math, pygame

class NoiseEvent:
    def __init__(self, position, intensity, type=None):
        self.position = position # base coords
        self.intensity = intensity
        self.type = type # describes source / useful for informing enemy actions based on sound types
    
    def draw_noise_circles(self, surface, PCF, detectable_threshold, directable_threshold, scale):
        detectable_radius = (PCF**2) * math.sqrt(self.intensity / (detectable_threshold))
        directable_radius = (PCF**2) * int(math.sqrt(self.intensity / directable_threshold))
        pygame.draw.circle(surface, (255, 255, 255), scale*self.position, int(detectable_radius), 2)
        pygame.draw.circle(surface, (255, 255, 255), scale*self.position, int(directable_radius), 2)
        

        