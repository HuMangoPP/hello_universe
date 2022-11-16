import pygame as pg

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
        'type': ['skillshot', 'movement'],
        'damage_modifiers': [],
        'cd': 500,
    },
    'intimidate': {
        'type': ['aoe'],
        'damage_modifiers': ['weaken'],
        'cd': 500,
    },
    'rush': {
        'type': ['skillshot', 'movement'],
        'damage_modifiers': ['critical', 'stun'],
        'cd': 500,
    },
    'hit': {
        'type': ['skillshot', 'strike'],
        'damage_modifiers': ['critical', 'stun'],
        'cd': 500,
    },
    'bite': {
        'type': ['skillshot', 'strike'],
        'damage_modifiers': ['critical', 'bleed'],
        'cd': 500,
    },
    'slash': {
        'type': ['skillshot', 'strike'],
        'damage_modifiers': ['bleed'],
        'cd': 500,
    },
    'fly': {
        'type': ['skillshot'],
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
        self.get_rects()

    def get_rects(self):
        self.rects = []
        for pos in self.pos:
            self.rects.append(pg.Rect(pos[0]-self.range, 
                                      pos[1]-self.range, 
                                      self.range*2, 
                                      self.range*2))

    def draw(self, screen, camera):
        for pos in self.pos:
            x, y = camera.transform_to_screen(pos[0], pos[1], pos[2])
            pg.draw.circle(screen, 'blue', (x, y), self.range)