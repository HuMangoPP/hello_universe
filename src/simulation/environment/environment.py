import pygame as pg
import numpy as np
import math

from ...util import QuadTree, draw_shape

SHAPE_MAP = {
    'circle': 0,
    'triangle': 1,
    'square': 2,
    'pentagon': 3,
    'hexagon': 4,
}

PARTICLE_LIFETIME = 1

class Environment:
    def __init__(self):
        self.num_particles = 0
        self.positions = np.array([]) # shape=(n,3)
        self.lifetimes = np.array([]) #shape=(n,)
        self.shapes = np.array([]) # shape=(n,)
        self.densities = np.array([]) # shape=(n,)

        self.build_qtree()
    
    # func
    def build_qtree(self):
        self.qtree = QuadTree(np.array([0,0]), 500, 4)
        [self.qtree.insert(pos, data=[i, shape, density]) for i, (pos, shape, density) in enumerate(zip(self.positions, self.shapes, self.densities))]

    def clear_particles(self):
        self.num_particles = 0
        self.positions = np.array([]) # shape=(n,3)
        self.lifetimes = np.array([]) #shape=(n,)
        self.shapes = np.array([]) # shape=(n,)
        self.densities = np.array([]) # shape=(n,)

    def add_new_particles(self, num_new_particles: int, 
                          positions: np.ndarray, shapes: np.ndarray, densities: np.ndarray):
        self.num_particles += num_new_particles
        if self.positions.size == 0:
            self.positions = positions
            self.lifetimes = np.full((num_new_particles,), PARTICLE_LIFETIME)
            self.shapes = shapes
            self.densities = densities
        else:
            self.positions = np.concatenate([self.positions, positions])
            self.lifetimes = np.concatenate([self.lifetimes, np.full((num_new_particles,), PARTICLE_LIFETIME)])
            self.shapes = np.concatenate([self.shapes, shapes])
            self.densities = np.concatenate([self.densities, densities])
    
    def eat(self, index):
        self.lifetimes[index] = 0

    # update
    def update(self, dt: float):
        if self.num_particles > 0:
            self.lifetimes = self.lifetimes - np.full((self.num_particles,), dt)
            keep = self.lifetimes > 0
            self.positions = self.positions[keep]
            self.lifetimes = self.lifetimes[keep]
            self.shapes = self.shapes[keep]
            self.densities = self.densities[keep]
            self.num_particles = np.sum(keep)
        
        self.build_qtree()
    
    # render
    def render_rt(self, display: pg.Surface, camera):
        for pos, shape, dens in zip(self.positions, self.shapes, self.densities):
            radius = 7
            color = np.ceil(np.array([0,255,0]) * dens)
            draw_shape(display, camera.transform_to_screen(pos),
                       color, radius, shape)

    def render_monitor(self, display: pg.Surface, entity, anchor: tuple):
        p_data = entity.receptors.get_in_range(entity.pos, entity.z_angle, 100, self)
        indices = [p[0] for p in p_data]
        for pos, shape, dens in zip(self.positions[indices], self.shapes[indices], self.densities[indices]):
            radius = 5
            color = np.ceil(np.array([0,255,0]) * dens)
            drawpos = (pos - entity.pos)[:2] + anchor
            draw_shape(display, drawpos, color, radius, shape)


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
