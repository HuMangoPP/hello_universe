from math import sqrt

RES = WIDTH, HEIGHT = 1280, 720
OUT_OF_BOUNDS = 100
FPS = 60

MIN_SIZE = 5
MAX_SIZE = 5
MAX_NUM_PARTS = 10

NEW_GEN_TIME = 10000

BASE_MIN_STATS = {
    'itl': 0,
    'pwr': 0,
    'def': 0,
    'mbl': 0,
    'hp': 1,
    'stl': 0,
}

BASE_MAX_STATS = {
    'itl': 1,
    'pwr': 1,
    'def': 1,
    'mbl': 5,
    'hp': 1,
    'stl': 1,
}

STAT_GAP = 5

BASE_STATS = {
    # intelligence has to do with heavioural traits of entities
    # awareness, vision, breeding/herding behaviour, etc
    'itl': 5,
    # power has to do with the raw damage output during combat
    # different types of moves/abilities and features that
    # are used during combat
    'pwr': 5,
    # defense has to do with damage absorption during combat
    # different types of fur/scales/feathers that might make
    # the entity more sturdy/capable of blocking attacks
    'def': 5,
    # mobility has to do with the movement/evasiveness during 
    # and outside of combat
    # dodging attacks, running away from other entities to avoid
    # combat, etc
    # stamina and mobility outside of combat
    'mbl': 20,
    # stealth has to do with evasiveness during and outside 
    # of combat
    # dodging attacks/fleeing from combat
    # detection/awareness outside of combat
    'stl': 5,
    # essentially a measure of population size
    # with each generation, health increases randomly
    'hp': 10,
    # maximum and minimum stats attainable as the current creature
    'min': BASE_MIN_STATS,
    'max': BASE_MAX_STATS,
}

TRAIT_AND_BODY_LEVELS = {
    'start': 1, # starting, does nothing, offers minimal benefits and minimal drawbacks
    'intermediate': 2, # does something, offers some benefits and some drawbacks
    'max': 3, # transforms into the full fledged thing
}

RESOURCE_TYPES = {
    'inorganic',        # chemical soup
    'energy',           # sunlight, energy, etc 
    'organic',          # vegetation
}

MODEL_COLORS = {
    'skeleton': 'white',
    'head': 'red',
    'hit_box': 'yellow',
    'hurt_box': 'magenta',
    'leg': 'green',
    'foot': 'blue'
}

### UI

# main menu rendering
CBODY_TEXTURE_KEY = {
    'sun': 'yellow',
    'mercury': 'gray',
    'venus': 'bisque',
    'earth': 'green',
    'mars': 'red',
    'jupiter': 'chocolate',
    'saturn': 'cornsilk3',
    'uranus': 'dodgerblue',
    'neptune': 'blue',
}

SUN = {
    'pos': [0, 0, 0],
    'vel': [0, 0],
    'size': 20,
    'type': 'sun',
}

ORBIT_RADIUS = 50

CBODIES = [
    {
        'pos': (30, 0),
        'vel': (0, sqrt(100/3)),
        'size': 2,
        'type': 'mercury',
    },
    {
        'pos': (60, 0),
        'vel': (0, sqrt(50/3)),
        'size': 4,
        'type': 'venus',
    },
    {
        'pos': (100, 0),
        'vel': (0, sqrt(10)),
        'size': 5,
        'type': 'earth',
    },
    {
        'pos': (200, 0),
        'vel': (0, sqrt(10/2)),
        'size': 3,
        'type': 'mars',
    },
    {
        'pos': (300, 0),
        'vel': (0, sqrt(10/3)),
        'size': 10,
        'type': 'jupiter'
    },
    {
        'pos': (400, 0),
        'vel': (0, sqrt(10/4)),
        'size': 8,
        'type': 'saturn',
    },
    {
        'pos': (550, 0),
        'vel': (0, sqrt(20/11)),
        'size': 7,
        'type': 'uranus',
    },
    {
        'pos': (700, 0),
        'vel': (0, sqrt(10/7)),
        'size': 6,
        'type': 'neptune',
    },
]

# health and energy
GAUGE_UI = {
    'radius': 75,
    'colours': [
                'red',
                'blue'
                ]
}

# stats
STAT_BAR_UI = {
    'bottom_pad': 50,
    'left_pad': 20,
    'width': 64,
    'bar_pad': 16,
    'frame_pad': 6,
    'colours': [
                'white',
                'orange',
                'blue',
                'green',
                'grey',
                ]
}

ATS_UI = {
    'bottom_pad': 100,
    'right_pad': 20,
    'frame_pad': 16,
    'icon_size': 64,
    'reg_pad': 10,
    'frame_width': 4,
}

HUD_HEIGHT = 164
HUD_WIDTH = 560
HUD_BOTTOM = HEIGHT-16

HEADER = 75
TITLE_FONT_SIZE = 24

# quests
QUEST_CARD_UI = {
    'w': 200,
    'h': 300,
    'p': 15,
    'c': {
        'alloc': (255, 0, 0),
        'ability': (0, 255, 0),
        'trait': (0, 0, 255),
        'upgrade': (255, 0, 255),
        'physiology': (0, 255, 255),
    },
    's_ratio': 2,
    'a_ratio': 2,
    'f': 12,
    'r': 200,
}

# interactions
INTERACTION_WHEEL_UI = {
    'out_r': 200,
    'in_r': 75,
    'c': (255, 255, 255), 
    'a': 50
}
