from math import atan2, sqrt
import pygame as pg

from src.settings import HEIGHT, WIDTH

class PlayerController():
    def __init__(self, index):
        self.index = index
        self.queued_ability = -1
    
    def movement_input(self):

        keys = pg.key.get_pressed()
        horizontal_input = 0
        vertical_input = 0

        if keys[pg.K_w]:
            vertical_input-=1

        if keys[pg.K_s]:
            vertical_input+=1

        if keys[pg.K_a]:
            horizontal_input-=1

        if keys[pg.K_d]:
            horizontal_input+=1
        

        return horizontal_input, vertical_input
    
    def ability_input(self, entity):
        keys = pg.key.get_pressed()
        for i in range(pg.K_1, pg.K_1+len(entity.abilities[self.index])):
            if keys[i]:
                self.queued_ability = i-pg.K_1
        
        if pg.mouse.get_pressed()[0] and self.queued_ability!=-1:
            angle = atan2(pg.mouse.get_pos()[1]-HEIGHT//2, pg.mouse.get_pos()[0]-WIDTH//2)
            ability = {
                'ability': entity.abilities[self.index][self.queued_ability],
                'angle': angle,
            }
            self.queued_ability = -1
            return ability
        
        if pg.mouse.get_pressed()[2] and self.queued_ability!=-1:
            self.queued_ability = -1
        
        return {'ability': -1}