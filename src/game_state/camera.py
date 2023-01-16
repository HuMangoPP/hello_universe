from src.settings import WIDTH, HEIGHT
import numpy as np

class Camera():
    def __init__(self, x, y, z):
        self.pos = np.array([x, y, z])

        self.transform = np.array([[1, 0.5, 0], [-1, 0.5, 0], [0, -1, 1]]).transpose()
        self.inverse = np.linalg.inv(self.transform)
        self.collapse_z = np.array([[1, 0], [0, 1], [0, 0]]).transpose()

    def transform_to_screen(self, pos):
        return self.collapse_z.dot(self.transform.dot(np.array(pos)-self.pos))+np.array([WIDTH//2, HEIGHT//2])

    def screen_to_world(self, x, y):
        return self.collapse_z.dot(self.inverse.dot(np.array([x, y, 0])))

    def follow_entity(self, entities, following):
        self.update_pos(np.array(entities.pos[following][0:3]))
    
    def update_pos(self, pos):
        self.pos = pos