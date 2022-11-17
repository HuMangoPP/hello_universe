import pygame as pg
from math import atan2, sqrt, pi, sin, cos, acos, tan

class Legs:
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

    def draw(self, screen, skeleton, camera):
        for i in range(self.num_pair_legs):
            screen_pos = []
            # foot pos
            screen_pos.append(camera.transform_to_screen(self.feet_pos[2*i][0], 
                                                         self.feet_pos[2*i][1], 
                                                         self.feet_pos[2*i][2]))
            # joint pos
            joint_x, joint_y, joint_z = self.calculate_leg_joint_pos(self.feet_pos[2*i], skeleton[self.attached_segments[i]], 1)
            screen_pos.append(camera.transform_to_screen(joint_x, joint_y, joint_z))
            # body pos
            screen_pos.append(camera.transform_to_screen(skeleton[self.attached_segments[i]][0],
                                                         skeleton[self.attached_segments[i]][1],
                                                         skeleton[self.attached_segments[i]][2]))
            # draw the feet
            pg.draw.circle(screen, 'blue', screen_pos[0], self.feet_size)
            pg.draw.line(screen, 'green', screen_pos[0],
                                          screen_pos[1])
            pg.draw.line(screen, 'green', screen_pos[1],
                                          screen_pos[2])

            # other leg of pair
            screen_pos = []
            # foot pos
            screen_pos.append(camera.transform_to_screen(self.feet_pos[2*i+1][0], 
                                                         self.feet_pos[2*i+1][1], 
                                                         self.feet_pos[2*i+1][2]))
            # joint pos
            joint_x, joint_y, joint_z = self.calculate_leg_joint_pos(self.feet_pos[2*i+1], skeleton[self.attached_segments[i]], 1)
            screen_pos.append(camera.transform_to_screen(joint_x, joint_y, joint_z))
            # body pos
            screen_pos.append(camera.transform_to_screen(skeleton[self.attached_segments[i]][0],
                                                         skeleton[self.attached_segments[i]][1],
                                                         skeleton[self.attached_segments[i]][2]))
            pg.draw.circle(screen, 'blue', screen_pos[0], self.feet_size)
            pg.draw.line(screen, 'green', screen_pos[0],
                                          screen_pos[1])
            pg.draw.line(screen, 'green', screen_pos[1],
                                          screen_pos[2])
    
    def move_arms(self, skeleton, i):
        # first, calculate where it should be
        index = self.attached_segments[i]
        x, y, z = skeleton[index][0], skeleton[index][1], skeleton[index][2]
        angle = skeleton[index][3]
        self.step_pos[2*i] = [x+self.leg_length/2*cos(pi/2+angle),
                              y+self.leg_length/2*sin(pi/2+angle),
                              z-self.leg_length/2]
        self.step_pos[2*i+1] = [x+self.leg_length/2*cos(-pi/2+angle),
                                y+self.leg_length/2*sin(-pi/2+angle),
                                z-self.leg_length/2]

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
            
            self.step_pos[2*i] = [x+self.leg_length*cos(self.step_bend+angle), 
                                  y+self.leg_length*sin(self.step_bend+angle), 
                                  z]
            self.step_pos[2*i+1] = [x+self.leg_length*cos(-self.step_bend+angle), 
                                    y+self.leg_length*sin(-self.step_bend+angle), 
                                    z]
        
        # update the renderable feet pos as neceessary
        for i in range(self.num_pair_legs):
            if i in self.arm_attachments:
                self.move_arms(skeleton, i)
            elif i in self.wing_attachments: 
                self.feet_pos[2*i] = self.step_pos[2*i]
                self.feet_pos[2*i+1] = self.step_pos[2*i+1]
            else: 
                if self.dist_foot_to_body(self.feet_pos[2*i], skeleton[self.attached_segments[i]]) >= self.leg_length:
                    # if the distance from the foot to the body segment
                    # is greater than the length of the leg, take a step
                    self.feet_pos[2*i] = self.step_pos[2*i]
                if self.dist_foot_to_body(self.feet_pos[2*i+1], skeleton[self.attached_segments[i]]) >= self.leg_length:
                    # same for the other foot
                    self.feet_pos[2*i+1] = self.step_pos[2*i+1]

    def transform_wings(self):
        for i in range(len(self.attached_segments)):
            if i not in self.arm_attachments and i not in self.wing_attachments:
                self.arm_attachments.append(i)
                return

    def transform_arms(self):
        for i in range(len(self.attached_segments)):
            if i not in self.arm_attachments and i not in self.wing_attachments:
                self.arm_attachments.append(i)
                return

    def num_legs(self):
        return len(self.attached_segments)-len(self.arm_attachments)-len(self.wing_attachments)

    def get_torso_start(self):
        for i in self.attached_segments:
            if i not in self.arm_attachments and i not in self.wing_attachments:
                return i-1


    def dist_foot_to_body(self, foot_pos, body_seg_pos):
        return sqrt((foot_pos[0]-body_seg_pos[0])**2+(foot_pos[1]-body_seg_pos[1])**2)

    def calculate_leg_joint_pos(self, foot_pos, body_seg_pos, neg):
        xy_dist = sqrt((foot_pos[0]-body_seg_pos[0])**2+(foot_pos[1]-body_seg_pos[1])**2)
        half_dist = xy_dist/2
        dx = foot_pos[0]-body_seg_pos[0]
        dy = foot_pos[1]-body_seg_pos[1]
        body_to_foot_horizontal_angle = neg*atan2(dy,dx)
        joint_x = body_seg_pos[0]+half_dist*cos(body_to_foot_horizontal_angle)
        joint_y = body_seg_pos[1]+neg*half_dist*sin(body_to_foot_horizontal_angle)
        half_length = self.leg_length/2
        joint_z = body_seg_pos[2]+sqrt(abs(half_length**2-half_dist**2))

        # dist = (foot_pos[0]-body_seg_pos[0])**2+(foot_pos[1]-body_seg_pos[1])**2
        # cos_bend_angle = (dist-self.leg_length**2/2)/(-self.leg_length**2/2)
        # cos_bend_angle = round(cos_bend_angle, 3)
        # bend_angle = acos(cos_bend_angle)
        # body_to_joint_vertical_angle = pi/2-body_to_foot_horizontal_angle-(pi-bend_angle)/2
        # joint_x = body_seg_pos[0]+self.leg_length/2*sin(body_to_joint_vertical_angle)
        # joint_y = body_seg_pos[1]+neg*self.leg_length/2*cos(body_to_joint_vertical_angle)
        return joint_x, joint_y, joint_z
        
