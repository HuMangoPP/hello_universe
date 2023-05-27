from src.util.settings import WIDTH, HEIGHT
import numpy as np

class Camera():
    def __init__(self, follow: np.ndarray):
        self.pos = follow

        self.scale = -6 # micrometer scale

        self.transform = np.array([[1, 0, 0], [0, 1, 0], [0, -1, 1]]).transpose()
        self.inverse = np.linalg.inv(self.transform)
        self.collapse_z = np.array([[1, 0], [0, 1], [0, 0]]).transpose()

    def transform_to_screen(self, pos: np.ndarray):
        # returns the full transformation with the shift to the center of the screen
        return self.dir_transform(np.array(pos)-self.pos)+np.array([WIDTH//2, HEIGHT//2])

    def dir_transform(self, pos: np.ndarray):
        # returns the transformation but without a shift to the center of the screen
        return self.collapse_z.dot(self.transform.dot(np.array(pos)))

    def screen_to_world(self, x: float, y: float):
        pos = np.array([x,y,0])-np.array([WIDTH//2, HEIGHT//2,0])
        return self.inverse.dot(pos)+self.pos

    def follow_entity(self, entity_pos: np.ndarray, entity_scale: int):
        self.update_pos(entity_pos)
        self.scale = entity_scale
    
    def update_pos(self, pos: np.ndarray):
        self.pos = pos