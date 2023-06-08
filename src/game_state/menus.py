# from math import sqrt, sin, cos, pi
# from random import randint, choice
# import pygame as pg
# from src.util.settings import NEW_GEN_TIME, FPS, CBODY_TEXTURE_KEY, SUN, ORBIT_RADIUS, WIDTH, HEIGHT, TITLE_FONT_SIZE
# from src.util.save_data import entity_data_to_df
# from src.game_state.camera import Camera
# from src.combat.world_event import WorldEvent

# def start_menu(screen, game_data):

#     grav_constant = randint(900, 1100)

#     # local functions for updating/render/loading the solar system animation
#     def draw_solar_system(screen):
#         # draw the c bodies
#         for body in c_bodies:
#             pg.draw.circle(screen, CBODY_TEXTURE_KEY[body['type']], 
#                             camera.transform_to_screen(body['pos'][0:3]), 
#                             body['size'])
#         pg.draw.circle(screen, CBODY_TEXTURE_KEY[sun['type']],
#                         camera.transform_to_screen(sun['pos'][0:3]),
#                         sun['size'])
    
#     def update_solar_system():
#         for body in c_bodies:
#             dx = sun['pos'][0]-body['pos'][0]
#             dy = sun['pos'][1]-body['pos'][1]
#             dr_sq = dx*dx+dy*dy
#             a = grav_constant/dr_sq
#             a_x, a_y = a*dx/sqrt(dr_sq), a*dy/sqrt(dr_sq)
#             v_x, v_y = body['vel'][0]+a_x, body['vel'][1]+a_y
#             body['vel'] = [v_x, v_y, 0]
#             x, y = body['pos'][0]+v_x, body['pos'][1]+v_y
#             body['pos'] = [x, y, 0]
#         camera.update_pos(sun['pos'][0:3])
    
#     def load_solar_system():
#         cbodies = []
#         num_bodies = randint(6, 9)
#         for i in range(num_bodies):
#             angle = randint(1, 360)/180*pi
#             radius = (i+1)*ORBIT_RADIUS
#             cbodies.append({
#                 'pos': [radius*cos(angle), radius*sin(angle), 0],
#                 'vel': [sqrt(grav_constant/radius)*sin(-angle), sqrt(grav_constant/radius)*cos(-angle)],
#                 'size': randint(3, 10),
#                 'type': choice(list(CBODY_TEXTURE_KEY.keys()))
#             })

#         return cbodies
#     # ================================ #

#     clock = game_data['clock']
#     ui = game_data['ui']
#     font = game_data['font']
#     sun = SUN
#     c_bodies = load_solar_system()
#     camera = Camera(0, 0, 0)
#     camera.update_pos(c_bodies[0]['pos'][0:3])
#     r, g, b = 255, 255, 255

#     # main game loop
#     while True:
#         for event in pg.event.get():
#             if event.type==pg.QUIT:
#                 pg.quit()
#                 exit()
#             if event.type==pg.KEYDOWN:
#                 if event.key==pg.K_ESCAPE:
#                     pg.quit()
#                     exit()

#             if event.type==pg.MOUSEBUTTONDOWN:
#                 # start game by clicking anywhere
#                 game_menu(screen, game_data)
        

#         screen.fill('black')
#         draw_solar_system(screen)
#         time = pg.time.get_ticks()/1000
#         r = 255*sin(time)%256
#         g = 255*sin(time+pi/4)%256
#         b = 255*sin(time+pi/2)%256
#         font.render(screen=screen, text='hello, universe', 
#                     x=WIDTH//2, y=50, 
#                     colour=(r, g, b), 
#                     size=TITLE_FONT_SIZE, style='center')
#         font.render(screen=screen, text='press anywhere to continue', 
#                     x=WIDTH//2, y=HEIGHT-50,
#                     colour=(r, g, b),
#                     size=TITLE_FONT_SIZE, style='center')
#         update_solar_system()

#         ui.draw_mouse(screen)

#         clock.tick(FPS)
#         pg.display.update()

# def game_menu(screen, game_data):
#     entities = game_data['entities']
#     corpses = game_data['corpses']
#     evo_system = game_data['evo_system']
#     combat_system = game_data['combat_system']
#     environment = game_data['environment']

#     controller = game_data['controller']
#     ai_controller = game_data['ai']
#     camera = game_data['camera']
#     player = game_data['player']
#     ui = game_data['ui']

#     clock = game_data['clock']
#     font = game_data['font']

#     generation = 0
#     generation_time = pg.time.get_ticks()

#     while True:
#         events = pg.event.get()
#         for event in events:
#             if event.type == pg.QUIT:
#                 pg.quit()
#                 exit()
#             if event.type == pg.KEYDOWN:
#                 if event.key == pg.K_ESCAPE:
#                     return
#                 if event.key == pg.K_SPACE:
#                     evo_system.in_species_reproduce()
#                 # if event.key == pg.K_TAB:
#                 #     ui.toggle_quests_menu()
#                 #     ui.update_quests(WorldEvent(entities.get_entity_data(player)))
#                 #     ui.input(events, entities, corpses)
#                 if event.key == pg.K_DELETE:
#                     entities.health[player] = -100
                    
#         ui.input(events, entities, corpses, evo_system)
#         # refresh screen
#         screen.fill('black')
#         dt = clock.tick()/15

#         # player input
#         entities.parse_input(controller.movement_input(), camera, dt)
#         combat_system.use_ability(controller.ability_input(entities))

#         # ai controller
#         ai_controller.movement_input(entities, corpses, camera, dt)
#         ai_controller.ability_input(entities, combat_system)
        
#         # update loop
#         entities.update(camera, dt)
#         camera.follow_entity(entities, player)
#         corpses.update()
#         combat_system.update(entities, camera)

#         # drawing
#         entities.render(screen, camera)
#         corpses.render(screen, camera)
#         if controller.queued_ability!=-1:
#             ui.ability_indicator(screen, entities, controller, camera)
#         ui.display(screen, entities, generation)
#         # ui.arrow_to_corpse(screen, entities, player, corpses, camera)

#         # death
#         if entities.kill(player, corpses):
#             game_over(screen, font, clock, entities, camera, ui)
#             return

#         # new generation
#         if pg.time.get_ticks() - generation_time > NEW_GEN_TIME:
#             # update the generation
#             df = entity_data_to_df(generation, len(entities.pos), entities.get_save_data())
#             generation_time = pg.time.get_ticks()
#             generation+=1

#             # call the evo systems to operate on entities
#             # evo_system.new_generation(entities)

#             # tell the ai to accept the new quests for the ais
#             ai_controller.accept_quests(entities, evo_system)

#             # allow the player to accept new quests
#             ui.toggle_quests_menu()
#             ui.update_quests(WorldEvent(entities, player))
#             ui.input(events, entities, corpses, evo_system)

#             # update the environment based on creature actions
#             environment.new_generation(generation)


    
#         pg.display.update()
#         pg.display.set_caption(f'{clock.get_fps()}, {dt}')

# def game_over(screen, font, clock, entities, camera, ui):

#     black_screen = pg.Surface((WIDTH, HEIGHT))
#     black_screen.fill('black')
#     screen_alpha = 0
#     text_alpha = 0
#     time_delay = 2000

#     while True:

#         for event in pg.event.get():
#             if event.type == pg.QUIT:
#                 pg.quit()
#                 exit()
    
#         black_screen.set_alpha(screen_alpha)

#         screen.fill('black')
#         entities.render(screen, camera)
#         ui.display(screen, entities)
        
#         screen.blit(black_screen, (0, 0))
#         font.render(screen=screen, text='you died', 
#                     x=WIDTH/2, y=HEIGHT/2, 
#                     colour=(255, 0, 0), size=50, style='center', 
#                     alpha=text_alpha)

#         if screen_alpha >= 255:
#             text_alpha+=3
#         else:
#             screen_alpha+=3
#         if text_alpha < 255:
#             time = pg.time.get_ticks()
        
#         if pg.time.get_ticks()-time>time_delay:
#             return

#         pg.display.update()
#         clock.tick(FPS)

import pygame as pg
import numpy as np
import math

from ..util.transitions import transition_in, transition_out, TRANSITION_TIME
from ..util.save_data import entity_data_to_df
from ..util.asset_loader import load_assets

from ..entities.entity_manager import EntityManager
from ..environment.environment import Environment

from ..game_state.ai_controller import Agents
from ..game_state.camera import Camera
from ..game_state.ui import UserInterface

DEFAULT_DISPLAY = 'default'
EFFECTS_DISPLAY = 'gaussian_blur'
OVERLAY_DISPLAY = 'black_alpha'

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
                self.goto = 'game'
        
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
    
class GameMenu:
    def __init__(self, client):
        # import game
        self.width, self.height = client.res
        self.displays = client.displays
        self.font = client.font
        self.clock = client.clock
        self.client = client

        # sprites
        self.ui_sprites = {
            'stat_icons': load_assets('./assets/stats', 1.0),
            'ability_icons': load_assets('./assets/abilities', 2.0),
            'trait_icons': load_assets('./assets/traits', 2.0),
            'hud_frames': load_assets('./assets/hud/', 1.0),
            'status_effect_icons': load_assets('./assets/status_effects', 1.0),
        }

        # transition handler
        self.goto = 'start'

        # data
        self.generation_time = 10
        self.current_generation = 0
        self.new_particle_time = 0.1

        # objects
        self.entity_manager = EntityManager({
            'creature': { # TODO change to default later
                'num_parts': 5,
                'pos': np.array([0, 0, 0], dtype=np.float32),
                'size': 5,
                'max_parts': 10,
                'num_pair_legs': 2,
                'leg_length': 100,
            },
            'brain': { # TODO change to default later
                'neurons': [0,0, # circle dens, angle
                            0,0, # triangle dens, angle
                            0,0, # square dens, angle
                            0,0, # pentagon dens, angle 
                            0,0, # hexagon dens, angle
                            # no hidden neurons
                            2, # move forward
                            2, # turn right
                            2, # turn left
                            ],
                'axons': [
                    {'in':0,'out':10,'w':1},
                    {'in':1,'out':11,'w':1},
                    {'in':1,'out':12,'w':-1},
                ]
            }, 
            'receptor': { # TODO change to default later
                'num_of_type': {
                    'circle': np.array([3]),
                    'triangle': np.array([0]),
                    'square': np.array([0]),
                    'pentagon': np.array([0]),
                    'hexagon': np.array([0]),
                },
                'spread': {
                    'circle': np.array([math.pi/6]),
                    'triangle': np.array([math.pi/6]),
                    'square': np.array([math.pi/6]),
                    'pentagon': np.array([math.pi/6]),
                    'hexagon': np.array([math.pi/6]),
                },
                'fov': {
                    'circle': np.array([math.pi/6]),
                    'triangle': np.array([math.pi/6]),
                    'square': np.array([math.pi/6]),
                    'pentagon': np.array([math.pi/6]),
                    'hexagon': np.array([math.pi/6]),
                },
                'opt_dens': {
                    'circle': np.array([0.5]),
                    'triangle': np.array([0.5]),
                    'square': np.array([0.5]),
                    'pentagon': np.array([0.5]),
                    'hexagon': np.array([0.5]),
                },
            },
            'stomach': { # TODO
                'circle': np.array([0.5]),
                'triangle': np.array([0.5]),
                'square': np.array([0.5]),
                'pentagon': np.array([0.5]),
                'hexagon': np.array([0.5]),
            },
            'traits': { # TODO change to default later
                'traits': [],
                'min_stats': {
                    'itl': 0, 'pwr': 0, 'def': 0, 'mbl': 0, 'stl': 0,
                }, 
                'max_stats': {
                    'itl': 1, 'pwr': 1, 'def': 1, 'mbl': 1, 'stl': 1,
                }
            },
        })
        self.environment = Environment()
        # self.environment.add_new_particles(
        #     2,
        #     np.array([[-100,0,0],[100,100,100]]),
        #     np.array([0,2]),
        #     np.array([0.5, 0.25])
        # )
        self.ai_agents = Agents(1)
        self.camera = Camera(self.entity_manager.pos[0])
        # self.ui = UserInterface(self.font, self.ui_sprites)

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
        # for event in events:
            # if event.type == pg.MOUSEBUTTONDOWN:
                # pos = self.camera.screen_to_world(event.pos[0], event.pos[1])
                # self.environment.add_new_particles(
                #     1, pos.reshape((1,3)), 
                #     np.zeros((1,), dtype=np.int32), 
                #     np.full((1,), 0.1, dtype=np.float32))

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

        self.generation_time -= dt
        if self.generation_time <= 0:
            # store data
            basic_data, receptor_data, stomach_data, brain_data = self.entity_manager.get_save_data()
            entity_data_to_df(self.current_generation, self.entity_manager.num_entities, basic_data, 'basic')
            entity_data_to_df(self.current_generation, self.entity_manager.num_entities, receptor_data, 'receptor')
            entity_data_to_df(self.current_generation, self.entity_manager.num_entities, stomach_data, 'stomach')
            entity_data_to_df(self.current_generation, self.entity_manager.num_entities, brain_data, 'brain')

            # update generation
            self.generation_time = 10
            self.current_generation += 1

            self.entity_manager.new_generation(self.current_generation)
            # self.ui.toggle_quests_menu()
            # self.ui.update_quests()

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

        # x_input = 0
        # y_input = 0
        # keys = pg.key.get_pressed()
        # if keys[pg.K_d]:
        #     x_input = 1
        # if keys[pg.K_a]:
        #     x_input = -1
        # if keys[pg.K_w]: 
        #     y_input = -1
        # if keys[pg.K_s]:
        #     y_input = 1
        # self.entity_manager.input(self.camera, {
        #     'index': 0,
        #     'x': x_input,
        #     'y': y_input,
        # })
        self.ai_agents.agent_input(self.entity_manager, self.environment, self.camera)
        self.entity_manager.update(self.camera, dt, self.environment)
        self.environment.update(dt)
        # self.camera.follow_entity(self.entity_manager.pos[0], self.entity_manager.scale[0])

        return {}

    def render(self) -> list[str]:
        self.displays[DEFAULT_DISPLAY].fill((20, 26, 51))
        self.entity_manager.render(self.displays[DEFAULT_DISPLAY], self.camera)
        self.environment.render(self.displays[DEFAULT_DISPLAY], self.camera)

        match self.transition_phase:
            case 1: 
                transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
            case 2:
                self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
            case 3:
                transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)
        
        # self.ui.render(self.displays[DEFAULT_DISPLAY], self.entity_manager.get_ui_data(0), self.current_generation)

        self.font.render(self.displays[DEFAULT_DISPLAY], str(self.current_generation), 
                         25, 25, (255,255,255), size=25, style='left')

        displays_to_render = [DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        return displays_to_render