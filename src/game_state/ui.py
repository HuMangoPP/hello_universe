from math import atan2, cos, pi, sin
import pygame as pg
from src.util.settings import GAUGE_UI, STAT_BAR_UI, HEIGHT, WIDTH, ATS_UI, QUEST_CARD_UI, HEADER, TITLE_FONT_SIZE, HUD_HEIGHT, HUD_WIDTH, HUD_BOTTOM
from src.combat.abilities import ALL_ABILITIES, BASE_AOE_RADIUS

QUEST_LINGER_TIME = 1000

class UserInterface:
    def __init__(self, player, font, ui_sprites):
        self.font = font
        self.player = player
        self.colorkey_all(ui_sprites)
        self.stat_icons = list(ui_sprites['stat_icons'].values())
        self.ability_icons = ui_sprites['ability_icons']
        self.trait_icons = ui_sprites['trait_icons']
        self.hud_frames = ui_sprites['hud_frames']
        self.status_icons = ui_sprites['status_effect_icons']

        self.quest_ui = {
            'display': False,
            'ui': Quest_UI([])
        }
        self.interaction_ui = Interaction_UI({
            'bone': ui_sprites['hud_frames']['bone'],
            'capsule': ui_sprites['hud_frames']['capsule'],
            'nutrients': ui_sprites['hud_frames']['nutrients'],
        })
    
    def colorkey_all(self, ui_sprites):
        for sprite_type in ui_sprites:
            for sprite in ui_sprites[sprite_type]:
                ui_sprites[sprite_type][sprite].set_colorkey((0, 0, 0))
    
    ############################# 
    # hud and mouse             #
    ############################# 
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

    def display(self, screen, entities, generation):

        self.display_hud_frame(screen)

        # hp and energy bars
        self.display_hp(screen, entities)
        
        self.display_energy(screen, entities)

        # stats
        self.display_stats(screen, entities)

        # traits and abilities
        self.display_traits_and_abilities(screen, entities)

        # status effects
        self.display_statuses(screen, entities)

        self.draw_mouse(screen)
        self.display_generation(screen, generation)

        # quest
        if self.quest_ui['display']:
            self.quest_ui['ui'].display(screen, self.font)
        
        # interactions
        self.interaction_ui.display(screen, self.font)

    def input(self, pg_events, entities, corpses, evo_system):
        if self.quest_ui['display']:
            quest = self.quest_ui['ui'].input(pg_events)
            if quest:
                evo_system.rec_quest(self.player, quest)
                self.toggle_quests_menu()
        
        self.interaction_ui.detection(entities.pos[self.player], corpses)
        interact = self.interaction_ui.input(pg_events)
        if interact['type'] == 'consume':
            entities.consume(self.player, interact['index'], corpses)
    
    def display_generation(self, screen, generation):
        frame = self.hud_frames['gen_frame']
        screen.blit(frame,
                    (WIDTH//2-frame.get_width()//2, HEADER-frame.get_height()//2))
        self.font.render(screen=screen,
                         text=f'gen {generation}',
                         x=WIDTH//2, y=HEADER,
                         colour=(255, 255, 255),
                         size=TITLE_FONT_SIZE, style='center')
        ...

    def display_hud_frame(self, screen):
        frame = self.hud_frames['enclosing_frame']
        bottom = min(HEIGHT-HUD_HEIGHT+WIDTH//2-HUD_WIDTH-frame.get_width()//2, HUD_BOTTOM)
        dist = bottom-(HEIGHT-HUD_HEIGHT)
        points = [
            (0, HEIGHT-HUD_HEIGHT),
            (HUD_WIDTH, HEIGHT-HUD_HEIGHT),
            (HUD_WIDTH+dist, bottom),
            (WIDTH-HUD_WIDTH-dist, bottom),
            (WIDTH-HUD_WIDTH, HEIGHT-HUD_HEIGHT),
            (WIDTH, HEIGHT-HUD_HEIGHT),
            (WIDTH, HEIGHT),
            (0, HEIGHT),
        ]
        pg.draw.polygon(screen, (50, 50, 50), points)

        for i in range(5):
            pg.draw.line(screen, (255, 255, 255), points[i], points[i+1], 4)
        screen.blit(frame, (WIDTH//2-frame.get_width()//2, bottom-frame.get_height()//2-2))

    def display_hp(self, screen, entities):
        # health bar, taking inspiration from Diablo/PoE
        health_bar = pg.Surface((2*GAUGE_UI['radius'], 2*GAUGE_UI['radius']))
        health_bar.set_colorkey('black')
        health_ratio = 1-entities.health[self.player]/entities.stats[self.player]['hp']
        hp_frame = self.hud_frames['hp_frame']
        pg.draw.circle(health_bar, GAUGE_UI['colours'][0], 
                        (GAUGE_UI['radius'], GAUGE_UI['radius']), 
                        GAUGE_UI['radius'])
        pg.draw.rect(health_bar, 'black', (0, 0, 2*GAUGE_UI['radius'], health_ratio*GAUGE_UI['radius']*2))
        screen.blit(health_bar, (hp_frame.get_width()/2-GAUGE_UI['radius'], 
                                HEIGHT-hp_frame.get_height()/2-GAUGE_UI['radius']))
        screen.blit(hp_frame, (0, HEIGHT-hp_frame.get_height()))

    def display_energy(self, screen, entities):
        # energy bar, similar in style to the health
        energy_bar = pg.Surface((2*GAUGE_UI['radius'], 2*GAUGE_UI['radius']))
        energy_bar.set_colorkey('black')
        total_energy_calculation = entities.entity_calculation(self.player, 'energy')
        energy_ratio = 1-entities.energy[self.player]/total_energy_calculation
        energy_frame = self.hud_frames['energy_frame']
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
        left_edge_pad = WIDTH-right_pad-frame.get_width()-ATS_UI['right_pad']
        icon_edge_pad = left_edge_pad+ATS_UI['frame_pad']
        for i in range(len(abilities)):
            icon = self.ability_icons[abilities[i]]
            screen.blit(icon, (icon_edge_pad+i*(ATS_UI['icon_size']+ATS_UI['frame_width']),
                                HEIGHT-frame.get_height()//2+ATS_UI['frame_width']//2))

    def trait_slots(self, screen, entities):
        traits = entities.traits[self.player].traits
        new_trait = entities.traits[self.player].new_trait
        frame = self.hud_frames['ability_and_trait_frame']
        right_pad = self.hud_frames['energy_frame'].get_width()
        left_edge_pad = WIDTH-right_pad-frame.get_width()-ATS_UI['right_pad']
        icon_edge_pad = left_edge_pad+ATS_UI['frame_pad']
        for i in range(len(traits)):
            icon = self.trait_icons[traits[i]]
            screen.blit(icon, (icon_edge_pad+i*(ATS_UI['icon_size']+ATS_UI['frame_width']),
                                HEIGHT-frame.get_height()+ATS_UI['frame_pad']))
        
        # display new traits
        if new_trait:
            icon = self.trait_icons[new_trait['reward']].copy()
            icon.fill((255, 0, 0, 100), special_flags=pg.BLEND_RGBA_ADD)
            screen.blit(icon, (icon_edge_pad+len(traits)*ATS_UI['icon_size'],
                                HEIGHT-frame.get_height()+ATS_UI['frame_pad']))

    def display_traits_and_abilities(self, screen, entities):
        frame = self.hud_frames['ability_and_trait_frame']
        right_pad = self.hud_frames['energy_frame'].get_width()
        left_edge_pad = WIDTH-right_pad-frame.get_width()-ATS_UI['right_pad']
        screen.blit(frame, (left_edge_pad, 
                    HEIGHT-frame.get_height()))
        self.ability_slots(screen, entities)
        self.trait_slots(screen, entities)

    def ability_indicator(self, screen, entities, controller, camera):
        ability_num = controller.queued_ability
        ability_key = entities.abilities[self.player][ability_num]
        x, y = camera.transform_to_screen(entities.pos[self.player][0:3])

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
            radius = entities.entity_calculation(self.player, 'intimidation')
            pg.draw.circle(screen, 'cyan', (x, y), radius, 5) 
    
    def display_statuses(self, screen, entities):
        frame = self.hud_frames['ability_and_trait_frame']
        status_effects = entities.status_effects[self.player]
        right_pad = WIDTH-self.hud_frames['energy_frame'].get_width()-2*ATS_UI['right_pad']
        bottom_pad = HEIGHT-frame.get_height()-ATS_UI['reg_pad']-ATS_UI['icon_size']//2
        for i in range(len(status_effects['effects'])):
            icon = self.status_icons[status_effects['effects'][i]]
            screen.blit(icon, (-(i+1)*(icon.get_width()+ATS_UI['reg_pad'])+right_pad, bottom_pad))

    def arrow_to_corpse(self, screen, entities, player, corpses, camera):
        for i in range(len(corpses.pos)):
            dx = corpses.pos[i][0]-entities.pos[player][0]
            dy = corpses.pos[i][1]-entities.pos[player][1]
            angle = atan2(dy, dx)
            x, y = camera.dir_transform([cos(angle), sin(angle), 0])
            x, y = camera.screen_to_world(x, y)
            pg.draw.line(screen, (255, 0, 0), (WIDTH/2, HEIGHT/2), (WIDTH/2+50*x, HEIGHT/2+50*y))

    ############################# 
    # questing menus            #
    ############################# 
    def toggle_quests_menu(self):
        self.quest_ui = {
            'display': not self.quest_ui['display'],
            'ui': self.quest_ui['ui']
        }
    
    def update_quests(self, world_event):
        self.quest_ui = {
            'display': self.quest_ui['display'],
            'ui': Quest_UI(world_event.quests)
        }

    def quest_anim(self, screen):
        circle = pg.Surface((100, 100))
        pg.draw.circle(circle, (255, 255, 0), (50, 50), 50)
        circle.set_colorkey((0, 0, 0))
        circle.set_alpha(100)
        screen.blit(circle, (WIDTH/2-50, HEIGHT/2-50))
    
############################# 
# questing menus class      #
############################# 
class Quest_UI:
    def __init__(self, quests):
        self.quests = quests
        self.hover = 0
    
    def display(self, screen, font):
        font.render(screen=screen, 
                    text='quests', 
                    x=WIDTH/2, y=HEIGHT/4, 
                    colour=(0, 255, 0), size=TITLE_FONT_SIZE, 
                    style='center')
        if not self.quests:
            return

        # make prev and next auto-balance, so they have the same number of cards?
        prev = self.quests[:self.hover]
        next = self.quests[self.hover+1:]
        next.reverse()
        gradient = max(len(next), len(prev))
        # draw the previous cards
        if gradient!=0:
            size_ratio = QUEST_CARD_UI['s_ratio']**(1/gradient)
            alpha_ratio = QUEST_CARD_UI['a_ratio']**(1/gradient)
            for i in range(len(prev)):
                # reverse the index
                rev_i = len(prev)-i
                # quest type and reward to be displayed
                q_type = prev[i]['type']
                reward = prev[i]['reward']
                # card width, height, padding, font size, alpha
                w = QUEST_CARD_UI['w']/(size_ratio**rev_i)
                h = QUEST_CARD_UI['h']/(size_ratio**rev_i)
                p = QUEST_CARD_UI['p']/(size_ratio**rev_i)
                f = QUEST_CARD_UI['f']/(size_ratio**rev_i)
                a = 255/(alpha_ratio**rev_i)

                # make the card
                card = pg.Surface((w, h))
                card.fill(QUEST_CARD_UI['c'][q_type])
                card.set_alpha(a)
                screen.blit(card, (WIDTH/2-(w+p)*rev_i-w/2, HEIGHT/2-h/2))
                font.render(screen=screen, text=f'{q_type} {reward}', 
                            x=WIDTH/2-(w+p)*rev_i, y=HEIGHT/2, 
                            colour=(255, 255, 255), size=f, 
                            style='center',
                            box_width=w)
        
            for i in range(len(next)):
                # reverse the index
                rev_i = len(next)-i
                # quest type and reward to be displayed
                q_type = next[i]['type']
                reward = next[i]['reward']
                # card width, height, padding, font size, alpha
                w = QUEST_CARD_UI['w']/(size_ratio**rev_i)
                h = QUEST_CARD_UI['h']/(size_ratio**rev_i)
                a = 255/(alpha_ratio**rev_i)
                p = QUEST_CARD_UI['p']/(size_ratio**rev_i)
                f = QUEST_CARD_UI['f']/(size_ratio**rev_i)

                # make the card
                card = pg.Surface((w, h))
                card.fill(QUEST_CARD_UI['c'][q_type])
                card.set_alpha(a)
                screen.blit(card, (WIDTH/2+(w+p)*rev_i-w/2, HEIGHT/2-h/2))
                font.render(screen=screen, text=f'{q_type} {reward}', 
                            x=WIDTH/2+(w+p)*rev_i, y=HEIGHT/2, 
                            colour=(255, 255, 255), size=f, 
                            style='center',
                            box_width=w)
        
        # draw the hovered card
        q_type = self.quests[self.hover]['type']
        reward = self.quests[self.hover]['reward']
        card = pg.Surface((QUEST_CARD_UI['w'], QUEST_CARD_UI['h']))
        card.fill(QUEST_CARD_UI['c'][q_type])
        screen.blit(card, (WIDTH/2-QUEST_CARD_UI['w']/2, HEIGHT/2-QUEST_CARD_UI['h']/2))
        font.render(screen=screen, text=f'{q_type} {reward}',
                    x=WIDTH/2, y=HEIGHT/2, 
                    colour=(255, 255, 255), size=QUEST_CARD_UI['f'], 
                    style='center', box_width=QUEST_CARD_UI['w'])
    
    def input(self, pg_events):
        for event in pg_events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RIGHT:
                    if self.quests:
                        self.hover+=1
                        self.hover%=len(self.quests)
                    else:
                        self.hover = 0
                if event.key == pg.K_LEFT:
                    if self.quests:
                        self.hover-=1
                        self.hover%=len(self.quests)
                    else:
                        self.hover = 0
                if event.key == pg.K_RETURN:
                    # take quest
                    return self.quests[self.hover]
        
        return None

############################# 
# interactions menus class  #
#############################

class Interaction_UI:
    def __init__(self, sprites):
        self.in_range = -1
        self.sprites = sprites
        self.sprites['capsule'] = pg.transform.scale(self.sprites['capsule'], (144, 48))
        self.sprites['capsule'].set_alpha(100)

    def display(self, screen, font):
        ping = pg.Surface((100, 100))
        ping.set_colorkey((0, 0, 0))
        ping.set_alpha(100)

        if self.in_range != -1:
            capsule = self.sprites['capsule']
            nutrients = self.sprites['nutrients']
            pad = nutrients.get_height()/2
            radius = (nutrients.get_height()/2 + capsule.get_height()/2)/2
            right_margin = 20
            x, y = WIDTH/2 + nutrients.get_width(), HEIGHT/2
            screen.blit(capsule, (x - capsule.get_height()/2 + right_margin, y - capsule.get_height()/2))
            pg.draw.circle(screen, (10, 10, 10), (x + right_margin, y), radius)
            screen.blit(nutrients, (x-pad + right_margin, y-pad))

        screen.blit(ping, (WIDTH/2-50, HEIGHT/2-50))

    def detection(self, pos, corpses):
        self.in_range = -1
        for i, corpse_pos in enumerate(corpses.pos):
            dr_sq = (corpse_pos[0]-pos[0])**2 + (corpse_pos[1]-pos[1])**2
            if dr_sq <= 50**2:
                self.in_range = i
    
    def input(self, pg_event):
        for event in pg_event:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_f:
                    if self.in_range!=-1:
                        return {
                            'type': 'consume',
                            'index': self.in_range,
                        }
                if event.key == pg.K_k:
                    if self.range!=-1:
                        return {
                            'type': 'scavenge',
                            'index': self.in_range,
                        }
        
        return {
            'type': None
        }