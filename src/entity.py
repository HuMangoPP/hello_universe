import pygame as pg
from random import choice, randint
from math import atan2, cos, sin, sqrt, pi
from src.combat.abilities import BASIC_ABILITIES, ALL_ABILITIES, ActiveAbility
from src.settings import HEIGHT, WIDTH
from src.models.creature import Creature
from src.physics.physics import accelerate, de_accelerate
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
        self.health = [] # the entity's current health
        self.energy = [] # the entitiy's current energy level

        self.abilities = []
        self.status_effects = []
        self.traits = []
        self.hurt_box = []

        self.behaviours = []
    
    def add_new_entity(self, entity_data, stats):
        # physical/render data
        self.pos.append(entity_data['pos'])
        self.vel.append([0, 0, 0])
        self.spd.append(entity_data['spd'])
        self.acc.append(entity_data['acc'])
        self.creature.append(Creature(entity_data['body_parts'], 
                                      entity_data['pos'], 
                                      entity_data['size'], 
                                      entity_data['num_legs'],
                                      entity_data['leg_length']))

        # game data
        self.stats.append(stats)
        self.health.append(stats['health'])
        self.energy.append(self.energy_calculation(stats['power'], 
                                                   stats['defense'], 
                                                   entity_data['body_parts'])) # energy calculation
        
        self.abilities.append(BASIC_ABILITIES)
        self.status_effects.append({
            'effects': [],
            'cd': [],
            'time': [],
        })
        self.traits.append(Traits([], stats['min'], stats['max']))
        self.hurt_box.append(None)

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
    def draw(self, screen, camera):
        for i in range(len(self.creature)):
            if self.creature[i].draw(screen, camera) and self.hurt_box[i]:
                self.hurt_box[i].draw(screen, camera)

    def update(self):
        self.move()
        self.status_effect_cds()
        self.active_abilities()
        self.collide()

    def parse_input(self, x_i, y_i, player, camera):
        if 'ability_lock' in self.status_effects[player]['effects']:
            x_i, y_i = 0, 0

        # entity movement
        x_dir, y_dir = camera.screen_to_world(x_i, y_i)
        if x_dir==0:
            self.vel[player][0] = de_accelerate(self.acc[player], self.vel[player][0])
        else:
            self.vel[player][0] = accelerate(x_dir,
                                                 self.acc[player],
                                                 self.vel[player][0])
        
        if y_dir==0:
            self.vel[player][1] = de_accelerate(self.acc[player], self.vel[player][1])
        else:
            self.vel[player][1] = accelerate(y_dir,
                                                 self.acc[player],
                                                 self.vel[player][1])
        
        if 'ability_lock' not in self.status_effects[player]['effects']:
            if self.vel[player][0]**2 + self.vel[player][1]**2 > self.spd[player]**2:
                # normalize the speed
                ratio = sqrt(self.spd[player]**2/(self.vel[player][0]**2 + self.vel[player][1]**2))
                self.vel[player][0]*=ratio
                self.vel[player][1]*=ratio
    
    def move(self):
        for i in range(len(self.pos)):
            self.pos[i][0]+=self.vel[i][0]
            self.pos[i][1]+=self.vel[i][1]
            self.creature[i].move(self.pos[i])
    
    ############################# 
    # combat systems            #
    ############################# 
    def kill(self, player):
        remove = []
        for i in range(len(self.health)):
            if self.health[i]<=0:
                remove.append(i)
        
        if player in remove:
            return True

        for j in range(len(remove)-1, -1, -1):
            i = remove[j]
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

    def use_ability(self, a_i, player, camera):
        if a_i['ability']!=-1:
            # all abilities
            if type(a_i['ability']) is str:
                queued_ability = a_i['ability']
            else:
                queued_ability = self.abilities[player][a_i['ability']]
            
            self.status_effects[player]['effects'].append('ability_lock')
            self.status_effects[player]['cd'].append(ALL_ABILITIES[queued_ability]['cd'])
            self.status_effects[player]['time'].append(pg.time.get_ticks())

            # abilities with movement tag
            if 'movement' in ALL_ABILITIES[queued_ability]['type']:
                # get the direction of the movement
                x_dir = cos(a_i['angle'])
                y_dir = sin(a_i['angle'])
                x_dir, y_dir = camera.screen_to_world(x_dir, y_dir)
                angle = atan2(y_dir, x_dir)
                spd_mod = 3+(self.stats[player]['mobility']+self.stats[player]['power'])/100
                self.vel[player][0] = spd_mod*self.spd[player]*cos(angle)
                self.vel[player][1] = spd_mod*self.spd[player]*sin(angle)

                # update the entity hurt box to deal damage
                movement_hurt_box = []
                for part in self.creature[player].skeleton:
                    movement_hurt_box.append([part[0], part[1], part[2]])
                self.hurt_box[player] = ActiveAbility('movement', movement_hurt_box, 2*self.creature[player].size)

                # consume energy to use ability
                energy_usage = 1/2*self.creature[player].num_parts*(spd_mod*self.spd[player])**2/1000
                self.energy[player]-=energy_usage

            if 'strike' in ALL_ABILITIES[queued_ability]['type']:
                # get the strike direction
                x_dir = a_i['mx']-WIDTH//2
                y_dir = a_i['my']-HEIGHT//2
                x_dir, y_dir = camera.screen_to_world(x_dir, y_dir)
                angle = atan2(y_dir, x_dir)

                # update hurtboxes
                strike_hurt_box = []
                for i in range(10):
                    strike_hurt_box.append([self.pos[player][0]+i*2*self.creature[player].size*cos(angle), 
                                           self.pos[player][1]+i*2*self.creature[player].size*sin(angle),
                                           self.pos[player][2]])
                self.hurt_box[player] = ActiveAbility('strike', strike_hurt_box, 2*self.creature[player].size)

    def collide(self):
        for i in range(len(self.hurt_box)):
            if self.hurt_box[i]:
                for j in range(len(self.creature)):
                    if i!=j and self.creature[j].collide(self.hurt_box[i].get_pos()):
                        # decrease hp
                        self.health[j]-=1

                        # increase the target's aggression score against the attacker
                        self.behaviours[j].aggression[i]+=0.1

    def consume(self, index, target):
        energy_calculation = 0
        self.energy[index]+=energy_calculation
        pass

    def status_effect_cds(self):
        for i in range(len(self.status_effects)):
            if self.status_effects[i]['effects']:
                new_status_effects_cd = []
                new_status_effects = []
                new_status_effects_time = []
                for j in range(len(self.status_effects[i]['effects'])):
                    effect = self.status_effects[i]['effects'][j]
                    cd = self.status_effects[i]['cd'][j]
                    time = self.status_effects[i]['time'][j]
                    if pg.time.get_ticks()-time<cd:
                        new_status_effects_cd.append(cd)
                        new_status_effects.append(effect)
                        new_status_effects_time.append(time)
                    else:
                        if effect=='ability_lock':
                            self.hurt_box[i] = None
                    
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
        return max(intelligence-target_stealth, 1000)

    ############################# 
    # evolution systems         #
    ############################# 
    def remove_abilities(self, index):
        pass

    def give_abilities(self, index):
        if 'wings' in self.traits[index].traits and 'fly' not in self.abilities[index]:
            self.abilities[index].append('fly')
        
        if 'head_weapon' in self.traits[index].traits and 'rush' not in self.abilities[index]:
            self.abilities[index].append('rush')

        if 'leg_weapon' in self.traits[index].traits and 'slash' not in self.abilities[index]:
            self.abilities[index].append('slash')

    def new_generation(self):
        self.mutate()
        self.regen()

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
            'intelligence': (self.stats[i]['intelligence']+self.stats[i]['intelligence'])/2,
            'power': (self.stats[i]['power']+self.stats[j]['power'])/2,
            'defense': (self.stats[i]['defense']+self.stats[j]['defense'])/2,
            'health': (self.stats[i]['health']+self.stats[j]['health'])/2,
            'mobility': (self.stats[i]['mobility']+self.stats[j]['mobility'])/2,
            'stealth': (self.stats[i]['stealth']+self.stats[j]['stealth'])/2,
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
            'intelligence': self.stats[i]['intelligence'],
            'power': self.stats[i]['power'],
            'defense': self.stats[i]['defense'],
            'health': self.stats[i]['health'],
            'mobility': self.stats[i]['mobility'],
            'stealth': self.stats[i]['stealth'],
            'min': self.traits[i].min_stats.copy(),
            'max': self.traits[i].max_stats.copy(),
        }

        self.add_new_entity(entity_data, stats)

    def mutate(self):
        # mutation is completely random
        # choose a random stat to decrease and increase
        for i in range(len(self.stats)):
            # increasing and decreasing stats
            increase = choice(list(self.stats[i].keys())[:6])
            decrease = choice(list(self.stats[i].keys())[:6])
            self.stats[i][increase]+=randint(1, 2)
            self.stats[i][decrease]-=randint(1, 2)
            if self.stats[i][decrease]<self.traits[i].min_stats[decrease]:
                self.stats[i][decrease] = self.traits[i].min_stats[decrease]
            if self.stats[i][increase]>self.traits[i].max_stats[increase]:
                self.stats[i][increase] = self.traits[i].max_stats[increase]
            
            # choosing stats to let creatures "breakthrough"
            breakthrough = choice(list(self.stats[i].keys())[:6])
            if self.stats[i][breakthrough] == self.traits[i].max_stats[breakthrough]:
                # if the chosen stat is at the maximum, "roll" the dice to
                # see if the creature can breakthrough
                roll = randint(1,6)
                if roll==1:
                    self.traits[i].change_physiology(self.creature[i], breakthrough)

            # giving creatures traits and abilities based on their new stats
            self.traits[i].give_traits(self.creature[i], self.stats[i])
            self.remove_abilities(i)
            self.give_abilities(i)
    
    def regen(self):
        for i in range(len(self.health)):
            if self.health[i]<self.stats[i]['health']:
                self.health[i]+=1
