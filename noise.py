class NoiseEvent:
    def __init__(self, position, intensity, type=None):
        self.position = position # base coords
        self.intensity = intensity
        self.type = type # describes source / useful for informing enemy actions based on sound types