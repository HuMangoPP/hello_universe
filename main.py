import pygame as pg
from src.game_state.ai_controller import AIController
from src.entity import Entities
from src.game_state.player_controller import PlayerController
from src.game_state.camera import Camera
from src.settings import RES, HEIGHT, WIDTH, BASE_STATS, NEW_GEN_TIME, FPS
from src.game_state.menus import start_menu
from src.game_state.ui import UserInterface
from src.asset_loader import load_assets
from src.font import Font


if __name__ == '__main__':
    pg.init()
    screen = pg.display.set_mode(RES)
    pg.mouse.set_visible(False)
    
    stat_icons = load_assets('./assets/stats', 1.0)
    ability_icons = load_assets('./assets/abilities', 1.5)
    trait_icons = load_assets('./assets/traits', 1.5)
    hud_frames = load_assets('./assets/hud/', 1.0)
    sprites = {}
    sprites['stat_icons'] = stat_icons
    sprites['ability_icons'] = ability_icons
    sprites['trait_icons'] = trait_icons
    sprites['hud_frames'] = hud_frames

    clock = pg.time.Clock()

    player = 0

    camera = Camera(0, 0)
    entities = Entities()
    entities.add_new_entity({
        'pos': [0, 0, 20, 0],
        'spd': 5,
        'acc': 0.5,
        'body_parts': 5,
        'size': 5,
        'num_legs': 2,
        'leg_length': 100,
        'aggression': [],
        'herd': [],
    }, BASE_STATS)
    
    controller = PlayerController(player)
    ai_controller = AIController(player)

    font = Font(pg.image.load('./assets/font/font.png'))
    ui = UserInterface(player, font, sprites)

    game_data = {
        'entities': entities,
        'camera': camera,
        'player': player,
        'controller': controller,
        'ai': ai_controller,
        'ui': ui,
        'clock': clock,
        'sprites': sprites,
        'font': font,
    }
    start_menu(screen , game_data)
