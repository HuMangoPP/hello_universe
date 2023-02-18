import pygame as pg
from math import sqrt, pi, sin, cos, exp
from src.util.settings import MODEL_COLORS
import numpy as np

class Legs:
    ############################# 
    # init and spawn            #
    ############################# 
    def __init__(self, num_pair_legs, leg_length, 
                       arm_attachments, wing_attachments,
                       size=5, step_bend = pi/6,):
        # entity data
        self.num_pair_legs = num_pair_legs
        self.leg_length = leg_length
        self.attached_segments = []
        self.leg_types = []

        # rendering and physics
        self.feet_pos = []
        self.step_pos = []
        self.step_bend = step_bend
        self.feet_size = size
    
    def build_legs(self, body_seg_pos):
        self.feet_pos.append([body_seg_pos[0], 
                                body_seg_pos[1]+self.leg_length/2, 
                                0])
        self.step_pos.append([body_seg_pos[0]+self.leg_length*cos(self.step_bend), 
                                body_seg_pos[1]+self.leg_length*sin(self.step_bend), 
                                0])
        self.feet_pos.append([body_seg_pos[0], 
                                body_seg_pos[1]+self.leg_length/-2, 
                                0])
        self.step_pos.append([body_seg_pos[0]+self.leg_length*cos(-self.step_bend), 
                                body_seg_pos[1]+self.leg_length*sin(-self.step_bend), 
                                0])



    ############################# 
    # draw                      #
    ############################# 
    def draw(self, screen, skeleton, camera):
        for i in range(self.num_pair_legs):
            screen_pos = []
            # foot pos
            screen_pos.append(camera.transform_to_screen(self.feet_pos[2*i][0:3]))
            # joint pos
            joint_x, joint_y, joint_z = self.calculate_leg_joint_pos(self.feet_pos[2*i], skeleton[self.attached_segments[i]], -1)
            screen_pos.append(camera.transform_to_screen([joint_x, joint_y, joint_z]))
            # body pos
            screen_pos.append(camera.transform_to_screen(skeleton[self.attached_segments[i]][0:3]))
            # draw the feet
            pg.draw.circle(screen, MODEL_COLORS['foot'], screen_pos[0], self.feet_size)
            pg.draw.line(screen, MODEL_COLORS['leg'], screen_pos[0],
                                          screen_pos[1])
            pg.draw.line(screen, MODEL_COLORS['leg'], screen_pos[1],
                                          screen_pos[2])

            # other leg of pair
            screen_pos = []
            # foot pos
            screen_pos.append(camera.transform_to_screen(self.feet_pos[2*i+1][0:3]))
            # joint pos
            joint_x, joint_y, joint_z = self.calculate_leg_joint_pos(self.feet_pos[2*i+1], skeleton[self.attached_segments[i]], 1)
            screen_pos.append(camera.transform_to_screen([joint_x, joint_y, joint_z]))
            # body pos
            screen_pos.append(camera.transform_to_screen(skeleton[self.attached_segments[i]][0:3]))
            pg.draw.circle(screen, MODEL_COLORS['foot'], screen_pos[0], self.feet_size)
            pg.draw.line(screen, MODEL_COLORS['leg'], screen_pos[0],
                                          screen_pos[1])
            pg.draw.line(screen, MODEL_COLORS['leg'], screen_pos[1],
                                          screen_pos[2])
    
    ############################# 
    # movement                  #
    ############################# 
    def move_wings(self, skeleton, i):
        index = self.attached_segments[i]
        x, y, z = skeleton[index][0], skeleton[index][1], skeleton[index][2]
        angle = skeleton[index][3]
        self.step_pos[2*i] = [x+self.leg_length/2*cos(5/6*pi+angle),
                              y+self.leg_length/2*sin(5/6*pi+angle),
                              z]
        self.step_pos[2*i+1] = [x+self.leg_length/2*cos(-5/6*pi+angle),
                                y+self.leg_length/2*sin(-5/6*pi+angle),
                                z]
        self.feet_pos[2*i] = self.step_pos[2*i]
        self.feet_pos[2*i+1] = self.step_pos[2*i+1]

    def move_arms(self, skeleton, i):
        # first, calculate where it should be
        index = self.attached_segments[i]
        x, y, z = skeleton[index][0], skeleton[index][1], skeleton[index][2]
        angle = skeleton[index][3]
        self.step_pos[2*i] = [x+self.leg_length/4*cos(pi/6+angle),
                              y+self.leg_length/4*sin(pi/6+angle),
                              z-self.leg_length/4]
        self.step_pos[2*i+1] = [x+self.leg_length/4*cos(-pi/6+angle),
                                y+self.leg_length/4*sin(-pi/6+angle),
                                z-self.leg_length/6]

        # then move it there depending on other factors
        self.feet_pos[2*i] = self.step_pos[2*i]
        self.feet_pos[2*i+1] = self.step_pos[2*i+1]

    def move_feet(self, skeleton, effects):
        # update the step pos: where the feet should be 
        # it took a step
        abilities = effects['effects']

        for i in range(self.num_pair_legs):
            index = self.attached_segments[i]
            x, y, z = skeleton[index][0], skeleton[index][1], 0          
            angle = skeleton[index][3]
            
            leg_length_left = sqrt(self.leg_length**2-skeleton[index][2]**2)
            self.step_pos[2*i] = [x+leg_length_left*cos(self.step_bend+angle), 
                                y+leg_length_left*sin(self.step_bend+angle), 
                                z]
            self.step_pos[2*i+1] = [x+leg_length_left*cos(-self.step_bend+angle), 
                                    y+leg_length_left*sin(-self.step_bend+angle), 
                                    z]
        
        # update the renderable feet pos as neceessary
        for i in range(self.num_pair_legs):
            if self.leg_types[i]['type'] == 'arm':
                self.move_arms(skeleton, i)
            elif self.leg_types[i]['type'] == 'wing': 
                self.move_wings(skeleton, i)
            elif 'in_air' in abilities or 'underwater' in abilities:
                self.feet_pos[2*i] = skeleton[self.attached_segments[i]][:3]
                self.feet_pos[2*i+1] = skeleton[self.attached_segments[i]][:3]
            else:
                if self.dist_foot_to_body(self.feet_pos[2*i], skeleton[self.attached_segments[i]]) >= self.leg_length:
                    # if the distance from the foot to the body segment
                    # is greater than the length of the leg, take a step
                    self.feet_pos[2*i] = self.step_pos[2*i]
                if self.dist_foot_to_body(self.feet_pos[2*i+1], skeleton[self.attached_segments[i]]) >= self.leg_length:
                    # same for the other foot
                    self.feet_pos[2*i+1] = self.step_pos[2*i+1]

        for i in range(len(abilities)):
            self.ability_animate(skeleton, abilities[i], effects['time'][i])

    def ability_animate(self, skeleton, ability, time):
        if ability == 'strike':
            # use the time to model the trajectory of the swing
            leg_length = self.leg_length*3/4
            index = self.attached_segments[0]
            x, y, z = skeleton[index][0], skeleton[index][1], skeleton[index][2]
            angle = skeleton[index][3]
            elev_angle = pi/6

            t = 3 / (1 + exp(-(pg.time.get_ticks()-time-100)/10))

            para = leg_length/2*(1-cos(t))
            perp = sqrt(leg_length**2-para**2)*sin(t)
            pos_0 = [x+para*cos(angle)+perp*cos(pi/2+angle)*cos(elev_angle),
                     y+para*sin(angle)+perp*sin(pi/2+angle)*cos(elev_angle),
                     z+perp*sin(elev_angle)]
            pos_1 = [x+para*cos(angle)+perp*cos(-pi/2+angle)*cos(elev_angle),
                     y+para*sin(angle)+perp*sin(-pi/2+angle)*cos(elev_angle),
                     z+perp*sin(elev_angle)]
            self.feet_pos[0] = pos_0
            self.feet_pos[1] = pos_1
        
        if ability == 'in_air':
            # use a sine wave to model the wing flap
            index = 0
            for i in range(len(self.attached_segments)):
                if self.leg_types[i]['type'] == 'wing':
                    index = i
                    break
            
            skeleton_index = self.attached_segments[index]
            x, y, z = skeleton[skeleton_index][0], skeleton[skeleton_index][1], skeleton[skeleton_index][2]
            angle = skeleton[skeleton_index][3]

            t = (pg.time.get_ticks()-time)/100
            perp = self.leg_length*2/3
            up = sqrt(self.leg_length**2-perp)*sin(t)

            pos_0 = [x+perp*cos(pi/2+angle),
                    y+perp*sin(pi/2+angle),
                    z+up]
            pos_1 = [x+perp*cos(-pi/2+angle),
                    y+perp*sin(-pi/2+angle),
                    z+up]
            
            self.feet_pos[2*index] = pos_0
            self.feet_pos[2*index+1] = pos_1

        
        if ability == 'underwater':
            # use a sine wave to model the fin flutter
            index = len(self.attached_segments)-1
            
            skeleton_index = self.attached_segments[-1]
            x, y, z = skeleton[skeleton_index][0], skeleton[skeleton_index][1], skeleton[skeleton_index][2]
            angle = skeleton[skeleton_index][3]

            t = (pg.time.get_ticks()-time)/100
            para = -self.leg_length*3/4
            up = sqrt(self.leg_length**2-para)*sin(t)

            pos_0 = [x+para*cos(angle),
                    y+para*sin(angle),
                    z+up]
            pos_1 = [x+para*cos(angle),
                    y+para*sin(angle),
                    z+up]
            
            self.feet_pos[2*index] = pos_0
            self.feet_pos[2*index+1] = pos_1
    
    ############################# 
    # evolution systems         #
    ############################# 
    def transform_leg(self, index, new_type, new_level):
        self.leg_types[index] = {
            'type': new_type,
            'new_level': new_level
        }
    
    def free_leg(self):
        for i in range(len(self.attached_segments)):
            if self.leg_types[i]['type'] != 'wing' and self.leg_types[i]['type'] != 'arm':
                return i

    ############################# 
    # data getters              #
    ############################# 
    def num_legs(self):
        return len(list(filter(lambda type : type['type'] == 'leg', self.leg_types)))

    def get_torso_start(self):
        for i in range(len(self.attached_segments)):
            if self.leg_types[i]['type'] != 'wing' and self.leg_types[i]['type'] != 'arm':
                return i-1

        return -1

    ############################# 
    # calculations              #
    ############################# 
    def dist_foot_to_body(self, foot_pos, body_seg_pos):
        return sqrt((foot_pos[0]-body_seg_pos[0])**2 +
                    (foot_pos[1]-body_seg_pos[1])**2 + 
                    (foot_pos[2]-body_seg_pos[2])**2)

    def calculate_leg_joint_pos(self, foot_pos, body_seg_pos, neg):
        # xy_dist = sqrt((foot_pos[0]-body_seg_pos[0])**2+(foot_pos[1]-body_seg_pos[1])**2)
        
        # distance from foot to body segment
        dist = self.dist_foot_to_body(foot_pos, body_seg_pos)
        # vector pointing from body to foot
        body_to_foot_dir = [
            foot_pos[0]-body_seg_pos[0],
            foot_pos[1]-body_seg_pos[1],
            foot_pos[2]-body_seg_pos[2]
        ]
        # vector that the body is point in on the xy plane
        facing_dir = [
            cos(body_seg_pos[3]),
            sin(body_seg_pos[3]),
            0
        ]
        # take the cross product of these two vectors and normalize
        # to find the direction that the joint should be perpendicular to the 
        # body-foot disp and the facing direction
        bend_vec = [
            body_to_foot_dir[1]*facing_dir[2]-body_to_foot_dir[2]*facing_dir[1],
            body_to_foot_dir[2]*facing_dir[0]-body_to_foot_dir[0]*facing_dir[2],
            body_to_foot_dir[0]*facing_dir[1]-body_to_foot_dir[1]*facing_dir[0],
        ]
        bend_vec = np.cross(np.array(body_to_foot_dir), np.array(facing_dir))
        norm = np.linalg.norm(bend_vec)
        bend_dir = bend_vec
        if norm !=0:
            bend_dir = neg*bend_vec/norm
            
        # find the tail of the joint vector
        bend_root = [
            body_seg_pos[0]+(foot_pos[0]-body_seg_pos[0])/2,
            body_seg_pos[1]+(foot_pos[1]-body_seg_pos[1])/2,
            body_seg_pos[2]+(foot_pos[2]-body_seg_pos[2])/2,
        ]
        # each segment of the leg is half of the length of the entire leg
        # use pythagorean to determine the magnitude of the joint vector
        joint_vec_size = (self.leg_length/2)**2-(dist/2)**2
        # absolute value to account for floating point arithmetic
        joint_vec_size = sqrt(abs(joint_vec_size))
        # now calculate the position of the joint
        joint_pos = np.array(bend_root) + joint_vec_size*bend_dir

        return joint_pos
        
