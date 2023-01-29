import pygame as pg
from random import choice, randint
from math import atan2, cos, sin, sqrt, pi
from src.combat.abilities import BASIC_ABILITIES, ALL_ABILITIES, ActiveAbility, BASE_AOE_RADIUS
from src.combat.status_effects import BASE_CD
from src.util.settings import HEIGHT, WIDTH, STAT_GAP
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
        self.creature.append(Creature(entity_data['body_parts'], 
                                      entity_data['pos'], 
                                      entity_data['size'], 
                                      entity_data['num_legs'],
                                      entity_data['leg_length']))

        # game data
        self.stats.append(stats)
        self.health.append(stats['hp'])
        self.energy.append(self.stat_calculation(len(self.energy), preset='energy')) # energy calculation
        
        self.abilities.append(BASIC_ABILITIES)
        self.status_effects.append({
            'effects': [],
            'cd': [],
            'time': [],
            'source': [],
        })
        self.traits.append(Traits([], stats['min'], stats['max']))
        self.hurt_box.append(None)
        self.quests.append({
            'active': False,
            'type': '',
            'reward': '',
            'goal_type': '',
            'goal': 0,
            'progress': 0,
        })

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

        # entity movement
        x_dir, y_dir = camera.screen_to_world(x_i, y_i)

        self.vel[index][0] = new_vel(self.acc[index], self.vel[index][0], x_dir, dt)
        self.vel[index][1] = new_vel(self.acc[index], self.vel[index][1], y_dir, dt)

        if 'ability_lock' not in self.status_effects[index]['effects']:
            if self.vel[index][0]**2 + self.vel[index][1]**2 > self.spd[index]**2:
                # normalize the speed
                angle = atan2(y_dir, x_dir)
                self.vel[index][0] = self.spd[index]*cos(angle)
                self.vel[index][1] = self.spd[index]*sin(angle)
   
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
        
        print(calc)
        return calc


    def get_entity_data(self, index):
        stats = [
            self.stats[index]['itl'],
            self.stats[index]['pwr'],
            self.stats[index]['def'],
            self.stats[index]['mbl'],
            self.stats[index]['stl']
        ]

        max_stats = [
            self.traits[index].max_stats['itl'],
            self.traits[index].max_stats['pwr'],
            self.traits[index].max_stats['def'],
            self.traits[index].max_stats['mbl'],
            self.traits[index].max_stats['stl'],
        ]
        return {
            'creature': self.creature[index],
            'traits': self.traits[index],
            'stats': stats,
            'abilities': self.abilities[index],
            'max_stats': max_stats
        }