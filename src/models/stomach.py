import numpy as np
import random, math

from ..util.adv_math import lerp, gaussian_dist

MUTATION_RATE = 0.2
DIGEST_MUTATION = 0.1
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
    def __init__(self, stomach_data: dict):
        self.optimal_dens = stomach_data['optimal_dens']
    
    def mutate(self):
        if random.uniform(0, 1) <= MUTATION_RATE:
            self.optimal_dens = {
                receptor_type: np.clip(dens + random.uniform(-DIGEST_MUTATION, DIGEST_MUTATION), a_min=0, a_max=1)
                for receptor_type, dens in self.optimal_dens.items()
            }
    
    def cross_breed(self, other_stomach) -> dict:
        t = random.uniform(0.25, 0.75)
        return {
            receptor_type: lerp(self.optimal_dens[receptor_type], 
                                other_stomach.optimal_dens[receptor_type],
                                t)
            for receptor_type in self.optimal_dens
        }

    def eat(self, pos: np.ndarray, env) -> float:
        digest_amt = 0
        edible_in_range = env.qtree.query_data(np.array([pos[0],pos[1],10]))
        for edible_item in edible_in_range:
            digest_item = digest(edible_item[2], self.optimal_dens[INV_SHAPE_MAP[edible_item[1]]])
            if digest_item > 0:
                digest_amt += digest_item
                env.eat(edible_item[0])
        
        return digest_amt
