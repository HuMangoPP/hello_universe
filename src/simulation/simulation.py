import numpy as np
import pygame as pg

from .entities import Entity, BrainHistory
from .environment import Environment

from ..util import write_entity_data_as_json, write_entity_data_as_csv

# data collection types
# 0: data that is static and does not change for the lifetime of the creature
# (scale, stats, brain structure, receptor structure, stomach structure)
# mainly for monitor/real-time simulation to save entity data for later
# collected at birth of a creature

# 1: data that changes from update to update 
# (position and z_angle, brain activations for all neurons, 
# health and energy, maybe clock time and reproduction guage)
# mainly for simple simulation to analyze overall behaviours of creatures
# collected at regular intervals of sim time

# 2: both



class Simulation:
    def __init__(self, collection_type = 0, collection_freq = 1):
        self.environment = Environment()
        self.entities : list[Entity] = []
        self.brain_history = BrainHistory()

        self.sim_time = 0
        self.collection_type = collection_type
        self.collection_freq = collection_freq
        self.collection_time = 0
    
    def spawn_entities(self, entities_data: list):
        entities = [Entity({
            **entity_data,
            'brain_history': self.brain_history,
        }) for entity_data in entities_data]
        self.entities = self.entities + entities

        if self.collection_type in [0, 2]:
            basic, receptors, stomach, brain = self.get_model()
            write_entity_data_as_csv(0, basic, 'basic_models')
            write_entity_data_as_csv(0, receptors, 'receptors_models')
            write_entity_data_as_csv(0, stomach, 'stomach_models')
            write_entity_data_as_json(0, brain, 'brain_models')
    
    # update
    def update(self):
        # sim timer
        dt = 1 / 100
        self.sim_time += dt
        if self.collection_type in [1, 2]:
            self.collection_time += dt
            if self.collection_time > self.collection_freq:
                ...
                self.collection_time = 0

        # environment and entity update
        update_data = [entity.update(self.environment, dt) for entity in self.entities]
        self.environment.update(dt)

        # new children
        self.spawn_entities([{**data, 
                             'id': f'{self.sim_time}-{i}'} 
                             for i, data in enumerate(update_data) if 'child' in data])

        # entity death
        self.entities = [entity for entity, data in zip(self.entities, update_data) if 'dead' not in data]

    # rendering
    def render_rt(self, display: pg.Surface, camera):
        [entity.render_rt(display, camera) for entity in self.entities]

        self.environment.render_rt(display, camera)
    
    def render_monitor(self, display: pg.Surface, index: int):
        ...

    # data
    def get_model(self):
        '''
            CSV: basic, receptors, stomach
            JSON: brain
        '''
        basic = {}
        receptors = {}
        stomach = {}
        brain = []
        for entity in self.entities:
            e_basic, e_receptor, e_stomach, e_brain = entity.get_model()
            for field, data in e_basic.items():
                if field in basic:
                    basic[field] = np.array([*basic[field], data]) 
                else:
                    basic[field] = np.array([data])

            for field, data in e_receptor.items():
                if field in receptors:
                    receptors[field] = np.array([*receptors[field], data]) 
                else:
                    receptors[field] = np.array([data])
            
            for field, data in e_stomach.items():
                if field in basic:
                    stomach[field] = np.array([*stomach[field], data]) 
                else:
                    stomach[field] = np.array([data])
            
            brain.append(e_brain)

        return basic, receptors, stomach, brain