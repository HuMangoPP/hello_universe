from src.settings import STAT_GAP

EVENT_GOALS = [
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

class WorldEvent:
    def __init__(self, entity_data):
        self.entity_data = entity_data
        self.quests = self.generate_quest()
        if self.quests: print(self.quests)
    
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
                all_quests.append(quest)
        
        return all_quests

    def update(self):
        pass