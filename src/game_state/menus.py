from math import sqrt, sin, cos, pi
from random import randint, choice
import pygame as pg
from src.util.settings import NEW_GEN_TIME, FPS, CBODY_TEXTURE_KEY, SUN, ORBIT_RADIUS, WIDTH, HEIGHT
from src.game_state.camera import Camera
from src.combat.world_event import WorldEvent

def start_menu(screen, game_data):

    grav_constant = randint(900, 1100)

    # local functions for updating/render/loading the solar system animation
    def draw_solar_system(screen):
        # draw the c bodies
        for body in c_bodies:
            pg.draw.circle(screen, CBODY_TEXTURE_KEY[body['type']], 
                            camera.transform_to_screen(body['pos'][0:3]), 
                            body['size'])
        pg.draw.circle(screen, CBODY_TEXTURE_KEY[sun['type']],
                        camera.transform_to_screen(sun['pos'][0:3]),
                        sun['size'])
    
    def update_solar_system():
        for body in c_bodies:
            dx = sun['pos'][0]-body['pos'][0]
            dy = sun['pos'][1]-body['pos'][1]
            dr_sq = dx*dx+dy*dy
            a = grav_constant/dr_sq
            a_x, a_y = a*dx/sqrt(dr_sq), a*dy/sqrt(dr_sq)
            v_x, v_y = body['vel'][0]+a_x, body['vel'][1]+a_y
            body['vel'] = [v_x, v_y, 0]
            x, y = body['pos'][0]+v_x, body['pos'][1]+v_y
            body['pos'] = [x, y, 0]
        camera.update_pos(sun['pos'][0:3])
    
    def load_solar_system():
        cbodies = []
        num_bodies = randint(6, 9)
        for i in range(num_bodies):
            angle = randint(1, 360)/180*pi
            radius = (i+1)*ORBIT_RADIUS
            cbodies.append({
                'pos': [radius*cos(angle), radius*sin(angle), 0],
                'vel': [sqrt(grav_constant/radius)*sin(-angle), sqrt(grav_constant/radius)*cos(-angle)],
                'size': randint(3, 10),
                'type': choice(list(CBODY_TEXTURE_KEY.keys()))
            })

        return cbodies
    # ================================ #

    clock = game_data['clock']
    ui = game_data['ui']
    font = game_data['font']
    sun = SUN
    c_bodies = load_solar_system()
    camera = Camera(0, 0, 0)
    camera.update_pos(c_bodies[0]['pos'][0:3])
    r, g, b = 255, 255, 255

    # main game loop
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
        font.render(screen, 'press anywhere to continue', WIDTH//2, HEIGHT-50,
                    (r, g, b),
                    24, 'center')
        update_solar_system()

        ui.draw_mouse(screen)

        clock.tick(FPS)
        pg.display.update()

def game_menu(screen, game_data):
    entities = game_data['entities']
    corpses = game_data['corpses']
    evo_system = game_data['evo_system']
    combat_system = game_data['combat_system']

    controller = game_data['controller']
    ai_controller = game_data['ai']
    camera = game_data['camera']
    player = game_data['player']
    ui = game_data['ui']

    clock = game_data['clock']
    font = game_data['font']

    generation = 0
    generation_time = pg.time.get_ticks()

    while True:
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return
                if event.key == pg.K_SPACE:
                    evo_system.in_species_reproduce()
                # if event.key == pg.K_TAB:
                #     ui.toggle_quests_menu()
                #     ui.update_quests(WorldEvent(entities.get_entity_data(player)))
                #     ui.input(events, entities, corpses)
                if event.key == pg.K_DELETE:
                    entities.health[player] = -100
                    
        ui.input(events, entities, corpses, evo_system)
        # refresh screen
        screen.fill('black')
        dt = clock.tick()/15

        # player input
        entities.parse_input(controller.movement_input(), camera, dt)
        combat_system.use_ability(controller.ability_input(entities))

        # ai controller
        ai_controller.movement_input(entities, corpses, camera, dt)
        ai_controller.ability_input(entities, combat_system)
        
        # update loop
        entities.update(camera, dt)
        camera.follow_entity(entities, player)
        corpses.update()
        combat_system.update(entities, camera)

        # drawing
        entities.render(screen, camera)
        corpses.render(screen, camera)
        if controller.queued_ability!=-1:
            ui.ability_indicator(screen, entities, controller, camera)
        ui.display(screen, entities)
        # ui.arrow_to_corpse(screen, entities, player, corpses, camera)

        # death
        if entities.kill(player, corpses):
            game_over(screen, font, clock, entities, camera, ui)
            return

        # new generation
        if pg.time.get_ticks() - generation_time > NEW_GEN_TIME:
            # update the generation
            generation_time = pg.time.get_ticks()
            generation+=1

            # call the evo systems to operate on entities
            evo_system.new_generation(entities)

            # tell the ai to accept the new quests for the ais
            ai_controller.accept_quests(entities, evo_system)

            # allow the player to accept new quests
            ui.toggle_quests_menu()
            ui.update_quests(WorldEvent(entities.get_entity_data(player)))
            ui.input(events, entities, corpses, evo_system)
    
        pg.display.update()
        pg.display.set_caption(f'{clock.get_fps()}, {dt}')

def game_over(screen, font, clock, entities, camera, ui):

    black_screen = pg.Surface((WIDTH, HEIGHT))
    black_screen.fill('black')
    screen_alpha = 0
    text_alpha = 0
    time_delay = 2000

    while True:

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
    
        black_screen.set_alpha(screen_alpha)

        screen.fill('black')
        entities.render(screen, camera)
        ui.display(screen, entities)
        
        screen.blit(black_screen, (0, 0))
        font.render(screen, 'you died', WIDTH/2, HEIGHT/2, (255, 0, 0), 50, 'center', text_alpha)

        if screen_alpha >= 255:
            text_alpha+=3
        else:
            screen_alpha+=3
        if text_alpha < 255:
            time = pg.time.get_ticks()
        
        if pg.time.get_ticks()-time>time_delay:
            return

        pg.display.update()
        clock.tick(FPS)