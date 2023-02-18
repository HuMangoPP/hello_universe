import pygame as pg
from math import atan2, cos, sin, sqrt, pi, exp
from src.combat.abilities import BASE_AOE_RADIUS
from src.combat.status_effects import MOVEMENT_IMPAIR_EFFECTS
from src.util.settings import WIDTH, MAX_SIZE, MIN_SIZE
from src.util.physics import new_vel, angles_between
from src.models.creature import Creature
from src.models.traits import Traits
from src.models.behaviour import Behaviour

sigmoid = lambda a, x : round(a * (1+exp(-x)))
sum_stats = lambda entities, index, stats : sum([entities.stats[index][stat_type] for stat_type in stats])

ENTITY_CALCULATIONS = {
    'energy': (lambda entities, index : 100 + sum_stats(entities, index, ['def', 'mbl'])),
    'intimidation': (lambda entities, index : BASE_AOE_RADIUS + sum_stats(entities, index, ['itl', 'pwr', 'mbl'])),
    'awareness': (lambda entities, index : 100 + sum_stats(entities, index, ['itl', 'stl'])),
    'stealth': (lambda entities, index : sum_stats(entities, index, ['itl', 'stl'])),
    'damage': (lambda entities, index : sum_stats(entities, index, ['pwr', 'def', 'mbl'])),
    'evasion': (lambda entities, index : sum_stats(entities, index, ['mbl', 'stl'])),
    'damage_mitigate': (lambda entities, index : sum_stats(entities, index, ['def', 'mbl'])),
    'movement': (lambda entities, index : 5 + sum_stats(entities, index, ['mbl'])),
    'max_legs': (lambda entities, index : sigmoid(entities.creature[index].num_parts*2, 
                                                  entities.stats[index]['mbl']/entities.creature[index].num_parts) 
                                                  - entities.creature[index].num_parts),
    'max_size': (lambda entities, index : sigmoid(2*MAX_SIZE, entities.creature[index].size/MAX_SIZE)),
    'min_size': (lambda entities, index : MIN_SIZE)
}

class Entities:
    ############################# 
    # init and spawning         #
    ############################# 
    def __init__(self):
        # physical/render data
        self.pos = []            
        self.vel = []  
        self.spd = []     
        self.acc = []          
        self.creature = []     
        self.scale = [] 

        # game data
        self.stats = [] 
        self.health = []
        self.energy = []    

        self.abilities = []      
        self.status_effects = []   
        self.traits = []        
        self.hurt_box = []      
        self.quests = []    

        self.behaviours = []    
    
    def add_new_entity(self, entity_data, stats):
        # physical/render data
        self.pos.append(entity_data['pos']) # [x, y, z, a]
        self.vel.append([0, 0, 0])          # [x, y, z]
        self.spd.append(entity_data['spd'])
        self.acc.append(entity_data['acc'])
        self.creature.append(Creature(num_parts=entity_data['body_parts'], 
                                      pos=entity_data['pos'], 
                                      size=entity_data['size'], 
                                      max_parts=entity_data['max_parts'],
                                      num_pair_legs=entity_data['num_legs'],
                                      leg_length=entity_data['leg_length']))
        self.scale.append(entity_data['scale'])

        # game data
        self.stats.append(stats)
        self.health.append(stats['hp'])
        self.energy.append(self.entity_calculation(len(self.energy), 'energy')) # energy calculation
        
        self.abilities.append(entity_data['abilities'])
        self.status_effects.append({
            'effects': [],
            'cd': [],
            'time': [],
            'source': [],
        })
        self.traits.append(Traits([], stats['min'], stats['max']))
        for trait in entity_data['traits']:
            index = len(self.traits)-1
            self.traits[index].give_traits(self.creature[index], trait)
        self.hurt_box.append(None)
        self.quests.append({})

        self.behaviours.append(Behaviour({
            'aggression': entity_data['aggression'],
            'herding': entity_data['herd']
        }))

        for i in range(len(self.behaviours)):
            self.behaviours[i].update_aggression(len(self.creature)-1, 0)
            self.behaviours[i].update_herd_behaviour(len(self.creature)-1, 0)

    ############################# 
    # draw, update, movement    #
    ############################# 
    def render(self, screen, camera):
        for i in range(len(self.creature)):
            dx = self.pos[i][0]-camera.pos[0]
            dy = self.pos[i][1]-camera.pos[1]
            if sqrt(dx**2+dy**2)<=WIDTH/2 and abs(self.scale[i] - camera.scale) <= 2:
                self.creature[i].render(screen, camera)
            # if self.hurt_box[i]:
            #     self.hurt_box[i].render(screen, camera)

    def update(self, camera, dt):
        self.spend_energy(dt)
        self.move(camera, dt)

    def parse_input(self, mv_input, camera, dt):

        index = mv_input['i']
        x_i = mv_input['x']
        y_i = mv_input['y']
        if 'ability_lock' in self.status_effects[index]['effects']:
            x_i, y_i = 0, 0
        
        # entity is stunned cannot move
        if 'stunned' in self.status_effects[index]['effects']:
            x_i, y_i = 0, 0

        # entity movement
        x_dir, y_dir = camera.screen_to_world(x_i, y_i)

        for j in range(len(self.status_effects[index]['effects'])):
            if self.status_effects[index]['effects'][j] == 'intimidated':
                source = self.status_effects[index]['source'][j]
                angle = angles_between(self.pos[source], self.pos[index])['z']
                x_dir, y_dir = cos(angle+pi), sin(angle+pi)

        self.vel[index][0] = new_vel(self.acc[index], self.vel[index][0], x_dir, dt)
        self.vel[index][1] = new_vel(self.acc[index], self.vel[index][1], y_dir, dt)

        if 'ability_lock' not in self.status_effects[index]['effects']:
            if self.vel[index][0]**2 + self.vel[index][1]**2 > self.spd[index]**2:
                # normalize the speed
                angle = atan2(y_dir, x_dir)
                self.vel[index][0] = self.spd[index]*cos(angle)
                self.vel[index][1] = self.spd[index]*sin(angle)

        for impair in MOVEMENT_IMPAIR_EFFECTS:
            if impair in self.status_effects[index]['effects']:
                self.vel[index][0] *= 0.8
                self.vel[index][1] *= 0.8
                # cumulative 20% reduction to movement speed if
                # entity is bleeding, poisoned, or weakened
   
    def move(self, camera, dt):
        for i in range(len(self.pos)):
            self.pos[i][0]+=self.vel[i][0]*dt
            self.pos[i][1]+=self.vel[i][1]*dt
            # angle the creature is facing
            if self.vel[i][0]**2+self.vel[i][1]**2!=0:
                self.pos[i][3] = atan2(self.vel[i][1], self.vel[i][0])

            # check if the entity is in bounds to
            # see if updating the model is necessary
            dx = self.pos[i][0]-camera.pos[0]
            dy = self.pos[i][1]-camera.pos[1]
            if sqrt(dx**2+dy**2)<=WIDTH/2:
                self.creature[i].move(self.pos[i], {
                    'effects': self.status_effects[i]['effects'], 
                    'time': self.status_effects[i]['time']
                }, self.vel[i][0]**2 + self.vel[i][1]**2 != 0)
    
    def spend_energy(self, dt):
        for i in range(len(self.energy)):
            spd_sq = (self.vel[i][0]**2 + self.vel[i][1]**2 + self.vel[i][2]**2)/1000
            mass = self.creature[i].num_parts*self.creature[i].size/10
            energy_spent = 1/2*mass*spd_sq
            if self.energy[i]<=0:
                # self.health[i]-=energy_spent*dt
                ...
            else:
                self.energy[i]-=energy_spent*dt
            total_energy = self.entity_calculation(i, 'energy')
            if self.energy[i]>total_energy:
                self.energy[i] = total_energy

    ####
    def kill(self, player, corpses):
        remove = []
        for i in range(len(self.health)):
            if self.health[i]<=0:
                remove.append(i)
        
        if player in remove:
            return True

        for j in range(len(remove)-1, -1, -1):
            i = remove[j]
            pos = self.pos[i]
            pos[2] = 0
            corpse_data = {
                'pos': pos,
                'nutrients': 100,
                'materials': {
                    'bone': 10,
                },
                'creature': self.creature[i]
            }
            corpses.add_new_corpse(corpse_data)
            self.pos[i:i+1] = []
            self.vel[i:i+1] = []
            self.spd[i:i+1] = []
            self.acc[i:i+1] = []
            self.creature[i:i+1] = []
            self.stats[i:i+1] = []
            self.health[i:i+1] = []
            self.energy[i:i+1] = []
            self.abilities[i:i+1] = []
            self.status_effects[i:i+1] = []
            self.traits[i:i+1] = []
            self.hurt_box[i:i+1] = []
            self.behaviours[i:i+1] = []

        return False

    def consume(self, index, target_index, corpses):
        self.energy[index] += corpses.nutrients[target_index]
        corpses.nutrients[target_index] = 0
        print(f'consumed')
    
    def scavenge(self, index, target_index, corpses):
        ...

    def entity_calculation(self, index, calculation):
        fn = ENTITY_CALCULATIONS[calculation]
        return fn(self, index)

    def health_and_energy_ratios(self, index):
        energy_ratio = self.energy[index]/self.entity_calculation(index, 'energy') * 100
        health_ratio = self.health[index]/self.stats[index]['hp'] * 100
        
        return [health_ratio, energy_ratio]

    def interact_calculation(self, index, index_preset, target, target_preset):
        calc = 0
        calc += self.entity_calculation(index, index_preset)
        calc -= self.entity_calculation(target, target_preset)
        return calc

    def get_entity_quest_data(self, index):
        data = self.get_entity_data(index)

        return data

    def get_entity_data(self, index):

        return {
            'creature': self.creature[index],
            'traits': self.traits[index],
            'stats': self.stats[index],
            'abilities': self.abilities[index],
            'max_stats': self.traits[index].max_stats
        }