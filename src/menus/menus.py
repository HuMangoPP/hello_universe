import pygame as pg
import numpy as np

from ..util import transition_in, transition_out, TRANSITION_TIME, draw_shape, render_neuron, render_axon

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


def render_brain(display: pg.Surface, font, neuron_loc: dict, neuron_actv: dict, axons: list):
        for nid in neuron_loc:
            render_neuron(display, *neuron_loc[nid], font, nid, neuron_actv[nid])

        for axon in axons:
            render_axon(display, neuron_loc[axon[0]], neuron_loc[axon[1]], axon[2])


def render_stomach(display: pg.Surface, font, width, height, fullness: float):
    stomachbar = pg.Rect(width - 130, height - 110, 10, 100 * fullness)
    stomachbar.bottom = height - 10
    pg.draw.rect(display, (0, 255, 0), stomachbar)
    stomachbar.height = 100
    stomachbar.bottom = height - 10
    pg.draw.rect(display, (255, 255, 255), stomachbar, 2)


def render_health_and_energy(display: pg.Surface, font, health: float, energy: float):
    hpbar = pg.Rect(10, 300, health, 10)
    pg.draw.rect(display, (255, 0, 0), hpbar)
    hpbar.width = 100
    pg.draw.rect(display, (255, 255, 255), hpbar, 2)
    
    enbar = pg.Rect(10, 285, energy, 10)
    pg.draw.rect(display, (0, 0, 255), enbar)
    enbar.width = 100
    pg.draw.rect(display, (255, 255, 255), enbar, 2)


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

        render_data = self.sim.render_monitor(self.entity_pointer)

        # creature
        drawpos = (self.width/2, self.height *3/4)
        pg.draw.circle(self.displays[DEFAULT_DISPLAY], (255, 255, 255), drawpos, 5)

        # env
        for ph in render_data['env']['pheromones']:
            pos = ph[:3] - render_data['entity']['pos']
            color = (0, 255 * ph[3], 0)
            draw_shape(self.displays[DEFAULT_DISPLAY], pos[:2] + drawpos, color, 5, ph[4])
        
        # glands
        self.font.render(self.displays[DEFAULT_DISPLAY], 'glands', self.width - 55, self.height - 120, (255, 255, 255), 
                         size=10, style='center')
        self.displays[DEFAULT_DISPLAY].blit(render_data['entity']['glands'], (self.width - 110, self.height - 110))

        # receptors
        drawbox = render_data['entity']['receptors'].get_rect()
        drawbox.center = drawpos
        self.displays[DEFAULT_DISPLAY].blit(render_data['entity']['receptors'], drawbox)

        # health and energy
        render_health_and_energy(self.displays[DEFAULT_DISPLAY], self.font,
                                 render_data['entity']['health'], render_data['entity']['energy'])

        # stomach
        render_stomach(self.displays[DEFAULT_DISPLAY], self.font, self.width, self.height, 
                       render_data['entity']['stomach'])

        # brain
        render_brain(self.displays[DEFAULT_DISPLAY], self.font, *render_data['entity']['brain'])


        # timer
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
    
