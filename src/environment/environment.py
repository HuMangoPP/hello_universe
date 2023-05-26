# from random import randint
# from random import uniform

# NUM_REGIONS = 10
# CLIMATE_START = 100
# DENSITY_START = 0.2

# class Environment:
#     def __init__(self, env_data):
#         self.climate = [0]*NUM_REGIONS        # avg temperature (environmental effects)
#         self.res_density = [0]*NUM_REGIONS    # avg resource density (resource availability)
#         self.res_dist = [0]*NUM_REGIONS       # resource distribution (type of resource)
#         self.load_regions(env_data['region_data'])
    
#     def load_regions(self, region_data):
#         if region_data:
#             # save data, if any
#             self.climate = region_data['climate']
#             self.res_density = region_data['res_density']
#             self.res_dist = region_data['res_dist']
#         else:
#             # create new data, if none
#             ...
#             for i in range(NUM_REGIONS):
#                 self.climate[i] = CLIMATE_START
#                 self.res_density[i] = DENSITY_START
#                 self.res_dist[i] = 'inorganic' # all resources start as inorganic chemical compounds

#     def new_generation(self, generation):
#         # right now, it can be random and coded with extreme cycles/fluctuations
#         # ideally, it should be calculated based on creature behaviours
#         for i in range(NUM_REGIONS):
#             self.climate[i] += randint(-2, 2)
#             self.res_density[i] += uniform(-0.05, 0.05)

import pygame as pg
import numpy as np
import math

SHAPE_MAP = {
    'circle': 0,
    'triangle': 1,
    'square': 2,
    'pentagon': 3,
    'hexagon': 4,
}

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
        self.shapes = np.array([]) # shape=(n,)
        self.densities = np.array([]) # shape=(n,)
    
    def add_new_particles(self, num_new_particles: int, 
                          positions: np.ndarray, shapes: np.ndarray, densities: np.ndarray):
        self.num_particles += num_new_particles
        if self.positions.size == 0:
            self.positions = positions
            self.shapes = shapes
            self.densities = densities
        else:
            self.positions = np.concatenate([self.positions, positions])
            self.shapes = np.concatenate([self.shapes, shapes])
            self.densities = np.concatenate([self.densities, densities])
    
    def update(self, dt: float):
        self.density_decay(dt)

    def density_decay(self, dt: float):
        self.densities = self.densities - dt / 10
        keep = self.densities > 0
        self.positions = self.positions[keep]
        self.shapes = self.shapes[keep]
        self.densities = self.densities[keep]

    def drift(self, dt: float):
        self.positions = self.positions + np.random.rand(self.num_particles, 3)
    
    def render(self, display: pg.Surface, camera):
        for pos, shape, dens in zip(self.positions, self.shapes, self.densities):
            radius = 50 * dens
            color = np.ceil(np.array([255,255,255]) * dens)
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

