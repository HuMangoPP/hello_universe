from src.settings import WIDTH, HEIGHT

class Camera():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, entities, following):
        self.x = entities.pos[following][0]-WIDTH//2
        self.y = entities.pos[following][1]-HEIGHT//2