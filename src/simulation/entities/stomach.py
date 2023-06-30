import numpy as np
import pygame as pg

from ...util import gaussian_dist, draw_shape

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

def digest(x: float | np.ndarray, opt: float) -> tuple[np.ndarray, np.ndarray]:
    digest_amt = gaussian_dist(x, opt, VARIATION)
    return digest_amt, digest_amt > DIGEST_THRESHOLD

class Stomach:
    def __init__(self, stomach_data: dict):
        self.opt_dens : np.ndarray = stomach_data['opt_dens']
        self.swallowed = 0
        self.metabolism : float = stomach_data['metabolism']

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
            'opt_dens': self.opt_dens.copy(),
            'metabolism': self.metabolism
        }
    
    # func
    def eat(self, pos: np.ndarray, env, dt: float) -> float:
        # get pheromones
        pheromone_data = env.get_pheromone_data(pos[:2], np.full((5,), 10, np.float32))
        # iterate through pheromones types and digest them
        for shape, (pheromone_type, opt_dens) in enumerate(zip(pheromone_data, self.opt_dens)):
            digest_ph, digested = digest(pheromone_type['dens'], opt_dens)
            self.swallowed += np.sum(digest_ph[digested])
            env.eat(pheromone_type['pos'][digested], pheromone_type['ind'][digested], shape)
        
        digest_amt = min(self.metabolism * dt, self.swallowed)
        self.swallowed -= digest_amt
        return digest_amt

    # render
    def render_monitor(self, display: pg.Surface, box: tuple):
        dists = pg.transform.scale(self.dists, (box[2], box[2]))
        display.blit(dists, box[:2])
        
    # data
    def get_model(self):
        '''CSV format'''
        return {
            **{f'{receptor_type}': opt_dens
            for receptor_type, opt_dens in zip(SHAPE_MAP, self.opt_dens)},
            'metabolism': self.metabolism
        }