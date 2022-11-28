from math import atan2, cos, sin, sqrt
from random import choice
from src.combat.abilities import ALL_ABILITIES

class AIController:
    def __init__(self, index):
        self.index = index

    def movement_input(self, entity, camera):
        for i in range(len(entity.pos)):
            if i!=self.index:
                # give the ai controlled creature some 
                # movement input
                for j in range(len(entity.pos)):
                    dist = self.dist_between(entity.pos[i], entity.pos[j])
                    awareness = entity.awareness_calculation(entity.stats[i]['intelligence'],
                                                             entity.stats[j]['stealth'])
                    aggression = entity.behaviours[i].aggression[j]

                    if aggression>0:
                        if dist<=awareness*aggression:
                            # move towards the target
                            angles = self.angles_between(entity.pos[i], entity.pos[j])
                            entity.parse_input(cos(angles['z']), sin(angles['z']), i, camera)
                        else: 
                            entity.parse_input(0, 0, i, camera)
                    else:
                        if dist<=awareness*abs(aggression):
                            # move away from the target
                            pass

    def ability_input(self, entity, camera):
        for i in range(len(entity.pos)):
            if i!=self.index:
                # give the ai controlled creature some 
                # ability input
                for j in range(len(entity.pos)):
                    dist = self.dist_between(entity.pos[i], entity.pos[j])
                    awareness = entity.awareness_calculation(entity.stats[i]['intelligence'],
                                                             entity.stats[j]['stealth']) 
                    aggression = entity.behaviours[i].aggression[j]

                    if aggression>0:
                        if dist<=awareness*aggression/2:
                            angles = self.angles_between(entity.pos[i], entity.pos[j])
                            attack_abilities = list(filter(lambda ability: 'attack' in ALL_ABILITIES[ability]['type'], 
                                                entity.abilities[i]))
                            queued_ability = choice(attack_abilities)
                            print(queued_ability)
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