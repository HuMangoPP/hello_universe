import numpy as np
import pygame as pg
import math

from ..models.creature import Creature
from ..models.receptors import Receptors
from ..models.brain import BrainHistory, Brain
from ..models.traits import Traits

def draw_arrowhead(display: pg.Surface, pos: np.ndarray, angle: float, radius: float, color: tuple):
    pg.draw.circle(display, color, pos, radius)
    perp = angle + math.pi/2
    points = [
        pos + radius * np.array([math.cos(perp), math.sin(perp)]),
        pos + 2 * radius * np.array([math.cos(angle), math.sin(angle)]),
        pos - radius * np.array([math.cos(perp), math.sin(perp)]),
    ]
    pg.draw.polygon(display, color, points)

class EntityManager:
    def __init__(self, first_entity: dict):
        # physical data
        self.num_entities = 1
        self.pos = np.zeros((1,3), dtype=np.float32) # shape=(n,3)
        self.flat_angle = np.zeros((1,), dtype=np.float32) # shape=(n,)
        self.vel = np.zeros((1,3), dtype=np.float32) # shape=(n,3)
        self.scale = np.ones((1,), dtype=np.float32) # shape=(n,)
        # self.creature : list[Creature] = [Creature(first_entity['creature'])]

        # game data
        self.stats = {
            'itl': np.zeros((1,), dtype=np.float32), # shape=(n,)
            'pwr': np.zeros((1,), dtype=np.float32), # shape=(n,)
            'def': np.zeros((1,), dtype=np.float32), # shape=(n,)
            'mbl': np.zeros((1,), dtype=np.float32), # shape=(n,)
            'stl': np.zeros((1,), dtype=np.float32), # shape=(n,)
        }
        self.health = np.full((1,), 100, dtype=np.float32) # shape=(n,)
        self.energy = np.full((1,), 100, dtype=np.float32) # shape=(n,)

        # interactive
        self.brain_history = BrainHistory()
        self.brain : list[Brain] = [Brain(first_entity['brain'], self.brain_history)]
        self.receptors : list[Receptors] = [Receptors(first_entity['receptors'])]
        self.abilities = [[]]
        self.traits : list[Traits] = [Traits(first_entity['traits'])]
        self.status_effects = [[]]
        self.hurt_box = [None]

    def add_new_entities(self, num_new_entities: int, physical_data: dict, stats_data: dict, interactive_data: dict):
        # physical
        self.num_entities += num_new_entities
        self.pos = np.concatenate([self.pos, physical_data['pos']])
        self.flat_angle = np.concatenate([self.flat_angle, physical_data['flat_angle']])
        self.vel = np.concatenate([self.vel, np.zeros((num_new_entities,3), dtype=np.float32)])
        self.scale = np.concatenate([self.scale, physical_data['scale']])
        # self.creature = self.creature + physical_data['creature']

        # game
        self.stats = {
            stat_type: np.concatenate([self.stats[stat_type], stats_data[stat_type]])
            for stat_type in self.stats
        }
        self.health =  np.concatenate([self.health, stats_data['health']])
        self.energy = np.concatenate([self.energy, stats_data['energy']])

        # interactive
        self.brain = self.brain + interactive_data['brain']
        self.receptors = self.receptors + interactive_data['receptors']
        self.abilities = self.abilities + interactive_data['abilities']
        self.status_effects = self.status_effects + [[] for _ in range(num_new_entities)]
        self.traits = self.traits + interactive_data['traits']
        self.hurt_box = self.hurt_box + interactive_data['hurt_box']

    # update and input
    def input(self, camera, mv_input: dict):
        entity_index = mv_input['index']
        x_input, y_input = mv_input['x'], mv_input['y']
        
        x_dir,y_dir = x_input,y_input
        # x_dir, y_dir = camera.screen_to_world(x_input, y_input)

        if x_dir != 0 and y_dir != 0:
            input_vec = np.array([x_dir, y_dir])
            input_vec = input_vec / np.linalg.norm(input_vec)
            x_dir, y_dir = input_vec[0], input_vec[1]

        self.vel[entity_index] = np.array([[x_dir, y_dir, 0]])

    def update(self, camera, dt: float):
        # movements
        # self.vel = self.vel + self.acc * dt
        self.pos = self.pos + 200 * self.vel * dt
        spd = np.linalg.norm(self.vel[:, 0:2], axis=1)
        moving = spd > 0
        flat_angles = np.arctan2(self.vel[moving,1],self.vel[moving,0])
        self.flat_angle[moving] = flat_angles

        # [creature.update(self.pos[i]) for i, creature in enumerate(self.creature)]

        # TODO spend energy based on movement
    
    # mutation
    def mutate(self):
        # mutate stats
        self.stats = {
            stat_type: np.clip(stats + np.random.rand(stats.size)*4-2, a_min=0, a_max=100)
            for stat_type, stats in self.stats.items()
        }

        # mutate receptors, change the number of receptors, spread, or fov
        [receptor.mutate() for receptor in self.receptors]

        # mutate brain
        [brain.mutate(itl_stat) for brain, itl_stat in zip(self.brain, self.stats['itl'])]

    # render
    def render_health_and_energy(self, display: pg.Surface, drawpos: tuple, health: float, energy: float):
        health_rect = pg.Rect(drawpos[0]-20, drawpos[1]-30,40,5)
        energy_rect = pg.Rect(drawpos[0]-20, drawpos[1]-25,40,5)
        health_bar = pg.Surface((40, 5))
        energy_bar = pg.Surface((40, 5))
        health_bar.fill((0,0,0))
        pg.draw.rect(health_bar, (255, 0, 0), pg.Rect(0,0,health/100*40,5))
        energy_bar.fill((0,0,0))
        pg.draw.rect(energy_bar, (0,0,255), pg.Rect(0,0,energy/100*40,5))
        display.blit(health_bar, health_rect)
        display.blit(energy_bar, energy_rect)
        pg.draw.rect(display, (255,255,255), health_rect, 1)
        pg.draw.rect(display, (255,255,255), energy_rect, 1)
    
    def render_stats(self, display: pg.Surface, drawpos: tuple, stats: tuple):
        for i, stat in enumerate(stats):
            stat_bar = pg.Rect(0,0,5,stat*2)
            stat_bar.bottom = drawpos[1]-35
            stat_bar.centerx = drawpos[0] + (i-2)*5
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

        [receptor.render(pos, angle, 100, display, camera) 
         for pos, angle, receptor in zip(self.pos, self.flat_angle, self.receptors)]
    
    # save data
    def get_save_data(self):
        receptors_data = [receptors.get_receptor_data()
                          for receptors in self.receptors]
        first_entity = receptors_data[0]
        receptor_save_data = {
            receptor_data_key: np.array([entity_receptor_data[receptor_data_key]
                                         for entity_receptor_data in receptors_data])
            for receptor_data_key in first_entity
        }
        data = {
            'x': self.pos[:,0],
            'y': self.pos[:,1],
            'z': self.pos[:,2],
            'scale': self.scale,
            'itl': self.stats['itl'],
            'pwr': self.stats['pwr'],
            'def': self.stats['def'],
            'mbl': self.stats['mbl'],
            'stl': self.stats['stl'],
            # 'body_parts': [creature.num_parts for creature in self.creature],
            # 'num_pair_legs': [creature.legs.num_pair_legs for creature in self.creature],
            # 'receptors': [receptors.zip_num_receptors() for receptors in self.receptors]
            **receptor_save_data,
        }
        return data

    # ui
    def get_ui_data(self, index: int):
        stats = {
            stat_type: math.ceil(stats[index]) 
            for stat_type, stats in self.stats.items()
        }
        return {
            **stats
        }
