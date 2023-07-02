import numpy as np
import pygame as pg

'''
HU

create pheromones to send out for creatures (independent placing into environment and not the user)
-> make a gland system that manages this

refactor menus to decouple simulation - make a simulation class that runs all of the simulations rather than in the menu so it runs independent of the menu (rendering)
-> what data should be in the monitor?
-> optimize collision code? c extensions?

separate phermones from food ---> receptors should be able to detect food though
--- repurpose circle phermone as food?
----- this is already built, just need to change how the glands work and how the stomach works 
--- or creature separate thing for food
----- this will give me more control over the system, need to change how the stomach works and need to add onto the receptors

EXTRA if have time
--- multicell branch --- 
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
from .glands import Glands

from ...util import rotate_z, triangle_wave

MOVEMENT_OPTIONS = ['mvf', 'mvs']

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
        self.glands = Glands(entity_data['glands'])

        # mutate on birth
        self.mutate()
        self.brain.adv_init()
        self.receptors.adv_init() # calculate some static values
        self.stomach.adv_init()
        self.glands.adv_init()
    
    # sim update
    def update(self, env, dt: float) -> dict:
        ret = {}
        # clock
        self.clock_time += dt
        if self.clock_time > self.clock_period:
            self.clock_time = 0
            self.glands.release_pheromones(self.pos, env)

        # movement
        self.movement(env, dt)

        # energy deplete
        energy_spent = np.linalg.norm(self.vel) * self.scale / 50
        energy_spent += self.receptors.get_energy_cost()
        energy_spent += self.brain.get_energy_cost()
        energy_spent *= (dt * np.sum(self.stomach.metabolism))
        self.energy -= energy_spent

        # energy regen
        digest = self.stomach.eat(self.pos, env, dt)
        self.energy += (digest + dt)
        if self.energy > 100 and self.clock_time == 0:
            offset_angle = np.random.uniform(0, 2 * np.pi)
            env.add_food(np.array([self.pos + 25 * np.array([np.cos(offset_angle), np.sin(offset_angle), 0])]), 
                         np.zeros(1, np.int32))
            self.energy = 100
            
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
        activations = self.brain.think(self.receptors.poll_receptors(self.pos, self.z_angle, env).flatten(),
                                       triangle_wave(self.clock_period, self.clock_time))
        self.z_angle += activations['rot'] * dt
        self.vel = (50 + self.stats['mbl']) * np.sum(np.array([rotate_z(activations[mv] * np.array([1,0,0]), self.z_angle + i * np.pi/2) 
                                               for i, mv in enumerate(MOVEMENT_OPTIONS)]), axis=0)
        self.pos = self.pos + self.vel * dt

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

            'stomach': self.stomach.reproduce(),

            'glands': self.glands.reproduce(),
        }

    # rendering
    def render_rt(self, display: pg.Surface, camera):
        drawpos = camera.transform_to_screen(self.pos)

        pg.draw.circle(display, (255, 0, 0), drawpos, 5)
        pg.draw.line(display, (255,0,0), drawpos, drawpos + 10 * np.array([np.cos(self.z_angle), np.sin(self.z_angle)]))

    def render_monitor(self, display: pg.Surface, anchor: tuple, font):
        # creature
        pg.draw.circle(display, (255, 0, 0), anchor, 5)
        pg.draw.line(display, (255, 0, 0), anchor, 
                     anchor + 10 * np.array([np.cos(self.z_angle), np.sin(self.z_angle)]))
        
        # health and energy
        pg.draw.rect(display, (255, 0, 0), pg.Rect(420, 270, int(self.health), 10))
        pg.draw.rect(display, (255, 255, 255), pg.Rect(420, 270, 100, 10), 2)
        pg.draw.rect(display, (0, 0, 255), pg.Rect(530, 270, int(self.energy), 10))
        pg.draw.rect(display, (255, 255, 255), pg.Rect(530, 270, 100, 10), 2)
        

        # systems
        self.receptors.render_monitor(display, anchor, self.z_angle)
        font.render(display, 'stomach', 580, 300, (255, 255, 255), size=10, style='center')
        self.stomach.render_monitor(display, (530, 310, 100))
        font.render(display, 'glands', 470, 300, (255, 255, 255), size=10, style='center')
        self.glands.render_monitor(display, (420, 310, 100))
        self.brain.render_monitor(display, font)

    # data
    def get_model(self):
        '''
        CSV: basic, receptor, stomach, glands
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
        glands = {
            'id': self.id,
            **self.glands.get_model()
        }
        brain = {
            'id': self.id,
            **self.brain.get_model()
        }

        return basic, receptor, stomach, glands, brain
    
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