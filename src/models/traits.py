from src.settings import STAT_GAP

MAX_NUM_TRAITS = 5

ALL_TRAITS = [
    'leg_weapon', # claws/talons
    'head_weapon', # antler, corn, horn
    'wings', # wings, modified leg
    'arms', # arm, modified leg
    'head_appendage', # tongue or trunk
    'body_armour', # scales or fur or feathers
]

class Traits:
    def __init__(self, traits, min_stats, max_stats):
        self.traits = traits
        self.min_stats = min_stats
        self.max_stats = max_stats

    def give_traits(self, creature, stats):
        # stops the entity from gaining more than 10 traits at any given time 
        if len(self.traits)>=10:
            return

        if creature.legs.num_legs()>1:
            # then this entity has two pairs of legs
            # so one can specialize
            if 'wings' not in self.traits and stats['mbl']>=40:
                # mobility = wings
                # if the entity doesn't yet have wings, 
                # can give them wings
                self.traits.append('wings')
                self.min_stats['mbl'] = 8
                creature.give_wings()
                creature.upright()
            
            if 'arms' not in self.traits and stats['itl']>=30:
                # intelligence = arms
                # if the entity doesn't yet have arms,
                # can give them arms
                self.traits.append('arms')
                self.min_stats['itl'] = 6
                creature.give_arms()
                creature.upright()

        if creature.legs.num_pair_legs>0:
            if 'leg_weapon' not in self.traits and stats['pwr']>=10 and stats['mbl']>=10:
                # power = claws/talons/weapons
                # if the entity doesn't yet have weapons,
                # can give them weapons
                self.traits.append('leg_weapon')
                self.min_stats['pwr'] = 2
                self.min_stats['mbl'] = 2

        if 'head_weapon' not in self.traits and stats['pwr']>=20 and stats['mbl']>=10:
            # power = horn/antler
            # if the entity doesn't yet have weapons,
            # can give them weapons
            self.traits.append('head_weapon')
            self.min_stats['pwr'] = 4
            self.min_stats['mbl'] = 2
        
        if 'body_armour' not in self.traits and stats['def']>=10:
            self.traits.append('body_armour')
            self.min_stats['def'] = 2
        
    def change_physiology(self, creature, breakthrough):
        self.max_stats[breakthrough]+=1
        print(f'upgraded {breakthrough} to {self.max_stats[breakthrough]*STAT_GAP}')
        if breakthrough=='def' or breakthrough=='hp':
            creature.change_physiology(1, 0)
            return 
        if breakthrough=='mbl':
            creature.change_physiology(0, 1)
            return
