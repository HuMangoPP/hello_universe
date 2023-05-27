# from math import cos, sin, pi
# from random import choice, randint
# from src.combat.abilities import ALL_ABILITIES
# from src.combat.world_event import WorldEvent

# from src.util.physics import dist_between, angles_between

# class AIController:
#     def __init__(self, non_controllable):
#         self.non_controllable = non_controllable

#     def movement_input(self, entities, corpses, camera, dt):
#         for i in range(len(entities.pos)):
#             if i!=self.non_controllable:
#                 # give the ai controlled creature some 
#                 # movement input
#                 x_i, y_i = 0, 0
                
#                 # detect enemies
#                 x_i, y_i = self.detect_enemies(entities, i)

#                 # detect food
#                 x, y = self.detect_food(corpses, entities, i)
#                 if x or y:
#                     x_i, y_i = x, y

#                 # submit input to the updater
#                 if x_i==0 and y_i==0:
#                     x_i, y_i = self.idle_movement()
#                 entities.parse_input({
#                     'i': i,
#                     'x': x_i,
#                     'y': y_i
#                 }, camera, dt)

#     def detect_food(self, corpses, entities, index):
#         for i in range(len(corpses.pos)):
#             dist = dist_between(entities.pos[index], corpses.pos[i])
#             awareness = 500
#             if self.corpse_interact(entities, corpses, index, i, dist):
#                 continue
#             if dist<=awareness:
#                 angles = angles_between(entities.pos[index], corpses.pos[i])
#                 return cos(angles['z']), sin(angles['z'])

#         return 0, 0

#     def detect_enemies(self, entities, index):
#         for i in range(len(entities.pos)):
#             if i != index:
#                 dist = dist_between(entities.pos[i], entities.pos[index])
#                 awareness = entities.interact_calculation(index, 'awareness', i, 'stealth')
#                 aggression = entities.behaviours[index].aggression[i]
#                 # determine the input to send
#                 # TODO: sort input based on priority (aggression score) to see which one should be sent
#                 if aggression>0 and dist<=awareness*aggression:
#                     # move towards the target
#                     angles = angles_between(entities.pos[index], entities.pos[i])
#                     return cos(angles['z']), sin(angles['z'])
#                 elif aggression<0 and dist<=awareness*abs(aggression):
#                     angles = angles_between(entities.pos[index], entities.pos[i])
#                     return cos(angles['z']+pi), sin(angles['z']+pi)
#         return 0, 0

#     def idle_movement(self):
#         return randint(-1, 1), randint(-1, 1)

#     def ability_input(self, entities, combat_systemm):
#         for i in range(len(entities.abilities)):
#             if i!=self.non_controllable:
#                 # give the ai controlled creature some 
#                 # ability input
#                 for j in range(len(entities.abilities)):
#                     if i==j: continue

#                     if 'ability_cd' not in entities.status_effects[i]['effects']:
#                         dist = dist_between(entities.pos[i], entities.pos[j])
#                         awareness = entities.interact_calculation(i, 'awareness', j, 'stealth')
#                         aggression = entities.behaviours[i].aggression[j]

#                         if aggression>0:
#                             if dist<=awareness*aggression/2:
#                                 angles = angles_between(entities.pos[i], entities.pos[j])
#                                 attack_abilities = list(filter(lambda ability: 'attack' in ALL_ABILITIES[ability]['type'], 
#                                                     entities.abilities[i]))
#                                 queued_ability = choice(attack_abilities)
#                                 ability = {
#                                     'i': i,
#                                     'ability': queued_ability,
#                                     'angle': angles['z']
#                                 }
#                                 combat_systemm.use_ability(ability)
    
#     def accept_quests(self, entities, evo_system):
#         for i in range(len(entities.stats)):
#             if i != self.non_controllable:

#                 quests = WorldEvent(entities, i).quests
#                 abl_tr_quests = list(filter(lambda quest : quest['type'] in ['ability', 'trait'], quests))
#                 alloc_quests = list(filter(lambda quest : quest['type'] == 'alloc', quests))
#                 upg_quests = list(filter(lambda quest : quest['type'] == 'upgrade', quests))
#                 if abl_tr_quests:
#                     evo_system.rec_quest(i, abl_tr_quests[0])
#                 elif alloc_quests:
#                     evo_system.rec_quest(i, alloc_quests[0])
#                 else:
#                     evo_system.rec_quest(i, upg_quests[0])

#     def corpse_interact(self, entities, corpses, index, target, dist):
#         if entities.energy[index]<entities.stat_calculation(index, preset='energy')/2:
#             if dist<=100:
#                 entities.consume(index, target, corpses)
#                 return True

#         return False

import numpy as np
import math

BASIC_MOVEMENTS = {
    'move_forward': 0,
    'turn_right': 1,
    'turn_left': 2,
}

DEFAULT_TURN = math.pi/6

class Agents:
    def __init__(self, no_control: int):
        self.no_control = no_control # defines which entity is not ai controlled
    

    def agent_input(self, entity_manager, environment, camera):
        for i, (pos, angle, receptors, brain) in enumerate(zip(entity_manager.pos, 
                                                  entity_manager.flat_angle,
                                                  entity_manager.receptors,
                                                  entity_manager.brain)):
            if i == self.no_control: continue
            receptors.poll_sensory(pos, angle, 100, environment)

            sensory = np.array([receptors.sensory[receptor_type]
                                for receptor_type in receptors.sensory]).flatten()
            actions = brain.think(sensory)
            new_angle = angle
            if BASIC_MOVEMENTS['turn_right'] in actions:
                new_angle += DEFAULT_TURN
            elif BASIC_MOVEMENTS['turn_left'] in actions:
                new_angle -= DEFAULT_TURN
            if actions.size > 0:
                entity_manager.input(camera, {
                    'index': i,
                    'x': math.cos(new_angle),
                    'y': math.sin(new_angle)
                })
            else: 
                entity_manager.input(camera, {
                    'index': i,
                    'x': 0,
                    'y': 0
                })