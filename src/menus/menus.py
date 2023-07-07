import pygame as pg
import numpy as np

from ..util import transition_in, transition_out, TRANSITION_TIME, draw_shape

from ..simulation import Simulation
from .camera import Camera

# constants
DEFAULT_DISPLAY = 'default'
EFFECTS_DISPLAY = 'gaussian_blur'
OVERLAY_DISPLAY = 'black_alpha'

class StartMenu:
    def __init__(self, game):
        # import game
        self.width, self.height = game.res
        self.displays : dict = game.displays
        self.font = game.font
        self.clock : pg.time.Clock = game.clock

        # transition handler
        self.goto = 'sim'
    
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
        # for transitions
        dt = self.clock.get_time() / 1000
        # handle events
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key in [pg.K_r, pg.K_SPACE]:
                    self.transition_phase = 1
                    self.transition_time = 0
                    self.goto = 'sim'
                if event.key == pg.K_m:
                    self.transition_phase = 1
                    self.transition_time = 0
                    self.goto = 'monitor'
                if event.key == pg.K_s:
                    return {
                        'exit': True,
                        'run_sim': True
                    }
            if event.type == pg.MOUSEBUTTONDOWN:
                self.transition_phase = 1
                self.transition_time = 0
                self.goto = 'sim'
        
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

        # text
        self.font.render(self.displays[DEFAULT_DISPLAY], 'Hello Universe', self.width/2, 100, 
                         (255, 255, 255), 25, style='center')

        # transitions
        match self.transition_phase:
            case 1: 
                transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
            case 2:
                self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
            case 3:
                transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)
        
        # displays
        displays_to_render = [DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        return displays_to_render
    

class SimMenu:
    def __init__(self, game):
        # import game
        self.width, self.height = game.res
        self.displays : dict = game.displays
        self.font = game.font
        self.clock : pg.time.Clock = game.clock
        self.game = game

        # transition handler
        self.goto = 'start'

        # sim
        self.sim = Simulation()
        
        # rendering
        self.camera = Camera(np.zeros((3,), np.float32), game.res)

    def on_load(self):
        self.on_transition()
        self.sim.spawn_entities(
            [{
                'id': 'e0',
                'pos': np.zeros((3,), np.float32),
                'scale': 1,
                'clock_period': 2,

                'stats': {'itl': 1, 'pwr': 1, 'def': 1, 'mbl': 1, 'stl': 1},

                'brain': {
                    'neurons': [],
                    'axons': [],
                },

                'receptors': {
                    'num_of_type': np.zeros((5,), np.int32),
                    'spread': np.full((5,), np.pi/6, np.float32),
                    'fov': np.full((5,), np.pi/6, np.float32),
                    'opt_dens': np.full((5,), 0.5, np.float32),
                    'sense_radius': np.full((5,), 100, np.float32),
                },
                
                'stomach': {
                    'metabolism': np.ones((2,), np.float32),
                    'capacity': 10,
                },

                'glands': {
                    'opt_dens': np.arange(0.3, 0.71, 0.1),
                },
            }]
        )
  
    def on_transition(self):
        # 0 -> no transition
        # 1 -> transition out
        # 2 -> black screen
        # 3 -> transition in
        self.transition_phase = 2
        self.transition_time = 0

    def update(self, events):
        dt = self.clock.get_time() / 1000

        # handle events
        for event in events:
            ...

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
        else:
            self.sim.update()
    
    def render(self) -> list[str]:
        self.displays[DEFAULT_DISPLAY].fill((20, 26, 51))

        render_data = self.sim.render_rt()

        for e_render in render_data['entities']:
            drawpos = self.camera.transform_to_screen(e_render[:3])
            pg.draw.circle(self.displays[DEFAULT_DISPLAY], (255, 255, 255), drawpos, 5)
            pg.draw.line(self.displays[DEFAULT_DISPLAY], (255, 255, 255), drawpos,
                         drawpos + 10 * np.array([np.cos(e_render[3]), np.sin(e_render[3])]))
        
        for p_render in render_data['env']['pheromones']:
            drawpos = self.camera.transform_to_screen(p_render[:3])
            color = (0, p_render[3] * 255, 0)
            draw_shape(self.displays[DEFAULT_DISPLAY], drawpos, color, 5, p_render[4])
        
        for f_render in render_data['env']['food']:
            drawpos = self.camera.transform_to_screen(f_render[:3])
            color = (0, 0, 255)
            draw_shape(self.displays[DEFAULT_DISPLAY], drawpos, color, 5, f_render[3])

        # transitions
        match self.transition_phase:
            case 1: 
                transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
            case 2:
                self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
            case 3:
                transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)

        # displays
        displays_to_render = [DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        return displays_to_render


class MonitorMenu:
    def __init__(self, game):
        # import game
        self.width, self.height = game.res
        self.displays : dict = game.displays
        self.font = game.font
        self.clock : pg.time.Clock = game.clock

        # transition handler
        self.goto = 'start'

        # sim
        self.sim = Simulation()

        # render
        self.entity_pointer = 0
    
    def on_load(self):
        self.on_transition()
        self.sim.spawn_entities(
            [{
                'id': 'e0',
                'pos': np.zeros((3,), np.float32),
                'scale': 1,
                'clock_period': 2,

                'stats': {'itl': 1, 'pwr': 1, 'def': 1, 'mbl': 1, 'stl': 1},

                'brain': {
                    'neurons': [],
                    'axons': [['i_c', 'o_mvf', 1],
                              ['i_c', 'o_mvs', -1]],
                },

                'receptors': {
                    'num_of_type': np.array([3,2,0,0,0]),
                    'spread': np.full((5,), np.pi/6, np.float32),
                    'fov': np.full((5,), np.pi/6, np.float32),
                    'opt_dens': np.full((5,), 0.5, np.float32),
                    'sense_radius': np.array([100, 65, 65, 77, 45], np.float32),
                },
                
                'stomach': {
                    'metabolism': np.ones((2,), np.float32),
                    'capacity': 10,
                },

                'glands': {
                    'opt_dens': np.arange(0.3, 0.71, 0.1),
                },
            }]
        )

    def on_transition(self):
        # 0 -> no transition
        # 1 -> transition out
        # 2 -> black screen
        # 3 -> transition in
        self.transition_phase = 2
        self.transition_time = 0
    
    def update(self, events: list[pg.Event]):
        # for transitions
        dt = self.clock.get_time() / 1000

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RIGHT:
                    self.entity_pointer += 1
                if event.key == pg.K_LEFT:
                    self.entity_pointer -= 1
                self.entity_pointer %= len(self.sim.entities)
        
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
        else:
            self.sim.update()
        return {}

    def render(self) -> list[str]:
        self.displays[DEFAULT_DISPLAY].fill((20, 26, 51))

        self.sim.render_monitor(self.displays[DEFAULT_DISPLAY], self.entity_pointer, self.font)

        self.font.render(self.displays[DEFAULT_DISPLAY], f'{self.entity_pointer + 1}-{len(self.sim.entities)}',
                         20, 400, (255, 255, 255), size=15, style='left')
        self.font.render(self.displays[DEFAULT_DISPLAY], f'st {round(self.sim.sim_time, 2)}',
                         20, 350, (255, 255, 255), size=15, style='left')

        # transitions
        match self.transition_phase:
            case 1: 
                transition_out(self.displays[OVERLAY_DISPLAY], self.transition_time)
            case 2:
                self.displays[OVERLAY_DISPLAY].fill((10, 10, 10))
            case 3:
                transition_in(self.displays[OVERLAY_DISPLAY], self.transition_time)
        
        # displays
        displays_to_render = [DEFAULT_DISPLAY]
        if self.transition_phase > 0:
            displays_to_render.append(OVERLAY_DISPLAY)
        return displays_to_render
    
