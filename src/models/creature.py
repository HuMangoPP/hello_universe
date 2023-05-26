# import pygame as pg
# import numpy as np
# from math import cos, sin, ceil, pi, log10
# from src.models.legs import Legs
# from src.util.physics import collide, dist_between, angles_between
# from src.util.settings import HEIGHT, MODEL_COLORS, OUT_OF_BOUNDS, WIDTH, MAX_SIZE, MIN_SIZE

# class Creature:
#     def __init__(self, creature_data: dict):
#         self.num_parts:int = creature_data['num_parts']
#         self.head:np.ndarray = creature_data['pos']
#         self.z_pos:float = self.head[2]
#         self.skeleton:np.ndarray = np.array([])
#         self.size:int = creature_data['size']
#         self.max_parts:int = creature_data['max_parts']
#         self.legs = Legs(num_pair_legs=creature_data['num_pair_legs'], 
#                         leg_length=creature_data['leg_length'], )
#         self.build_skeleton(self.head)
#         self.give_legs()
    
#     def build_skeleton(self, pos, a=0, upright=False):
#         offsets = [np.array(x,0,0) 
#                    for x in np.arange(2*self.size, 2*self.size*(self.num_parts+1), 2*self.size)]
#         self.skeleton = np.full((self.num_parts,), pos) - offsets
        
#         if upright:
#             self.upright()
    
#     def upright(self):
#         torso_segment = self.legs.get_torso_start()
#         for i in range(torso_segment, self.num_parts, 1):
#             self.skeleton[i][2] = self.z_pos
#         for i in range(torso_segment, -1, -1):
#             self.skeleton[i][2]=self.z_pos+self.size*2*(torso_segment-i)
#         self.head[2]=self.z_pos+self.size*2*(torso_segment+1)

#     def give_legs(self):
#         if self.legs.num_pair_legs == 0:
#             return
#         if self.legs.num_pair_legs>self.num_parts:
#             return
        
#         ratio_body_to_legs = ceil(self.num_parts/(self.legs.num_pair_legs+1))
            
#         self.legs.attached_segments = []
#         for i, segment in enumerate(self.skeleton): 
#             if i%ratio_body_to_legs==0:
#                 self.legs.attached_segments.append(i)
#                 self.legs.leg_types.append({
#                     'type': 'leg',
#                     'level': 1,
#                 })
#                 self.legs.build_legs(segment)
#                 if self.legs.num_legs()==self.legs.num_pair_legs:
#                     break
        
#         self.upright()

#     # later
#     def give_wings(self):
#         self.legs.transform_leg(self.legs.free_leg(), 'wing', 1)

#     def give_arms(self):
#         self.legs.transform_leg(self.legs.free_leg(), 'arm', 1)

#     def update_legs(self):
#         if self.legs.num_pair_legs == 0:
#             return
#         if self.legs.num_pair_legs>self.num_parts:
#             return
        
#         ratio_body_to_legs = self.num_parts/self.legs.num_pair_legs

#         # first add new legs
#         for i in range(self.legs.num_pair_legs-len(self.legs.attached_segments)):
#             self.legs.attached_segments.insert(0, 0)
#             self.legs.leg_types.insert(0, {
#                     'type': 'leg',
#                     'level': 1,
#                 })

#         # then update how they are connected
#         for i in range(self.legs.num_pair_legs):
#             self.legs.attached_segments[i] = int(i*ratio_body_to_legs)
#             self.legs.build_legs(self.skeleton[self.legs.attached_segments[i]])

#         self.upright()

#     def change_body(self, change_in_size):
#         self.size+=change_in_size
#         if self.size<MIN_SIZE:
#             self.size = MIN_SIZE
#         if self.size > MAX_SIZE:
#             self.size = MIN_SIZE
#             self.num_parts+=1
#             new_pos = [self.head[0], self.head[1], self.z_pos]
#             if self.num_parts > self.max_parts:
#                 self.num_parts = self.legs.num_pair_legs
#                 self.build_skeleton(new_pos, upright=True)
#                 self.update_legs() # TODO: change to a different one 
#                 return round(log10(self.max_parts*MAX_SIZE))
            
#             self.build_skeleton(new_pos, upright=True)
#         return 0

#     def increase_body_potential(self):
#         self.max_parts+=1

#     def change_legs(self, type):
#         if type == 'new':
#             self.legs.num_pair_legs += 1
#             self.update_legs()
#             return
        
#         existing_leg_index = -1
#         for i in range(len(self.legs.leg_types)-1, -1, -1):
#             if self.legs.leg_types[i]['type'] == 'leg' and self.legs.leg_types[i]['level'] < 3:
#                 existing_leg_index = i
#                 break
        
#         if existing_leg_index != -1:
#             self.legs.leg_types[existing_leg_index]['level'] += 1

#         self.upright()

#     def render(self, screen, camera):

#         # if is_moving:
#         #     t = pg.time.get_ticks()
#         #     self.wiggle(t)

#         x, y = camera.transform_to_screen(self.head[0:3])
#         if x>WIDTH+OUT_OF_BOUNDS or x<-OUT_OF_BOUNDS or y>HEIGHT+OUT_OF_BOUNDS or y<-OUT_OF_BOUNDS:
#             return False 
#         pg.draw.circle(screen, MODEL_COLORS['head'], (x, y), self.size)
#         for i in range(self.num_parts):
#             x, y = camera.transform_to_screen(self.skeleton[i][0:3])
#             pg.draw.circle(screen, MODEL_COLORS['skeleton'], (x, y), self.size)
#             pg.draw.circle(screen, MODEL_COLORS['hurt_box'], (x, y), self.size, 1)

#         # if is_moving:
#         #     self.dewiggle(t)

#         self.legs.draw(screen, self.skeleton, camera)
#         return True

#     def move(self, pos, effects, is_moving):
#         self.head = pos
#         if self.skeleton:
#             dist = dist_between(self.skeleton[0], self.head)
#             angle = angles_between(self.skeleton[0], self.head)['z']
#             self.skeleton[0][0]+=(dist-2*self.size)*cos(angle)
#             self.skeleton[0][1]+=(dist-2*self.size)*sin(angle)
#             self.skeleton[0][3] = angle

#             for i in range(1, len(self.skeleton)):
#                 dist = dist_between(self.skeleton[i], self.skeleton[i-1])
#                 angle = angles_between(self.skeleton[i], self.skeleton[i-1])['z']
#                 self.skeleton[i][0]+=(dist-2*self.size)*cos(angle)
#                 self.skeleton[i][1]+=(dist-2*self.size)*sin(angle)
#                 self.skeleton[i][3] = angle

#             self.legs.move_feet(self.skeleton, effects)

#         if is_moving:
#             self.wiggle(pg.time.get_ticks())

#     def wiggle(self, t):
#         wiggle_mag = 0.25
#         if self.skeleton:
#             start = self.legs.get_torso_start()
#             period = (len(self.skeleton) - start)
#             for i in range(start, len(self.skeleton)):
#                 perp_offset = wiggle_mag*sin(pi/period*i)*cos(t/100)
#                 self.skeleton[i][0]+=perp_offset*cos(self.skeleton[i][3]+pi/2)
#                 self.skeleton[i][1]+=perp_offset*sin(self.skeleton[i][3]+pi/2)

#     def collide(self, hurt_boxes):

#         hit_box = [self.head[0], self.head[1], self.head[2], self.size]
#         for hurt_box in hurt_boxes:
#             if collide(hit_box, hurt_box):
#                 return True

#         for i in range(len(self.skeleton)):
#             segment = self.skeleton[i]
#             hit_box = [segment[0], segment[1], segment[2], self.size]
#             for hurt_box in hurt_boxes:
#                 if collide(hit_box, hurt_box):
#                     return True

import pygame as pg
import numpy as np
import math

from ..util.settings import MODEL_COLORS
from .legs import Legs

class Creature:
    def __init__(self, creature_data: dict):
        self.num_parts:int = creature_data['num_parts']
        self.head:np.ndarray = creature_data['pos']
        self.z_pos:float = self.head[2]
        self.skeleton:np.ndarray = np.array([])
        self.flat_angles:np.ndarray = np.array([])
        self.size:int = creature_data['size']
        self.max_parts:int = creature_data['max_parts']
        self.legs = Legs(creature_data['num_pair_legs'], 
                         creature_data['leg_length'], )
        self.build_skeleton()
        self.give_legs()
    
    def build_skeleton(self):
        offsets = np.array([[x,0,0] for x in np.arange(2*self.size, 2*self.size*(self.num_parts+1), 2*self.size)])
        self.skeleton = np.full((self.num_parts,3), self.head) - offsets
        self.flat_angles = np.zeros((self.num_parts,),np.float32)

    def give_legs(self):
        if self.legs.num_pair_legs == 0:
            return
        if self.legs.num_pair_legs>self.num_parts:
            return
        
        ratio_body_to_legs = math.ceil(self.num_parts/(self.legs.num_pair_legs+1))
            
        self.legs.skeleton_segments_with_legs = ratio_body_to_legs * np.arange(self.legs.num_pair_legs)
        self.legs.build_legs(self.skeleton, self.flat_angles)
        # self.upright()
    
    def upright(self):
        ...

    def update(self, new_head: np.ndarray):
        self.head = new_head

        if self.skeleton.size > 0:
            first_segment = self.skeleton[0]
            disp = self.head - first_segment
            flat_angle = math.atan2(disp[1], disp[0])
            disp = disp - 2*self.size * np.array([math.cos(flat_angle),math.sin(flat_angle),0])
            self.skeleton[0] = self.skeleton[0] + disp
            self.flat_angles[0] = flat_angle

            for i, _ in enumerate(self.skeleton):
                if i < 1: continue
                disp = self.skeleton[i-1] - self.skeleton[i]
                flat_angle = math.atan2(disp[1], disp[0])
                disp = disp - 2*self.size * np.array([math.cos(flat_angle), math.sin(flat_angle), 0])
                self.skeleton[i] = self.skeleton[i] + disp
                self.flat_angles[i] = flat_angle
        
        self.legs.update(self.skeleton, self.flat_angles)


    def render(self, display: pg.Surface, camera):
        x, y = camera.transform_to_screen(self.head)
        pg.draw.circle(display, MODEL_COLORS['head'], (x,y), self.size)
        for segment in self.skeleton:
            x, y = camera.transform_to_screen(segment)
            pg.draw.circle(display, MODEL_COLORS['body'], (x,y), self.size)
        self.legs.render(self.skeleton, self.flat_angles, display, camera)