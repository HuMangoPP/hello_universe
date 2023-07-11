import pygame as pg
import numpy as np
import math

from .adv_math import sigmoid

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

def draw_shape(display: pg.Surface, center: tuple, color: tuple, radius: float, type: int):
    match type:
        case 0:
            draw_circle(display, center, color, radius)
        case 1:
            draw_triangle(display, center, color, radius)
        case 2:
            draw_square(display, center, color, radius)
        case 3:
            draw_pentagon(display, center, color, radius)
        case 4:
            draw_hexagon(display, center, color, radius)

def render_neuron(display: pg.Surface, x: float, y: float, font, nid: str, actv: float,
                  radius=5, font_size=10, text_loc : str | None=None):
    actv = np.clip(actv, a_min=-1, a_max=1)
    color = (max(-255 * actv, 0), max(255 * actv, 0), 0)
    pg.draw.circle(display, color, (x, y), radius)
    if text_loc is None:
        return
    if text_loc == 'left':
        font.render(display, nid, x - 1.25 * (len(nid) + 1) * font_size, y, (255, 255, 255), size=font_size, style='left')
    else:
        font.render(display, nid, x + 2.25 * font_size, y, (255, 255, 255), size=font_size, style='left')

def render_axon(display: pg.Surface, inn: tuple, outn: tuple, weight: float):
    norm = sigmoid(weight, 255, 1)
    color = (max(-norm, 0), max(norm, 0), 0)
    pg.draw.line(display, color, inn, outn)