import pygame as pg

class Corpses:
    def __init__(self):
        self.pos = []
        self.nutrients = []
        self.creature = []

    def add_new_corpse(self, corpse_data):
        self.pos.append(corpse_data['pos'])
        self.nutrients.append(corpse_data['nutrients'])
        self.creature.append(corpse_data['creature'])
    
    def render(self, screen, camera):
        for pos in self.pos:
            x, y, z = pos[0], pos[1], pos[2]
            pg.draw.circle(screen, (255, 0, 0), camera.transform_to_screen([x, y, z]), 10)
    
    def update(self):
        self.remove()

    def remove(self):
        to_remove = []
        for i in range(len(self.nutrients)):
            if self.nutrients[i]==0:
                to_remove.append(i)
        
        to_remove.reverse()
        
        for rmv in to_remove:
            self.pos[rmv:rmv+1] = []
            self.nutrients[rmv:rmv+1] = []
            self.creature[rmv:rmv+1] = []