import numpy as np
import pygame as pg

from .entities import Entity, BrainHistory
from .environment import Environment

from ..util import write_entity_data_as_json, write_entity_data_as_csv

'''
Data Collection Types:

0: data that is static and does not change for the lifetime of the creature
(scale, stats, brain structure, receptors structure, stomach structure,
geographical location)
main uses are for monitor/real-time simulation to save entity data for later use
collected at birth of creature

1: data that changes from update to update in the simulation
(position and z_angle, brain activations for all neurons,
health and energy, reproduction gauge, environment data)
main use is for simple simulation to analyze overall behaviours of creatures
collected at regular intervals of sim time

2: both collection methods
'''



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
            self.save_models(entities)
    
    # update
    def update(self):
        # sim timer
        dt = 1 / 100
        self.sim_time += dt
        if self.collection_type in [1, 2]:
            self.collection_time += dt
            if self.collection_time > self.collection_freq:
                self.save_sim_data()
                self.collection_time = 0

        # environment and entity update
        update_data = [entity.update(self.environment, dt) for entity in self.entities]
        self.environment.update(dt)

        # entity death
        self.entities = [entity for entity, data in zip(self.entities, update_data) if 'dead' not in data]

        # new children
        self.spawn_entities([{**data['child'], 
                             'id': f'{self.sim_time}-{i}'} 
                             for i, data in enumerate(update_data) if 'child' in data])

    # rendering
    def render_rt(self, display: pg.Surface, camera):
        [entity.render_rt(display, camera) for entity in self.entities]

        self.environment.render_rt(display, camera)
    
    def render_monitor(self, display: pg.Surface, index: int, font):
        if index < len(self.entities):
            entity_to_monitor = self.entities[index]
        else:
            entity_to_monitor = self.entities[0]
        entity_to_monitor.render_monitor(display, (320, 300), font)
        self.environment.render_monitor(display, entity_to_monitor, (320, 300))

    # data
    @staticmethod
    def save_models(entities: list[Entity]):
        '''
            CSV: basic, receptors, stomach
            JSON: brain
        '''
        basic = {}
        receptors = {}
        stomach = {}
        glands = {}
        brain = []
        for entity in entities:
            e_basic, e_receptor, e_stomach, e_glands, e_brain = entity.get_model()
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
                if field in stomach:
                    stomach[field] = np.array([*stomach[field], data]) 
                else:
                    stomach[field] = np.array([data])
            
            for field, data in e_glands.items():
                if field in glands:
                    glands[field] = np.array([*glands[field], data]) 
                else:
                    glands[field] = np.array([data])
            
            brain.append(e_brain)

        return basic, receptors, stomach, brain
    
    def save_sim_data(self):
        '''
            CSV: basic, environment
            JSON: brain
        '''
        basic = {}
        brain = []

        for entity in self.entities:
            e_basic, e_brain = entity.get_sim_data()
            for field, data in e_basic.items():
                if field in basic:
                    basic[field] = np.array([*basic[field], data]) 
                else:
                    basic[field] = np.array([data])

            brain.append(e_brain)
        
        environment = self.environment.get_sim_data()

        write_entity_data_as_csv(self.sim_time, basic, 'basic_rt')
        write_entity_data_as_csv(self.sim_time, environment, 'env_rt')
        write_entity_data_as_json(self.sim_time, brain, 'brain_rt')
