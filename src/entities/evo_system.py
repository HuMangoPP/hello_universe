from random import choice, uniform, randint
from src.util.settings import STAT_GAP
from math import log

class EvoSystem:
    def __init__(self, entities):
        self.entities = entities

    def new_generation(self, entities):
        self.entities = entities
        self.mutate()
        self.regen()
        self.behaviour_shift()
        self.in_species_reproduce()

    def calculate_performance(self):
        # for i in range(self.pos):
        #     # here we will calculate the performance of the creature during the generation
        #     pass

        return [0]

    def in_species_reproduce(self):
        # in-species reproduction allows for reproduction in-species
        # has the possibility of generating new mutations and traits

        next_gen = self.calculate_performance()

        for i in next_gen:
            entity_data = {
                'pos': self.entities.pos[i].copy(),
                'spd': self.entities.spd[i],
                'acc': self.entities.acc[i],
                'body_parts': int(self.entities.creature[i].num_parts),
                'size': int(self.entities.creature[i].size),
                'scale': int(self.entities.scale[i]),
                'max_parts': int(self.entities.creature[i].max_parts),
                'num_legs': int(self.entities.creature[i].legs.num_pair_legs),
                'leg_length': int(self.entities.creature[i].legs.leg_length),
                'aggression': self.entities.behaviours[i].aggression.copy(),
                'herd': self.entities.behaviours[i].herding.copy(),
                'abilities': self.entities.abilities[i].copy(),
                'traits': self.entities.traits[i].traits.copy()
            }

            stats = {
                'itl': self.entities.stats[i]['itl'],
                'pwr': self.entities.stats[i]['pwr'],
                'def': self.entities.stats[i]['def'],
                'hp': self.entities.stats[i]['hp'],
                'mbl': self.entities.stats[i]['mbl'],
                'stl': self.entities.stats[i]['stl'],
                'min': self.entities.traits[i].min_stats.copy(),
                'max': self.entities.traits[i].max_stats.copy(),
            }

            self.entities.add_new_entity(entity_data, stats)

    def give_abilities(self, index, ability):
        self.entities.abilities[index].append(ability)

    def give_traits(self, index, trait):
        if self.entities.traits[index].new_trait:
            self.entities.traits[index].new_trait['level']+=1
        else:
            self.entities.traits[index].new_trait = trait
            self.entities.traits[index].new_trait['level'] = 1
        
        if self.entities.traits[index].new_trait['level'] == 3:
            self.entities.traits[index].give_traits(self.entities.creature[index], trait['reward'])
            self.entities.traits[index].new_trait = {}

    def allocate_stat(self, index, stat):
        self.entities.stats[index]['max'][stat]+=1
    
    def mutate(self):
        # mutation is completely random
        for i in range(len(self.entities.stats)):
            # increasing and decreasing stats
            increase = choice(list(self.entities.stats[i].keys())[:5])
            decrease = choice(list(self.entities.stats[i].keys())[:5])
            self.entities.stats[i][increase]+=randint(1, 2)
            self.entities.stats[i][decrease]-=randint(1, 2)

            # check for max and min stats
            if self.entities.stats[i][decrease]<self.entities.traits[i].min_stats[decrease]*STAT_GAP:
                self.entities.stats[i][decrease] = self.entities.traits[i].min_stats[decrease]*STAT_GAP
            if self.entities.stats[i][increase]>self.entities.traits[i].max_stats[increase]*STAT_GAP:
                self.entities.stats[i][increase] = self.entities.traits[i].max_stats[increase]*STAT_GAP
            
            self.entities.spd[i] = self.entities.detailed_calculation(i, 'movement', [lambda calc : log(calc**2)])

            # randomly increase/decrease size
            size_change = uniform(-2, 2)
            self.entities.creature[i].change_body(size_change)

    def behaviour_shift(self):
        for behaviour in self.entities.behaviours:
            behaviour.shift()

    def change_physiology(self, type, index):
        if type == 'increase_body':
            increase_scale = self.entities.creature[index].change_body(10.0)
            if increase_scale != 0:
                self.entities.scale[index] += increase_scale
        elif type == 'decrease_body':
            self.entities.creature[index].change_body(-1.0)
        else:
            self.entities.creature[index].change_legs()

    def regen(self):
        for i in range(len(self.entities.health)):
            self.entities.health[i] = self.entities.stats[i]['hp']

    def rec_quest(self, index, quest):

        reward = quest['reward']
        match quest['type']:
            case 'upgrade':
                self.entities.stats[index][reward]+=1
                print(f"upgraded {reward}")
            case 'alloc':
                self.allocate_stat(index, reward)
                print(f"allocated {reward}")
            case 'trait':
                self.give_traits(index, quest)
                print(f'gained {reward}')
            case 'ability':
                self.give_abilities(index, reward)
                print(f'gained {reward}')
            case 'physiology':
                self.change_physiology(reward, index)
                print(f'gained {reward}')
        self.entities.energy[index] -= 1