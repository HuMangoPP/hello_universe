from math import atan2, cos, pi, sin
import pygame as pg
from src.settings import BAR_WIDTH, EDGE_PADDING, HEALTH_AND_ENERGY_RADIUS, UI_BG_COLOR, UI_BG_HEIGHT, WIDTH, HEIGHT, STAT_COLORS, GAUGE_COLORS, ABILITY_Y_ALIGN, TRAIT_Y_ALIGN
from src.combat.abilities import ALL_ABILITIES

class UserInterface:
    def __init__(self, player, ui_sprites):
        self.player = player
        self.stat_icons = list(ui_sprites['stat_icons'].values())
        self.ability_icons = ui_sprites['ability_icons']
        self.trait_icons = ui_sprites['trait_icons']
    
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
        intelligence = entities.stats[self.player]['intelligence']
        power = entities.stats[self.player]['power']
        defense = entities.stats[self.player]['defense']
        mobility = entities.stats[self.player]['mobility']
        stealth = entities.stats[self.player]['stealth']
        
        stats = [
            intelligence,
            power,
            defense,
            mobility,
            stealth
        ]

        # UI backgrounds
        pg.draw.rect(screen, UI_BG_COLOR, 
                        (0, HEIGHT-UI_BG_HEIGHT, WIDTH, UI_BG_HEIGHT))
        # health bar, taking inspiration from PoE
        health_bar = pg.Surface((2*HEALTH_AND_ENERGY_RADIUS, 2*HEALTH_AND_ENERGY_RADIUS))
        pg.draw.circle(health_bar, GAUGE_COLORS[0], 
                        (HEALTH_AND_ENERGY_RADIUS, 
                        HEALTH_AND_ENERGY_RADIUS), 
                        HEALTH_AND_ENERGY_RADIUS)
        health_bar.set_colorkey('black')
        health_ratio = 1-entities.health[self.player]/entities.stats[self.player]['health']
        pg.draw.rect(health_bar, 'black', (0, 0, 2*HEALTH_AND_ENERGY_RADIUS, health_ratio*HEALTH_AND_ENERGY_RADIUS*2))
        screen.blit(health_bar, (0, HEIGHT-2*HEALTH_AND_ENERGY_RADIUS))
        
        # energy bar, similar in style to the health
        energy_bar = pg.Surface((2*HEALTH_AND_ENERGY_RADIUS, 2*HEALTH_AND_ENERGY_RADIUS))
        pg.draw.circle(energy_bar, GAUGE_COLORS[1],
                        (HEALTH_AND_ENERGY_RADIUS,
                        HEALTH_AND_ENERGY_RADIUS),
                        HEALTH_AND_ENERGY_RADIUS)
        # total energy based on power and defense and number of body parts
        total_energy_calculation = (entities.stats[self.player]['power']+
                                    entities.stats[self.player]['defense']+
                                    entities.render[self.player].num_parts)
        energy_ratio = 1-entities.energy[self.player]/total_energy_calculation

        pg.draw.rect(energy_bar, 'black', (0, 0, 2*HEALTH_AND_ENERGY_RADIUS, energy_ratio*HEALTH_AND_ENERGY_RADIUS*2))

        energy_bar.set_colorkey('black')
        screen.blit(energy_bar, (2*HEALTH_AND_ENERGY_RADIUS, HEIGHT-2*HEALTH_AND_ENERGY_RADIUS))

        # stat bars on the right
        for i in range(len(stats)):
            stat_rect = pg.Rect(WIDTH-(len(stats)-i)*BAR_WIDTH-EDGE_PADDING,
                                HEIGHT-stats[i]-EDGE_PADDING, BAR_WIDTH, stats[i])
            pg.draw.rect(screen, STAT_COLORS[i], stat_rect)
            screen.blit(self.stat_icons[i], (WIDTH-(len(stats)-i)*BAR_WIDTH-EDGE_PADDING+BAR_WIDTH/2-self.stat_icons[i].get_width()/2, 
                                             HEIGHT-EDGE_PADDING+BAR_WIDTH/2-self.stat_icons[i].get_height()/2))
        
        self.ability_slots(screen, entities)
        self.trait_slots(screen, entities)

        self.draw_mouse(screen)

    def ability_slots(self, screen, entities):
        abilities = entities.abilities[self.player]

        for i in range(len(abilities)):
            screen.blit(self.ability_icons[abilities[i]], (WIDTH//2 + (i-2)*2*BAR_WIDTH - self.ability_icons[abilities[i]].get_width()/2, 
                                                           ABILITY_Y_ALIGN - self.ability_icons[abilities[i]].get_height()/2))

    def trait_slots(self, screen, entities):
        traits = entities.traits[self.player].traits

        for i in range(len(traits)):
            screen.blit(self.trait_icons[traits[i]], (WIDTH//2+(i-2)*2*BAR_WIDTH - self.trait_icons[traits[i]].get_width()/2,
                                                      TRAIT_Y_ALIGN - self.trait_icons[traits[i]].get_width()/2))

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