from math import atan2, cos, pi, sin
import pygame as pg
from src.settings import GAUGE_UI, STAT_BAR_UI, HEIGHT, WIDTH, ABILITY_TRAIT_UI
from src.combat.abilities import ALL_ABILITIES

class UserInterface:
    def __init__(self, player, ui_sprites):
        self.player = player
        self.stat_icons = list(ui_sprites['stat_icons'].values())
        self.ability_icons = ui_sprites['ability_icons']
        self.trait_icons = ui_sprites['trait_icons']
        self.hud_frames = ui_sprites['hud_frames']
    
    def draw_mouse(self, screen):
        mx, my = pg.mouse.get_pos()
        reticle_size = 10
        reticle_width = 3
        reticle_line_length = 5
        # reticle circle
        pg.draw.circle(screen, 'white', (mx, my), reticle_size, reticle_width)
        # down
        pg.draw.line(screen, 'white', (mx, my+reticle_line_length), (mx, my+reticle_size+reticle_line_length), reticle_width)
        # up
        pg.draw.line(screen, 'white', (mx, my-reticle_line_length), (mx, my-reticle_size-reticle_line_length), reticle_width)
        # right
        pg.draw.line(screen, 'white', (mx+reticle_line_length, my), (mx+reticle_size+reticle_line_length, my), reticle_width)
        # right
        pg.draw.line(screen, 'white', (mx-reticle_line_length, my), (mx-reticle_size-reticle_line_length, my), reticle_width)

    def display(self, screen, entities):

        # hp and energy bars
        self.display_hp(screen, entities)
        
        self.display_energy(screen, entities)

        # stats
        self.display_stats(screen, entities)

        # traits and abilities
        self.display_traits_and_abilities(screen, entities)

        self.draw_mouse(screen)

    def display_hp(self, screen, entities):
        # health bar, taking inspiration from Diablo/PoE
        health_bar = pg.Surface((2*GAUGE_UI['radius'], 2*GAUGE_UI['radius']))
        health_bar.set_colorkey('black')
        health_ratio = 1-entities.health[self.player]/entities.stats[self.player]['hp']
        pg.draw.rect(health_bar, 'black', (0, 0, 2*GAUGE_UI['radius'], health_ratio*GAUGE_UI['radius']*2))
        hp_frame = self.hud_frames['hp_frame']
        hp_frame.set_colorkey('black')
        pg.draw.circle(health_bar, GAUGE_UI['colours'][0], 
                        (GAUGE_UI['radius'], GAUGE_UI['radius']), 
                        GAUGE_UI['radius'])
        screen.blit(health_bar, (hp_frame.get_width()/2-GAUGE_UI['radius'], 
                                HEIGHT-hp_frame.get_height()/2-GAUGE_UI['radius']))
        screen.blit(hp_frame, (0, HEIGHT-hp_frame.get_height()))

    def display_energy(self, screen, entities):
        # energy bar, similar in style to the health
        energy_bar = pg.Surface((2*GAUGE_UI['radius'], 2*GAUGE_UI['radius']))
        energy_bar.set_colorkey('black')
        total_energy_calculation = (entities.stats[self.player]['pwr']+
                                    entities.stats[self.player]['def']+
                                    entities.creature[self.player].num_parts+1)
        energy_ratio = 1-entities.energy[self.player]/total_energy_calculation
        energy_frame = self.hud_frames['energy_frame']
        energy_frame.set_colorkey('black')
        pg.draw.circle(energy_bar, GAUGE_UI['colours'][1],
                        (GAUGE_UI['radius'], GAUGE_UI['radius']),
                        GAUGE_UI['radius'])
        # total energy based on power and defense and number of body parts

        pg.draw.rect(energy_bar, 'black', (0, 0, 2*GAUGE_UI['radius'], energy_ratio*GAUGE_UI['radius']*2))
        screen.blit(energy_bar, (WIDTH-energy_frame.get_width()/2-GAUGE_UI['radius'], 
                                HEIGHT-energy_frame.get_height()/2-GAUGE_UI['radius']))
        screen.blit(energy_frame, (WIDTH-energy_frame.get_width(), HEIGHT-energy_frame.get_height()))

    def display_stats(self, screen, entities):
        # stat bars on the right
        
        stats = [
            entities.stats[self.player]['itl'],
            entities.stats[self.player]['pwr'],
            entities.stats[self.player]['def'],
            entities.stats[self.player]['mbl'],
            entities.stats[self.player]['stl'],
        ]
        stats_frame = self.hud_frames['stats_frame']
        stats_frame.set_colorkey('black')
        left_edge_pad = self.hud_frames['hp_frame'].get_width()
        bar_edge_pad = left_edge_pad+STAT_BAR_UI['bar_pad']
        for i in range(len(stats)):
            stat_rect = pg.Rect(bar_edge_pad+STAT_BAR_UI['left_pad']+i*STAT_BAR_UI['width'],
                                HEIGHT-stats[i]-STAT_BAR_UI['bottom_pad'], STAT_BAR_UI['width'], stats[i])
            pg.draw.rect(screen, STAT_BAR_UI['colours'][i], stat_rect)
            icon = self.stat_icons[i]
            screen.blit(icon, (bar_edge_pad+STAT_BAR_UI['left_pad']+(i+0.5)*STAT_BAR_UI['width']-icon.get_width()/2, 
                                             HEIGHT-STAT_BAR_UI['bottom_pad']+STAT_BAR_UI['frame_pad']))
        
        screen.blit(stats_frame, (left_edge_pad+STAT_BAR_UI['left_pad'], HEIGHT-STAT_BAR_UI['bottom_pad']-stats_frame.get_height()+STAT_BAR_UI['frame_pad']))

    def ability_slots(self, screen, entities):
        abilities = entities.abilities[self.player]
        frame = self.hud_frames['ability_and_trait_frame']
        right_pad = self.hud_frames['energy_frame'].get_width()
        left_edge_pad = WIDTH-right_pad-frame.get_width()-ABILITY_TRAIT_UI['right_pad']
        icon_edge_pad = left_edge_pad+ABILITY_TRAIT_UI['frame_pad']
        for i in range(len(abilities)):
            icon = self.ability_icons[abilities[i]]
            screen.blit(icon, (icon_edge_pad+i*ABILITY_TRAIT_UI['icon_size'],
                                HEIGHT-ABILITY_TRAIT_UI['bottom_pad']))

    def trait_slots(self, screen, entities):
        traits = entities.traits[self.player].traits
        frame = self.hud_frames['ability_and_trait_frame']
        right_pad = self.hud_frames['energy_frame'].get_width()
        left_edge_pad = WIDTH-right_pad-frame.get_width()-ABILITY_TRAIT_UI['right_pad']
        icon_edge_pad = left_edge_pad+ABILITY_TRAIT_UI['frame_pad']
        for i in range(len(traits)):
            icon = self.trait_icons[traits[i]]
            screen.blit(icon, (icon_edge_pad+i*ABILITY_TRAIT_UI['icon_size'],
                                HEIGHT-ABILITY_TRAIT_UI['bottom_pad']-ABILITY_TRAIT_UI['icon_size']))

    def display_traits_and_abilities(self, screen, entities):
        frame = self.hud_frames['ability_and_trait_frame']
        frame.set_colorkey('black')
        right_pad = self.hud_frames['energy_frame'].get_width()
        left_edge_pad = WIDTH-right_pad-frame.get_width()-ABILITY_TRAIT_UI['right_pad']
        self.ability_slots(screen, entities)
        self.trait_slots(screen, entities)
        screen.blit(frame, (left_edge_pad, 
                            HEIGHT-ABILITY_TRAIT_UI['bottom_pad']-frame.get_height()/2))

    def ability_indicator(self, screen, entities, player, controller, camera):
        ability_num = controller.queued_ability
        ability_key = entities.abilities[player][ability_num]
        x, y = camera.transform_to_screen(entities.pos[player][0], entities.pos[player][1], entities.pos[player][2])

        if 'skillshot' in ALL_ABILITIES[ability_key]['type']:
            mx, my = pg.mouse.get_pos()
            # radius will be calculated using entity stats
            radius = 100
            angle = atan2((my-y), (mx-x))
            nx, ny = radius*cos(angle)+WIDTH//2, radius*sin(angle)+HEIGHT//2
            arrow_spread_angle = pi/4
            left_point_angle = angle-arrow_spread_angle/2
            right_point_angle = pi-arrow_spread_angle-left_point_angle
            indicator_color = pg.Color(0, 100, 100, 100)
            indicator_bg = pg.Color(0, 100, 100, 20)
            # skillshot range
            # pg.draw.circle(screen, indicator_bg, (x, y), radius)
            # pg.draw.circle(screen, indicator_color, (x, y), radius, 5)
            # skillshot indicator
            pg.draw.line(screen, 'cyan', (x, y), (nx, ny), 5)
            pg.draw.polygon(screen, 'cyan', [(nx, ny), 
                                             (nx-30*cos(left_point_angle), ny-30*sin(left_point_angle)),
                                             (nx+30*cos(right_point_angle), ny-30*sin(right_point_angle))])
        if 'aoe' in ALL_ABILITIES[ability_key]['type']:
            # aoe range
            # the radius will be calculated using entity stats
            radius = 100
            pg.draw.circle(screen, 'cyan', (x, y), radius, 5) 