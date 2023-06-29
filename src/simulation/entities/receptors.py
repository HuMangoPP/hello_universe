import pygame as pg
import numpy as np
import math, random

from ...util import gaussian_dist, proj

from .entity_constants import MUTATION_RATE, D_FOV, D_OPT_DENS, D_SPREAD, SHAPE_MAP, RECEPTOR_COLORS

# constants
MIN_FOV = 0.1
MIN_SPREAD = 0.1
ACTIVATION_THRESHOLD = 0.01
VARIATION = 0.05

# helper
def draw_view_cone(pos: np.ndarray, angle: float, fov: float, length: float, display: pg.Surface, color: tuple):
    points = [
        pos, 
        pos + length * np.array([math.cos(angle+fov/2), math.sin(angle+fov/2)]),
        pos + length * np.array([math.cos(angle-fov/2), math.sin(angle-fov/2)]),
    ]
    pg.draw.lines(display, color, True, points)

def draw_view_cones(receptor_angles: list, fovs: list):
    surf = pg.Surface((200, 200))
    for color, angles, fov in zip(RECEPTOR_COLORS, receptor_angles, fovs):
        for angle in angles:
            draw_view_cone((100,100), angle, fov, 100, surf, color)
    surf.set_colorkey((0,0,0))
    return surf

def get_receptor_angles(num_receptors: int, receptor_spread: float):
    return np.arange(
        receptor_spread * (1 - num_receptors)/2,
        receptor_spread * num_receptors/2,
        receptor_spread
    )

class Receptors:
    def __init__(self, receptor_data: dict):
        self.num_of_type : np.ndarray = receptor_data['num_of_type']
        self.spread : np.ndarray = receptor_data['spread']
        self.fov : np.ndarray = receptor_data['fov']
        self.opt_dens : np.ndarray = receptor_data['opt_dens']
        self.sense_radius = np.ndarray = receptor_data['sense_radius']

    def adv_init(self):
        self.receptor_angles = [get_receptor_angles(num_of_type, spread)
                                for num_of_type, spread in zip(self.num_of_type, self.spread)]
        self.receptor_threshold = np.array([math.cos(fov/2) for fov in self.fov])

        self.cones = draw_view_cones(self.receptor_angles, self.fov)

    # evo
    def mutate(self):
        if random.uniform(0, 1) <= MUTATION_RATE:
            self.num_of_type = np.clip(self.num_of_type + np.random.randint(-1, 1, size=(5,)), 
                                       a_min=0, a_max=10)
            self.spread = np.clip(self.spread + np.random.uniform(-D_SPREAD, D_SPREAD, size=(5,)), 
                                  a_min=MIN_SPREAD, a_max=math.pi)
            self.fov = np.clip(self.fov + np.random.uniform(-D_FOV, D_FOV, size=(5,)), 
                               a_min=MIN_FOV, a_max=math.pi)
            self.opt_dens = np.clip(self.opt_dens + np.random.uniform(-D_OPT_DENS, D_OPT_DENS, size=(5,)), 
                                    a_min=-1, a_max=1)
    
    def reproduce(self) -> dict:
        return {
            'num_of_type': self.num_of_type.copy(),
            'spread': self.spread.copy(),
            'fov': self.spread.copy(),
            'opt_dens': self.opt_dens.copy()
        }
    
    # functionality
    def poll_receptors(self, pos: np.ndarray, z_angle: float, radius: float, env):
        # list of np arrays with each np array as the size of how many receptors of that type there are
        receptor_sense = [np.zeros((num_of_type,), np.float32) for num_of_type in self.num_of_type]

        # pheromone data
        p_data = self.get_in_range(pos, z_angle, radius, env)
        for p in p_data:
            shape_index = p[1]
            for i, _ in enumerate(self.receptor_angles[shape_index]):
                receptor_sense[shape_index][i] += gaussian_dist(p[2], self.opt_dens[shape_index], VARIATION)
        
        # iterate through sensory activations
        sensory_data = []
        for sense, receptor_angle in zip(receptor_sense, self.receptor_angles):
            if sense.size == 0: # no receptors exist, so default to these activations
                avg_actv = 0
                avg_angle = 0
            else: # otherwise, determine the actv and angle
                avg_actv = np.average(sense)
                if avg_actv < ACTIVATION_THRESHOLD:
                    avg_angle = 0
                else:
                    avg_angle = np.sum(sense * receptor_angle) / np.sum(sense) / math.pi
            sensory_data.append(np.array([avg_actv, avg_angle]))

        return np.array(sensory_data)

    def get_in_range(self, pos: np.ndarray, z_angle: float, radius: float, env):
        p_pos = env.qtree.query_point(np.array([*pos[:2], radius]))
        p_data = env.qtree.query_data(np.array([*pos[:2], radius]))
        in_range = []
        for p, data in zip(p_pos, p_data):
            if np.linalg.norm(p - pos) <= radius:
                shape_index = data[1]
                # for all receptor angles in this receptor type
                for receptor_angle in self.receptor_angles[shape_index]:
                    # get relative measurements
                    rel_pos = p - pos
                    p_rel_angle = math.atan2(rel_pos[1], rel_pos[0]) - z_angle
                    # determine collision
                    r_unit_vec = np.array([math.cos(receptor_angle), math.sin(receptor_angle)])
                    p_unit_vec = np.array([math.cos(p_rel_angle), math.sin(p_rel_angle)])
                    if proj(p_unit_vec, r_unit_vec) >= self.receptor_threshold[shape_index]:
                        in_range.append(data)
        return in_range

    def get_energy_cost(self) -> float:
        return 0.5 * np.sum([num_of_type for num_of_type in self.num_of_type])

    # render
    def render_monitor(self, display: pg.Surface, anchor: tuple, z_angle: float):
        rot = pg.transform.rotate(self.cones, z_angle)
        drawrect = rot.get_rect()
        drawrect.center = anchor
        display.blit(rot, drawrect)

    # data
    def get_model(self) -> dict:
        '''CSV format'''
        # get the num, spread, and fov of each receptor type (uniform)
        num = {
            f'num_{receptor_type}': num_of_type
            for receptor_type, num_of_type in zip(SHAPE_MAP, self.num_of_type)
        }
        spread = {
            f'spread_{receptor_type}': spread
            for receptor_type, spread in zip(SHAPE_MAP, self.spread)
        }
        fov = {
            f'fov_{receptor_type}': fov
            for receptor_type, fov in zip(SHAPE_MAP, self.fov)
        }
        opt_dens = {
            f'dens_{receptor_type}': opt_dens
            for receptor_type, opt_dens in zip(SHAPE_MAP, self.opt_dens)
        }
        radius = {
            f'radius_{receptor_type}': radius
            for receptor_type, radius in zip(SHAPE_MAP, self.sense_radius)
        }
        return {
            **num, **spread, **fov, **opt_dens
        }
