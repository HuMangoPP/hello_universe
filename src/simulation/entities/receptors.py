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

def draw_view_cones(receptor_angles: list, fovs: list, radii: list):
    surf = pg.Surface((200, 200))
    for color, angles, fov, radius in zip(RECEPTOR_COLORS, receptor_angles, fovs, radii):
        for angle in angles:
            draw_view_cone((100,100), angle, fov, radius, surf, color)
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
        self.sense_radius : np.ndarray = receptor_data['sense_radius']

    def adv_init(self):
        self.receptor_angles = [get_receptor_angles(num_of_type, spread)
                                for num_of_type, spread in zip(self.num_of_type, self.spread)]
        self.receptor_threshold = np.array([math.cos(fov/2) for fov in self.fov])

        self.cones = draw_view_cones(self.receptor_angles, self.fov, self.sense_radius)

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
            'opt_dens': self.opt_dens.copy(),
            'sense_radius': self.sense_radius.copy()
        }
    
    # functionality
    def poll_receptors(self, pos: np.ndarray, z_angle: float, env):
        # sensory information
        receptor_data = self.get_in_range(pos, z_angle, env, True)

        sensory_data = []
        for receptor_type in receptor_data:
            if receptor_type['actv'].size == 0:
                avg_actv = 0
                avg_angle = 0
            else:
                avg_actv = np.average(receptor_type['actv'])
                if avg_actv == 0:
                    avg_angle = 0
                else:
                    avg_angle = (np.sum(receptor_type['actv'] * receptor_type['angle']) / 
                                 np.sum(receptor_type['actv']) / np.pi)
            sensory_data.append(np.array([avg_actv, avg_angle]))
        
        return np.array(sensory_data)

    def get_in_range(self, pos: np.ndarray, z_angle: float, env, get_angles=False) -> list[dict[str, np.ndarray]]:
        pheromone_data = env.get_pheromone_data(pos[:2], self.sense_radius)

        in_range = []
        for i, (p_data, radius, angles, threshold) in enumerate(zip(pheromone_data, 
                                                                    self.sense_radius, 
                                                                    self.receptor_angles, 
                                                                    self.receptor_threshold)):
            p_pos = p_data['pos']
            if p_pos.size == 0: # sentinel
                in_range.append({
                        'angle': np.empty((0,), np.float32),
                        'actv': np.empty((0,), np.float32),
                        'pos': np.empty((0,), np.float32),
                        'dens': np.empty((0,), np.float32),
                })
                continue
            
            p_dens = p_data['dens']
            rel_pos = p_pos - pos
            rel_angle = np.arctan2(rel_pos[:,1], rel_pos[:,0]) - z_angle
            rel_angle = np.vstack([rel_angle - angle for angle in angles])

            in_radius = np.linalg.norm(rel_pos, axis=1) <= radius
            in_cone = np.cos(rel_angle) >= threshold
            in_cone_reduce = np.sum(in_cone, axis=0) > 0

            if get_angles:
                which_cone = np.tile(np.array([angles]).T, (1, p_dens.size))[in_cone]
                in_range.append({
                    'angle': np.average(which_cone, axis=0)[in_radius],
                    'actv': gaussian_dist(p_dens[np.logical_and(in_range, in_cone_reduce)], 
                                          self.opt_dens[i], VARIATION)
                })
            else:
                in_range.append({
                    'pos': p_pos[np.logical_and(in_range, in_cone_reduce)],
                    'dens': p_dens[np.logical_and(in_range, in_cone_reduce)],
                })
        
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
