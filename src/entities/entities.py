import pygame as pg
from math import atan2, cos, sin, sqrt, pi
from src.combat.abilities import BASE_AOE_RADIUS
from src.combat.status_effects import MOVEMENT_IMPAIR_EFFECTS
from src.util.settings import WIDTH
from src.util.physics import new_vel
from src.models.creature import Creature
from src.models.traits import Traits
from src.models.behaviour import Behaviour

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
                                      max_size=entity_data['max_size'],
                                      num_pair_legs=entity_data['num_legs'],
                                      leg_length=entity_data['leg_length']))

        # game data
        self.stats.append(stats)
        self.health.append(stats['hp'])
        self.energy.append(self.stat_calculation(len(self.energy), preset='energy')) # energy calculation
        
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
            if sqrt(dx**2+dy**2)<=WIDTH/2:
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
                angle = atan2(self.pos[source][1]-self.pos[index][1],
                              self.pos[source][0]-self.pos[index][0])
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
                })
    
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
            total_energy = self.stat_calculation(i, preset='energy')
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

    def stat_calculation(self, index, preset):
        calc = 0
        
        # presets
        stats_to_calc = []
        constants = []
        if preset == 'energy':
            stats_to_calc = ['def', 'pwr']
            constants = [100]
        elif preset == 'intimidation':
            stats_to_calc = ['itl', 'pwr', 'mbl']
            constants = [BASE_AOE_RADIUS]
        elif preset == 'awareness':
            stats_to_calc = ['itl', 'stl']
            constants = [100]
        elif preset == 'stealth':
            stats_to_calc = ['itl', 'stl']
            constants = []
        elif preset == 'damage':
            stats_to_calc = ['pwr', 'def', 'mbl']
            constants = []
        elif preset == 'evasion':
            stats_to_calc = ['mbl', 'stl']
            constants = []
        elif preset == 'damage_mitigate':
            stats_to_calc = ['def', 'mbl']
            constants = []
        elif preset == 'movement':
            stats_to_calc = ['mbl']
            constants = [5]

        for stat_to_calc in stats_to_calc:
            calc+=self.stats[index][stat_to_calc]
        for constant in constants:
            calc+=constant
        return calc

    def max_calc(self, index, preset):
        calc = 0

        # presets
        stats_to_calc = []
        constants = []
        if preset == 'potential_growth_size':
            stats_to_calc = ['def', 'mbl']
            constants = []
        
        for stat_to_calc in stats_to_calc:
            calc+=self.stats[index]['max'][stat_to_calc]
        for constant in constants:
            calc+=constant
        
        return calc
    
    def health_and_energy_ratios(self, index):
        energy_ratio = self.energy[index]/self.stat_calculation(index, 'energy') * 100
        health_ratio = self.health[index]/self.stats[index]['hp'] * 100
        
        return [health_ratio, energy_ratio]

    def interact_calculation(self, index, index_preset, target, target_preset):
        calc = 0
        calc += self.stat_calculation(index, preset=index_preset)
        calc -= self.stat_calculation(target, preset=target_preset)
        return calc

    # TODO: figure out how to format this to take into account other calculations like
    # maybe size/num_parts/etc
    def detailed_calculation(self, index, preset, fns):
        calc = self.stat_calculation(index, preset)
        for fn in fns:
            calc = fn(calc)
        
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