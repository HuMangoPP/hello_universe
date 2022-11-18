import pygame as pg
from math import atan2, sqrt, cos, sin, floor, tan, pi
from src.models.legs import Legs

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
        self.upright()
    
    def build_skeleton(self, pos, a=0):
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
        if ratio_body_to_legs>=1:
            for i in range(len(self.skeleton)):
                if i%ratio_body_to_legs==0 and i!=0:
                    self.legs.attached_segments.append(i)
                    self.legs.build_legs(self.skeleton[i])
                    if self.legs.num_legs()==self.legs.num_pair_legs:
                        return
        else:
            for i in range(len(self.skeleton)):
                if i%ratio_body_to_legs==0:
                    self.legs.attached_segments.append(i)
                    self.legs.build_legs(self.skeleton[i])
                    if self.legs.num_legs()==self.legs.num_pair_legs:
                        return

    def draw(self, screen, camera):
        x, y = camera.transform_to_screen(self.head[0], self.head[1], self.head[2])
        pg.draw.circle(screen, 'red', (x, y), self.size)
        for i in range(self.num_parts):
            x, y = camera.transform_to_screen(self.skeleton[i][0], self.skeleton[i][1], self.skeleton[i][2])
            pg.draw.circle(screen, 'white', (x, y), self.size)
        self.legs.draw(screen, self.skeleton, camera)

    def move(self, pos):
        self.head = pos
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

    def collide(self, hurt_box):

        hit_box = pg.Rect(self.head[0]-self.size, self.head[1]-self.size, self.size*2, self.size*2)
        
        for rect in hurt_box.rects:
            if hit_box.colliderect(rect):
                return True

        for i in range(len(self.skeleton)):
            hit_box = pg.Rect(self.skeleton[i][0]-self.size, self.skeleton[i][1]-self.size, self.size*2, self.size*2)
            for rect in hurt_box.rects:
                if hit_box.colliderect(rect):
                    return True

    def dist_between_segment(self, seg1, seg2):
        return sqrt((seg1[0]-seg2[0])**2 +
                    (seg1[1]-seg2[1])**2 +
                    (seg1[2]-seg2[2])**2)
    
    def angle_between_segment(self, seg1, seg2):
        return atan2(seg2[1]-seg1[1], seg2[0]-seg1[0])