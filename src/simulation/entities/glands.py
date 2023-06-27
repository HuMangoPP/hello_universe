import numpy as np
import pygame as pg

from ...util import gaussian_dist, draw_circle, draw_triangle, draw_square, draw_pentagon, draw_hexagon

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
        env.add_new_particles(5, pos + offsets, np.arange(5), self.release)

    # render
    def render_monitor(self, display: pg.Surface, box: tuple):
        dists = pg.transform.scale(self.dists, (box[2], box[2]))
        if self.release is not None:
            xs = box[2] * self.release
            ys = box[2] * (1 - gaussian_dist(self.release, self.opt_dens, VARIATION))
            draw_circle(dists, (xs[0], ys[0]), np.ceil(np.array([0,255,0]) * self.release[0]), 5)
            draw_triangle(dists, (xs[1], ys[1]), np.ceil(np.array([0,255,0]) * self.release[1]), 5)
            draw_square(dists, (xs[2], ys[2]), np.ceil(np.array([0,255,0]) * self.release[2]), 5)
            draw_pentagon(dists, (xs[3], ys[3]), np.ceil(np.array([0,255,0]) * self.release[3]), 5)
            draw_hexagon(dists, (xs[4], ys[4]), np.ceil(np.array([0,255,0]) * self.release[4]), 5)
        display.blit(dists, box[:2])
        
    
    # data
    def get_model(self):
        '''CSV format'''
        return {
            receptor_type: opt_dens
            for receptor_type, opt_dens in zip(SHAPE_MAP, self.opt_dens)
        }