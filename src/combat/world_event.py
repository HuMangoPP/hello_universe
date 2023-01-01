from src.settings import STAT_GAP

EVENT_REQ = [
    'kill', # pwr stat increase / trait / ability
    'tank', # def stat increase / trait / ability
    'escape', # mbl stat increase / trait / ability
    'hide', # stl stat increase / trait / ability
]

TRAIT_REQS = {
    'no_dupe': lambda data: data['trait'] not in data['traits'].traits,
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
        'misc_req': ['no_dupe', 'legs'],
        'stat_req': [0, 2, 0, 2, 0]
    },
    'head_weapon': {
        'misc_req': ['no_dupe'],
        'stat_req': [0, 4, 0, 2, 0]
    },
    'body_armour': {
        'misc_req': ['no_dupe'],
        'stat_req': [0, 0, 2, 0, 0]
    }
}

ABILITY_QUESTS = {
    'fly': {
        'trait_req': ['wings'],
    },
    'rush': {
        'trait_req': ['head_weapon'],
    },
    'slash': {
        'trait_req': ['leg_weapon'],
    },
}

STAT_QUESTS = ['itl', 'pwr', 'def', 'mbl', 'stl']

class WorldEvent:
    def __init__(self, entity_data):
        self.entity_data = entity_data
        self.quests = self.generate_quest()
    
    def generate_quest(self):
        all_quests = []
        stats = self.entity_data['stats']
        
        for quest in TRAIT_QUESTS.keys():
            misc_req = TRAIT_QUESTS[quest]['misc_req']
            stat_req = TRAIT_QUESTS[quest]['stat_req']
            meets_misc_req = True
            meets_stat_req = True
            self.entity_data['trait'] = quest
            for req in misc_req:
                meets_misc_req = meets_misc_req and TRAIT_REQS[req](self.entity_data)
            for i in range(len(stat_req)):
                meets_stat_req = meets_stat_req and stats[i]>=stat_req[i]*STAT_GAP
            if meets_misc_req and meets_stat_req:
                all_quests.append({
                    'type': 'trait',
                    'reward': quest,
                    'req_type': '',
                    'req': '',
                })
        
        for quest in ABILITY_QUESTS.keys():
            trait_req = ABILITY_QUESTS[quest]['trait_req']
            meets_trait_req = True
            for req in trait_req:
                meets_trait_req = meets_trait_req and req in self.entity_data['traits'].traits and quest not in self.entity_data['abilities']
            
            if meets_trait_req:
                all_quests.append({
                    'type': 'ability',
                    'reward': quest,
                    'req_type': '',
                    'req': '',
                })
        
        for i in range(len(STAT_QUESTS)):
            max_stats = self.entity_data['max_stats']
            if stats[i]==max_stats[i]*STAT_GAP:
                all_quests.append({
                    'type': 'alloc',
                    'reward': STAT_QUESTS[i],
                    'req_type': '',
                    'req': '',
                })
            else:
                all_quests.append({
                    'type': 'upgrade',
                    'reward': STAT_QUESTS[i],
                    'req_type': '',
                    'req': '',
                })

        return all_quests

    def update(self):
        pass