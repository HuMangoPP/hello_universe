import numpy as np
import pygame as pg

from ...util import gaussian_dist, draw_shape

from .entity_constants import MUTATION_RATE, D_META, FOOD_MAP

class Stomach:
    def __init__(self, stomach_data: dict):
        self.swallowed = np.zeros(2, np.float32)
        self.metabolism : np.ndarray = stomach_data['metabolism']

    def adv_init(self):
        ...
    
    # evo
    def mutate(self):
        if np.random.uniform(0, 1) <= MUTATION_RATE:
            self.metabolism = np.clip(self.metabolism + np.random.uniform(-D_META, D_META, size=(2,)),
                                      a_min=0.1, a_max=None)

    def reproduce(self) -> dict:
        return {
            'metabolism': self.metabolism.copy()
        }
    
    # func
    def eat(self, pos: np.ndarray, env, dt: float) -> float:
        # get food
        food_data = env.get_food_data(pos[:2], 10.)
        # iterate through food types and digest them
        for food_type, f_data in enumerate(food_data):
            self.swallowed[food_type] += f_data.shape[0]
        
        # determine how much of each type was digested and digest from swallowed particles
        digest_amt = np.minimum(self.swallowed, self.metabolism)
        self.swallowed = np.clip(self.swallowed - self.metabolism, a_min=0, a_max=None)

        return digest_amt[0] + digest_amt[1] * 5

    # render
    def render_monitor(self, display: pg.Surface, box: tuple):
        ...
        
    # data
    def get_model(self):
        '''CSV format'''
        return {
            **{f'{food_type}_metabolism': metabolism
            for food_type, metabolism in zip(FOOD_MAP, self.metabolism)},
        }