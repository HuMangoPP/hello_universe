import pygame as pg
from src.game_state.ai_controller import AIController
from src.game_state.player_controller import PlayerController
from src.game_state.camera import Camera
from src.game_state.menus import start_menu
from src.game_state.ui import UserInterface

from src.entities.entities import Entities
from src.entities.corpse import Corpses
from src.entities.evo_system import EvoSystem
from src.entities.combat_system import CombatSystem

from src.combat.abilities import BASIC_ABILITIES

from src.environment.environment import Environment

from src.util.settings import RES, BASE_STATS
from src.util.asset_loader import load_assets
from src.util.font import Font

def main():
    pg.init()
    screen = pg.display.set_mode(RES)
    pg.mouse.set_visible(False)
    
    stat_icons = load_assets('./assets/stats', 1.0)
    ability_icons = load_assets('./assets/abilities', 1.5)
    trait_icons = load_assets('./assets/traits', 1.5)
    hud_frames = load_assets('./assets/hud/', 1.0)
    status_effect_icons = load_assets('./assets/status_effects', 1.5)
    sprites = {}
    sprites['stat_icons'] = stat_icons
    sprites['ability_icons'] = ability_icons
    sprites['trait_icons'] = trait_icons
    sprites['hud_frames'] = hud_frames
    sprites['status_effect_icons'] = status_effect_icons

    clock = pg.time.Clock()

    player = 0

    camera = Camera(0, 0, 0)
    entities = Entities()
    entities.add_new_entity({
        'pos': [0, 0, 20, 0],
        'spd': 5,
        'acc': 0.5,
        'body_parts': 5,
        'size': 5,
        'scale': -6,
        'max_parts': 10,
        'num_legs': 0,
        'leg_length': 100,
        'aggression': [],
        'herd': [],
        'abilities': BASIC_ABILITIES,
        'traits': []
    }, BASE_STATS)
    corpses = Corpses()
    evo_system = EvoSystem(entities)
    combat_system = CombatSystem(entities, camera)
    
    controller = PlayerController(player)
    ai_controller = AIController(player)

    environment = Environment()

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
        'corpses': corpses,
        'evo_system': evo_system,
        'combat_system': combat_system,
        'environment': environment,
    }
    start_menu(screen, game_data)

if __name__ == '__main__':
    main()
