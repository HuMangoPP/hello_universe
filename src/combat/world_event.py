from random import choice
from src.util.settings import STAT_GAP

EVENT_REQ = [
    'kill', # pwr stat increase / trait / ability
    'tank', # def stat increase / trait / ability
    'escape', # mbl stat increase / trait / ability
    'hide', # stl stat increase / trait / ability
]

MISC_REQS = {
    'no_dupe_trait': lambda data: data['trait'] not in data['traits'].traits,
    'no_dupe_ability': lambda data: data['ability'] not in data['abilities'],
    'legs': lambda data: data['creature'].legs.num_legs()>0,
    'free_legs': lambda data: data['creature'].legs.num_legs()>1, 
}

TRAIT_QUESTS = {
    'wings': {
        'misc_req': ['free_legs'],
        'stats_req': {'mbl': 2},
    },
    'arms': {
        'misc_req': ['free_legs'],
        'stats_req': {'itl': 2, 'mbl': 1}
    },
    'claws': {
        'misc_req': ['no_dupe_trait', 'legs'],
        'stats_req': {'pwr': 1, 'mbl': 1}
    },
    'horn': {
        'misc_req': ['no_dupe_trait'],
        'stats_req': {'pwr': 1, 'def': 1}
    },
    'body': {
        'misc_req': ['no_dupe_trait'],
        'stats_req': {'def': 1, 'stl': 1}
    },
    'fangs': {
        'misc_req': ['no_dupe_trait'],
        'stats_req': {'pwr': 2}
    },
    'gills': {
        'misc_req': ['no_dupe_trait'],
        'stats_req': {'def': 1, 'mbl': 2}
    }
}

ABILITY_QUESTS = {
    'fly': {
        'trait_req': ['wings'],
        'misc_req': ['no_dupe_ability'],
    },
    'rush': {
        'trait_req': ['head_weapon'],
        'misc_req': ['no_dupe_ability'],
    },
    'hit': {
        'trait_req': [],  
        'misc_req': ['free_legs', 'no_dupe_ability'],
    },
    'slash': {
        'trait_req': ['leg_weapon'],
        'misc_req': ['no_dupe_ability'],
    },
    'swim': {
        'trait_req': ['gill'],
        'misc_req': ['no_dupe_ability'],
    },
    'grapple': {
        'trait_req': ['arms'],
        'misc_req': ['no_dupe_ability']
    },
    'throw': {
        'trait_req': ['arms'],
        'misc_req': ['no_dupe_ability']
    },
    'bite': {
        'trait_req': ['teeth'],
        'misc_req': ['no_dupe_ability']
    }, 
    'dash': {
        'trait_req': [],
        'misc_req': ['legs', 'no_dupe_ability']
    }, 
    'intimidate': {
        'trait_req': [],
        'misc_req': ['no_dupe_ability']
    }
}

STAT_QUESTS = ['itl', 'pwr', 'def', 'mbl', 'stl']

def meets_misc_req(trait, data):
    data['trait'] = trait
    return all([MISC_REQS[req](data) for req in TRAIT_QUESTS[trait]['misc_req']])

class WorldEvent:
    def __init__(self, entities, index):
        self.quests = self.generate_quest(entities, index)
    
    def generate_quest(self, entities, index):
        entity_data = entities.get_entity_quest_data(index)
        all_quests = []
        stats = entity_data['stats']
        max_stats = entity_data['max_stats']
        new_trait = entity_data['traits'].new_trait
        traits = entity_data['traits'].traits
        

        possible_stat_quests = STAT_QUESTS
        if new_trait:
            # get which stats should be upgradeable
            stats_req = new_trait['stats_req']
            possible_stat_quests = list(filter(lambda x : x in stats_req.keys(), STAT_QUESTS))
            # also check if the trait can move onto the next level

            trait_level = new_trait['level']
            meets_level_up = True
            for req in stats_req:
                if stats_req[req] * trait_level > max_stats[req]:
                    meets_level_up = False
                    break
            
            if meets_level_up:
                all_quests.append(new_trait)
                possible_stat_quests = []
        else:
            # if the entity is not currently trying to get a 
            # new trait, give them a random one they can accept
            possible_trait_quests = list(filter(lambda x : x not in traits, TRAIT_QUESTS.keys()))
            possible_trait_quests = list(filter(lambda x : meets_misc_req(x, entity_data), possible_trait_quests))
            
            trait = choice(possible_trait_quests)
            all_quests.append({
                'type': 'trait',
                'reward': trait,
                'stats_req': TRAIT_QUESTS[trait]['stats_req']
            })

        # alternatively, they can choose to upgrade any stat/allocate
        # # stat upgrade / allocation quests
        
        for quest in possible_stat_quests:
            if stats[quest]==max_stats[quest]*STAT_GAP:
                all_quests.append({
                    'type': 'alloc',
                    'reward': quest,
                })
            else:
                all_quests.append({
                    'type': 'upgrade',
                    'reward': quest,
                })
        
        
        # # obtain trait quests
        # for quest in TRAIT_QUESTS.keys():
        #     misc_req = TRAIT_QUESTS[quest]['misc_req']
        #     stats_req = TRAIT_QUESTS[quest]['stats_req']
        #     meets_misc_req = True
        #     entity_data['trait'] = quest
        #     for req in misc_req:
        #         meets_misc_req = meets_misc_req and MISC_REQS[req](entity_data)
        #     if meets_misc_req:
        #         all_quests.append({
        #             'type': 'trait',
        #             'reward': quest,
        #             'stats_req': stats_req,
        #         })
        
        # obtain ability quests
        for quest in ABILITY_QUESTS.keys():
            trait_req = ABILITY_QUESTS[quest]['trait_req']
            misc_req = ABILITY_QUESTS[quest]['misc_req']
            meets_trait_req = True
            entity_data['ability'] = quest
            for req in trait_req:
                meets_trait_req = (meets_trait_req and 
                                  req in entity_data['traits'].traits)
            
            for req in misc_req:
                meets_trait_req = (meets_trait_req and
                                   MISC_REQS[req](entity_data))
                
            if meets_trait_req:
                all_quests.append({
                    'type': 'ability',
                    'reward': quest,
                })
        
        # new body part quests
        # body part
        # potential_growth_size = entities.max_calc(index, preset='potential_growth_size')
        max_growth_size = entities.entity_calculation(index, 'max_size')
        min_growth_size = entities.entity_calculation(index, 'min_size')
        if entity_data['creature'].size < max_growth_size:
            all_quests.append({
                'type': 'physiology',
                'reward': 'increase_body',
            })
        if entity_data['creature'].size > min_growth_size:
            all_quests.append({
                'type': 'physiology',
                'reward': 'decrease_body',
            })
        
        # base this on the mbl stat as well
        max_legs_allowed = entities.entity_calculation(index, 'max_legs')
        if entity_data['creature'].legs.num_pair_legs < max_legs_allowed:
            all_quests.append({
                'type': 'physiology',
                'reward': 'new_leg',
            })
        
        if entity_data['creature'].legs.get_unmaxed_leg_index() != -1:
            all_quests.append({
                'type': 'physiology',
                'reward': 'leg_upgrade'
            })

        
        return all_quests

    def update(self):
        pass