import pygame as pg
import os

def load_assets(path, scale_factor):
    files = os.listdir(path)
    sprites = {}
    for file in files:
        if file.split('.')[1] == 'png':
            key = file.split('.')[0]
            image = pg.image.load(os.path.join(path, file))
            image = pg.transform.scale(image, (image.get_width()*scale_factor, image.get_height()*scale_factor))
            sprites[key] = image
    
    return sprites