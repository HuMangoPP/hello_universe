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
            'optimal_dens': {
                receptor_type: lerp(self.optimal_dens[receptor_type], 
                                    other_stomach.optimal_dens[receptor_type],
                                    t)
                for receptor_type in self.optimal_dens
            }
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

    def get_df(self):
        return self.optimal_dens

class StomachManager:
    def __init__(self, num_stomachs: int, stomach_data: dict):
        self.num_stomachs = num_stomachs
        self.optimal_dens = stomach_data
    
    def add_new_stomachs(self, num_new_stomachs: int, stomach_data: dict):
        self.num_stomachs += num_new_stomachs
        self.optimal_dens = {
            shape: np.concatenate([existing_stomach_of_shape, stomach_data[shape]])
            for shape, existing_stomach_of_shape in self.optimal_dens.items()
        }

    def mutate(self):
        should_mutate = np.random.rand(self.num_stomachs) <= MUTATION_RATE
        num_should_mutate = sum(should_mutate)
        mutations = {
            shape: np.random.uniform(-DIGEST_MUTATION, DIGEST_MUTATION, size=(num_should_mutate,))
            for shape in INV_SHAPE_MAP
        }
        for receptor_type, dens_of_type in self.optimal_dens.items():
            self.optimal_dens[receptor_type][should_mutate] = dens_of_type[should_mutate] + mutations[receptor_type]
    
    def cross_breed(self, num_elites: int, elite_mask: np.ndarray, breeding_pairs: np.ndarray):
        elites = {
            receptor_type: dens[elite_mask]
            for receptor_type, dens in self.optimal_dens.items()
        }
        cross_breed_weight = np.random.uniform(0.25, 0.75, size=(num_elites,))
        new_generation = {
            receptor_type: lerp(dens, dens[breeding_pairs], cross_breed_weight)
            for receptor_type, dens in elites.items()
        }
        return new_generation
    
    def eat(self, entity_poss: np.ndarray, env):
        digest_amts = np.array([])
        edible_in_range = [env.qtree.query_data(np.array([pos[0], pos[1], 10]))
                           for pos in entity_poss]
        for i, edible_items in enumerate(edible_in_range):
            digest_amt = 0
            for j, edible_item in enumerate(edible_items):
                digest_item = digest(edible_item[2], self.optimal_dens[INV_SHAPE_MAP[edible_item[1]]][i])
                if digest_item > 0:
                    digest_amt += digest_item
                    env.eat(edible_item[0])
            
            if digest_amts.size == 0:
                digest_amts = np.array([digest_amt])
            else:
                digest_amts = np.concatenate([digest_amts, np.array([digest_amt])])
        
        return digest_amts
    
    def keep(self, to_keep: np.ndarray):
        self.optimal_dens = {
            receptor_type: dens[to_keep]
            for receptor_type, dens in self.optimal_dens.items()
        }
        self.num_stomachs = np.sum(to_keep)
        # print(self.optimal_dens)

    def get_df(self):
        return self.optimal_dens