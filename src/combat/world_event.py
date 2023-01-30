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
        'stat_req': [0, 0, 0, 8, 0],
    },
    'arms': {
        'misc_req': ['free_legs'],
        'stat_req': [6, 0, 0, 2, 0]
    },
    'leg_weapon': {
        'misc_req': ['no_dupe_trait', 'legs'],
        'stat_req': [0, 2, 0, 2, 0]
    },
    'head_weapon': {
        'misc_req': ['no_dupe_trait'],
        'stat_req': [0, 4, 0, 2, 0]
    },
    'body_armour': {
        'misc_req': ['no_dupe_trait'],
        'stat_req': [0, 0, 2, 0, 0]
    },
    'teeth': {
        'misc_req': ['no_dupe_trait'],
        'stat_req': [0, 2, 0, 0, 0],
    },
    'gills': {
        'misc_req': ['no_dupe_trait'],
        'stat_req': [1, 0, 0, 4, 0],
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

class WorldEvent:
    def __init__(self, entities, index):
        self.quests = self.generate_quest(entities, index)
    
    def generate_quest(self, entities, index):
        entity_data = entities.get_entity_data(index)
        all_quests = []
        stats = entity_data['stats']
        max_stats = entity_data['max_stats']
        
        # obtain trait quests
        for quest in TRAIT_QUESTS.keys():
            misc_req = TRAIT_QUESTS[quest]['misc_req']
            stat_req = TRAIT_QUESTS[quest]['stat_req']
            meets_misc_req = True
            meets_stat_req = True
            entity_data['trait'] = quest
            for req in misc_req:
                meets_misc_req = meets_misc_req and MISC_REQS[req](entity_data)
            for i in range(len(stat_req)):
                meets_stat_req = meets_stat_req and stats[i]>=stat_req[i]*STAT_GAP
            if meets_misc_req and meets_stat_req:
                all_quests.append({
                    'type': 'trait',
                    'reward': quest,
                    'req_type': '',
                    'req': 0,
                })
        
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
                    'req_type': '',
                    'req': 0,
                })
        
        # new body part quests
        # body part
        potential_growth_size = entities.max_calc(index, preset='potential_growth_size')
        if entity_data['creature'].size < potential_growth_size:
            all_quests.append({
                'type': 'physiology',
                'reward': 'body',
                'req_type': '',
                'req': 0,
            })
        
        if entity_data['creature'].legs.num_pair_legs < entity_data['creature'].num_parts:
            all_quests.append({
                'type': 'physiology',
                'reward': 'leg',
                'req_type': '',
                'req': 0,
            })

        # stat upgrade / allocation quests
        for i in range(len(STAT_QUESTS)):
            if stats[i]==max_stats[i]*STAT_GAP:
                all_quests.append({
                    'type': 'alloc',
                    'reward': STAT_QUESTS[i],
                    'req_type': '',
                    'req': 0,
                })
            else:
                all_quests.append({
                    'type': 'upgrade',
                    'reward': STAT_QUESTS[i],
                    'req_type': '',
                    'req': 0,
                })

        
        return all_quests

    def update(self):
        pass