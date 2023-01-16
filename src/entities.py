import pygame as pg
from random import choice, randint
from math import atan2, cos, sin, sqrt, pi
from src.combat.abilities import BASIC_ABILITIES, ALL_ABILITIES, ActiveAbility
from src.combat.status_effects import BASE_CD
from src.settings import HEIGHT, WIDTH, STAT_GAP
from src.physics.physics import new_vel
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
        self.energy.append(self.energy_calculation(stats['pwr'], 
                                                   stats['def'], 
                                                   entity_data['body_parts'])) # energy calculation
        
        self.abilities.append(BASIC_ABILITIES)
        self.status_effects.append({
            'effects': [],
            'cd': [],
            'time': [],
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
            self.creature[i].render(screen, camera)

    def update(self, dt):
        self.spend_energy(dt)
        self.move(dt)
        self.status_effect_cds()
        self.active_abilities()
        self.collide()

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
                ratio = sqrt(self.spd[index]**2/(self.vel[index][0]**2 + self.vel[index][1]**2))
                self.vel[index][0]*=ratio
                self.vel[index][1]*=ratio

        
    def move(self, dt):
        for i in range(len(self.pos)):
            self.pos[i][0]+=self.vel[i][0]*dt
            self.pos[i][1]+=self.vel[i][1]*dt
            # angle the creature is facing
            if self.vel[i][0]**2+self.vel[i][1]**2!=0:
                self.pos[i][3] = atan2(self.vel[i][1], self.vel[i][0])
            self.creature[i].move(self.pos[i])
    
    ############################# 
    # combat systems            #
    ############################# 
    def spend_energy(self, dt):
        for i in range(len(self.energy)):
            spd_sq = self.vel[i][0]**2 + self.vel[i][1]**2 + self.vel[i][2]**2
            energy_spent = 1/2000*self.creature[i].num_parts*spd_sq
            if self.energy[i]<=0:
                self.health[i]-=energy_spent*dt
            else:
                self.energy[i]-=energy_spent*dt
            total_energy = self.energy_calculation(self.stats[i]['pwr'], self.stats[i]['def'], self.creature[i].num_parts)
            if self.energy[i]>total_energy:
                self.energy[i] = total_energy

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

    def use_ability(self, abl_input, camera):
        a_i = abl_input['ability']
        index = abl_input['i']
        input_angle =  abl_input['angle']
        # no input 
        if a_i==-1:
            return
        
        # prevent spamming
        if 'ability_lock' in self.status_effects[index]['effects']:
            return

        # all abilities
        queued_ability = a_i
            
        self.status_effects[index]['effects'].append('ability_lock')
        self.status_effects[index]['cd'].append(ALL_ABILITIES[queued_ability]['cd'])
        self.status_effects[index]['time'].append(pg.time.get_ticks())

        # abilities with movement tag
        if 'movement' in ALL_ABILITIES[queued_ability]['type']:
            # get the direction of the movement
            x_dir = cos(input_angle)
            y_dir = sin(input_angle)
            x_dir, y_dir = camera.screen_to_world(x_dir, y_dir)
            angle = atan2(y_dir, x_dir)
            spd_mod = 3+(self.stats[index]['mbl']+self.stats[index]['pwr'])/100
            self.vel[index][0] = spd_mod*self.spd[index]*cos(angle)
            self.vel[index][1] = spd_mod*self.spd[index]*sin(angle)

            # update the entity hurt box to deal damage
            movement_hurt_box = []
            for part in self.creature[index].skeleton:
                movement_hurt_box.append([part[0], part[1], part[2]])
            
            self.hurt_box[index] = ActiveAbility('movement', movement_hurt_box, 2*self.creature[index].size)

            # consume energy to use ability
            energy_usage = 1/2*self.creature[index].num_parts*(spd_mod*self.spd[index])**2/1000
            self.energy[index]-=energy_usage

        if 'strike' in ALL_ABILITIES[queued_ability]['type']:
            # get the strike direction
            x_dir = cos(a_i['angle'])
            y_dir = sin(a_i['angle'])
            x_dir, y_dir = camera.screen_to_world(x_dir, y_dir)
            angle = atan2(y_dir, x_dir)

            # update hurtboxes
            strike_hurt_box = []
            for i in range(10):
                strike_hurt_box.append([self.pos[index][0]+i*2*self.creature[index].size*cos(angle), 
                                       self.pos[index][1]+i*2*self.creature[index].size*sin(angle),
                                       self.pos[index][2]])
            self.hurt_box[index] = ActiveAbility('strike', strike_hurt_box, 2*self.creature[index].size)

    def collide(self):
        for i in range(len(self.hurt_box)):
            if self.hurt_box[i]:
                for j in range(len(self.creature)):
                    if i!=j and self.creature[j].collide(self.hurt_box[i].get_pos()):
                        # decrease hp
                        self.health[j]-=10

                        # increase the target's aggression score against the attacker
                        self.behaviours[j].aggression[i]+=0.1

    def status_effect_cds(self):
        # entity loop
        for i in range(len(self.status_effects)):
            if self.status_effects[i]['effects']:
                new_status_effects_cd = []
                new_status_effects = []
                new_status_effects_time = []
                # status loop
                for j in range(len(self.status_effects[i]['effects'])):
                    effect = self.status_effects[i]['effects'][j]
                    cd = self.status_effects[i]['cd'][j]
                    time = self.status_effects[i]['time'][j]
                    if pg.time.get_ticks()-time<cd:
                        new_status_effects_cd.append(cd)
                        new_status_effects.append(effect)
                        new_status_effects_time.append(time)
                    else:
                        if effect == 'ability_lock':
                            self.hurt_box[i] = None
                            new_status_effects_cd.append(BASE_CD)
                            new_status_effects.append('ability_cd')
                            new_status_effects_time.append(pg.time.get_ticks())
                    
                self.status_effects[i]['cd'] = new_status_effects_cd
                self.status_effects[i]['effects'] = new_status_effects
                self.status_effects[i]['time'] = new_status_effects_time

    def active_abilities(self):
        for i in range(len(self.hurt_box)):
            if self.hurt_box[i] and self.hurt_box[i].type=='movement':
                movement_hurt_box = []
                for part in self.creature[i].skeleton:
                    movement_hurt_box.append([part[0], part[1], part[2]])
                self.hurt_box[i].update(movement_hurt_box, 2*self.creature[i].size)

    def energy_calculation(self, power, defense, num_parts):
        return power+defense+num_parts

    def awareness_calculation(self, intelligence, target_stealth):
        # return max(intelligence-target_stealth, 1000)
        return 100*max(intelligence-target_stealth, 1)

    def consume(self, index, target_index, corpses):
        self.energy[index] += corpses.nutrients[target_index]
        corpses.nutrients[target_index] = 0
        print(f'consumed')

    ############################# 
    # evolution systems         #
    ############################# 
    def give_abilities(self, index, ability):
        self.abilities[index].append(ability)

    def give_traits(self, index, trait):
        self.traits[index].give_traits(self.creature[index], trait)

    def allocate_stat(self, index, stat):
        self.stats[index]['max'][stat]+=1

    def new_generation(self):
        self.mutate()
        # self.regen()
        self.behaviour_shift()

    def inter_species_reproduce(self, i, j):
        # inter-species reproduction allows for reproduction
        # with another creature
        # the new creature will get traits from both parents
        # to perform inter-species reproduction, a world quest must be completed

        i = 0
        j = 0

        entity_data = {
            'pos': self.pos[i].copy(),
            'spd': (self.spd[i]+self.spd[j])/2,
            'acc': (self.acc[i]+self.acc[j])/2,
            'body_parts': int((self.creature[i].num_parts+self.creature[j].num_parts)/2),
            'size': (self.creature[i].size+self.creature[j].size)/2,
            'num_legs': int((self.creature[i].legs.num_pair_legs+self.creature[j].legs.num_pair_legs)/2),
            'leg_length': int((self.creature[i].legs.leg_length+self.creature[i].legs.leg_length)/2),
        }
        stats = {
            'itl': (self.stats[i]['itl']+self.stats[i]['itl'])/2,
            'pwr': (self.stats[i]['pwr']+self.stats[j]['pwr'])/2,
            'def': (self.stats[i]['def']+self.stats[j]['def'])/2,
            'hp': (self.stats[i]['hp']+self.stats[j]['hp'])/2,
            'mbl': (self.stats[i]['mbl']+self.stats[j]['mbl'])/2,
            'stl': (self.stats[i]['stl']+self.stats[j]['stl'])/2,
            'min': 0,
            'max': 0,
        }
        self.add_new_entity(entity_data, stats)

    def in_species_reproduce(self, i):
        # in-species reproduction allows for reproduction in-species
        # has the possibility of generating new mutations and traits
        i = 0
        entity_data = {
            'pos': self.pos[i].copy(),
            'spd': self.spd[i],
            'acc': self.acc[i],
            'body_parts': int(self.creature[i].num_parts),
            'size': int(self.creature[i].size),
            'num_legs': int(self.creature[i].legs.num_pair_legs),
            'leg_length': int(self.creature[i].legs.leg_length),
            'aggression': self.behaviours[i].aggression.copy(),
            'herd': self.behaviours[i].herding.copy(),
        }

        stats = {
            'itl': self.stats[i]['itl'],
            'pwr': self.stats[i]['pwr'],
            'def': self.stats[i]['def'],
            'hp': self.stats[i]['hp'],
            'mbl': self.stats[i]['mbl'],
            'stl': self.stats[i]['stl'],
            'min': self.traits[i].min_stats.copy(),
            'max': self.traits[i].max_stats.copy(),
        }

        self.add_new_entity(entity_data, stats)

    def mutate(self):
        # mutation is completely random
        # choose a random stat to decrease and increase
        for i in range(len(self.stats)):
            # increasing and decreasing stats
            increase = choice(list(self.stats[i].keys())[:5])
            decrease = choice(list(self.stats[i].keys())[:5])
            self.stats[i][increase]+=randint(1, 2)
            self.stats[i][decrease]-=randint(1, 2)

            if self.stats[i][decrease]<self.traits[i].min_stats[decrease]*STAT_GAP:
                self.stats[i][decrease] = self.traits[i].min_stats[decrease]*STAT_GAP
            if self.stats[i][increase]>self.traits[i].max_stats[increase]*STAT_GAP:
                self.stats[i][increase] = self.traits[i].max_stats[increase]*STAT_GAP

    def behaviour_shift(self):
        for behaviour in self.behaviours:
            behaviour.shift()

    def regen(self):
        for i in range(len(self.health)):
            if self.health[i]<self.stats[i]['hp']:
                self.health[i]+=1

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
    
    def rec_quest(self, index, quest):
        if not self.quests[index]['active']:
            quest['progress'] = 0
            quest['active'] = False
            self.quests[index] = quest

            # for now, accepting a quest automatically completes it
            reward = self.quests[index]['reward']
            match self.quests[index]['type']:
                case 'upgrade':
                    self.stats[index][reward]+=1
                    print(f"upgraded {reward}")
                case 'alloc':
                    self.allocate_stat(index, reward)
                    print(f"allocated {reward}")
                case 'trait':
                    self.give_traits(index, reward)
                case 'ability':
                    self.give_abilities(index, reward)