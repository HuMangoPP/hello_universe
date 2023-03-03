from src.util.settings import STAT_GAP

MAX_NUM_TRAITS = 5

ALL_TRAITS = [
    'digestion', # a modifier on digestion that allows for bonuses when eating
    'autotrophic', # a modifier that allows energy regen passively
    'claws', # claws/talons
    'horn', # antler, corn, horn
    'wings', # wings, modified leg
    'arms', # arm, modified leg
    'head_appendage', # tongue or trunk
    'body', # scales or fur or feathers
    'gills', # gills, specialize for aquatic gameplay
    'fangs', # fangs for bite damage 
]

class Traits:
    def __init__(self, traits, min_stats, max_stats):
        self.traits = traits
        self.new_trait = {}
        self.min_stats = min_stats
        self.max_stats = max_stats

    def give_traits(self, creature, trait):
        # stops the entity from gaining more than 10 traits at any given time 
        if len(self.traits)>=5:
            return

        self.traits.append(trait)

        match trait:
            case 'wings':
                self.min_stats['mbl'] = 8
                creature.upright()
            
            case 'arms':
                self.min_stats['itl'] = 6
                creature.upright()

            case 'claws':
                self.min_stats['pwr'] = 2
                self.min_stats['mbl'] = 2

            case 'horn':
                self.min_stats['pwr'] = 4
                self.min_stats['mbl'] = 2
        
            case 'body':
                self.min_stats['def'] = 2
        
    def change_physiology(self, creature, breakthrough):
        self.max_stats[breakthrough]+=1
        if breakthrough=='def' or breakthrough=='hp':
            creature.change_physiology(1, 0)
            return 
        if breakthrough=='mbl':
            creature.change_physiology(0, 1)
            return
