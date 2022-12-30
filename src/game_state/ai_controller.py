from math import atan2, cos, sin, sqrt, pi
from random import choice, randint
from src.combat.abilities import ALL_ABILITIES

class AIController:
    def __init__(self, non_controllable):
        self.non_controllable = non_controllable

    def movement_input(self, entity, camera):
        for i in range(len(entity.pos)):
            if i!=self.non_controllable:
                # give the ai controlled creature some 
                # movement input
                x_i, y_i = 0, 0
                for j in range(len(entity.pos)):
                    if i == j:
                        continue
                    dist = self.dist_between(entity.pos[i], entity.pos[j])
                    awareness = entity.awareness_calculation(entity.stats[i]['itl'],
                                                             entity.stats[j]['stl'])
                    aggression = entity.behaviours[i].aggression[j]

                    # determine the input to send
                    # TODO: sort input based on priority (aggression score) to see which one should be sent
                    if aggression>0 and dist<=awareness*aggression:
                        # move towards the target
                        angles = self.angles_between(entity.pos[i], entity.pos[j])
                        x_i = cos(angles['z'])
                        y_i = sin(angles['z'])
                    elif aggression<0 and dist<=awareness*abs(aggression):
                        angles = self.angles_between(entity.pos[i], entity.pos[j])
                        x_i = cos(angles['z']+pi)
                        y_i = sin(angles['z']+pi)
                
                # submit input to the updater
                if x_i==0 and y_i==0:
                    x_i, y_i = self.idle_movement()
                entity.parse_input(x_i, y_i, i, camera)

    def idle_movement(self):
        return randint(-1, 1), randint(-1, 1)

    def ability_input(self, entity, camera):
        for i in range(len(entity.abilities)):
            if i!=self.non_controllable:
                # give the ai controlled creature some 
                # ability input
                for j in range(len(entity.abilities)):
                    if i==j: continue

                    if 'ability_cd' not in entity.status_effects[i]['effects']:
                        dist = self.dist_between(entity.pos[i], entity.pos[j])
                        awareness = entity.awareness_calculation(entity.stats[i]['itl'],
                                                                entity.stats[j]['stl']) 
                        aggression = entity.behaviours[i].aggression[j]

                        if aggression>0:
                            if dist<=awareness*aggression/2:
                                angles = self.angles_between(entity.pos[i], entity.pos[j])
                                attack_abilities = list(filter(lambda ability: 'attack' in ALL_ABILITIES[ability]['type'], 
                                                    entity.abilities[i]))
                                queued_ability = choice(attack_abilities)
                                ability = {
                                    'ability': queued_ability,
                                    'angle': angles['z']
                                }
                                entity.use_ability(ability, i, camera)
    
    def dist_between(self, pos1, pos2):
        return sqrt((pos1[0]-pos2[0])**2+
                    (pos1[1]-pos2[1])**2+
                    (pos1[2]-pos2[2])**2)
    
    def angles_between(self, pos1, pos2):
        angles = {
            'x': atan2(pos2[2]-pos1[2], pos2[1]-pos1[1]),
            'y': atan2(pos2[2]-pos1[2], pos2[0]-pos1[0]),
            'z': atan2(pos2[1]-pos1[1], pos2[0]-pos1[0]),
        }
        return angles