from random import choice, randint
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
                'num_legs': int(self.entities.creature[i].legs.num_pair_legs),
                'leg_length': int(self.entities.creature[i].legs.leg_length),
                'aggression': self.entities.behaviours[i].aggression.copy(),
                'herd': self.entities.behaviours[i].herding.copy(),
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
        self.entities.traits[index].give_traits(self.entities.creature[index], trait)

    def allocate_stat(self, index, stat):
        self.entities.stats[index]['max'][stat]+=1
    
    def mutate(self):
        # mutation is completely random
        # choose a random stat to decrease and increase
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
            
            self.entities.spd[i] = self.entities.detailed_calculation(i, ['mbl'], [5], [lambda calc : log(calc**2)])

    def behaviour_shift(self):
        for behaviour in self.entities.behaviours:
            behaviour.shift()

    def regen(self):
        for i in range(len(self.entities.health)):
            self.entities.health[i] = self.entities.stats[i]['hp']
    
    def rec_quest(self, index, quest):
        if not self.entities.quests[index]['active']:
            quest['progress'] = 0
            quest['active'] = False
            self.entities.quests[index] = quest

            # for now, accepting a quest automatically completes it
            reward = self.entities.quests[index]['reward']
            match self.entities.quests[index]['type']:
                case 'upgrade':
                    self.entities.stats[index][reward]+=1
                    print(f"upgraded {reward}")
                case 'alloc':
                    self.allocate_stat(index, reward)
                    print(f"allocated {reward}")
                case 'trait':
                    self.give_traits(index, reward)
                    print(f'gained {reward}')
                case 'ability':
                    self.give_abilities(index, reward)
                    print(f'gained {reward}')
    
    # def inter_species_reproduce(self, i, j):
    #     # inter-species reproduction allows for reproduction
    #     # with another creature
    #     # the new creature will get traits from both parents
    #     # to perform inter-species reproduction, a world quest must be completed

    #     i = 0
    #     j = 0

    #     entity_data = {
    #         'pos': self.pos[i].copy(),
    #         'spd': (self.spd[i]+self.spd[j])/2,
    #         'acc': (self.acc[i]+self.acc[j])/2,
    #         'body_parts': int((self.creature[i].num_parts+self.creature[j].num_parts)/2),
    #         'size': (self.creature[i].size+self.creature[j].size)/2,
    #         'num_legs': int((self.creature[i].legs.num_pair_legs+self.creature[j].legs.num_pair_legs)/2),
    #         'leg_length': int((self.creature[i].legs.leg_length+self.creature[i].legs.leg_length)/2),
    #     }
    #     stats = {
    #         'itl': (self.stats[i]['itl']+self.stats[i]['itl'])/2,
    #         'pwr': (self.stats[i]['pwr']+self.stats[j]['pwr'])/2,
    #         'def': (self.stats[i]['def']+self.stats[j]['def'])/2,
    #         'hp': (self.stats[i]['hp']+self.stats[j]['hp'])/2,
    #         'mbl': (self.stats[i]['mbl']+self.stats[j]['mbl'])/2,
    #         'stl': (self.stats[i]['stl']+self.stats[j]['stl'])/2,
    #         'min': 0,
    #         'max': 0,
    #     }
    #     self.add_new_entity(entity_data, stats)