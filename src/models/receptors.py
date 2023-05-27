import numpy as np
import math

SINGLE_RECEPTOR_CAPACITY = 1
SHAPE_MAP = {
    'circle': 0,
    'triangle': 1,
    'square': 2,
    'pentagon': 3,
    'hexagon': 4,
}
INV_SHAPE_MAP = [
    'circle',
    'triangle',
    'square',
    'pentagon',
    'hexagon',
]
RECEPTOR_FOV = math.pi/6
DENS_THRESHOLD = 0.05

class Receptors:
    def __init__(self, receptor_data: dict):
        self.receptors = {
            receptor_type: receptor_data[receptor_type]
            for receptor_type in SHAPE_MAP
        }

        self.sensory = {
            receptor_type: np.zeros((2,), dtype=np.float32)
            for receptor_type in self.receptors
        }
        # self.sensory_change = {
        #     receptor_type: np.zeros((2,), dtype=np.float32)
        #     for receptor_type in self.receptors
        # }

    
    def poll_sensory(self, pos: np.ndarray, facing_angle: float, sense_radius: float, env):
        # TODO sense_radius based on itl stat? num receptors?
        # print(pos, facing_angle)
        sensory_for_each_receptor = {
            receptor_type: np.zeros(receptor_spread.shape, dtype=np.float32)
            for receptor_type,receptor_spread in self.receptors.items()
        }
        for m_pos, m_shape, m_dens in zip(env.positions, env.shapes, env.densities):
            if np.linalg.norm(pos - m_pos) < sense_radius:
                flat_angle = np.arctan2(m_pos[1]-pos[1], m_pos[0]-pos[0]) - facing_angle
                for i, sensory_angle in enumerate(self.receptors[INV_SHAPE_MAP[m_shape]]):
                    if (sensory_angle - RECEPTOR_FOV/2 < flat_angle and flat_angle <= sensory_angle + RECEPTOR_FOV/2):
                        sensory_for_each_receptor[INV_SHAPE_MAP[m_shape]][i] = m_dens

        # self.sensory_change = {
        #     sensory_type: sensory[sensory_type] - self.sensory[sensory_type]
        #     for sensory_type in sensory
        # }
        for receptor_type, sensory in sensory_for_each_receptor.items():
            if sensory.size == 0:
                avg_dens = 0
                avg_angle = 0
            else:
                avg_dens = np.average(sensory)
                if avg_dens < DENS_THRESHOLD:
                    avg_angle = 0
                else:
                    avg_angle = np.sum(self.receptors[receptor_type] * sensory) / np.sum(sensory)
            self.sensory[receptor_type] = np.array([avg_dens, avg_angle])

    def zip_num_receptors(self) -> list[int]:
        return np.sum(np.array([
            receptors.size
            for receptors in self.receptors.values()
        ]))