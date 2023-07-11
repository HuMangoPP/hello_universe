import numpy as np
import pygame as pg

from ...util import gaussian_dist, draw_shape

from .entity_constants import MUTATION_RATE, D_OPT_DENS, SHAPE_MAP, RECEPTOR_COLORS

# constants
VARIATION = 0.25

# helpers
def get_dists(opt: np.ndarray, steps = 20) -> pg.Surface:
    surf = pg.Surface((100, 100))
    points = np.array([gaussian_dist(t, opt, VARIATION)
                       for t in np.arange(0, (1 + steps) / steps, 1 / steps)])
    for i in range(steps):
        for j, color in enumerate(RECEPTOR_COLORS):
            pg.draw.line(surf, color, (100 * i / steps, 100 * points[i,j]),
                         (100 * (i + 1) / steps, 100 * points[i+1,j]))
    surf.set_colorkey((0,0,0))
    return surf

class Glands:
    def __init__(self, glands_data: dict):
        self.opt_dens = glands_data['opt_dens']
        self.release = None
    
    def adv_init(self):
        self.dists = get_dists(self.opt_dens)
        self.dists = pg.transform.flip(self.dists, False, True)
    
    # evo
    def mutate(self):
        if np.random.uniform(0, 1) <= MUTATION_RATE:
            self.opt_dens = np.clip(self.opt_dens + np.random.uniform(-D_OPT_DENS, D_OPT_DENS, size=(5,)), 
                                    a_min=0, a_max=1)
    
    def reproduce(self) -> dict:
        return {
            'opt_dens': self.opt_dens.copy()
        }

    # func
    def release_pheromones(self, pos: np.ndarray, env):
        offsets = np.random.uniform(-25., 25., (5,3))
        self.release = np.clip(self.opt_dens + VARIATION * np.random.randn(5), a_min=0, a_max=1)
        env.add_pheromones(pos + offsets, np.arange(5), self.release)

    # render
    def render_monitor(self, size: float):
        dists = pg.transform.scale(self.dists, (size, size))
        if self.release is not None:
            xs = size * self.release
            ys = size * (1 - gaussian_dist(self.release, self.opt_dens, VARIATION))
            for i, (value, x, y) in enumerate(zip(self.release, xs, ys)):
                draw_shape(dists, (x, y), np.ceil(np.array([0,255,0]) * value), 5, i)
        
        return dists
        
    
    # data
    def get_model(self):
        '''CSV format'''
        return {
            **{f'{receptor_type}': opt_dens
            for receptor_type, opt_dens in zip(SHAPE_MAP, self.opt_dens)},
        }