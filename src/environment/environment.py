from random import randint
from random import uniform

NUM_REGIONS = 10
CLIMATE_START = 100
DENSITY_START = 0.2
RESOURCE_TYPES = {
    'inorganic',        # chemical soup
    'energy',           # sunlight, energy, etc 
    'organic',          # vegetation
}

class Environment:
    def __init__(self, env_data):
        self.climate = [0]*NUM_REGIONS        # avg temperature (environmental effects)
        self.res_density = [0]*NUM_REGIONS    # avg resource density (resource availability)
        self.res_dist = [0]*NUM_REGIONS       # resource distribution (type of resource)
        self.load_regions(env_data['region_data'])
    
    def load_regions(self, region_data):
        if region_data:
            # save data, if any
            self.climate = region_data['climate']
            self.res_density = region_data['res_density']
            self.res_dist = region_data['res_dist']
        else:
            # create new data, if none
            ...
            for i in range(NUM_REGIONS):
                self.climate[i] = CLIMATE_START
                self.res_density[i] = DENSITY_START
                self.res_dist[i] = 'inorganic' # all resources start as inorganic chemical compounds

    def new_generation(self, generation):
        # right now, it can be random and coded with extreme cycles/fluctuations
        # ideally, it should be calculated based on creature behaviours
        for i in range(NUM_REGIONS):
            self.climate[i] += randint(-2, 2)
            self.res_density[i] += uniform(-0.05, 0.05)