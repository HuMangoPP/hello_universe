import pygame as pg
import numpy as np
import math, random

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
DENS_THRESHOLD = 0.01

RECEPTOR_COLORS = {
    'circle': (255, 0, 0),
    'triangle': (0, 255, 0),
    'square': (0, 0, 255),
    'pentagon': (255, 255, 0),
    'hexagon': (255, 0, 255),
}

MUTATION_RATE = 0.1

MIN_FOV = 0.1
MIN_SPREAD = 0.1

def draw_view_cone(pos: np.ndarray, angle: float, fov: float, length: float, display: pg.Surface, color: tuple):
    points = [
        pos, 
        pos + length * np.array([math.cos(angle+fov/2), math.sin(angle+fov/2)]),
        pos + length * np.array([math.cos(angle-fov/2), math.sin(angle-fov/2)]),
    ]
    pg.draw.lines(display, color, True, points)

def get_receptor_angles(num_receptors: int, receptor_spread: float):
    return np.arange(
        receptor_spread * (1 - num_receptors)/2,
        receptor_spread * num_receptors/2,
        receptor_spread
    )

VARIATION = 0.05
def optimal_distribution(x: float, opt: float):
    return math.exp(-1/2 * ((x - opt) / VARIATION) ** 2)

RECEPTOR_DATA_MAP = {
    'num_receptors': 0,
    'receptor_spread': 1,
    'receptor_fov': 2,
    'optimal_dens': 3,
}

class Receptors:
    def __init__(self, receptor_data: dict):
        self.receptors = { # [num_receptors, spread, fov, optimal_dens]
            receptor_type: receptor_data[receptor_type]
            for receptor_type in SHAPE_MAP
        }

        self.sensory = {
            receptor_type: np.zeros((2,), dtype=np.float32)
            for receptor_type in self.receptors
        }

    def mutate(self):
        for receptor_type, receptor_data in self.receptors.items():
            if random.uniform(0, 1) <= MUTATION_RATE:
                # change the number of receptors, either add or subtract one
                # minimum number of receptors is 0
                change = 1 if random.uniform(0,1) > 0.5 else -1
                self.receptors[receptor_type][0] = np.clip(receptor_data[0] + change,
                                                           a_min=0, a_max=10)
            if random.uniform(0, 1) <= MUTATION_RATE:
                # change the spread of receptors 
                # minimum spread of receptors is 0.1 rad
                self.receptors[receptor_type][1] = np.clip(receptor_data[1] + random.uniform(-0.1, 0.1), 
                                                           a_min=MIN_SPREAD, a_max=math.pi)
            if random.uniform(0, 1) <= MUTATION_RATE:
                # change the fov of receptors
                # minimum fov of receptors is 0.1 rad
                self.receptors[receptor_type][2] = np.clip(receptor_data[1] + random.uniform(-0.1, 0.1), 
                                                           a_min=MIN_FOV, a_max=math.pi)
            if random.uniform(0, 1) <= MUTATION_RATE:
                # change the optimal value of the receptor 
                # TODO: not implemented
                self.receptors[receptor_type][2] = np.clip(receptor_data[2] + random.uniform(-0.1, 0.1),
                                                           a_min=-1, a_max=1)
             
    
    def poll_sensory(self, pos: np.ndarray, facing_angle: float, sense_radius: float, env):
        # TODO sense_radius based on itl stat? num receptors?
        # for each type of sensor, create a list for each receptor of the sensory typee
        sensory_for_each_receptor = {
            receptor_type: np.zeros((receptor_data[0],), dtype=np.float32)
            for receptor_type, receptor_data in self.receptors.items()
        }
        for m_pos, m_shape, m_dens in zip(env.positions, env.shapes, env.densities):
            if np.linalg.norm(pos - m_pos) < sense_radius:
                flat_angle = np.arctan2(m_pos[1]-pos[1], m_pos[0]-pos[0]) - facing_angle
                receptor_data = self.receptors[INV_SHAPE_MAP[m_shape]]
                for i, sensor_angle in enumerate(get_receptor_angles(receptor_data[0], receptor_data[1])):
                    # determine if the messenger is within range of this sensor
                    receptor = np.array([math.cos(sensor_angle),
                                         math.sin(sensor_angle)])
                    sense = np.array([math.cos(flat_angle),
                                      math.sin(flat_angle)])
                    proj = sense.dot(receptor) / np.linalg.norm(receptor)
                    if proj >= math.cos(receptor_data[2]/2):
                        sensory_for_each_receptor[INV_SHAPE_MAP[m_shape]][i] = m_dens

        
        for receptor_type, sensory in sensory_for_each_receptor.items():
            # for each receptor type, determine the avg messenger density as sensed by all receptors
            # and the avg messenger angle as sensed by all receptors 
            # with a resolution dependent on the spread angle
            if sensory.size == 0:
                avg_dens = 0
                avg_angle = 0
            else:
                avg_dens = np.average(sensory)
                if avg_dens < DENS_THRESHOLD:
                    avg_angle = 0
                else:
                    receptor_data = self.receptors[receptor_type]
                    avg_angle = np.sum(get_receptor_angles(receptor_data[0], receptor_data[1]) * sensory) / np.sum(sensory)
            self.sensory[receptor_type] = np.array([avg_dens, avg_angle])

    def render(self, pos: np.ndarray, facing_angle: float, sense_radius: float, display: pg.Surface, camera):
        for receptor_type, receptor_data in self.receptors.items():
            [draw_view_cone(camera.transform_to_screen(pos), facing_angle+offset_angle, receptor_data[2],
                             sense_radius, display, RECEPTOR_COLORS[receptor_type])
             for offset_angle in get_receptor_angles(receptor_data[0], receptor_data[1])] 

    def get_energy_cost(self) -> float:
        return np.sum([receptor_data[0] for receptor_data in self.receptors.values()])

    def get_receptor_data(self) -> dict:
        # get the num, spread, and fov of each receptor type (uniform)
        num = {
            f'num_{receptor_type}': receptor_data[0]
            for receptor_type, receptor_data in self.receptors.items()
        }
        spread = {
            f'spread_{receptor_type}': receptor_data[1]
            for receptor_type, receptor_data in self.receptors.items()
        }
        fov = {
            f'fov_{receptor_type}': receptor_data[2]
            for receptor_type, receptor_data in self.receptors.items()
        }
        return {
            **num, **spread, **fov
        }
    
    def num_receptors(self):
        return {
            receptor_type: receptor_data[0]
            for receptor_type, receptor_data in self.receptors.items()
        }

    def receptor_spreads(self):
        return {
            receptor_type: receptor_data[1]
            for receptor_type, receptor_data in self.receptors.items()
        }

    def receptor_fovs(self):
        return {
            receptor_type: receptor_data[2]
            for receptor_type, receptor_data in self.receptors.items()
        }
