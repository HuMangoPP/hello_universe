import numpy as np
import pygame as pg
import math

from ..models.creature import Creature
from ..models.receptors import Receptors
from ..models.traits import Traits

class EntityManager:
    def __init__(self, first_entity: dict):
        # physical data
        self.num_entities = 1
        self.pos = np.zeros((1,3), dtype=np.float32)
        self.vel = np.zeros((1,3), dtype=np.float32)
        self.scale = np.ones((1,), dtype=np.float32)
        self.creature : list[Creature] = [Creature(first_entity['creature'])]

        # game data
        self.stats = {
            'itl': np.zeros((1,), dtype=np.float32),
            'pwr': np.zeros((1,), dtype=np.float32),
            'def': np.zeros((1,), dtype=np.float32),
            'mbl': np.zeros((1,), dtype=np.float32),
            'stl': np.zeros((1,), dtype=np.float32),
        }
        self.health = np.full((1,), 100, dtype=np.float32)
        self.energy = np.full((1,), 100, dtype=np.float32)

        # interactive
        self.receptors : list[Receptors] = [Receptors(first_entity['receptors'])]
        self.abilities = [[]]
        self.traits : list[Traits] = [Traits(first_entity['traits'])]
        self.status_effects = [[]]
        self.hurt_box = [None]

    def add_new_entities(self, num_new_entities: int, physical_data: dict, stats_data: dict, interactive_data: dict):
        # physical
        self.num_entities += num_new_entities
        self.pos = np.concatenate([self.pos, physical_data['pos']])
        self.vel = np.concatenate([self.vel, np.zeros((num_new_entities,3), dtype=np.float32)])
        self.scale = np.concatenate([self.scale, physical_data['scale']])
        self.creature = self.creature + physical_data['creature']

        # game
        self.stats['itl'] = np.concatenate([self.stats['itl'], stats_data['itl']])
        self.stats['pwr'] = np.concatenate([self.stats['pwr'], stats_data['pwr']])
        self.stats['def'] = np.concatenate([self.stats['def'], stats_data['def']])
        self.stats['mbl'] = np.concatenate([self.stats['mbl'], stats_data['mbl']])
        self.stats['stl'] = np.concatenate([self.stats['stl'], stats_data['stl']])
        self.health =  np.concatenate([self.health, stats_data['health']])
        self.energy = np.concatenate([self.energy, stats_data['energy']])

        # interactive
        self.receptors = self.receptors + interactive_data['receptors']
        self.abilities = self.abilities + interactive_data['abilities']
        self.status_effects = self.status_effects + [[] for _ in range(num_new_entities)]
        self.traits = self.traits + interactive_data['traits']
        self.hurt_box = self.hurt_box + interactive_data['hurt_box']

    # update and input
    def input(self, camera, mv_input: dict):
        entity_index = mv_input['index']
        x_input, y_input = mv_input['x'], mv_input['y']
        
        x_dir, y_dir = camera.screen_to_world(x_input, y_input)

        if x_dir != 0 and y_dir != 0:
            x_dir *= math.sqrt(2)/2
            y_dir *= math.sqrt(2)/2

        self.vel[entity_index] = np.array([[x_dir, y_dir, 0]])

    def update(self, camera, dt: float):
        # movements
        # self.vel = self.vel + self.acc * dt
        self.pos = self.pos + 200 * self.vel * dt
        # print(self.pos)

        [creature.update(self.pos[i]) for i, creature in enumerate(self.creature)]

        # TODO spend energy based on movement
    
    # mutation
    def mutate(self):
        self.stats = {
            stat_type: np.clip(stats + np.random.rand(stats.size)*2-1, 0, None)
            for stat_type, stats in self.stats.items()
        }

    # render
    def render(self, display: pg.Surface, camera):
        [creature.render(display, camera) for creature in self.creature]
    
    # save data
    def get_save_data(self):
        data = {
            'x': self.pos[:,0],
            'y': self.pos[:,1],
            'z': self.pos[:,2],
            'scale': self.scale,
            'itl': self.stats['itl'],
            'pwr': self.stats['pwr'],
            'def': self.stats['def'],
            'mbl': self.stats['mbl'],
            'stl': self.stats['stl'],
            'body_parts': [creature.num_parts for creature in self.creature],
            'num_pair_legs': [creature.legs.num_pair_legs for creature in self.creature],
            'receptors': [receptors.zip_num_receptors() for receptors in self.receptors]
        }
        return data

    # ui
    def get_ui_data(self, index: int):
        stats = {
            stat_type: math.ceil(stats[index]) 
            for stat_type, stats in self.stats.items()
        }
        return {
            **stats
        }
