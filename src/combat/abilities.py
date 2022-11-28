import pygame as pg
from src.settings import MODEL_COLORS

MAX_NUM_ABILITIES = 5

BASIC_ABILITIES = [
    'advance', # basic charging move // body slam
    'intimidate', # basic intimidation move
]

SPECIAL_ABILITIES = [
    'grapple', # with arm/tongue/tail with high intelligence
    'bite', # with mouth and teeth
    'hit', # with legs/arm/tail
    'rush' # upgraded version of advance with antlers/horn/corn
    'fly', # for flying creatures -> basically increase z value
    'swim', # for creatures that can swim -> decrease z value
    'run', # begin running for creatures that can run -> faster top speed
    'throw', # with arm/leg/tongue with high mobility -> must be able to grapple
    'slash', # with leg weapon -> deals bleed status effect
]

ALL_ABILITIES = {
    'advance': {
        'type': ['attack', 'skillshot', 'movement'],
        'damage_modifiers': [],
        'cd': 500,
    },
    'intimidate': {
        'type': ['utility', 'aoe'],
        'damage_modifiers': ['weaken'],
        'cd': 500,
    },
    'rush': {
        'type': ['attack', 'skillshot', 'movement'],
        'damage_modifiers': ['critical', 'stun'],
        'cd': 500,
    },
    'hit': {
        'type': ['attack', 'skillshot', 'strike'],
        'damage_modifiers': ['critical', 'stun'],
        'cd': 500,
    },
    'bite': {
        'type': ['attack', 'skillshot', 'strike'],
        'damage_modifiers': ['critical', 'bleed'],
        'cd': 500,
    },
    'slash': {
        'type': ['attack', 'skillshot', 'strike'],
        'damage_modifiers': ['bleed'],
        'cd': 500,
    },
    'fly': {
        'type': ['utility', 'skillshot'],
        'damage_modifiers': [],
        'cd': 500,
    }
}

class ActiveAbility:
    def __init__(self, type, pos, range):
        self.type = type
        self.effects = []
        self.damaging = False
        self.update(pos, range)
    
    def update(self, pos, range):
        self.pos = pos
        self.range = range
    
    def get_pos(self):
        all_pos = []
         # gets the position and size of the hit_boxes
        for pos in self.pos:
            all_pos.append([pos[0], pos[1], pos[2], self.range])

        return all_pos

    def draw(self, screen, camera):
        for pos in self.pos:
            x, y = camera.transform_to_screen(pos[0], pos[1], pos[2])
            pg.draw.circle(screen, MODEL_COLORS['hit_box'], (x, y), self.range, 1)