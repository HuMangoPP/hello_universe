# import pygame as pg

# class Corpses:
#     def __init__(self):
#         self.pos = []
#         self.nutrients = []
#         self.materials = []
#         self.creature = []
#         self.type = []

#     def add_new_corpse(self, corpse_data):
#         self.pos.append(corpse_data['pos'])
#         self.nutrients.append(corpse_data['nutrients'])
#         self.materials.append(corpse_data['materials'])
#         self.creature.append(corpse_data['creature'])
#         self.digestion.append(corpse_data['digestion'])
    
#     def render(self, screen, camera):
#         for pos in self.pos:
#             pg.draw.circle(screen, (255, 0, 0), camera.transform_to_screen(pos[0:3]), 10)
    
#     def update(self):
#         self.remove()

#     def remove(self):
#         to_remove = []
#         for i in range(len(self.nutrients)):
#             if self.nutrients[i]==0:
#                 to_remove.append(i)
        
#         to_remove.reverse()
        
#         for rmv in to_remove:
#             self.pos[rmv:rmv+1] = []
#             self.nutrients[rmv:rmv+1] = []
#             self.creature[rmv:rmv+1] = []