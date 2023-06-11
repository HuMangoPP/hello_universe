import pygame as pg
import numpy as np
import math


from ..util.transitions import transition_in, transition_out, TRANSITION_TIME
from ..util.save_data import entity_data_to_df
from ..util.asset_loader import load_assets
from ..util.adv_math import gaussian_dist

from ..models.brain import BrainHistory
from ..entities.entity_manager import EntityManager, Entity
from ..environment.environment import Environment

from ..game_state.ai_controller import Agents
from ..game_state.camera import Camera
from ..game_state.ui import UserInterface

DEFAULT_DISPLAY = 'default'
EFFECTS_DISPLAY = 'gaussian_blur'
OVERLAY_DISPLAY = 'black_alpha'

def draw_dist(box: pg.Rect, display: pg.Surface, opt: float, variation: float, width: float, height: float, step: int):
    steps = np.arange(0, 1+1/step, 1/step)
    points = np.array([(x * width, (1-gaussian_dist(x, opt, variation)) * height) for x in steps])
    dist = pg.Surface(box.size)
    dist.fill((0,0,0))
    dist.set_colorkey((0,0,0))
    pg.draw.lines(dist, (255, 255, 255), False, points)
    display.blit(dist, box)

class StartMenu:
    def __init__(self, client):
        # import game
        self.width, self.height = client.res
        self.displays = client.displays
        self.font = client.font
        self.clock = client.clock

        # transition handler
        self.goto = 'game'
    
    def on_load(self):
        self.on_transition()

    def on_transition(self):
        # 0 -> no transition
        # 1 -> transition out
        # 2 -> black screen
        # 3 -> transition in
        self.transition_phase = 2
        self.transition_time = 0
    
    def update(self, events: list[pg.Event]):
        dt = self.clock.get_time() / 1000
        for event in events:
            if event.type == pg.MOUSEBUTTONDOWN:
                self.transition_phase = 1
                self.transition_time = 0
                self.goto = 'dev'
            if event.type == pg.KEYDOWN and event.key == pg.K_d:
                self.transition_phase = 1
                self.transition_time = 0
                self.goto = 'dev'
        
        # handle transitions
        if self.transition_phase > 0:
            self.transition_time += dt
            if self.transition_phase == 1 and self.transition_time > TRANSITION_TIME:
                return {
                    'exit': False,
                    'goto': self.goto
                }
            if self.transition_time > TRANSITION_TIME:
                self.transition_time = 0
                self.transition_phase = (self.transition_phase + 1) % 4
        return {}

    def render(self) -> list[str]:
        self.displays[DEFAULT_DISPLAY].fill((20, 26, 51))
        self.font.render(self.displays[DEFAULT_DISPLAY], 'Hello Universe', self.width/2, 100, 
                         (255, 255, 255), 50, style='center')

        match self.transition_phase:
            case 1: 
                transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
            case 2:
                self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
            case 3:
                transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)
        
        displays_to_render = [DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        return displays_to_render
    
# class GameMenu:
#     def __init__(self, client):
#         # import game
#         self.width, self.height = client.res
#         self.displays = client.displays
#         self.font = client.font
#         self.clock = client.clock
#         self.client = client

#         # sprites
#         self.ui_sprites = {
#             'stat_icons': load_assets('./assets/stats', 1.0),
#             'ability_icons': load_assets('./assets/abilities', 2.0),
#             'trait_icons': load_assets('./assets/traits', 2.0),
#             'hud_frames': load_assets('./assets/hud/', 1.0),
#             'status_effect_icons': load_assets('./assets/status_effects', 1.0),
#         }

#         # transition handler
#         self.goto = 'start'

#         # data
#         self.generation_time = 10
#         self.current_generation = 0
#         self.new_particle_time = 0.1

#         # objects
#         self.entity_manager = EntityManager({
#             'creature': { # TODO change to default later
#                 'num_parts': 5,
#                 'pos': np.array([0, 0, 0], dtype=np.float32),
#                 'size': 5,
#                 'max_parts': 10,
#                 'num_pair_legs': 2,
#                 'leg_length': 100,
#             },
#             'brain': { # TODO change to default later
#                 'neurons': [0,0, # circle dens, angle
#                             0,0, # triangle dens, angle
#                             0,0, # square dens, angle
#                             0,0, # pentagon dens, angle 
#                             0,0, # hexagon dens, angle
#                             # no hidden neurons
#                             2, # move forward
#                             2, # turn right
#                             2, # turn left
#                             ],
#                 'axons': [
#                     {'in':0,'out':10,'w':1},
#                     {'in':1,'out':11,'w':1},
#                     {'in':1,'out':12,'w':-1},
#                 ]
#             }, 
#             'receptor': { # TODO change to default later
#                 'num_of_type': {
#                     'circle': np.array([3]),
#                     'triangle': np.array([0]),
#                     'square': np.array([0]),
#                     'pentagon': np.array([0]),
#                     'hexagon': np.array([0]),
#                 },
#                 'spread': {
#                     'circle': np.array([math.pi/6]),
#                     'triangle': np.array([math.pi/6]),
#                     'square': np.array([math.pi/6]),
#                     'pentagon': np.array([math.pi/6]),
#                     'hexagon': np.array([math.pi/6]),
#                 },
#                 'fov': {
#                     'circle': np.array([math.pi/6]),
#                     'triangle': np.array([math.pi/6]),
#                     'square': np.array([math.pi/6]),
#                     'pentagon': np.array([math.pi/6]),
#                     'hexagon': np.array([math.pi/6]),
#                 },
#                 'opt_dens': {
#                     'circle': np.array([0.5]),
#                     'triangle': np.array([0.5]),
#                     'square': np.array([0.5]),
#                     'pentagon': np.array([0.5]),
#                     'hexagon': np.array([0.5]),
#                 },
#             },
#             'stomach': { # TODO
#                 'circle': np.array([0.5]),
#                 'triangle': np.array([0.5]),
#                 'square': np.array([0.5]),
#                 'pentagon': np.array([0.5]),
#                 'hexagon': np.array([0.5]),
#             },
#             'traits': { # TODO change to default later
#                 'traits': [],
#                 'min_stats': {
#                     'itl': 0, 'pwr': 0, 'def': 0, 'mbl': 0, 'stl': 0,
#                 }, 
#                 'max_stats': {
#                     'itl': 1, 'pwr': 1, 'def': 1, 'mbl': 1, 'stl': 1,
#                 }
#             },
#         })
#         self.environment = Environment()
#         self.ai_agents = Agents(1)
#         self.camera = Camera(self.entity_manager.pos[0])
#         # self.ui = UserInterface(self.font, self.ui_sprites)

#     def on_load(self):
#         self.on_transition()
    
#     def on_transition(self):
#         # 0 -> no transition
#         # 1 -> transition out
#         # 2 -> black screen
#         # 3 -> transition in
#         self.transition_phase = 2
#         self.transition_time = 0
    
#     def update(self, events: list[pg.Event]):
#         dt = self.clock.get_time() / 1000

#         if pg.mouse.get_pressed()[0]:
#             self.new_particle_time -= dt
#             if self.new_particle_time < 0:
#                 mpos = pg.mouse.get_pos()
#                 pos = self.camera.screen_to_world(mpos[0], mpos[1])
#                 self.environment.add_new_particles(
#                     1, pos.reshape((1,3)),
#                     np.zeros((1,), dtype=np.int32),
#                     np.full((1,), 0.5, dtype=np.float32)
#                 )
#                 self.new_particle_time = 0.1

#         self.generation_time -= dt
#         if self.generation_time <= 0:
#             # store data
#             basic_data, receptor_data, stomach_data, brain_data = self.entity_manager.get_save_data()
#             entity_data_to_df(self.current_generation, self.entity_manager.num_entities, basic_data, 'basic')
#             entity_data_to_df(self.current_generation, self.entity_manager.num_entities, receptor_data, 'receptor')
#             entity_data_to_df(self.current_generation, self.entity_manager.num_entities, stomach_data, 'stomach')
#             entity_data_to_df(self.current_generation, self.entity_manager.num_entities, brain_data, 'brain')

#             # update generation
#             self.generation_time = 10
#             self.current_generation += 1

#             self.entity_manager.new_generation(self.current_generation)
#             # self.ui.toggle_quests_menu()
#             # self.ui.update_quests()

#         # handle transitions
#         if self.transition_phase > 0:
#             self.transition_time += dt
#             if self.transition_phase == 1 and self.transition_time > TRANSITION_TIME:
#                 return {
#                     'exit': False,
#                     'goto': self.goto
#                 }
#             if self.transition_time > TRANSITION_TIME:
#                 self.transition_time = 0
#                 self.transition_phase = (self.transition_phase + 1) % 4

#         self.ai_agents.agent_input(self.entity_manager, self.environment, self.camera)
#         self.entity_manager.update(self.camera, dt, self.environment)
#         self.environment.update(dt)
#         # self.camera.follow_entity(self.entity_manager.pos[0], self.entity_manager.scale[0])

#         return {}

#     def render(self) -> list[str]:
#         self.displays[DEFAULT_DISPLAY].fill((20, 26, 51))
#         self.entity_manager.render(self.displays[DEFAULT_DISPLAY], self.camera)
#         self.environment.render(self.displays[DEFAULT_DISPLAY], self.camera)

#         match self.transition_phase:
#             case 1: 
#                 transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
#             case 2:
#                 self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
#             case 3:
#                 transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)
        
#         # self.ui.render(self.displays[DEFAULT_DISPLAY], self.entity_manager.get_ui_data(0), self.current_generation)

#         self.font.render(self.displays[DEFAULT_DISPLAY], str(self.current_generation), 
#                          25, 25, (255,255,255), size=25, style='left')

#         displays_to_render = [DEFAULT_DISPLAY]
#         if self.transition_phase > 0:
#             displays_to_render.append(OVERLAY_DISPLAY)
#         return displays_to_render

RECEPTOR_SHAPES = [
    'circle', 'triangle', 'square', 'pentagon', 'hexagon'
]

class DevMenu:
    def __init__(self, client):
        # import game
        self.width, self.height = client.res
        self.displays = client.displays
        self.font = client.font
        self.clock = client.clock
        self.client = client

        # transition handler
        self.goto = 'start'
    
        # objects
        self.new_particle_time = 0.1
        self.entity = Entity({
            'id': '0-0',
            'pos': np.array([0,0,0]),
            'scale': 1,
            'stats': {
                'itl': 1,
                'pwr': 1,
                'def': 1,
                'mbl': 1,
                'stl': 1,
            },
            'brain_history': BrainHistory(),
            'brain': { # TODO change to default later
                'neurons': [],
                'axons': []
            }, 
            'receptors': {
                'num_of_type': np.array([3, 0, 0, 0, 0]),
                'spread': np.full((5,), np.pi/6),
                'fov': np.full((5,), np.pi/6),
                'opt_dens': np.full((5,), 0.5),
            },
            'stomach': {
                # 'opt_dens': np.full((5,), 0.5)
                'opt_dens': np.arange(0.1, 0.6, 0.1)
            },
            'skeleton': {
                'joints': [{'jid': 'j0', 'rel_pos': np.array([0,0,0])},
                           {'jid': 'j1', 'rel_pos': np.array([50,0,0])},
                           {'jid': 'j2', 'rel_pos': np.array([50,0,0])+50*np.array([math.cos(0.1),math.sin(0.1),0])}],
                'bones': [{'bid': 'b0', 'joint1': 'j0', 'joint2': 'j1', 'depth': 0},
                          {'bid': 'b1', 'joint1': 'j1', 'joint2': 'j2', 'depth': 1}],
                'muscles': [{'mid': 'm0', 'bone1': 'b0', 'bone2': 'b1'}],
            }
        })
        self.environment = Environment()
        self.camera = Camera(self.entity.pos)

        self.sensory_activation = {}
    
    def on_load(self):
        self.on_transition()
    
    def on_transition(self):
        # 0 -> no transition
        # 1 -> transition out
        # 2 -> black screen
        # 3 -> transition in
        self.transition_phase = 2
        self.transition_time = 0

    def update(self, events: list[pg.Event]):
        dt = self.clock.get_time() / 1000

        if pg.mouse.get_pressed()[0]:
            self.new_particle_time -= dt
            if self.new_particle_time < 0:
                mpos = pg.mouse.get_pos()
                pos = self.camera.screen_to_world(mpos[0], mpos[1])
                self.environment.add_new_particles(
                    1, pos.reshape((1,3)),
                    np.zeros((1,), dtype=np.int32),
                    np.full((1,), 0.5, dtype=np.float32)
                )
                self.new_particle_time = 0.1
        
        keys = pg.key.get_pressed()
        if keys[pg.K_SPACE]:
            muscle_activations = {'m0': 1}
        else:
            muscle_activations = {'m0': 0}
        self.entity.pos = self.entity.pos + self.entity.skeleton.fire_muscles(self.entity.pos, muscle_activations, dt)

        # handle transitions
        if self.transition_phase > 0:
            self.transition_time += dt
            if self.transition_phase == 1 and self.transition_time > TRANSITION_TIME:
                return {
                    'exit': False,
                    'goto': self.goto
                }
            if self.transition_time > TRANSITION_TIME:
                self.transition_time = 0
                self.transition_phase = (self.transition_phase + 1) % 4
        
        self.sensory_activation = self.entity.receptors.poll_receptors(self.entity.pos, self.entity.z_angle, 
                                                                       100, self.environment)
        self.sensory_activation = {
            receptor_type: activation_data
            for receptor_type, activation_data in zip(RECEPTOR_SHAPES, self.sensory_activation)
        }

        self.entity.stomach.eat(self.entity.pos, self.environment)
        self.environment.update(dt)
    
    def render_sensory_activation(self):
        y_pos = 50
        for receptor_type, activation_data in self.sensory_activation.items():
            self.font.render(self.displays[DEFAULT_DISPLAY], receptor_type, 50, y_pos, (255, 255, 255), size=15, style='left')
            pg.draw.rect(self.displays[DEFAULT_DISPLAY], (255, 255, 255), pg.Rect(210, y_pos-10, activation_data[0], 20))
            y_pos += 30
            center = np.array([self.width/2, self.height/2])
            if activation_data[0] > 0:
                pg.draw.line(self.displays[DEFAULT_DISPLAY], (255, 255, 255), center,
                            100 * np.array([math.cos(activation_data[1]), math.sin(activation_data[1])]) + center)

    def render_stomach(self):
        drawbox = pg.Rect(0, 0, 300, 200)
        drawbox.left = 50
        drawbox.bottom = self.height-50
        [draw_dist(drawbox, self.displays[DEFAULT_DISPLAY], opt_dens, 0.2, 300, 200, 20)
         for opt_dens in self.entity.stomach.opt_dens]

    def render_brain_structure(self):
        ...

    def render(self) -> list[str]:
        self.displays[DEFAULT_DISPLAY].fill((20, 26, 51))
        self.entity.render(self.displays[DEFAULT_DISPLAY], self.camera)
        self.environment.render(self.displays[DEFAULT_DISPLAY], self.camera)

        self.render_sensory_activation()
        self.render_stomach()

        match self.transition_phase:
            case 1: 
                transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
            case 2:
                self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
            case 3:
                transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)
        
        # self.ui.render(self.displays[DEFAULT_DISPLAY], self.entity_manager.get_ui_data(0), self.current_generation)

        # self.font.render(self.displays[DEFAULT_DISPLAY], str(self.current_generation), 
        #                  25, 25, (255,255,255), size=25, style='left')

        displays_to_render = [DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        return displays_to_render