import sys
import numpy as np

from src.game import Game
from src.simulation import Simulation

if __name__ == '__main__':
    game = Game()
    if game.run():
        sim = Simulation(collection_type=2)
        sim.spawn_entities(
            [{
                'id': 'e0',
                'pos': np.zeros((3,), np.float32),
                'scale': 1,
                'clock_period': 2,

                'stats': {'itl': 1, 'pwr': 1, 'def': 1, 'mbl': 1, 'stl': 1},

                'brain': {
                    'neurons': [],
                    'axons': [['i_c', 'o_mvf', 1],
                              ['i_c', 'o_mvs', -1]],
                },

                'receptors': {
                    'num_of_type': np.array([3,2,0,0,0]),
                    'spread': np.full((5,), np.pi/6, np.float32),
                    'fov': np.full((5,), np.pi/6, np.float32),
                    'opt_dens': np.full((5,), 0.5, np.float32),
                    'sense_radius': np.array([100, 65, 65, 77, 45], np.float32),
                },
                
                'stomach': {
                    'metabolism': np.ones((2,), np.float32),
                    'capacity': 10,
                },

                'glands': {
                    'opt_dens': np.arange(0.3, 0.71, 0.1),
                },
            }]
        )
        while True:
            sim.update()
    sys.exit()