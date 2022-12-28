from math import sqrt, sin, pi
import pygame as pg
from src.settings import NEW_GEN_TIME, FPS, CBODY_TEXTURE_KEY, CBODIES, SUN, WIDTH, HEIGHT
from src.game_state.camera import Camera

def start_menu(screen, game_data):

    clock = game_data['clock']
    ui = game_data['ui']
    font = game_data['font']
    # include an animation of the solar system as the start menu screen
    sun = SUN
    c_bodies = CBODIES
    camera = Camera(0, 0)
    camera.update_pos(c_bodies[0]['pos'][0], c_bodies[0]['pos'][1], 0)
    def draw_solar_system(screen):

        # draw the c bodies
        for body in c_bodies:
            pg.draw.circle(screen, CBODY_TEXTURE_KEY[body['type']], 
                            camera.transform_to_screen(body['pos'][0], body['pos'][1], 0), 
                            body['size'])
        pg.draw.circle(screen, CBODY_TEXTURE_KEY[sun['type']],
                        camera.transform_to_screen(sun['pos'][0], sun['pos'][1], 0),
                        sun['size'])
    def update_solar_system():
        for body in c_bodies:
            dx = sun['pos'][0]-body['pos'][0]
            dy = sun['pos'][1]-body['pos'][1]
            dr_sq = dx*dx+dy*dy
            a = 1000/dr_sq
            a_x, a_y = a*dx/sqrt(dr_sq), a*dy/sqrt(dr_sq)
            v_x, v_y = body['vel'][0]+a_x, body['vel'][1]+a_y
            body['vel'] = (v_x, v_y)
            x, y = body['pos'][0]+v_x, body['pos'][1]+v_y
            body['pos'] = (x, y)
        camera.update_pos(sun['pos'][0], sun['pos'][1], 0)
    
    r, g, b = 255, 255, 255
    while True:
        for event in pg.event.get():
            if event.type==pg.QUIT:
                pg.quit()
                exit()
            if event.type==pg.KEYDOWN:
                if event.key==pg.K_ESCAPE:
                    pg.quit()
                    exit()

            if event.type==pg.MOUSEBUTTONDOWN:
                # start game by clicking anywhere
                game_menu(screen, game_data)
        

        screen.fill('black')
        draw_solar_system(screen)
        time = pg.time.get_ticks()/1000
        r = 255*sin(time)%256
        g = 255*sin(time+pi/4)%256
        b = 255*sin(time+pi/2)%256
        font.render(screen, 'hello, universe', WIDTH//2, 50, 
                    (r, g, b), 
                    24, 'center')
        font.render(screen, 'press any key to continue', WIDTH//2, HEIGHT-50,
                    (r, g, b),
                    24, 'center')
        update_solar_system()

        ui.draw_mouse(screen)

        clock.tick(FPS)
        pg.display.update()

def game_menu(screen, game_data):
    entities = game_data['entities']
    controller = game_data['controller']
    ai_controller = game_data['ai']
    camera = game_data['camera']
    player = game_data['player']
    ui = game_data['ui']
    clock = game_data['clock']

    generation = 0
    generation_time = pg.time.get_ticks()

    while True:
        for event in pg.event.get():
            if event.type==pg.QUIT:
                pg.quit()
                exit()
            if event.type==pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return
                if event.key == pg.K_SPACE:
                    entities.in_species_reproduce(0)
        
        screen.fill('black')
        x_i, y_i = controller.movement_input()
        a_i = controller.ability_input(entities)
        entities.use_ability(a_i, player, camera)
        entities.parse_input(x_i, y_i, player, camera)
        ai_controller.movement_input(entities, camera)
        ai_controller.ability_input(entities, camera)
        if controller.queued_ability!=-1:
            ui.ability_indicator(screen, entities, player, controller, camera)
        entities.update()
        camera.follow_entity(entities, player)
        entities.draw(screen, camera)
        ui.display(screen, entities)

        if entities.kill(player):
            return

        if pg.time.get_ticks() - generation_time > NEW_GEN_TIME:
            generation_time = pg.time.get_ticks()
            generation+=1
            entities.new_generation()
    
        clock.tick(FPS)
        pg.display.update()
        pg.display.set_caption(f'{clock.get_fps()}, {len(entities.pos)}')