import pygame as pg
from math import sqrt, pi, sin, cos
from src.util.settings import MODEL_COLORS
import numpy as np

class Legs:
    ############################# 
    # init and spawn            #
    ############################# 
    def __init__(self, num_pair_legs, leg_length, 
                       arm_attachments, wing_attachments,
                       size=5, step_bend = pi/6,):
        self.num_pair_legs = num_pair_legs
        self.leg_length = leg_length
        self.attached_segments = []
        self.feet_pos = []
        self.step_pos = []
        self.step_bend = step_bend
        self.feet_size = size
        self.arm_attachments = arm_attachments
        self.wing_attachments = wing_attachments
    
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
        self.step_pos[2*i] = [x+self.leg_length/2*cos(3*pi/4+angle),
                              y+self.leg_length/2*sin(3*pi/4+angle),
                              z]
        self.step_pos[2*i+1] = [x+self.leg_length/2*cos(-3*pi/4+angle),
                               y+self.leg_length/2*sin(-3*pi/4+angle),
                               z]
        self.feet_pos[2*i] = self.step_pos[2*i]
        self.feet_pos[2*i+1] = self.step_pos[2*i+1]

    def move_arms(self, skeleton, i):
        # first, calculate where it should be
        index = self.attached_segments[i]
        x, y, z = skeleton[index][0], skeleton[index][1], skeleton[index][2]
        angle = skeleton[index][3]
        self.step_pos[2*i] = [x+self.leg_length/4*cos(pi/4+angle),
                              y+self.leg_length/4*sin(pi/4+angle),
                              z-self.leg_length/sqrt(2)]
        self.step_pos[2*i+1] = [x+self.leg_length/4*cos(-pi/4+angle),
                                y+self.leg_length/4*sin(-pi/4+angle),
                                z-self.leg_length/sqrt(2)]

        # then move it there depending on other factors
        self.feet_pos[2*i] = self.step_pos[2*i]
        self.feet_pos[2*i+1] = self.step_pos[2*i+1]

    def move_feet(self, skeleton):
        # update the step pos: where the feet should be 
        # it took a step
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
            if self.attached_segments[i] in self.arm_attachments:
                self.move_arms(skeleton, i)
            elif self.attached_segments[i] in self.wing_attachments: 
                self.move_wings(skeleton, i)
            else: 
                if self.dist_foot_to_body(self.feet_pos[2*i], skeleton[self.attached_segments[i]]) >= self.leg_length:
                    # if the distance from the foot to the body segment
                    # is greater than the length of the leg, take a step
                    self.feet_pos[2*i] = self.step_pos[2*i]
                if self.dist_foot_to_body(self.feet_pos[2*i+1], skeleton[self.attached_segments[i]]) >= self.leg_length:
                    # same for the other foot
                    self.feet_pos[2*i+1] = self.step_pos[2*i+1]

    ############################# 
    # evolution systems         #
    ############################# 
    def transform_wings(self):
        for i in self.attached_segments:
            if i not in self.arm_attachments and i not in self.wing_attachments:
                self.wing_attachments.append(i)
                return

    def transform_arms(self):
        for i in self.attached_segments:
            if i not in self.arm_attachments and i not in self.wing_attachments:
                self.arm_attachments.append(i)
                return

    ############################# 
    # data getters              #
    ############################# 
    def num_legs(self):
        return len(self.attached_segments)-len(self.arm_attachments)-len(self.wing_attachments)

    def get_torso_start(self):
        for i in self.attached_segments:
            if i not in self.arm_attachments and i not in self.wing_attachments:
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
        
