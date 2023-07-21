import pygame as pg
import moderngl as mgl

from .pyfont import Font
from .pymgl import GraphicsEngine

from .menus import StartMenu, SimMenu, MonitorMenu

MENU_MAP = {
    'start': 0,
    'sim': 1,
    'monitor': 2,
}

class Game:
    def __init__(self):
        pg.init()
        self.res = (640, 420)
        
        pg.display.set_mode(self.res, pg.OPENGL | pg.DOUBLEBUF)
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = (
            mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        )
        self.graphics_engine = GraphicsEngine(self.ctx, self.res)
        self.font = Font(pg.image.load('./src/pyfont/font.png').convert())
        self.displays = {
            'default': pg.Surface(self.res),
            'black_alpha': pg.Surface(self.res)
        }
        self.clock = pg.time.Clock()

        self.menus = [StartMenu(self), SimMenu(self), MonitorMenu(self)]
        self.current_menu = 0

    def update(self):
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                return {
                    'exit': True
                }
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return {
                    'exit': True
                }
    
        return self.menus[self.current_menu].update(events)

    def render(self):
        self.ctx.clear(0.08, 0.1, 0.2)
        displays_to_render = self.menus[self.current_menu].render()
        [self.graphics_engine.render(self.displays[display], self.displays[display].get_rect(),
                                     shader=display) for display in displays_to_render]

    def run(self):
        self.menus[self.current_menu].on_load()
        while True:
            exit_status = self.update()
            if exit_status:
                if exit_status['exit']:
                    pg.quit()
                    return
                else:
                    self.current_menu = MENU_MAP[exit_status['goto']]
                    self.menus[self.current_menu].on_load()
            self.render()
            self.clock.tick()
            pg.display.flip()

            pg.display.set_caption(f'fps: {self.clock.get_fps()}')