import numpy as np
import random, math

from ...util import lerp, gaussian_dist

MUTATION_RATE = 0.2
DMUT = 0.1
INV_SHAPE_MAP = [
    'circle',
    'triangle',
    'square',
    'pentagon',
    'hexagon',
]
DIGEST_THRESHOLD = 0.5
VARIATION = 0.2

def digest(x: float, opt: float) -> float:
    digest_amt = gaussian_dist(x, opt, VARIATION)
    return digest_amt if digest_amt > DIGEST_THRESHOLD else 0

class Stomach:
    def __init__(self, stomach_data: np.ndarray):
        self.opt_dens = stomach_data['opt_dens']
    
    # evo
    def mutate(self):
        if random.uniform(0, 1) <= MUTATION_RATE:
            self.opt_dens = np.clip(self.opt_dens + np.random.uniform(-DMUT, DMUT, size=(5,)), 
                                    a_min=0, a_max=1)
    
    def cross_breed(self, other_stomach) -> dict:
        t = random.uniform(0.25, 0.75)
        return {
            'opt_dens': lerp(self.opt_dens, other_stomach.opt_dens, t)
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

    # data
    def get_df(self):
        '''CSV format'''
        return {
            receptor_type: opt_dens
            for receptor_type, opt_dens in zip(INV_SHAPE_MAP, self.opt_dens)
        }