import pygame as pg
import numpy as np
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
            self.entities.vel[index][0] = self.entities.spd[index]*cos(angle)
            self.entities.vel[index][1] = self.entities.spd[index]*sin(angle)

            # update hurtboxes
            self.entities.hurt_box[index] = ActiveAbility('strike', [], 
                                                        ALL_ABILITIES[queued_ability]['modifiers'],
                                                        2*self.entities.creature[index].size)

        if 'aoe' in ALL_ABILITIES[queued_ability]['type']:
            self.aoe_collide(index, 
                            self.entities.stat_calculation(index, preset='intimidation'),
                            ALL_ABILITIES[queued_ability])
        
        toggled = []
        if 'toggle' in ALL_ABILITIES[queued_ability]['type']:
            for toggle in ALL_ABILITIES[queued_ability]['side_effects']:
                for j in range(len(self.entities.status_effects[index]['effects'])-1, -1, -1):
                    if self.entities.status_effects[index]['effects'][j] == toggle:
                        toggled.append(toggle)
                        self.entities.status_effects[index]['effects'][j:j+1] = []
                        self.entities.status_effects[index]['cd'][j:j+1] = []
                        self.entities.status_effects[index]['time'][j:j+1] = []
                        self.entities.status_effects[index]['source'][j:j+1] = []


        for side_effect in ALL_ABILITIES[queued_ability]['side_effects']:
            if side_effect not in toggled:
                self.apply_status(index, index, side_effect, pg.time.get_ticks())

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
                    self.entities.health[target] -= 0
                    print(f'took damage from {source}')
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
                # status loop
                num_effects = len(self.entities.status_effects[i]['effects'])
                for j in range(num_effects):
                    effect = self.entities.status_effects[i]['effects'][0]
                    cd = self.entities.status_effects[i]['cd'][0]
                    time = self.entities.status_effects[i]['time'][0]
                    source = self.entities.status_effects[i]['source'][0]

                    self.entities.status_effects[i]['effects'][0:1] = []
                    self.entities.status_effects[i]['cd'][0:1] = []
                    self.entities.status_effects[i]['time'][0:1] = []
                    self.entities.status_effects[i]['source'][0:1] = []
                    if pg.time.get_ticks()-time<cd or effect in ['underwater', 'in_air']:
                        self.apply_status(source, i, effect, time)
                    elif effect == 'ability_lock':
                        self.entities.hurt_box[i] = None
                        self.apply_status(source, i, 'ability_cd', pg.time.get_ticks())

    def active_abilities(self):
        for i in range(len(self.entities.hurt_box)):
            if self.entities.hurt_box[i] and self.entities.hurt_box[i].type=='movement':
                movement_hurt_box = []
                for part in self.entities.creature[i].skeleton:
                    movement_hurt_box.append([part[0], part[1], part[2]])
                self.entities.hurt_box[i].update(movement_hurt_box, 2*self.entities.creature[i].size)
            
            if self.entities.hurt_box[i] and self.entities.hurt_box[i].type == 'strike':
                strike_hurt_box = []
                pos_1 = np.array(self.entities.creature[i].legs.feet_pos[0])
                pos_2 = np.array(self.entities.creature[i].legs.feet_pos[1])
                foot_index = self.entities.creature[i].legs.attached_segments[0]
                skeleton_part = np.array(self.entities.creature[i].skeleton[foot_index][:3])
                dir_1 = (pos_1 - skeleton_part) / 5
                dir_2 = (pos_2 - skeleton_part) / 5
                for j in range(5):
                    strike_hurt_box.append(skeleton_part + dir_1 * j)
                    strike_hurt_box.append(skeleton_part + dir_2 * j)
                
                self.entities.hurt_box[i].update(strike_hurt_box, 2*self.entities.creature[i].size)