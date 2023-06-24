import numpy as np

from .entities import Entity, BrainHistory
from .environment import Environment


class Simulation:
    def __init__(self):
        self.environment = Environment()
        self.entities : list[Entity] = []
        self.brain_history = BrainHistory()
    
    def spawn_entities(self, entities_data: list):
        entities = [Entity(entity_data) for entity_data in entities_data]
        self.entities = self.entities + entities
    
    # update
    def update(self):
        dt = 1 / 100
        self.entities = [entity for entity in self.entities if entity.update(self.environment, dt)]

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