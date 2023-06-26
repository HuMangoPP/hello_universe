import numpy as np
import pygame as pg

from ...util import gaussian_dist

from .entity_constants import MUTATION_RATE, D_OPT_DENS, SHAPE_MAP, RECEPTOR_COLORS

# constants
DIGEST_THRESHOLD = 0.5
VARIATION = 0.2

# helper
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

def digest(x: float, opt: float) -> float:
    digest_amt = gaussian_dist(x, opt, VARIATION)
    return digest_amt if digest_amt > DIGEST_THRESHOLD else 0

class Stomach:
    def __init__(self, stomach_data: dict):
        self.opt_dens = stomach_data['opt_dens']

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
    def eat(self, pos: np.ndarray, env) -> float:
        digest_amt = 0
        # get pheromones
        edible_in_range = env.qtree.query_data(np.array([pos[0],pos[1],10]))
        # iterate through pheromones and digest them
        for edible_item in edible_in_range:
            digest_item = digest(edible_item[2], self.opt_dens[edible_item[1]])
            if digest_item > 0:
                digest_amt += digest_item
                env.eat(edible_item[0])
        
        return digest_amt

    # render
    def render_monitor(self, display: pg.Surface, box: tuple):
        display.blit(pg.transform.scale(self.dists, (box[2], box[2])),
                     box[:2])
        
    # data
    def get_model(self):
        '''CSV format'''
        return {
            receptor_type: opt_dens
            for receptor_type, opt_dens in zip(SHAPE_MAP, self.opt_dens)
        }