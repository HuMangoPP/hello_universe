from random import randint
import pygame as pg
from src.settings import WIDTH, HEIGHT, NEW_GEN_TIME, FPS

def start_menu(screen, game_data):

    start_button = pg.Rect(WIDTH//4, HEIGHT//4, WIDTH//2, HEIGHT//2)
    clock = game_data['clock']

    while True:
        for event in pg.event.get():
            if event.type==pg.QUIT:
                pg.quit()
                exit()
            if event.type==pg.KEYDOWN:
                if event.key==pg.K_ESCAPE:
                    pg.quit()
                    exit()

            if event.type==pg.MOUSEBUTTONUP:
                x, y = pg.mouse.get_pos()
                if start_button.collidepoint(x, y):
                    # game start
                    game_menu(screen, game_data)
        

        screen.fill('black')
        pg.draw.rect(screen, 'white', start_button)
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
        camera.update(entities, player)
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