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
            joint_x, joint_y, joint_z = self.calculate_leg_joint_pos(self.feet_pos[2*i], skeleton[self.attached_segments[i]], -1)
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
        for i in self.attached_segments:
            if i not in self.arm_attachments and i not in self.wing_attachments:
                self.arm_attachments.append(i)
                return

    def transform_arms(self):
        for i in self.attached_segments:
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
        return sqrt((foot_pos[0]-body_seg_pos[0])**2 +
                    (foot_pos[1]-body_seg_pos[1])**2 + 
                    (foot_pos[2]-body_seg_pos[2])**2)

    def calculate_leg_joint_pos(self, foot_pos, body_seg_pos, neg):
        # xy_dist = sqrt((foot_pos[0]-body_seg_pos[0])**2+(foot_pos[1]-body_seg_pos[1])**2)
        
        # distance from foot to body segment
        dist = self.dist_foot_to_body(foot_pos, body_seg_pos)
        # vector pointing from body to foot
        body_to_foot_dir = [foot_pos[0]-body_seg_pos[0],
                            foot_pos[1]-body_seg_pos[1],
                            foot_pos[2]-body_seg_pos[2]]
        # vector that the body is point in on the xy plane
        facing_dir = [cos(body_seg_pos[3]),
                      sin(body_seg_pos[3]),
                      0]
        # take the cross product of these two vectors to find the direction of the bend
        bend_vec = [
            neg*(body_to_foot_dir[1]*facing_dir[2]-body_to_foot_dir[2]*facing_dir[1]),
            neg*(body_to_foot_dir[2]*facing_dir[0]-body_to_foot_dir[0]*facing_dir[2]),
            neg*(body_to_foot_dir[0]*facing_dir[1]-body_to_foot_dir[1]*facing_dir[0]),
        ]
        # normalize the joint vector
        size = sqrt(bend_vec[0]**2+bend_vec[1]**2+bend_vec[2]**2)
        bend_dir = bend_vec
        if size!=0:
            bend_dir = [
                bend_vec[0]/size,
                bend_vec[1]/size,
                bend_vec[2]/size
            ]
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
        joint_pos = [
            bend_root[0]+joint_vec_size*bend_dir[0],
            bend_root[1]+joint_vec_size*bend_dir[1],
            bend_root[2]+joint_vec_size*bend_dir[2],
        ]

        return joint_pos[0], joint_pos[1], joint_pos[2]
        
