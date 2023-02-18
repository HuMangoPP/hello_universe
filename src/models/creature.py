import pygame as pg
from math import cos, sin, ceil, pi, log10
from src.models.legs import Legs
from src.util.physics import collide, dist_between, angles_between
from src.util.settings import HEIGHT, MODEL_COLORS, OUT_OF_BOUNDS, WIDTH, MAX_SIZE, MIN_SIZE

class Creature:
    def __init__(self, num_parts, pos, size, max_parts, num_pair_legs, leg_length):
        self.num_parts = num_parts
        self.head = pos
        self.z_pos = pos[2]
        self.skeleton = []
        self.size = size
        self.max_parts = max_parts
        self.legs = Legs(num_pair_legs=num_pair_legs, 
                        leg_length=leg_length, 
                        arm_attachments=[], 
                        wing_attachments=[])
        self.build_skeleton(pos)
        self.give_legs()
    
    def build_skeleton(self, pos, a=0, upright=False):
        self.skeleton = []
        for i in range(self.num_parts):
            self.skeleton.append([pos[0]-(i+1)*2*self.size, pos[1], pos[2], a])
        
        if upright:
            self.upright()
    
    def give_wings(self):
        self.legs.transform_leg(self.legs.free_leg(), 'wing', 1)

    def give_arms(self):
        self.legs.transform_leg(self.legs.free_leg(), 'arm', 1)

    def give_legs(self):
        if self.legs.num_pair_legs == 0:
            return
        if self.legs.num_pair_legs>self.num_parts:
            return
        
        ratio_body_to_legs = ceil(self.num_parts/(self.legs.num_pair_legs+1))

        if self.legs.num_pair_legs==self.num_parts:
            ratio_body_to_legs = 1
            
        self.legs.attached_segments = []
        for i in range(len(self.skeleton)):
            if i%ratio_body_to_legs==0:
                self.legs.attached_segments.append(i)
                self.legs.leg_types.append({
                    'type': 'leg',
                    'level': 1,
                })
                self.legs.build_legs(self.skeleton[i])
                if self.legs.num_legs()==self.legs.num_pair_legs:
                    break
        
        self.upright()

    def update_legs(self):
        if self.legs.num_pair_legs == 0:
            return
        if self.legs.num_pair_legs>self.num_parts:
            return
        
        ratio_body_to_legs = ceil(self.num_parts/(self.legs.num_pair_legs+1))

        # first add new legs
        for i in range(self.legs.num_pair_legs-len(self.legs.attached_segments)):
            self.legs.attached_segments.append(0)
            self.legs.leg_types.append({
                    'type': 'leg',
                    'level': 1,
                })

        # then update how they are connected
        for i in range(self.legs.num_pair_legs):
            self.legs.attached_segments[i] = i*ratio_body_to_legs
            self.legs.build_legs(self.skeleton[self.legs.attached_segments[i]])

    def change_body(self, change_in_size):
        self.size+=change_in_size
        if self.size<MIN_SIZE:
            self.size = MIN_SIZE
        if self.size > MAX_SIZE:
            print('new body part!')
            self.size = MIN_SIZE
            self.num_parts+=1
            new_pos = [self.head[0], self.head[1], self.z_pos]
            if self.num_parts > self.max_parts:
                self.num_parts = self.legs.num_pair_legs
                self.build_skeleton(new_pos, upright=True)
                self.update_legs() # TODO: change to a different one 
                return round(log10(self.max_parts*MAX_SIZE))
            
            self.build_skeleton(new_pos, upright=True)
        return 0

    def change_legs(self):
        self.legs.num_pair_legs+=1
        self.update_legs()

    def render(self, screen, camera):

        # if is_moving:
        #     t = pg.time.get_ticks()
        #     self.wiggle(t)

        x, y = camera.transform_to_screen(self.head[0:3])
        if x>WIDTH+OUT_OF_BOUNDS or x<-OUT_OF_BOUNDS or y>HEIGHT+OUT_OF_BOUNDS or y<-OUT_OF_BOUNDS:
            return False 
        pg.draw.circle(screen, MODEL_COLORS['head'], (x, y), self.size)
        for i in range(self.num_parts):
            x, y = camera.transform_to_screen(self.skeleton[i][0:3])
            pg.draw.circle(screen, MODEL_COLORS['skeleton'], (x, y), self.size)
            pg.draw.circle(screen, MODEL_COLORS['hurt_box'], (x, y), self.size, 1)

        # if is_moving:
        #     self.dewiggle(t)

        self.legs.draw(screen, self.skeleton, camera)
        return True

    def move(self, pos, effects, is_moving):
        self.head = pos
        if self.skeleton:
            dist = dist_between(self.skeleton[0], self.head)
            angle = angles_between(self.skeleton[0], self.head)['z']
            self.skeleton[0][0]+=(dist-2*self.size)*cos(angle)
            self.skeleton[0][1]+=(dist-2*self.size)*sin(angle)
            self.skeleton[0][3] = angle

            for i in range(1, len(self.skeleton)):
                dist = dist_between(self.skeleton[i], self.skeleton[i-1])
                angle = angles_between(self.skeleton[i], self.skeleton[i-1])['z']
                self.skeleton[i][0]+=(dist-2*self.size)*cos(angle)
                self.skeleton[i][1]+=(dist-2*self.size)*sin(angle)
                self.skeleton[i][3] = angle

            self.legs.move_feet(self.skeleton, effects)

        if is_moving:
            self.wiggle(pg.time.get_ticks())

    def wiggle(self, t):
        wiggle_mag = 0.25
        if self.skeleton:
            start = self.legs.get_torso_start()
            period = (len(self.skeleton) - start)
            for i in range(start, len(self.skeleton)):
                perp_offset = wiggle_mag*sin(pi/period*i)*cos(t/100)
                self.skeleton[i][0]+=perp_offset*cos(self.skeleton[i][3]+pi/2)
                self.skeleton[i][1]+=perp_offset*sin(self.skeleton[i][3]+pi/2)

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
