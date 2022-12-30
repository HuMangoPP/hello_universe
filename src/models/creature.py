import pygame as pg
from math import atan2, sqrt, cos, sin, floor, tan, pi
from src.models.legs import Legs
from src.physics.physics import collide
from src.settings import HEIGHT, MODEL_COLORS, OUT_OF_BOUNDS, WIDTH

class Creature:
    def __init__(self, num_parts, pos, size, num_pair_legs, leg_length):
        self.num_parts = num_parts
        self.head = pos
        self.z_pos = pos[2]
        self.skeleton = []
        self.size = size
        self.build_skeleton(pos)
        self.legs = Legs(num_pair_legs, leg_length, [], [])
        self.give_legs()
    
    def build_skeleton(self, pos, a=0):
        self.skeleton = []
        for i in range(self.num_parts):
            self.skeleton.append([pos[0]-(i+1)*2*self.size, pos[1], pos[2], a])
    
    def give_wings(self):
        self.legs.transform_wings()

    def give_arms(self):
        self.legs.transform_arms()

    def give_legs(self):
        if self.legs.num_pair_legs == 0:
            return
        if self.legs.num_pair_legs>self.num_parts:
            return
        
        ratio_body_to_legs = floor(self.num_parts/(self.legs.num_pair_legs+1))

        if self.legs.num_pair_legs==self.num_parts:
            ratio_body_to_legs = 1
        self.legs.attached_segments = []
        if ratio_body_to_legs>=1:
            for i in range(len(self.skeleton)):
                if i%ratio_body_to_legs==0 and i!=0:
                    self.legs.attached_segments.append(i)
                    self.legs.build_legs(self.skeleton[i])
                    if self.legs.num_legs()==self.legs.num_pair_legs:
                        break
        else:
            for i in range(len(self.skeleton)):
                if i%ratio_body_to_legs==0:
                    self.legs.attached_segments.append(i)
                    self.legs.build_legs(self.skeleton[i])
                    if self.legs.num_legs()==self.legs.num_pair_legs:
                        break
        self.upright()
        
    def change_physiology(self, parts, legs):
        self.num_parts+=parts
        new_pos = [self.head[0], self.head[1], self.z_pos]
        self.build_skeleton(new_pos)

        self.legs.num_pair_legs+=legs
        self.give_legs()

    def draw(self, screen, camera):
        x, y = camera.transform_to_screen(self.head[0], self.head[1], self.head[2])
        if x>WIDTH+OUT_OF_BOUNDS or x<-OUT_OF_BOUNDS or y>HEIGHT+OUT_OF_BOUNDS or y<-OUT_OF_BOUNDS:
            return False 
        pg.draw.circle(screen, MODEL_COLORS['head'], (x, y), self.size)
        for i in range(self.num_parts):
            x, y = camera.transform_to_screen(self.skeleton[i][0], self.skeleton[i][1], self.skeleton[i][2])
            pg.draw.circle(screen, MODEL_COLORS['skeleton'], (x, y), self.size)
            pg.draw.circle(screen, MODEL_COLORS['hurt_box'], (x, y), self.size, 1)
        self.legs.draw(screen, self.skeleton, camera)
        return True

    def move(self, pos):
        self.head = pos
        if self.skeleton:
            dist = self.dist_between_segment(self.skeleton[0], self.head)
            angle = self.angle_between_segment(self.skeleton[0], self.head)
            self.skeleton[0][0]+=(dist-2*self.size)*cos(angle)
            self.skeleton[0][1]+=(dist-2*self.size)*sin(angle)
            self.skeleton[0][3] = angle

            for i in range(1, len(self.skeleton)):
                dist = self.dist_between_segment(self.skeleton[i], self.skeleton[i-1])
                angle = self.angle_between_segment(self.skeleton[i], self.skeleton[i-1])
                self.skeleton[i][0]+=(dist-2*self.size)*cos(angle)
                self.skeleton[i][1]+=(dist-2*self.size)*sin(angle)
                self.skeleton[i][3] = angle
            
            self.legs.move_feet(self.skeleton)
    
    def upright(self):
        torso_segment = self.legs.get_torso_start()
        for i in range(torso_segment, -1, -1):
            self.skeleton[i][2]=self.z_pos+self.size*2*(torso_segment-i)
        self.head[2]=self.z_pos+self.size*2*(torso_segment+1)

    def collide(self, hurt_boxes):

        hit_box = [self.head[0], self.head[1], self.head[2], self.size]
        for hurt_box in hurt_boxes:
            if collide(hit_box, hurt_box):
                return True

        for i in range(len(self.skeleton)):
            segment = self.skeleton[i]
            hit_box = [segment[0], segment[1], segment[2], self.size]
            for hurt_box in hurt_boxes:
                if collide(hit_box, hurt_box):
                    return True

    def dist_between_segment(self, seg1, seg2):
        return sqrt((seg1[0]-seg2[0])**2 +
                    (seg1[1]-seg2[1])**2 +
                    (seg1[2]-seg2[2])**2)
    
    def angle_between_segment(self, seg1, seg2):
        return atan2(seg2[1]-seg1[1], seg2[0]-seg1[0])