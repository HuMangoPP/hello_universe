import pygame as pg
import numpy as np
import math

from ...util import QuadTree, draw_shape

'''
TODO:
- create a base pheromone density for each type and measure pheromone densities relative to the base
  for creatures
- separate pheromones from food?
'''

SHAPE_MAP = [
    'circle',
    'triangle',
    'square',
    'pentagon',
    'hexagon',
]
FOOD_MAP = [
    'produced',
    'dropped',
]

PHEROMONE_LIFETIME = 1
FOOD_LIFETIME = 10

class Environment:
    def __init__(self):
        self.pheromones = [{
            'pos': np.array([], np.float32), # (n,3)
            'dens': np.array([], np.float32), # (n,)
            'lifetime': np.array([], np.float32), # (n,)
        } for _ in SHAPE_MAP]
        self.ph_qtree = [QuadTree(np.zeros((2,), np.float32), 500, 4) for _ in SHAPE_MAP]

        self.food = [{
            'pos': np.array([], np.float32), # (n,3)
            'lifetime': np.array([], np.float32), # (n,)
        } for _ in FOOD_MAP]
        self.food_qtree = [QuadTree(np.zeros((2,), np.float32), 500, 4) for _ in FOOD_MAP]
        
        self.pheromones_changed = False
        self.food_changed = False
        
    # func
    def clear_particles(self):
        self.pheromones = [{
            'pos': np.array([], np.float32), # (n,3)
            'dens': np.array([], np.float32), # (n,)
            'lifetime': np.array([], np.float32), # (n,)
        } for _ in SHAPE_MAP]
        
        self.food = [{
            'pos': np.array([], np.float32), # (n,3)
            'lifetime': np.array([], np.float32), # (n,)
        } for _ in FOOD_MAP]

        self.pheromones_changed = True
        self.food_changed = True

    # phermones
    def add_pheromones(self, positions: np.ndarray, shapes: np.ndarray, densities: np.ndarray):
        for pos, shape, dens in zip(positions, shapes, densities):
            if self.pheromones[shape]:
                self.pheromones[shape] = {
                    'pos': np.array([*self.pheromones[shape]['pos'], pos]),
                    'dens': np.array([*self.pheromones[shape]['dens'], dens]),
                    'lifetime': np.array([*self.pheromones[shape]['lifetime'], PHEROMONE_LIFETIME])
                }
            else:
                self.pheromones[shape] = {
                    'pos': np.array([pos]),
                    'dens': np.array([dens]),
                    'lifetime': np.array([PHEROMONE_LIFETIME])
                }

        self.pheromones_changed = True

    def get_pheromone_data(self, xy: np.ndarray, boxradius: np.ndarray) -> list[dict[str, np.ndarray]]:
        return_data = []
        for shape, (radius, pheromone_data) in enumerate(zip(boxradius, self.pheromones)):
            indices = self.ph_qtree[shape].query_indices(xy, radius)
            return_data.append({
                'pos': pheromone_data['pos'][indices],
                'dens': pheromone_data['dens'][indices],
            })
        return return_data
    
    # food
    def add_food(self, positions: np.ndarray, food_types: np.ndarray):
        for pos, food_type in zip(positions, food_types):
            if self.food[food_type]:
                self.food[food_type] = {
                    'pos': np.array([*self.food[food_type]['pos'], pos]),
                    'lifetime': np.array([*self.food[food_type]['lifetime'], FOOD_LIFETIME])
                }
            else:
                self.food[food_type] = {
                    'pos': np.array([pos]),
                    'lifetime': np.array([FOOD_LIFETIME])
                }

        self.food_changed = True

    def get_food_data(self, xy: np.ndarray, radius: float) -> list[np.ndarray]:
        return_data = []
        for food_type, food_data in enumerate(self.food):
            indices = self.food_qtree[food_type].query_indices(xy, radius)
            return_data.append(food_data['pos'][indices])
        return return_data

    # update
    def update(self, dt: float):
        for shape, pheromone_data in enumerate(self.pheromones):
            pheromone_data['lifetime'] = pheromone_data['lifetime'] - dt
            keep = pheromone_data['lifetime'] > 0
            self.pheromones[shape] = {
                'pos': pheromone_data['pos'][keep],
                'dens': pheromone_data['dens'][keep],
                'lifetime': pheromone_data['lifetime'][keep]
            }
        self.make_ph_qtree()

        for food_type, food_data in enumerate(self.food):
            food_data['lifetime'] = food_data['lifetime'] - dt
            keep = food_data['lifetime'] > 0
            self.food[food_type] = {
                'pos': food_data['pos'][keep],
                'lifetime': food_data['lifetime'][keep]
            }
        self.make_food_qtree()

    def make_ph_qtree(self):
        for ph_qtree, phermone_data in zip(self.ph_qtree, self.pheromones):
            ph_qtree.clear()
            [ph_qtree.insert(pos, index) for index, pos in enumerate(phermone_data['pos'])]
    
    def make_food_qtree(self):
        for food_qtree, food_data in zip(self.food_qtree, self.food):
            food_qtree.clear()
            [food_qtree.insert(pos, index) for index, pos in enumerate(food_data['pos'])]

    # render
    def render_rt(self, display: pg.Surface, camera):
        for shape, pheromone_data in enumerate(self.pheromones):
            for pos, dens in zip(pheromone_data['pos'], pheromone_data['dens']):
                drawpos = camera.transform_to_screen(pos)
                color = np.ceil(np.array([0,255,0]) * dens)
                draw_shape(display, drawpos, color, 5, shape)
        
        for food_type, food_data in enumerate(self.food):
            for pos in food_data['pos']:
                drawpos = camera.transform_to_screen(pos)
                color = (0, 0, 255)
                draw_shape(display, drawpos, color, 5, food_type)

    def render_monitor(self, display: pg.Surface, entity, anchor: tuple):
        pheromone_data = entity.receptors.get_in_range(entity.pos, entity.z_angle, self)

        for shape, data in enumerate(pheromone_data):
            for pos, dens in zip(data['pos'], data['dens']):
                color = np.ceil(np.array([0,255,0]) * dens)
                drawpos = (pos - entity.pos)[:2] + anchor
                draw_shape(display, drawpos, color, 5, shape)

    # data
    def get_sim_data(self) -> dict[str, np.ndarray]:
        return {
            'x': self.positions[:,0],
            'y': self.positions[:,1],
            'z': self.positions[:,2],
            'lifetimes': self.lifetimes,
            'shapes': self.shapes,
            'densities': self.densities,
        }
