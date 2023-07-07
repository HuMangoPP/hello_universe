import pygame as pg
import numpy as np

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
    def render_rt(self):
        # for shape, pheromone_data in enumerate(self.pheromones):
        #     for pos, dens in zip(pheromone_data['pos'], pheromone_data['dens']):
        #         drawpos = camera.transform_to_screen(pos)
        #         color = np.ceil(np.array([0,255,0]) * dens)
        #         draw_shape(display, drawpos, color, 5, shape)
        
        # for food_type, food_data in enumerate(self.food):
        #     for pos in food_data['pos']:
        #         drawpos = camera.transform_to_screen(pos)
        #         color = (0, 0, 255)
        #         draw_shape(display, drawpos, color, 5, food_type)

        ph_render = np.zeros(0)
        for shape, ph_data in enumerate(self.pheromones):
            shapes = np.full_like(ph_data['dens'], shape)
            if shapes.size > 0:
                ph_render = np.array([*ph_render, *np.column_stack([ph_data['pos'], ph_data['dens'], shapes])])
        
        food_render = np.zeros(0)
        for food_type, food_data in enumerate(self.food):
            food_types = np.full_like(food_data['lifetime'], food_type)
            if food_types.size > 0:
                food_render = np.array([*food_render, *np.column_stack([food_data['pos'], food_types])])
        
        return {
            'pheromones': ph_render,
            'food': food_render
        }

    def render_monitor(self, display: pg.Surface, entity, anchor: tuple):
        pheromone_data = entity.receptors.get_in_range(entity.pos, entity.z_angle, self)

        for shape, data in enumerate(pheromone_data):
            for pos, dens in zip(data['pos'], data['dens']):
                color = np.ceil(np.array([0,255,0]) * dens)
                drawpos = (pos - entity.pos)[:2] + anchor
                draw_shape(display, drawpos, color, 5, shape)

    # data
    def get_sim_data(self) -> dict[str, np.ndarray]:
        x_pos = np.zeros(0)
        y_pos = np.zeros(0)
        z_pos = np.zeros(0)
        lt = np.zeros(0)
        dens = np.zeros(0)
        shape = np.zeros(0)
        p_type = np.zeros(0)

        for i, p_data in enumerate(self.pheromones):
            if p_data['lifetime'].size > 0:
                x_pos = np.array([*x_pos, *p_data['pos'][:,0]])
                y_pos = np.array([*y_pos, *p_data['pos'][:,1]])
                z_pos = np.array([*z_pos, *p_data['pos'][:,2]])

                lt = np.array([*lt, *p_data['lifetime']])

                dens = np.array([*dens, *p_data['dens']])

                shape = np.array([*shape, *np.full_like(p_data['lifetime'], i, np.int32)])

                p_type = np.array([*p_type, *np.full_like(p_data['lifetime'], 0)])

        for i, f_data in enumerate(self.food):
            if f_data['lifetime'].size > 0:
                x_pos = np.array([*x_pos, *f_data['pos'][:,0]])
                y_pos = np.array([*y_pos, *f_data['pos'][:,1]])
                z_pos = np.array([*z_pos, *f_data['pos'][:,2]])

                lt = np.array([*lt, *f_data['lifetime']])

                dens = np.array([*dens, *np.full_like(f_data['life_time'], 1, np.float32)])

                shape = np.array([*shape, *np.full_like(f_data['lifetime'], i, np.int32)])

                p_type = np.array([*p_type, *np.full_like(f_data['lifetime'], 1)])

        return {
            'x': x_pos,
            'y': y_pos,
            'z': z_pos,
            'lf': lt,
            'shapes': shape,
            'densities': dens,
            'particle_type': p_type,
        }
