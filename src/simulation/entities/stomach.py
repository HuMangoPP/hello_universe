import numpy as np
import pygame as pg

from ...util import gaussian_dist, draw_shape

from .entity_constants import MUTATION_RATE, D_META, FOOD_MAP

class Stomach:
    def __init__(self, stomach_data: dict):
        self.swallowed = np.zeros(2, np.float32)
        self.capacity : float = stomach_data['capacity']
        self.metabolism : np.ndarray = stomach_data['metabolism']

    def adv_init(self):
        ...
    
    # evo
    def mutate(self):
        if np.random.uniform(0, 1) <= MUTATION_RATE:
            self.metabolism = np.clip(self.metabolism + np.random.uniform(-D_META, D_META, size=(2,)),
                                      a_min=0.1, a_max=None)
        
        if np.random.uniform(0, 1) <= MUTATION_RATE:
            self.capacity = np.clip(self.capacity + np.random.uniform(-D_META, D_META),
                                    a_min=1, a_max=None)

    def reproduce(self) -> dict:
        return {
            'metabolism': self.metabolism.copy(),
            'capacity': self.capacity
        }
    
    # func
    def eat(self, pos: np.ndarray, env, dt: float) -> float:
        # get food
        food_data = env.get_food_data(pos[:2], 10.)
        # iterate through food types and digest them
        for food_type, f_data in enumerate(food_data):
            num_particles = f_data.shape[0]
            if np.sum(self.swallowed) <= self.capacity - num_particles:
                self.swallowed[food_type] += num_particles
        
        # determine how much of each type was digested and digest from swallowed particles
        digest_amt = np.minimum(self.swallowed, self.metabolism * dt)
        self.swallowed = np.clip(self.swallowed - self.metabolism * dt, a_min=0, a_max=None)

        return digest_amt[0] + digest_amt[1] * 5

    # render
    def render_monitor(self, display: pg.Surface, box: tuple):
        bar_bg = pg.Rect(box[0], box[1], 20, box[2])
        swallowed = np.sum(self.swallowed) / self.capacity
        bar = pg.Rect(box[0], box[1], 20, swallowed * box[2])
        bar.bottom = bar_bg.bottom

        pg.draw.rect(display, (255, 255, 255), bar_bg, 1)
        pg.draw.rect(display, (0, 0, 255), bar)
        
    # data
    def get_model(self):
        '''CSV format'''
        return {
            **{f'{food_type}_metabolism': metabolism
            for food_type, metabolism in zip(FOOD_MAP, self.metabolism)},
        }