from src.util.settings import STAT_GAP

MAX_NUM_TRAITS = 5

ALL_TRAITS = [
    'leg_weapon', # claws/talons
    'head_weapon', # antler, corn, horn
    'wings', # wings, modified leg
    'arms', # arm, modified leg
    'head_appendage', # tongue or trunk
    'body_armour', # scales or fur or feathers
    'gills' # gills, specialize for aquatic gameplay
]

class Traits:
    def __init__(self, traits, min_stats, max_stats):
        self.traits = traits
        self.min_stats = min_stats
        self.max_stats = max_stats

    def give_traits(self, creature, trait):
        # stops the entity from gaining more than 10 traits at any given time 
        if len(self.traits)>=10:
            return

        match trait:
            case 'wings':
                self.traits.append('wings')
                self.min_stats['mbl'] = 8
                creature.give_wings()
                creature.upright()
            
            case 'arms':
                self.traits.append('arms')
                self.min_stats['itl'] = 6
                creature.give_arms()
                creature.upright()

            case 'leg_weapon':
                self.traits.append('leg_weapon')
                self.min_stats['pwr'] = 2
                self.min_stats['mbl'] = 2

            case 'head_weapon':
                self.traits.append('head_weapon')
                self.min_stats['pwr'] = 4
                self.min_stats['mbl'] = 2
        
            case 'body_armour':
                self.traits.append('body_armour')
                self.min_stats['def'] = 2
        
    def change_physiology(self, creature, breakthrough):
        self.max_stats[breakthrough]+=1
        if breakthrough=='def' or breakthrough=='hp':
            creature.change_physiology(1, 0)
            return 
        if breakthrough=='mbl':
            creature.change_physiology(0, 1)
            return
