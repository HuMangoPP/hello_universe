import numpy as np
import pygame as pg
import math, random

from ..models.creature import Creature
from ..models.receptors import Receptors, ReceptorManager
from ..models.brain import BrainHistory, Brain
from ..models.stomach import Stomach, StomachManager
from ..models.skeleton import Skeleton
from ..models.traits import Traits

from ..util.collisions import QuadTree
from ..util.adv_math import lerp

from .evo_util import calculate_fitness

##################
# helpers
##################
def draw_arrowhead(display: pg.Surface, pos: np.ndarray, angle: float, radius: float, color: tuple):
    pg.draw.circle(display, color, pos, radius)
    perp = angle + math.pi/2
    points = [
        pos + radius * np.array([math.cos(perp), math.sin(perp)]),
        pos + 2 * radius * np.array([math.cos(angle), math.sin(angle)]),
        pos - radius * np.array([math.cos(perp), math.sin(perp)]),
    ]
    pg.draw.polygon(display, color, points)

##################
# constants
##################
ELITISM_PERCENTILE = 50

class EntityManager:
    ##################
    # init
    ##################
    def __init__(self, first_entity: dict):
        # physical data
        self.num_entities = 1
        self.ids = np.full((1,), '0-0')
        self.pos = np.zeros((1,3)) # shape=(n,3)
        self.flat_angle = np.zeros((1,)) # shape=(n,)
        self.vel = np.zeros((1,3)) # shape=(n,3)
        self.scale = np.ones((1,)) # shape=(n,)
        # self.creature : list[Creature] = [Creature(first_entity['creature'])]

        # game data
        self.stats = {
            'itl': np.ones((1,)), # shape=(n,)
            'pwr': np.ones((1,)), # shape=(n,)
            'def': np.ones((1,)), # shape=(n,)
            'mbl': np.ones((1,)), # shape=(n,)
            'stl': np.ones((1,)), # shape=(n,)
        }
        self.health = np.full((1,), 100) # shape=(n,)
        self.energy = np.full((1,), 100) # shape=(n,)

        # interactive
        self.brain_history = BrainHistory()
        self.brain : list[Brain] = [Brain(first_entity['brain'], self.brain_history)]
        # TODO change into a np array of floats with a receptor manager that operates on data
        # self.receptors : list[Receptors] = [Receptors(first_entity['receptors'])]
        self.receptor_manager = ReceptorManager(self.num_entities, first_entity['receptor'])
        # TODO change into a np array of floats with a stomach manager that operates on data
        self.stomach_manager = StomachManager(self.num_entities, first_entity['stomach'])
        # self.abilities = [[]]
        # self.traits : list[Traits] = [Traits(first_entity['traits'])]
        # self.status_effects = [[]]
        # self.hurt_box = [None]

    def add_new_entities(self, num_new_entities: int, physical_data: dict, stats_data: dict, interactive_data: dict):
        ''' 
            This function adds n new entities to the game.

            Physical data has the pos `shape=(n,3)` and scale `shape=(n,)` values.

            Stats data has values for each stat `shape=(n,)`.

            Interactive data has values for each structure (brain, receptor, stomach) `shape=(n,)`
        '''
        # physical
        self.num_entities += num_new_entities
        self.ids = np.concatenate([self.ids, physical_data['ids']])
        self.pos = np.concatenate([self.pos, physical_data['pos']])
        self.flat_angle = np.concatenate([self.flat_angle, np.zeros((num_new_entities,), dtype=np.float32)])
        self.vel = np.concatenate([self.vel, np.zeros((num_new_entities,3), dtype=np.float32)])
        self.scale = np.concatenate([self.scale, physical_data['scale']])
        # self.creature = self.creature + physical_data['creature']

        # game
        self.stats = {
            stat_type: np.concatenate([self.stats[stat_type], stats_data[stat_type]])
            for stat_type in self.stats
        }
        self.health = np.concatenate([self.health, np.full((num_new_entities,), 100)])
        self.energy = np.concatenate([self.energy, np.full((num_new_entities,), 100)])

        # interactive
        self.brain = self.brain + interactive_data['brain']
        # self.receptors = self.receptors + interactive_data['receptors']
        self.receptor_manager.add_new_receptor_structures(num_new_entities, interactive_data['receptors'])
        self.stomach_manager.add_new_stomachs(num_new_entities, interactive_data['stomach'])
        # self.abilities = self.abilities + interactive_data['abilities']
        # self.status_effects = self.status_effects + [[] for _ in range(num_new_entities)]
        # self.traits = self.traits + interactive_data['traits']
        # self.hurt_box = self.hurt_box + interactive_data['hurt_box']

    ##################
    # input and update
    ##################
    def input(self, camera, mv_input: dict):
        '''
            This function parses input.

            `mv_input = {'x', 'y', 'index'}`

            Where `x` is the horizontal input, `y` is the vertical input, and `index` is the index of the entity 
            in the data.
        '''
        entity_index = mv_input['index']
        x_input, y_input = mv_input['x'], mv_input['y']
        
        x_dir,y_dir = x_input,y_input
        # x_dir, y_dir = camera.screen_to_world(x_input, y_input)

        if x_dir != 0 and y_dir != 0:
            input_vec = np.array([x_dir, y_dir])
            input_vec = input_vec / np.linalg.norm(input_vec)
            x_dir, y_dir = input_vec[0], input_vec[1]

        self.vel[entity_index] = (100 + 5 * self.stats['mbl'][entity_index]) * np.array([[x_dir, y_dir, 0]])

    def update(self, camera, dt: float, env):
        '''
            Update the entity data in the following order:
            
            1. Movement

            2. Energy costs

            3. Energy regen

            4. Health regen

            5. Death
        '''
        # movements
        # self.vel = self.vel + self.acc * dt
        self.pos = self.pos + self.vel * dt
        spd = np.linalg.norm(self.vel[:, 0:2], axis=1)
        moving = spd > 0
        flat_angles = np.arctan2(self.vel[moving,1],self.vel[moving,0])
        self.flat_angle[moving] = flat_angles

        # [creature.update(self.pos[i]) for i, creature in enumerate(self.creature)]

        # energy cost
        energy_spent = np.linalg.norm(self.vel, axis=1) * (self.scale / 50)
        # energy_spent = energy_spent + np.array([receptor.get_energy_cost() for receptor in self.receptors])
        energy_spent = energy_spent + self.receptor_manager.get_energy_cost()
        energy_spent = energy_spent + np.array([brain.get_energy_cost() for brain in self.brain])
        energy_spent = energy_spent * dt
        self.energy = self.energy - energy_spent

        # energy regen
        self.energy = self.energy + self.stomach_manager.eat(self.pos, env)

        # check collision between entities
        qtree = QuadTree(np.array([0,0]), 500, 4)
        [qtree.insert(pos, i) for i, pos in enumerate(self.pos)]
        for i, (pos, def_stat) in enumerate(zip(self.pos, self.stats['def'])):
            collisions = qtree.query_data(np.array([pos[0],pos[1],10]))
            for col_index in collisions:
                if col_index == i: continue
                dmg_dealt = (1 + self.stats['pwr'][col_index]) * (1 - def_stat / 100)
                self.health[i] -= dmg_dealt

        # health regen
        should_regen = self.health < 100
        can_regen = self.energy > 50
        regen = np.logical_and(should_regen, can_regen)
        regen_amt = (1 + self.stats['def']) * dt
        self.energy[regen] = self.energy[regen] - regen_amt[regen]
        self.health[regen] = self.health[regen] + regen_amt[regen]

        # health deplete
        should_deplete = self.energy <= 0
        self.health[should_deplete] = self.health[should_deplete] - dt

        # check death
        keep = self.health > 0
        self.ids = self.ids[keep]
        self.pos = self.pos[keep]
        self.vel = self.vel[keep]
        self.flat_angle = self.flat_angle[keep]
        self.scale = self.scale[keep]

        self.stats = {
            stat_type: stats[keep]
            for stat_type, stats in self.stats.items()
        }
        self.health = self.health[keep]
        self.energy = self.energy[keep]

        for i in range(self.num_entities-1, -1, -1):
            if not keep[i]:
                self.brain.pop(i)
                # self.receptors.pop(i)
        
        self.receptor_manager.keep(keep)
        self.stomach_manager.keep(keep)
        self.num_entities = np.sum(keep)

        if self.num_entities == 0:
            print('extinction')

    ##################
    # evolution
    ##################
    def new_generation(self, generation: int):
        '''
            This function wraps all functionality for a new generation.

            Calculate fitness -> cross breed -> mutate.
        '''

        self.calculate_fitness(generation)
        self.mutate()

    def calculate_fitness(self, generation: int):
        fitness_values = calculate_fitness(self.num_entities, self.health, self.energy,
                                           self.stats, self.brain_history,
                                           self.brain, self.stomach_manager, self.receptor_manager)
        elitism_threshold = np.percentile(fitness_values, ELITISM_PERCENTILE)
        self.cross_breed(fitness_values >= elitism_threshold, generation)

    def cross_breed(self, in_gene_pool: np.ndarray, generation: int):
        num_new_entities = np.sum(in_gene_pool)
        if num_new_entities == 0:
            return
        breeding_pairs = np.random.randint(0, high=num_new_entities, size=(num_new_entities,))
        physical_data = {
            'ids': np.char.add(np.full((num_new_entities,), f'{generation}-'), 
                               np.arange(0, num_new_entities, 1).astype(str)),
            'pos': np.array([lerp(self.pos[in_gene_pool][index], self.pos[in_gene_pool][pair], 
                                  random.uniform(0.25, 0.75)) + np.random.uniform(low=-15, high=15, size=(3,))
                             for index, pair in enumerate(breeding_pairs)]),
            'scale': np.array([lerp(self.scale[in_gene_pool][index], self.scale[in_gene_pool][pair], 
                                    random.uniform(0.25, 0.75)) 
                               for index, pair in enumerate(breeding_pairs)])
        }
        stats_data = {
            stat_type: np.array([lerp(self.stats[stat_type][index], self.stats[stat_type][pair], 
                                      random.uniform(0.25, 0.75)) 
                                 for index, pair in enumerate(breeding_pairs)])
            for stat_type in self.stats
        }
        interactive_data = {
            'brain': [Brain(self.brain[index].cross_breed(self.brain[pair]), self.brain_history)
                      for index, pair in enumerate(breeding_pairs)],
            'receptors': self.receptor_manager.cross_breed(num_new_entities, in_gene_pool, breeding_pairs),
            'stomach': self.stomach_manager.cross_breed(num_new_entities, in_gene_pool, breeding_pairs)
        }
        self.add_new_entities(num_new_entities, physical_data, stats_data, interactive_data)

    def mutate(self):
        # mutate stats
        self.stats = {
            stat_type: np.clip(stats + np.random.rand(stats.size)*4-2, a_min=1, a_max=100)
            for stat_type, stats in self.stats.items()
        }

        # mutate receptors, change the number of receptors, spread, or fov
        self.receptor_manager.mutate()

        # mutate brain
        [brain.mutate(itl_stat) for brain, itl_stat in zip(self.brain, self.stats['itl'])]

        # mutate stomach
        self.stomach_manager.mutate()

    ##################
    # rendering
    ##################
    def render_health_and_energy(self, display: pg.Surface, drawpos: tuple, health: float, energy: float):
        health_rect = pg.Rect(drawpos[0]-25, drawpos[1]-40,50,10)
        energy_rect = pg.Rect(drawpos[0]-25, drawpos[1]-30,50,10)
        health_bar = pg.Surface((50, 10))
        energy_bar = pg.Surface((50, 10))
        health_bar.fill((0,0,0))
        pg.draw.rect(health_bar, (255, 0, 0), pg.Rect(0,0,health/100*50,10))
        energy_bar.fill((0,0,0))
        pg.draw.rect(energy_bar, (0,0,255), pg.Rect(0,0,energy/100*50,10))
        display.blit(health_bar, health_rect)
        display.blit(energy_bar, energy_rect)
        pg.draw.rect(display, (255,255,255), health_rect, 1)
        pg.draw.rect(display, (255,255,255), energy_rect, 1)
    
    def render_stats(self, display: pg.Surface, drawpos: tuple, stats: tuple):
        for i, stat in enumerate(stats):
            stat_bar = pg.Rect(0,0,10,stat*2)
            stat_bar.bottom = drawpos[1]-50
            stat_bar.centerx = drawpos[0] + (i-2)*10
            pg.draw.rect(display, (0,255,0), stat_bar)
            pg.draw.rect(display, (255,255,255), stat_bar,1)

    def render(self, display: pg.Surface, camera):
        # [creature.render(display, camera) for creature in self.creature]
        for i, (pos, angle, health, energy) in enumerate(zip(self.pos, self.flat_angle, self.health, self.energy)):
            drawpos = camera.transform_to_screen(pos)
            draw_arrowhead(display, drawpos, angle, 10, (255,0,0))
            self.render_health_and_energy(display, drawpos, health, energy)
            stats = [self.stats[stat_type][i] for stat_type in self.stats]
            self.render_stats(display, drawpos, stats)

        # [receptor.render(pos, angle, 100, display, camera) 
        #  for pos, angle, receptor in zip(self.pos, self.flat_angle, self.receptors)]
    
    ##################
    # getting data for save
    ##################
    def get_save_data(self):
        # get basic data
        basic_data = {
            'id': self.ids,
            'x': self.pos[:,0],
            'y': self.pos[:,1],
            'z': self.pos[:,2],
            'scale': self.scale,
            **self.stats
        }

        # get receptor data
        receptor_data = {
            'id': self.ids,
            **self.receptor_manager.get_df()
        }

        # get brain data
        brain_data = [brain.get_df() for brain in self.brain]
        first_entity = brain_data[0]
        brain_data = {
            brain_data_key: np.array([entity_brain_data[brain_data_key]
                                      for entity_brain_data in brain_data])
            for brain_data_key in first_entity
        }
        brain_data = {
            'id': self.ids,
            **brain_data
        }

        # get stomach data
        stomach_data = {
            'id': self.ids,
            **self.stomach_manager.get_df()
        }
        return basic_data, receptor_data, stomach_data, brain_data

    ##################
    # getting data for HUD UI
    ##################
    def get_ui_data(self, index: int):
        stats = {
            stat_type: math.ceil(stats[index]) 
            for stat_type, stats in self.stats.items()
        }
        return {
            **stats
        }

class Entity:
    def __init__(self, entity_data: dict):
        self.id : str = entity_data['id']
        self.pos : np.ndarray = entity_data['pos']
        self.vel = np.zeros(shape=(3,))
        self.z_angle = math.pi/2
        self.scale = entity_data['scale']

        self.stats = {
            stat_type: stat_value
            for stat_type, stat_value in entity_data['stats'].items()
        }
        self.health = 100
        self.energy = 100

        self.brain = Brain(entity_data['brain'], entity_data['brain_history'])
        self.receptors = Receptors(entity_data['receptors'])
        self.stomach = Stomach(entity_data['stomach'])
        self.skeleton = Skeleton(entity_data['skeleton'])

    # update
    def update(self, env, dt: float):
        # movement
        muscle_activations = self.brain.think(self.receptors.poll_receptors(self.pos, self.z_angle, 100, env).flatten(),
                                              self.skeleton.get_joint_touching(self.pos), 
                                              self.skeleton.get_muscle_flex_amt())
        movement, angle = self.skeleton.fire_muscles(self.pos, muscle_activations, dt)
        self.pos = self.pos + movement
        self.z_angle += angle

        
        # energy deplete
        energy_spent = np.linalg.norm(self.vel) * self.scale / 50
        energy_spent += self.receptors.get_energy_cost()
        energy_spent += self.brain.get_energy_cost()
        energy_spent *= dt
        self.energy -= energy_spent

        # energy regen
        self.energy += self.stomach.eat(self.pos, env)

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
            return False
        return True
    
    # rendering
    def render_health_and_energy(self, display: pg.Surface, drawpos: tuple):
        health_rect = pg.Rect(drawpos[0]-25, drawpos[1]-40,50,10)
        energy_rect = pg.Rect(drawpos[0]-25, drawpos[1]-30,50,10)
        health_bar = pg.Surface((50, 10))
        energy_bar = pg.Surface((50, 10))
        health_bar.fill((0,0,0))
        pg.draw.rect(health_bar, (255, 0, 0), pg.Rect(0,0,self.health/100*50,10))
        energy_bar.fill((0,0,0))
        pg.draw.rect(energy_bar, (0,0,255), pg.Rect(0,0,self.energy/100*50,10))
        display.blit(health_bar, health_rect)
        display.blit(energy_bar, energy_rect)
        pg.draw.rect(display, (255,255,255), health_rect, 1)
        pg.draw.rect(display, (255,255,255), energy_rect, 1)

    def render_stats(self, display: pg.Surface, drawpos: tuple):
        for i, stat in enumerate(self.stats.values()):
            stat_bar = pg.Rect(0,0,10,stat*2)
            stat_bar.bottom = drawpos[1]-50
            stat_bar.centerx = drawpos[0] + (i-2)*10
            pg.draw.rect(display, (0,255,0), stat_bar)
            pg.draw.rect(display, (255,255,255), stat_bar,1)

    def render(self, display: pg.Surface, camera):
        drawpos = camera.transform_to_screen(self.pos)
        draw_arrowhead(display, drawpos, self.z_angle, 10, (255, 0, 0))
        self.render_health_and_energy(display, drawpos)
        self.render_stats(display, drawpos)
        self.receptors.render(self.pos, self.z_angle, 100, display, camera)
        self.skeleton.render(display, self.pos, self.z_angle, camera)