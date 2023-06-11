import pygame as pg
import numpy as np
import math, random

from ..util.adv_math import lerp, gaussian_dist, proj

SINGLE_RECEPTOR_CAPACITY = 1
SHAPE_MAP = {
    'circle': 0,
    'triangle': 1,
    'square': 2,
    'pentagon': 3,
    'hexagon': 4,
}
INV_SHAPE_MAP = [
    'circle',
    'triangle',
    'square',
    'pentagon',
    'hexagon',
]
ACTIVATION_THRESHOLD = 0.01

RECEPTOR_COLORS = {
    'circle': (255, 0, 0),
    'triangle': (0, 255, 0),
    'square': (0, 0, 255),
    'pentagon': (255, 255, 0),
    'hexagon': (255, 0, 255),
}

MUTATION_RATE = 0.1

MIN_FOV = 0.1
MIN_SPREAD = 0.1

def draw_view_cone(pos: np.ndarray, angle: float, fov: float, length: float, display: pg.Surface, color: tuple):
    points = [
        pos, 
        pos + length * np.array([math.cos(angle+fov/2), math.sin(angle+fov/2)]),
        pos + length * np.array([math.cos(angle-fov/2), math.sin(angle-fov/2)]),
    ]
    pg.draw.lines(display, color, True, points)

def get_receptor_angles(num_receptors: int, receptor_spread: float):
    return np.arange(
        receptor_spread * (1 - num_receptors)/2,
        receptor_spread * num_receptors/2,
        receptor_spread
    )

VARIATION = 0.05

RECEPTOR_DATA_MAP = {
    'num_receptors': 0,
    'receptor_spread': 1,
    'receptor_fov': 2,
    'optimal_dens': 3,
}

class Receptors:
    def __init__(self, receptor_data: dict):
        self.num_of_type = receptor_data['num_of_type']
        self.spread = receptor_data['spread']
        self.fov = receptor_data['fov']
        self.opt_dens = receptor_data['opt_dens']

    # evo
    def mutate(self):
        if random.uniform(0, 1) <= MUTATION_RATE:
            self.num_of_type = np.clip(self.num_of_type + np.random.randint(-1, 1, size=(5,)), a_min=0, a_max=10)
            self.spread = np.clip(self.spread + np.random.uniform(-0.1, 0.1, size=(5,)), a_min=MIN_SPREAD, a_max=math.pi)
            self.fov = np.clip(self.fov + np.random.uniform(-0.1, 0.1, size=(5,)), a_min=MIN_FOV, a_max=math.pi)
            self.opt_dens = np.clip(self.opt_dens + np.random.uniform(-0.1, 0.1, size=(5,)), a_min=-1, a_max=1)
    
    def cross_breed(self, other_receptors) -> dict:
        t = random.uniform(0.25, 0.75)
        return {
            'num_of_type': np.round(lerp(self.num_of_type, other_receptors.num_of_type, t)).astype(int),
            'spread': lerp(self.spread, other_receptors.spread, t),
            'fov': lerp(self.fov, other_receptors.fov, t),
            'opt_dens': lerp(self.opt_dens, other_receptors.opt_dens, t)
        }
    
    # functionality
    def poll_receptors(self, pos: np.ndarray, z_angle: float, radius: float, env):
        receptor_sense = [np.zeros(shape=(num_of_type,)) for num_of_type in self.num_of_type]
        receptor_angles = [get_receptor_angles(num_of_type, spread) for num_of_type, spread in zip(self.num_of_type, self.spread)]
        receptor_threshold = [math.cos(fov/2) for fov in self.fov]
        p_pos = env.qtree.query_point(np.array([pos[0], pos[1], radius]))
        p_data = env.qtree.query_data(np.array([pos[0], pos[1], radius]))
        for p, data in zip(p_pos, p_data):
            if np.linalg.norm(p - pos) <= radius:
                shape_index = data[1]
                for i, receptor_angle in enumerate(receptor_angles[shape_index]):
                    rel_pos = p - pos
                    p_rel_angle = math.atan2(rel_pos[1], rel_pos[0]) - z_angle
                    r_unit_vec = np.array([math.cos(receptor_angle), math.sin(receptor_angle)])
                    p_unit_vec = np.array([math.cos(p_rel_angle), math.sin(p_rel_angle)])
                    if proj(p_unit_vec, r_unit_vec) >= receptor_threshold[shape_index]:
                        receptor_sense[shape_index][i] += gaussian_dist(data[2], self.opt_dens[shape_index], VARIATION)
        
        sensory_data = []
        for sense, receptor_angle in zip(receptor_sense, receptor_angles):
            if sense.size == 0:
                avg_actv = 0
                avg_angle = 0
            else:
                avg_actv = np.average(sense)
                if avg_actv < ACTIVATION_THRESHOLD:
                    avg_angle = 0
                else:
                    avg_angle = np.sum(sense * receptor_angle) / np.sum(sense)
            sensory_data.append(np.array([avg_actv, avg_angle]))
        return np.array(sensory_data)

    def get_energy_cost(self) -> float:
        return 0.5 * np.sum([num_of_type for num_of_type in self.num_of_type])

    # render
    def render(self, pos: np.ndarray, z_angle: float, radius: float, display: pg.Surface, camera):
        for i, (num_of_type, spread, fov) in enumerate(zip(self.num_of_type, self.spread, self.fov)):
            receptor_angles = get_receptor_angles(num_of_type, spread)
            [draw_view_cone(camera.transform_to_screen(pos), z_angle + receptor_angle, fov, radius,
                            display, RECEPTOR_COLORS[INV_SHAPE_MAP[i]])
             for receptor_angle in receptor_angles]
            # [pg.draw.line(display, RECEPTOR_COLORS[INV_SHAPE_MAP[i]], camera.transform_to_screen(pos),
            #               camera.transform_to_screen(radius * np.array([math.cos(receptor_angle), math.sin(receptor_angle), 0])))
            #  for receptor_angle in receptor_angles]


    def get_df(self) -> dict:
        # get the num, spread, and fov of each receptor type (uniform)
        num = {
            f'num_{receptor_type}': receptor_data[0]
            for receptor_type, receptor_data in self.receptors.items()
        }
        spread = {
            f'spread_{receptor_type}': receptor_data[1]
            for receptor_type, receptor_data in self.receptors.items()
        }
        fov = {
            f'fov_{receptor_type}': receptor_data[2]
            for receptor_type, receptor_data in self.receptors.items()
        }
        return {
            **num, **spread, **fov
        }
    
    def num_receptors(self):
        return {
            receptor_type: receptor_data[0]
            for receptor_type, receptor_data in self.receptors.items()
        }

    def receptor_spreads(self):
        return {
            receptor_type: receptor_data[1]
            for receptor_type, receptor_data in self.receptors.items()
        }

    def receptor_fovs(self):
        return {
            receptor_type: receptor_data[2]
            for receptor_type, receptor_data in self.receptors.items()
        }

class ReceptorManager:
    def __init__(self, num_receptors_structures: int, receptor_data: dict):
        self.num_structures = num_receptors_structures
        self.num_of_type = receptor_data['num_of_type']
        self.spread = receptor_data['spread']
        self.fov = receptor_data['fov']
        self.opt_dens = receptor_data['opt_dens']

    def add_new_receptor_structures(self, num_new_receptor_structures: int, receptor_data):
        self.num_structures += num_new_receptor_structures
        self.num_of_type = {
            receptor_type: np.concatenate([num_of_type, receptor_data['num_of_type'][receptor_type]])
            for receptor_type, num_of_type in self.num_of_type.items()
        }
        self.spread = {
            receptor_type: np.concatenate([spread, receptor_data['spread'][receptor_type]])
            for receptor_type, spread in self.spread.items()
        }
        self.fov = {
            receptor_type: np.concatenate([fov, receptor_data['fov'][receptor_type]])
            for receptor_type, fov in self.fov.items()
        }
        self.opt_dens = {
            receptor_type: np.concatenate([opt_dens, receptor_data['opt_dens'][receptor_type]])
            for receptor_type, opt_dens in self.opt_dens.items()
        }
    
    def keep(self, to_keep: np.ndarray):
        self.num_structures = np.sum(to_keep)
        self.num_of_type = {
            receptor_type: num_of_type[to_keep]
            for receptor_type, num_of_type in self.num_of_type.items()
        }
        self.spread = {
            receptor_type: spread[to_keep]
            for receptor_type, spread in self.spread.items()
        }
        self.fov = {
            receptor_type: fov[to_keep]
            for receptor_type, fov in self.fov.items()
        }
        self.opt_dens = {
            receptor_type: opt_dens[to_keep]
            for receptor_type, opt_dens in self.opt_dens.items()
        }
    
    def mutate(self):
        # mutate the number of receptors in the structure
        should_mutate = np.random.rand(self.num_structures) <= MUTATION_RATE
        num_should_mutate = np.sum(should_mutate)
        mutations = {
            receptor_type: np.random.randint(0, 1, size=(num_should_mutate,)) * 2 - 1
            for receptor_type in self.num_of_type
        }
        for receptor_type, num_of_type in self.num_of_type.items():
            self.num_of_type[receptor_type][should_mutate] = np.clip(num_of_type[should_mutate] + mutations[receptor_type],
                                                                     a_min=0, a_max=10)

        # mutate the spread of receptors in the structure
        should_mutate = np.random.rand(self.num_structures) <= MUTATION_RATE
        num_should_mutate = np.sum(should_mutate)
        mutations = {
            receptor_type: np.random.uniform(-0.1, 0.1, size=(num_should_mutate,))
            for receptor_type in self.spread
        }
        for receptor_type, spread in self.spread.items():
            self.spread[receptor_type][should_mutate] = np.clip(spread[should_mutate] + mutations[receptor_type],
                                                                a_min=MIN_SPREAD, a_max=math.pi)
        
        # mutate the fov of receptors in the structure
        should_mutate = np.random.rand(self.num_structures) <= MUTATION_RATE
        num_should_mutate = np.sum(should_mutate)
        mutations = {
            receptor_type: np.random.uniform(-0.1, 0.1, size=(num_should_mutate,))
            for receptor_type in self.fov
        }
        for receptor_type, fov in self.fov.items():
            self.fov[receptor_type][should_mutate] = np.clip(fov[should_mutate] + mutations[receptor_type],
                                                                a_min=MIN_FOV, a_max=math.pi)

        # mutate the optimal dens of receptors in the structure
        should_mutate = np.random.rand(self.num_structures) <= MUTATION_RATE
        num_should_mutate = np.sum(should_mutate)
        mutations = {
            receptor_type: np.random.uniform(-0.1, 0.1, size=(num_should_mutate,))
            for receptor_type in self.opt_dens
        }
        for receptor_type, opt_dens in self.opt_dens.items():
            self.opt_dens[receptor_type][should_mutate] = np.clip(opt_dens[should_mutate] + mutations[receptor_type],
                                                                a_min=-1, a_max=1)
    
    def cross_breed(self, num_elites: int, elite_mask: np.ndarray, breeding_pairs: np.ndarray):
        cross_breed_weight = np.random.uniform(0.25, 0.75, size=(num_elites,))
        new_generation = {}
        # num receptors
        elites = {
            receptor_type: num_of_type[elite_mask]
            for receptor_type, num_of_type in self.num_of_type.items()
        }
        new_generation['num_of_type'] = {
            receptor_type: np.round(lerp(num_of_type, num_of_type[breeding_pairs], cross_breed_weight)).astype(int)
            for receptor_type, num_of_type in elites.items()
        }

        # receptor spread
        elites = {
            receptor_type: spread[elite_mask]
            for receptor_type, spread in self.spread.items()
        }
        new_generation['spread'] = {
            receptor_type: lerp(spread, spread[breeding_pairs], cross_breed_weight)
            for receptor_type, spread in elites.items()
        }

        # receptor fov
        elites = {
            receptor_type: fov[elite_mask]
            for receptor_type, fov in self.fov.items()
        }
        new_generation['fov'] = {
            receptor_type: lerp(fov, fov[breeding_pairs], cross_breed_weight)
            for receptor_type, fov in elites.items()
        }

        # receptor opt dens
        elites = {
            receptor_type: opt_dens[elite_mask]
            for receptor_type, opt_dens in self.opt_dens.items()
        }
        new_generation['opt_dens'] = {
            receptor_type: lerp(opt_dens, opt_dens[breeding_pairs], cross_breed_weight)
            for receptor_type, opt_dens in elites.items()
        }

        return new_generation
    
    def poll_receptors(self, index: np.ndarray, pos: np.ndarray, angle: float, radius: float, env):
        # receptor_input_of_type = { # list of numpy arrays of different sizes
        #     receptor_type: [np.zeros(shape=(num,)) for num in num_of_type]
        #     for receptor_type, num_of_type in self.num_of_type.items()
        # }
        # # iterate through each pheromone
        # for m_pos, m_shape, m_dens in zip(env.positions, env.shapes, env.densities):
        #     # boolean mask of entities in range of pheromone
        #     in_radius = np.linalg.norm(entity_poss - m_pos, axis=1) <= radius
        #     # calculate the relative angle and offset of the pheromone to the entity
        #     m_rel_angles = np.arctan2(m_pos[1] - entity_poss[in_radius][:,1],
        #                               m_pos[0] - entity_poss[in_radius][:,0])
        #     m_rel_offset = np.array([np.cos(m_rel_angles), np.sin(m_rel_angles)])
        #     # getting the receptor data for the entities
        #     shape_name = INV_SHAPE_MAP[m_shape]
        #     num_of_type = self.num_of_type[shape_name][in_radius]
        #     spread = self.spread[shape_name][in_radius]
        #     fov = self.fov[shape_name][in_radius]
        #     fov_threshold = np.cos(fov)
        #     opt_dens = self.opt_dens[shape_name][in_radius]
        #     receptor_angles = [
        #         get_receptor_angles(num_receptors, receptor_spread)
        #         for num_receptors, receptor_spread in zip(num_of_type, spread)
        #     ]
        #     # for each entity, determine if the pheromone is within
        #     # the sensory cone and update the input based on a gaussian distribution
        #     # with that receptor's optimal density 
        #     for i, (receptor_angle, rel_offset) in enumerate(zip(receptor_angles, m_rel_offset)):
        #         unit_receptors = np.array([np.cos(receptor_angle), np.sin(receptor_angle)])
        #         for j, receptor_offset in enumerate(unit_receptors):
        #             if proj(receptor_offset, rel_offset) >= fov_threshold[i]:
        #                 receptor_input_of_type[shape_name][in_radius][i][j] += gaussian_dist(m_dens, opt_dens[i], VARIATION)

        # # determine the density and angle activations for each entity
        # receptor_angles = [
        #     get_receptor_angles(num_receptors, receptor_spread)
        #     for num_receptors, receptor_spread in zip(self.num_of_type, self.spread)
        # ]
        # activation_for_entities = {}
        # for receptor_type, input_of_type in receptor_input_of_type.items():
        #     # for each entity
        #     for entity_inputs in input_of_type:

        # for the entity at specified index, create a dict of np arrays
        # which will store the activations of each receptor
        receptor_activations = {
            receptor_type: np.zeros(shape=(num_of_type[index],))
            for receptor_type, num_of_type in self.num_of_type.items()
        }
        receptor_angles = {
            receptor_type: get_receptor_angles(self.num_of_type[receptor_type][index], self.spread[receptor_type][index])
            for receptor_type in self.num_of_type
        }

        for m_pos, m_shape, m_dens in zip(env.positions, env.shapes, env.densities):
            if np.linalg.norm(pos - m_pos) < radius:
                m_rel_angle = np.arctan2(m_pos[1]-pos[1], m_pos[0]-pos[0]) - angle
                m_rel_offset = np.array([math.cos(m_rel_angle), math.sin(m_rel_angle)])

                # fetching entity receptor data of type
                shape_name = INV_SHAPE_MAP[m_shape]
                fov = self.fov[shape_name][index]
                fov_threshold = math.cos(fov)
                opt_dens = self.opt_dens[shape_name][index]

                for i, receptor_angle in enumerate(receptor_angles[shape_name]):
                    receptor_offset = np.array([math.cos(receptor_angle), 
                                                math.sin(receptor_angle)])
                    if proj(m_rel_offset, receptor_offset) >= fov_threshold:
                        receptor_activations[shape_name][i] += gaussian_dist(m_dens, opt_dens, VARIATION)
        
        input_neuron_activations = {}
        for receptor_type, activations in receptor_activations.items():
            if activations.size == 0:
                dens_actv = 0
                angle_actv = 0
            else:
                dens_actv = np.average(activations)
                if dens_actv < ACTIVATION_THRESHOLD:
                    angle_actv = 0
                else:
                    angle_actv = np.sum(activations * receptor_angles[receptor_type]) / np.sum(activations)
                
            input_neuron_activations[receptor_type] = np.array([dens_actv, angle_actv])
        
        return input_neuron_activations
    
    def get_energy_cost(self):
        return 0.5 * np.sum(np.vstack(list(self.num_of_type.values())), axis=0)
    
    def get_df(self):
        return {
            **{
                f'num_{receptor_type}': num_of_type
                for receptor_type, num_of_type in self.num_of_type.items()
            },
            **{
                f'spread_{receptor_type}': spread
                for receptor_type, spread in self.spread.items()
            },
            **{
                f'fov_{receptor_type}': fov
                for receptor_type, fov in self.fov.items()
            },
            **{
                f'opt_dens_{receptor_type}': opt_dens
                for receptor_type, opt_dens in self.opt_dens.items()
            },
        }