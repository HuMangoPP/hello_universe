import numpy as np
import pygame as pg

from .entities import Entity, BrainHistory
from .environment import Environment


class Simulation:
    def __init__(self):
        self.environment = Environment()
        self.entities : list[Entity] = []
        self.brain_history = BrainHistory()

        self.timer = 0
    
    def spawn_entities(self, entities_data: list):
        entities = [Entity({
            **entity_data,
            'brain_history': self.brain_history,
        }) for entity_data in entities_data]
        self.entities = self.entities + entities
    
    # update
    def update(self):
        # sim timer
        dt = 1 / 100
        self.timer += dt

        # environment and entity update
        update_data = [entity.update(self.environment, dt, self.timer) for entity in self.entities]
        self.environment.update(dt)

        # new children
        self.spawn_entities([{**data, 
                             'id': f'{self.timer}-{i}'} 
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
    def get_df(self):
        '''
            CSV: basic, receptors, stomach
            JSON: brain
        '''
        basic = {}
        receptors = {}
        stomach = {}
        brain = []
        for entity in self.entities:
            e_basic, e_receptor, e_stomach, e_brain = entity.get_df()
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