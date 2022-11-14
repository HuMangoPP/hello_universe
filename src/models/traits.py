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
    def __init__(self, traits, min_stats):
        self.traits = traits
        self.min_stats = min_stats
        self.max_stats = None
    
    def remove_traits(self, creature, stats):
        # balance the number of traits attainable by giving a max on the number
        # a entity can have
        if len(self.traits)>=10:
            # remove some to get to 10 or some other value
            pass
    
    def give_traits(self, creature, stats):
        # stops the entity from gaining more than 10 traits at any given time 
        if len(self.traits)>=10:
            return

        if creature.legs.num_legs()>1:
            # then this entity has two pairs of legs
            # so one can specialize
            if 'wings' not in self.traits and stats['mobility']>=20:
                # mobility = wings
                # if the entity doesn't yet have wings, 
                # can give them wings
                self.traits.append('wings')
                self.min_stats['mobility'] = 20
                creature.give_wings()
            
            if 'arms' not in self.traits and stats['intelligence']>=30:
                # intelligence = arms
                # if the entity doesn't yet have arms,
                # can give them arms
                self.traits.append('arms')
                self.min_stats['intelligence'] = 30
                creature.give_arms()

        if creature.legs.num_pair_legs>0:
            if 'leg_weapon' not in self.traits and stats['power']>=10 and stats['mobility']>=10:
                # power = claws/talons/weapons
                # if the entity doesn't yet have weapons,
                # can give them weapons
                self.traits.append('leg_weapon')
                self.min_stats['power'] = 10
                self.min_stats['mobility'] = 10

        if 'head_weapon' not in self.traits and stats['power']>=20 and stats['mobility']>=10:
            # power = horn/antler
            # if the entity doesn't yet have weapons,
            # can give them weapons
            self.traits.append('head_weapon')
            self.min_stats['power'] = 20
            self.min_stats['mobility'] = 10
        
        if 'body_armour' not in self.traits and stats['defense']>=10:
            self.traits.append('body_armour')
            self.min_stats['defense'] = 10