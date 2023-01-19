import pygame as pg
from src.combat.abilities import ALL_ABILITIES, BASE_AOE_RADIUS, ActiveAbility
from src.combat.status_effects import BASE_CD

from math import sin, cos, atan2

class CombatSystem:
    def __init__(self, entities, camera):
        self.camera = camera
        self.entities = entities
    
    def update(self, entities, camera):
        self.camera = camera
        self.entities = entities
        self.status_effect_cds()
        self.active_abilities()
        self.collide()
   
    def use_ability(self, abl_input):
        a_i = abl_input['ability']
        index = abl_input['i']
        input_angle =  abl_input['angle']
        # no input 
        if a_i==-1:
            return
        
        # prevent spamming
        if 'ability_lock' in self.entities.status_effects[index]['effects']:
            return

        # all abilities
        queued_ability = a_i
        
        self.apply_status(index, index, 'ability_lock', pg.time.get_ticks())

        # abilities with movement tag
        if 'movement' in ALL_ABILITIES[queued_ability]['type']:
            # get the direction of the movement
            x_dir = cos(input_angle)
            y_dir = sin(input_angle)
            x_dir, y_dir = self.camera.screen_to_world(x_dir, y_dir)
            angle = atan2(y_dir, x_dir)
            spd_mod = 3+(self.entities.stats[index]['mbl']+self.entities.stats[index]['pwr'])/100
            self.entities.vel[index][0] = spd_mod*self.entities.spd[index]*cos(angle)
            self.entities.vel[index][1] = spd_mod*self.entities.spd[index]*sin(angle)

            # update the entity hurt box to deal damage
            movement_hurt_box = []
            for part in self.entities.creature[index].skeleton:
                movement_hurt_box.append([part[0], part[1], part[2]])
            
            self.entities.hurt_box[index] = ActiveAbility('movement', movement_hurt_box, 
                                                ALL_ABILITIES[queued_ability]['modifiers'],
                                                2*self.entities.creature[index].size)

            # consume energy to use ability
            energy_usage = 1/2*self.entities.creature[index].num_parts*(spd_mod*self.entities.spd[index])**2/1000
            self.entities.energy[index]-=energy_usage

        if 'strike' in ALL_ABILITIES[queued_ability]['type']:
            # get the strike direction
            x_dir = cos(input_angle)
            y_dir = sin(input_angle)
            x_dir, y_dir = self.camera.screen_to_world(x_dir, y_dir)
            angle = atan2(y_dir, x_dir)

            # update hurtboxes
            strike_hurt_box = []
            for i in range(10):
                strike_hurt_box.append([self.entities.pos[index][0]+i*2*self.entities.creature[index].size*cos(angle), 
                                       self.entities.pos[index][1]+i*2*self.entities.creature[index].size*sin(angle),
                                       self.entities.pos[index][2]])
            self.entities.hurt_box[index] = ActiveAbility('strike', strike_hurt_box, 2*self.entities.creature[index].size)



        if 'aoe' in ALL_ABILITIES[queued_ability]['type']:
            self.aoe_collide(index, 
                            self.entities.stat_calculation(index, ['itl', 'pwr', 'mbl'], [BASE_AOE_RADIUS]),
                            ALL_ABILITIES[queued_ability])


    def collide(self):
        for source in range(len(self.entities.hurt_box)):
            self.hurtbox_collide(source)
    
    def aoe_collide(self, source, aoe, ability):
        for target in range(len(self.entities.pos)):
            time = pg.time.get_ticks()
            if target!=source:
                dx = self.entities.pos[source][0]-self.entities.pos[target][0]
                dy = self.entities.pos[source][1]-self.entities.pos[target][1]
                if dx**2+dy**2<=aoe**2:
                    for mod in ability['modifiers']:
                        self.apply_status(source, target, mod, time)

    def hurtbox_collide(self, source):
        if self.entities.hurt_box[source]:
            time = pg.time.get_ticks()
            for target in range(len(self.entities.creature)):
                if source!=target and self.entities.creature[target].collide(self.entities.hurt_box[source].get_pos()):
                    # decrease hp
                    self.entities.health[target]-=10

                    # apply modifiers
                    for modifier in self.entities.hurt_box[source].modifiers:
                        self.entities.status_effects[target]['effects'].append(modifier)
                        self.entities.status_effects[target]['cd'].append(BASE_CD)
                        self.entities.status_effects[target]['time'].append(time)
                        self.entities.status_effects[target]['source'].append(source)
                    # increase the target's aggression score against the attacker
                    self.entities.behaviours[target].aggression[source]+=0.1
    
    def apply_status(self, source, target, effect, time):
        self.entities.status_effects[target]['effects'].append(effect)
        self.entities.status_effects[target]['cd'].append(BASE_CD)
        self.entities.status_effects[target]['time'].append(time)
        self.entities.status_effects[target]['source'].append(source)
    
    def status_effect_cds(self):
        # entity loop
        for i in range(len(self.entities.status_effects)):
            if self.entities.status_effects[i]['effects']:
                new_status_effects_cd = []
                new_status_effects = []
                new_status_effects_time = []
                new_status_effects_source = []
                # status loop
                for j in range(len(self.entities.status_effects[i]['effects'])):
                    effect = self.entities.status_effects[i]['effects'][j]
                    cd = self.entities.status_effects[i]['cd'][j]
                    time = self.entities.status_effects[i]['time'][j]
                    source = self.entities.status_effects[i]['source'][j]
                    if pg.time.get_ticks()-time<cd:
                        new_status_effects_cd.append(cd)
                        new_status_effects.append(effect)
                        new_status_effects_time.append(time)
                        new_status_effects_source.append(source)
                    else:
                        if effect == 'ability_lock':
                            self.entities.hurt_box[i] = None
                            new_status_effects_cd.append(BASE_CD)
                            new_status_effects.append('ability_cd')
                            new_status_effects_time.append(pg.time.get_ticks())
                            new_status_effects_source.append(i)
                    
                self.entities.status_effects[i]['cd'] = new_status_effects_cd
                self.entities.status_effects[i]['effects'] = new_status_effects
                self.entities.status_effects[i]['time'] = new_status_effects_time
                self.entities.status_effects[i]['source'] = new_status_effects_source

    def active_abilities(self):
        for i in range(len(self.entities.hurt_box)):
            if self.entities.hurt_box[i] and self.entities.hurt_box[i].type=='movement':
                movement_hurt_box = []
                for part in self.entities.creature[i].skeleton:
                    movement_hurt_box.append([part[0], part[1], part[2]])
                self.entities.hurt_box[i].update(movement_hurt_box, 2*self.entities.creature[i].size)