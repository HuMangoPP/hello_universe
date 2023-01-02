import pygame as pg

class Corpses:
    def __init__(self):
        self.pos = []
        self.nutrients = []
        self.creautre = []

    def add_new_corpse(self, corpse_data):
        self.pos.append(corpse_data['pos'])
        self.nutrients.append(corpse_data['nutrients'])
        self.creature.append(corpse_data['creature'])
    
    def render(self, screen):
        for pos in self.pos:
            x, y, z = self.pos[0], self.pos[1], self.pos[2]
            
