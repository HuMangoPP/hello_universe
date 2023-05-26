# import pygame as pg
# from src.util.settings import MODEL_COLORS

# MAX_NUM_ABILITIES = 5

# BASIC_ABILITIES = [
#     'dash', # basic charging move // body slam
#     'intimidate', # basic intimidation move
# ]

# SPECIAL_ABILITIES = [
#     'grapple', # with arm/tongue/tail with high intelligence
#     'bite', # with mouth and teeth
#     'hit', # with legs/arm/tail
#     'rush' # upgraded version of advance with antlers/horn/corn
#     'fly', # for flying creatures -> basically increase z value
#     'swim', # for swimming creatures -> decrease z value and move in water
#     # 'run', # begin running for creatures that can run -> faster top speed
#     'throw', # with arm/leg/tongue with high mobility -> must be able to grapple
#     'slash', # with leg weapon -> deals bleed status effect
# ]

# ALL_ABILITIES = {
#     'dash': {
#         'type': ['attack', 'skillshot', 'movement'],
#         'modifiers': [],
#         'side_effects': ['ability_lock'],
#         'cd': 500,
#     },
#     'intimidate': {
#         'type': ['utility', 'aoe', 'debuff'],
#         'modifiers': ['weakened', 'intimidated'],
#         'side_effects': ['ability_lock'],
#         'cd': 500,
#     },
#     'rush': {
#         'type': ['attack', 'skillshot', 'movement'],
#         'modifiers': ['stunned'],
#         'side_effects': ['ability_lock'],
#         'cd': 500,
#     },
#     'hit': {
#         'type': ['attack', 'skillshot', 'strike'],
#         'modifiers': ['stunned'],
#         'side_effects': ['ability_lock', 'strike'],
#         'cd': 500,
#     },
#     'bite': {
#         'type': ['attack', 'target'],
#         'modifiers': ['bleeding'],
#         'side_effects': ['ability_lock'],
#         'cd': 500,
#     },
#     'slash': { # should this be different from hit or should they be comined and the bleeding attribute given with the claw trait?
#         'type': ['attack', 'skillshot', 'strike'],
#         'modifiers': ['bleeding'],
#         'side_effects': ['ability_lock', 'strike'],
#         'cd': 500,
#     },
#     'fly': {
#         'type': ['utility', 'skillshot', 'movement', 'toggle'],
#         'modifiers': [],
#         'side_effects': ['ability_lock', 'in_air'],
#         'cd': 500,
#     },
#     'swim': {
#         'type': ['utility', 'skillshot', 'movement', 'toggle'],
#         'modifiers': [],
#         'side_effects': ['ability_lock', 'underwater'],
#         'cd': 500,
#     },
#     'grapple': {
#         'type': ['utility', 'toggle'],
#         'modifiers': [],
#         'side_effects': ['ability_lock', 'grapple'],
#         'cd': 500
#     },
#     'throw': {
#         'type': ['attack', 'skillshot'],
#         'modifiers': [],
#         'side_effects': ['ability_lock', 'grapple'],
#         'cd': 500,
#     }
# }

# BASE_AOE_RADIUS = 500

# class ActiveAbility:
#     def __init__(self, type, pos, modifiers, range):
#         self.type = type
#         self.modifiers = modifiers
#         self.damaging = False
#         self.update(pos, range)
    
#     def update(self, pos, range):
#         self.pos = pos
#         self.range = range
    
#     def get_pos(self):
#         all_pos = []
#          # gets the position and size of the hit_boxes
#         for pos in self.pos:
#             all_pos.append([pos[0], pos[1], pos[2], self.range])

#         return all_pos

#     def render(self, screen, camera):
#         for pos in self.pos:
#             x, y = camera.transform_to_screen(pos)
#             pg.draw.circle(screen, MODEL_COLORS['hit_box'], (x, y), self.range, 1)