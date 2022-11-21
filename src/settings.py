import pygame as pg

RES = WIDTH, HEIGHT = 1280, 720
FPS = 60

NEW_GEN_TIME = 100

BASE_STATS = {
    # intelligence has to do with heavioural traits of entities
    # awareness, vision, breeding/herding behaviour, etc
    'intelligence': 50,
    # power has to do with the raw damage output during combat
    # different types of moves/abilities and features that
    # are used during combat
    'power': 0,
    # defense has to do with damage absorption during combat
    # different types of fur/scales/feathers that might make
    # the entity more sturdy/capable of blocking attacks
    'defense': 0,
    # mobility has to do with the movement/evasiveness during 
    # and outside of combat
    # dodging attacks, running away from other entities to avoid
    # combat, etc
    # stamina and mobility outside of combat
    'mobility': 10,
    # essentially a measure of population size
    # with each generation, health increases randomly
    'health': 10,
    # stealth has to do with evasiveness during and outside 
    # of combat
    # dodging attacks/fleeing from combat
    # detection/awareness outside of combat
    'stealth': 0,
}

TRAITS = [
    'legs',
    'body_segments',
]

MODEL_COLORS = {
    'skeleton': 'white',
    'head': 'red',
    'hit_box': 'yellow',
    'hurt_box': 'magenta',
    'leg': 'green',
    'foot': 'blue'
}


STAT_COLORS = [
    'white',
    'orange',
    'blue',
    'green',
    'grey',
]

# UI
EDGE_PADDING = 50
HEALTH_AND_ENERGY_RADIUS = 75
GAUGE_COLORS = [
    'red',
    'blue'
]
BAR_WIDTH = 40
UI_BG_COLOR = pg.Color(99, 41, 107)
UI_BG_WDITH = 400
UI_BG_HEIGHT = 175
ABILITY_Y_ALIGN = HEIGHT - 50
TRAIT_Y_ALIGN = HEIGHT - 120