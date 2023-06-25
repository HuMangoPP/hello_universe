import pygame as pg
import numpy as np
import math

from ...util import QuadTree

SHAPE_MAP = {
    'circle': 0,
    'triangle': 1,
    'square': 2,
    'pentagon': 3,
    'hexagon': 4,
}

PARTICLE_LIFETIME = 5

def draw_circle(display: pg.Surface, center: tuple, color: tuple, radius: float):
    pg.draw.circle(display, color, center, radius)

def draw_triangle(display: pg.Surface, center: tuple, color:tuple, radius: float):
    points = [
        np.array(center) + radius * np.array([math.cos(angle), math.sin(angle)])
        for angle in np.arange(0, 2*math.pi, 2*math.pi/3)
    ]
    pg.draw.polygon(display, color, points)

def draw_square(display: pg.Surface, center: tuple, color:tuple, radius: float):
    side_length = np.linalg.norm(np.array([radius,radius]))
    pg.draw.rect(display, color, 
                 pg.Rect(center[0]-side_length/2,center[1]-side_length/2,
                         side_length,side_length))

def draw_pentagon(display: pg.Surface, center: tuple, color:tuple, radius: float):
    points = [
        np.array(center) + radius * np.array([math.cos(angle), math.sin(angle)])
        for angle in np.arange(0, 2*math.pi, 2*math.pi/5)
    ]
    pg.draw.polygon(display, color, points)

def draw_hexagon(display: pg.Surface, center: tuple, color:tuple, radius: float):
    points = [
        np.array(center) + radius * np.array([math.cos(angle), math.sin(angle)])
        for angle in np.arange(0, 2*math.pi, 2*math.pi/6)
    ]
    pg.draw.polygon(display, color, points)

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
            match shape:
                case 0:
                    draw_circle(display, camera.transform_to_screen(pos),
                                color, radius)
                case 1:
                    draw_triangle(display, camera.transform_to_screen(pos),
                                color, radius)
                case 2:
                    draw_square(display, camera.transform_to_screen(pos),
                                color, radius)
                case 3:
                    draw_pentagon(display, camera.transform_to_screen(pos),
                                color, radius)
                case 4:
                    draw_hexagon(display, camera.transform_to_screen(pos),
                                color, radius)

