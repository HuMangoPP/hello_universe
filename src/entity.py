import pygame as pg
from random import choice, randint
from math import atan2, cos, sin, sqrt, pi
from src.combat.abilities import BASIC_ABILITIES, ALL_ABILITIES, ActiveAbility
from src.settings import HEIGHT, WIDTH
from src.models.creature import Creature
from src.physics import accelerate, de_accelerate
from src.models.traits import Traits

class Entities:
    def __init__(self):
        # physical/render data
        self.pos = []
        self.vel = []
        self.spd = []
        self.acc = []
        self.render = []

        # game data
        self.stats = []
        self.health = [] # the entity's current health
        self.energy = [] # the entitiy's current energy level

        self.abilities = []
        self.status_effects = []
        self.traits = []
        self.hurt_box = []
    
    def add_new_entity(self, entity_data, stats):
        # physical/render data
        self.pos.append(entity_data['pos'])
        self.vel.append([0, 0, 0])
        self.spd.append(entity_data['spd'])
        self.acc.append(entity_data['acc'])
        body_parts = entity_data['body_parts']
        size = entity_data['size']
        num_legs = entity_data['num_legs']
        leg_length = entity_data['leg_length']
        self.render.append(Creature(body_parts, entity_data['pos'], size, num_legs, leg_length))

        # game data
        self.stats.append(stats)
        self.health.append(stats['health'])
        self.energy.append((self.stats[len(self.stats)-1]['power']+
                            self.stats[len(self.stats)-1]['defense']+
                            self.render[len(self.render)-1].num_parts)) # calculation based on stats
        self.abilities.append(BASIC_ABILITIES)
        self.status_effects.append({
            'effects': [],
            'cd': [],
            'time': [],
        })
        self.traits.append(Traits([], {
            'intelligence': 0,
            'power': 0,
            'defense': 0,
            'mobility': 0,
            'health': 1,
            'stealth': 0,
        }))
        self.hurt_box.append(None)
    
    def draw(self, screen, camera):
        for i in range(len(self.render)):
            self.render[i].draw(screen, camera)
            if self.hurt_box[i]:
                self.hurt_box[i].draw(screen, camera)

    def update(self):
        self.move()
        self.status_effect_cds()
        self.active_abilities()
        self.collide()

    def use_ability(self, a_i, player, camera):
        if a_i['ability']!=-1:
            # all abilities
            self.status_effects[player]['effects'].append('ability_lock')
            self.status_effects[player]['cd'].append(ALL_ABILITIES[self.abilities[player][a_i['ability']]]['cd'])
            self.status_effects[player]['time'].append(pg.time.get_ticks())

            # abilities with movement tag
            if 'movement' in ALL_ABILITIES[self.abilities[player][a_i['ability']]]['type']:
                # get the direction of the movement

                x_dir = a_i['mx']-WIDTH//2
                y_dir = a_i['my']-HEIGHT//2
                x_dir, y_dir = camera.screen_to_world(x_dir, y_dir)
                angle = atan2(y_dir, x_dir)
                spd_mod = 3+(self.stats[player]['mobility']+self.stats[player]['power'])/100
                self.vel[player][0] = spd_mod*self.spd[player]*cos(angle)
                self.vel[player][1] = spd_mod*self.spd[player]*sin(angle)

                # update the entity hurt box to deal damage
                self.hurt_box[player] = ActiveAbility('movement', [self.pos[player]], self.render[player].size)

                # consume energy to use ability
                energy_usage = 1/2000*self.render[player].num_parts*(spd_mod*self.spd[player])**2
                self.energy[player]-=energy_usage

            if 'strike' in ALL_ABILITIES[self.abilities[player][a_i['ability']]]['type']:
                # get the strike direction
                x_dir = a_i['mx']-WIDTH//2
                y_dir = a_i['my']-HEIGHT//2
                x_dir, y_dir = camera.screen_to_world(x_dir, y_dir)
                angle = atan2(y_dir, x_dir)

                # update hurtboxes
                strike_hurt_box = []
                for i in range(10):
                    strike_hurt_box.append([self.pos[player][0]+i*2*self.render[player].size*cos(angle), 
                                           self.pos[player][1]+i*2*self.render[player].size*sin(angle),
                                           self.pos[player][2]])
                self.hurt_box[player] = ActiveAbility('strike', strike_hurt_box, self.render[player].size)

    def collide(self):
        for i in range(len(self.hurt_box)):
            if self.hurt_box[i]:
                for j in range(len(self.render)):
                    if i!=j and self.render[j].collide(self.hurt_box[i]):
                        self.health[j]-=2
                        self.health[i]-=1

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
            self.render[i].move(self.pos[i])
    
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
                self.hurt_box[i].update([self.pos[i]], self.render[i].size)

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
        # choose some entities to duplicate

        # update entity stats with random mutation
        # add one/two points to a stat and remove one/two point from a stat
        # include a system that will choose the stat to increase/decrease 
        # based on playstyle (very far in future)
        for i in range(len(self.stats)):
            increase = choice(list(self.stats[i].keys()))
            decrease = choice(list(self.stats[i].keys()))
            self.stats[i][increase]+=randint(1, 2)
            self.stats[i][decrease]-=randint(1, 2)
            if self.stats[i][decrease]<self.traits[i].min_stats[decrease]:
                self.stats[i][decrease] = self.traits[i].min_stats[decrease]

            self.traits[i].remove_traits(self.render[i], self.stats[i])
            self.traits[i].give_traits(self.render[i], self.stats[i])
            self.remove_abilities(i)
            self.give_abilities(i)
            total_energy_calculation = (self.stats[i]['power']+
                                        self.stats[i]['defense']+
                                        self.render[i].num_parts)
            self.energy[i] = total_energy_calculation
            self.regen()

    def regen(self):
        for i in range(len(self.health)):
            if self.health[i]<self.stats[i]['health']:
                self.health[i]+=1

        