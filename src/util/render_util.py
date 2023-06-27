import pygame as pg
import numpy as np
import math

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
