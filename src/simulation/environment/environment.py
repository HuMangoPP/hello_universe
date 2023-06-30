import pygame as pg
import numpy as np
import math

from ...util import QuadTree, draw_shape

'''
TODO:
- separate each pheromone type into its own category, this might allow me to take advantage of numpy calculations
- create a base pheromone density for each type and measure pheromone densities relative to the base
  for creatures
- collisions use hashed grid in dict?
- separate pheromones from food?
'''

SHAPE_MAP = [
    'circle',
    'triangle',
    'square',
    'pentagon',
    'hexagon',
]

PARTICLE_LIFETIME = 1

class Environment:
    def __init__(self):
        self.pheromones = [{} for _ in SHAPE_MAP]
        
    # func
    def clear_particles(self):
        self.pheromones = {
            pheromone_type: {}
            for pheromone_type in SHAPE_MAP
        }

    def add_new_particles(self, positions: np.ndarray, shapes: np.ndarray, densities: np.ndarray):
        for pos, shape, dens in zip(positions, shapes, densities):
            gridx, gridy = pos[:2] // 10 * 10
            grid_label = f'{int(gridx),int(gridy)}'
            if grid_label in self.pheromones[shape]:
                self.pheromones[shape][grid_label] = {
                    'pos': np.array([*self.pheromones[shape][grid_label]['pos'], pos]),
                    'dens': np.array([*self.pheromones[shape][grid_label]['dens'], dens]),
                    'lifetime': np.array([*self.pheromones[shape][grid_label]['lifetime'], PARTICLE_LIFETIME])
                }
            else:
                self.pheromones[shape][grid_label] = {
                    'pos': np.array([pos]),
                    'dens': np.array([dens], np.float32),
                    'lifetime': np.array([PARTICLE_LIFETIME], np.float32)
                }

    def get_pheromone_data(self, xy: np.ndarray, boxradius: np.ndarray) -> list[dict[str, np.ndarray]]:
        gridx, gridy = xy // 10 * 10
        return_data = []
        for radius, pheromone_data in zip(boxradius, self.pheromones):
            pos = np.array([], np.float32)
            dens = np.array([], np.float32)
            indices = np.array([], np.int32)

            num_grids_along_axis = radius // 10 + 1
            grids_in_range = [
                f'{int(x + gridx)},{int(y + gridy)}'
                for x in np.arange(-num_grids_along_axis, num_grids_along_axis+1)
                for y in np.arange(-num_grids_along_axis, num_grids_along_axis+1)
            ]
            for grid in grids_in_range:
                if grid in pheromone_data:
                    pos = np.array([*pos, pheromone_data[grid]['pos']])
                    dens = np.array([*dens, pheromone_data[grid]['dens']])
                    indices = np.array([*indices, np.arange(pheromone_data[grid]['dens'].size)])
            return_data.append({
                'pos': pos,
                'dens': dens,
                'ind': indices,
            })
        return return_data

    def eat(self, positions: np.ndarray, indices: np.ndarray, shape: int):
        if indices.size > 0:
            grid_labels = np.char.add(np.char.add(positions[:,0].astype(str), 
                                                np.full_like(indices, ',')), 
                                    positions[:,1].astype(str))
            for grid_label in grid_labels.unique():
                index = indices[grid_labels == grid_label]
                self.pheromones[shape][grid_label]['lifetime'][index] = 0

    # update
    def update(self, dt: float):
        for i, pheromone_data in enumerate(self.pheromones):
            new_grid = {}
            for grid, data in pheromone_data.items():
                keep = data['lifetime'] > 0
                new_pos = data['pos'][keep]
                new_lifetime = data['lifetime'][keep] - dt
                new_dens = data['dens'][keep]
                if new_pos.size > 0:
                    new_grid[grid] = {
                        'pos': new_pos,
                        'dens': new_dens,
                        'lifetime': new_lifetime
                    }
            self.pheromones[i] = new_grid
    
    # render
    def render_rt(self, display: pg.Surface, camera):
        for i, pheromone_data in enumerate(self.pheromones):
            for tile in pheromone_data.values():
                for pos, dens in zip(tile['pos'], tile['dens']):
                    drawpos = camera.transform_to_screen(pos)
                    color = np.ceil(np.array([0,255,0]) * dens)
                    draw_shape(display, drawpos, color, 5, i)

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
