import numpy as np
import pygame as pg

'''
HU

refactor entity code
refactor brain to reflect amoeba movement rather than skeletal -> also switch to tanh and keep all activations normalized between -1 to +1
create pheromones to send out for creatures (independent placing into environment and not the user)

refactor menus to decouple simulation - make a simulation class that runs all of the simulations rather than in the menu so it runs independent of the menu (rendering)

create a separate renderer class -> send data to renderer to render onto the screen
have different renderers in different modes based on what type of gui the user wants 
- actual real-time simulation
- monitoring stats only

EXTRA if have time
segregate functions into single cells and have entities form via multicellular clumps
cells specialized through mutations -> based on their genome, they may be enabled or disabled (nonfunctional due to an incompatible genome)
have an idea of a genome, which encodes information

EXTRA EXTRA if have time
redo the skeleton code, but with variable friction forces
create a gravity module and test it
determine ways of increasing the resolution of physics updates
'''

from .brain import Brain
from .stomach import Stomach
from .receptors import Receptors

from ...util import rotate_z, triangle_wave

MOVEMENT_OPTIONS = ['mvf', 'mvr', 'mvb', 'mvl']

MUTATION_RATE = 0.1
STAT_MUT = 0.1
    
class Entity:
    def __init__(self, entity_data: dict):
        self.id : str = entity_data['id']

        # physical data
        self.pos : np.ndarray = entity_data['pos']
        self.vel = np.zeros((3,), np.float32)
        self.z_angle : float = 0
        self.scale : int = entity_data['scale']

        # clock
        self.clock_time : float = 0
        self.clock_period : float = entity_data['clock_period']

        # stats
        self.stats : dict = entity_data['stats']
        self.health = 100
        self.energy = 100
        self.reproduction_guage = 0

        # systems
        self.brain = Brain(entity_data['brain'], entity_data['brain_history'])
        self.receptors = Receptors(entity_data['receptors'])
        self.stomach = Stomach(entity_data['stomach'])

        # mutate on birth
        self.mutate()
    
    # sim update
    def update(self, env, dt: float) -> dict:
        ret = {}
        # clock
        self.clock_time += dt
        if self.clock_time > self.clock_period:
            self.clock_time = 0
            self.release_pheromones(env)

        # movement
        self.movement(env, dt)

        # energy deplete
        energy_spent = np.linalg.norm(self.vel) * self.scale / 50
        energy_spent += self.receptors.get_energy_cost()
        energy_spent += self.brain.get_energy_cost()
        energy_spent *= dt
        self.energy -= energy_spent

        # energy regen
        digest = self.stomach.eat(self.pos, env)
        self.energy += digest
        self.reproduction_guage += digest
        if self.reproduction_guage > 1:
            ret['child'] = self.reproduce()
            self.reproduction_guage = 0

        # health regen
        if self.health < 100 and self.energy > 50:
            regen_amt = (1 + self.stats['def']) * dt
            self.health += regen_amt
            self.energy -= regen_amt
    
        # health deplete
        if self.energy <= 0:
            self.health -= dt
    
        # death
        if self.health <= 0:
            return {
                **ret,
                'dead': True
            }
        return ret

    def movement(self, env, dt: float):
        activations = self.brain.think(self.receptors.poll_receptors(self.pos, self.z_angle, 100, env),
                                       triangle_wave(self.clock_period, self.clock_time))
        self.z_angle += activations['rot'] * dt
        self.vel = self.stats['mbl'] * np.sum(np.array([rotate_z(activations[mv] * np.array([1,0,0]), self.z_angle + i * np.pi/2) 
                                               for i, mv in enumerate(MOVEMENT_OPTIONS)]), axis=0)
        self.pos = self.pos + self.vel * dt
    
    def release_pheromones(self, env):
        offsets = np.random.uniform(-25., 25., (5,3))
        env.add_new_particles(5, self.pos + offsets, np.arange(5), np.random.uniform(0., 1., (5,)))

    def mutate(self):
        if np.random.uniform(0, 1) < MUTATION_RATE:
            self.stats = {
                stat_type: np.clip(stat_value + np.random.uniform(-STAT_MUT, STAT_MUT),
                                   a_min=1, a_max=100)
                for stat_type, stat_value in self.stats.items()
            }
        self.brain.mutate(self.stats['itl'])
        self.stomach.mutate()
        self.receptors.mutate()

    def reproduce(self) -> dict:
        offset_angle = np.random.uniform(0, 2*np.pi)
        return {
            'pos': self.pos + 50 * np.array([np.cos(offset_angle), np.sin(offset_angle), 0]),
            'scale': self.scale,
            'clock_period': self.clock_period,

            'stats': {
                stat_type: stat_value
                for stat_type, stat_value in self.stats.items()
            },

            'brain': self.brain.reproduce(),

            'receptors': self.receptors.reproduce(),

            'stomach': self.stomach.reproduce()
        }

    # rendering
    def render_rt(self, display: pg.Surface, camera):
        drawpos = camera.transform_to_screen(self.pos)

        pg.draw.circle(display, (255, 0, 0), drawpos, 5)
        pg.draw.line(display, (255,0,0), drawpos, drawpos + 10 * np.array([np.cos(self.z_angle), np.sin(self.z_angle)]))

    # data
    def get_model(self):
        '''
        CSV: basic, receptor, stomach
        JSON: brain
        '''
        basic = {
            'id': self.id,
            'x': self.pos[0],
            'y': self.pos[1],
            'z': self.pos[2],
            'z_angle': self.z_angle,
            'health': self.health,
            'energy': self.energy,
            'scale': self.scale,
            'clock_period': self.clock_period,
            **self.stats
        }
        receptor = {
            'id': self.id,
            **self.receptors.get_model()
        }
        stomach = {
            'id': self.id,
            **self.stomach.get_model()
        }
        brain = {
            'id': self.id,
            **self.brain.get_model()
        }

        return basic, receptor, stomach, brain
    
    def get_sim_data(self):
        '''
            CSV: basic
            JSON: brain
        '''
        basic = {
            'id': self.id,
            'x': self.pos[0],
            'y': self.pos[1],
            'z': self.pos[2],
            'z_angle': self.z_angle,
            'health': self.health,
            'energy': self.energy,
            'reproduction_guage': self.reproduction_guage,
        }

        brain = {
            'id': self.id,
            **self.brain.get_sim_data()
        }

        return basic, brain