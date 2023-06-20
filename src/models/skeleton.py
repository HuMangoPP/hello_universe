from scipy.spatial.transform import Rotation
import numpy as np
import pygame as pg
import math, random

from ..util.adv_math import angle_between, find_poi, get_matrix_from_quat, rotate_z

# tolerance epsilon
FLEX_TOLERANCE = 0.01 # muscle needs to be activated above this threshold to flex
PIVOT_TOLERANCE = 0.05 # the z position of a joint must be below this threshold to be considered a pivot
PARALLEL_TOLERANCE = 0.1 # the angle between two vectors must be below this threshold to be considered parallel
DRAG_TOLERANCE = 0.5 # the distance between the joint and its estimated position must be below for movement to occur
# rates
RELAXATION_RATE = 0.1
MUTATION_RATE = 0.05
# boundaries
MAX_FLEXED_ANGLE = math.pi - 0.1
MIN_FLEXED_ANGLE = 0.1

class Joint:
    def __init__(self, joint_data: dict):
        self.rest_pos : np.ndarray = joint_data['rel_pos'].copy() # saved rest position for reference
        self.rel_pos : np.ndarray = joint_data['rel_pos'] # relative position of joint to body
        self.new_rel_pos : np.ndarray = joint_data['rel_pos']
    
    def rotate(self, entity_pos: np.ndarray, pivot_point: np.ndarray, 
               r_matrix: np.ndarray): 
        self.new_rel_pos = r_matrix.dot(self.new_rel_pos - pivot_point) + pivot_point

    def is_pivot(self, pos: np.ndarray, angle: float, up_matrix: np.ndarray) -> bool:
        r_matrix = np.array([
            [math.cos(angle), -math.sin(angle), 0],
            [math.sin(angle),  math.cos(angle), 0],
            [0,                0,               1]
        ])
        return (
            (up_matrix.dot(r_matrix.dot(self.rel_pos)) + pos)[2] <= PIVOT_TOLERANCE and
            (up_matrix.dot(r_matrix.dot(self.new_rel_pos)) + pos)[2] <= PIVOT_TOLERANCE
        )

    def update_movement(self):
        self.rel_pos = self.new_rel_pos

    def rollback_movement(self):
        self.new_rel_pos = self.rel_pos

    def get_abs_pos(self, pos: np.ndarray, angle: float, up_matrix: np.ndarray):
        return up_matrix.dot(rotate_z(self.rel_pos, angle)) + pos

    def get_abs_z(self, pos: np.ndarray, angle: float, up_matrix: np.ndarray) -> float:
        return self.get_abs_pos(pos, angle, up_matrix)[2]

class Bone:
    def __init__(self, bone_data: dict):
        self.joint1 : str = bone_data['joint1']
        self.joint2 : str = bone_data['joint2']
        self.depth : int = bone_data['depth']
    
    def get_bone_vec(self, pivot_joint: str, joints: dict):
        if pivot_joint == self.joint1:
            return joints[self.joint2].new_rel_pos - joints[self.joint1].new_rel_pos
        else:
            return joints[self.joint1].new_rel_pos - joints[self.joint2].new_rel_pos

class Muscle:
    def __init__(self, muscle_data: dict, bones: dict, joints: dict):
        self.bone1 : str = muscle_data['bone1']
        self.bone2 : str = muscle_data['bone2']

        # find the current bend
        bone1 = bones[self.bone1]
        bone2 = bones[self.bone2]
        pivot_joint = bone1.joint1
        if bone1.joint2 in [bone2.joint1, bone2.joint2]:
            pivot_joint = bone1.joint2
        bone1_vec = bone1.get_bone_vec(pivot_joint, joints)
        bone2_vec = bone2.get_bone_vec(pivot_joint, joints)
        angle = math.pi - angle_between(bone1_vec, bone2_vec)
        self.cumul_flex = angle
        self.relaxed_angle = angle
        self.new_cumul_flex = angle
    
    def reset_angles(self):
        self.cumul_flex = self.relaxed_angle
        self.new_cumul_flex = self.relaxed_angle
        
    def flex(self, pos: np.ndarray, flex_amt: float, joints: dict, bones: dict, 
             stationary_bone: str | None, fixed_bone: str) -> dict:
        if MIN_FLEXED_ANGLE <= self.new_cumul_flex and self.new_cumul_flex <= MAX_FLEXED_ANGLE:
            flex_amt = np.clip(flex_amt, 
                            a_min=MIN_FLEXED_ANGLE-self.new_cumul_flex, 
                            a_max=MAX_FLEXED_ANGLE-self.new_cumul_flex)
            self.new_cumul_flex += flex_amt
            return self.rotate_bones(pos, flex_amt, joints, bones, stationary_bone, fixed_bone)
        return {
            'movement': np.zeros((3,))
        }

    def relax(self, pos: np.ndarray, dt: float, joints: dict, bones: dict, 
              stationary_bone: str | None, fixed_bone: str) -> dict:
        angle = dt if (stationary_bone is not None or fixed_bone in [self.bone1, self.bone2]) else dt * 2
        if self.new_cumul_flex > self.relaxed_angle:
            flex_ratio = min(self.new_cumul_flex - self.relaxed_angle, angle) / angle
            self.new_cumul_flex -= flex_ratio * angle
            return self.rotate_bones(pos, -flex_ratio * dt, joints, bones, stationary_bone, fixed_bone)
            
        return {
            'movement': np.zeros((3,))
        }

    def rotate_bones(self, pos: np.ndarray, angle: float, joints: dict, bones: dict, 
                     stationary_bone: str | None, fixed_bone: str) -> dict:
        
        pivot_joint = bones[self.bone1].joint1
        if bones[self.bone1].joint2 in [bones[self.bone2].joint1, bones[self.bone2].joint2]:
            pivot_joint = bones[self.bone1].joint2
        bone1_vec = bones[self.bone1].get_bone_vec(pivot_joint, joints)
        bone2_vec = bones[self.bone2].get_bone_vec(pivot_joint, joints)

        # set up the joints that have been rotated and which joints need to be rotated
        rotated_joints = set([pivot_joint])
        # rotate bone1
        joints_to_rotate = [bones[self.bone1].joint1, bones[self.bone1].joint2]
        rotation_axis = np.cross(bone1_vec, bone2_vec)
        rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
        r_matrix = Rotation.from_quat(np.concatenate([math.sin(angle/2) * rotation_axis, np.array([math.cos(angle/2)])])).as_matrix()
        if self.bone1 not in [stationary_bone, fixed_bone]:
            while joints_to_rotate: # TODO: reduce amount need to rotate by making each new joint relative to its parent joint
                joint_to_rotate = joints_to_rotate[0]
                if joint_to_rotate not in rotated_joints:
                    # rotate the joint
                    joints[joint_to_rotate].rotate(pos, joints[pivot_joint].new_rel_pos, r_matrix)
                    # keep track of all rotated joints
                    rotated_joints.add(joint_to_rotate)
                    # update the list of joints to rotate to include children of this 
                    # joint away from the body
                    joints_to_rotate = joints_to_rotate + [bone.joint1 for bone in bones.values() if bone.joint2 == joint_to_rotate and bone.joint1 not in rotated_joints]
                    joints_to_rotate = joints_to_rotate + [bone.joint2 for bone in bones.values() if bone.joint1 == joint_to_rotate and bone.joint2 not in rotated_joints]
                joints_to_rotate = joints_to_rotate[1:]
        
        # rotate bone2
        rotated_joints = set([pivot_joint])
        joints_to_rotate = [bones[self.bone2].joint1, bones[self.bone2].joint2]
        r_matrix = Rotation.from_quat(np.concatenate([math.sin(-angle/2) * rotation_axis, np.array([math.cos(-angle/2)])])).as_matrix()
        if self.bone2 not in [stationary_bone, fixed_bone]:
            while joints_to_rotate:
                joint_to_rotate = joints_to_rotate[0]
                if joint_to_rotate not in rotated_joints:
                    # rotate the joint
                    joints[joint_to_rotate].rotate(pos, joints[pivot_joint].new_rel_pos, r_matrix)
                    # keep track of all rotated joints
                    rotated_joints.add(joint_to_rotate)
                    # update the list of joints to rotate to include children of this 
                    # joint away from the body
                    joints_to_rotate = joints_to_rotate + [bone.joint1 for bone in bones.values() if bone.joint2 == joint_to_rotate and bone.joint1 not in rotated_joints]
                    joints_to_rotate = joints_to_rotate + [bone.joint2 for bone in bones.values() if bone.joint1 == joint_to_rotate and bone.joint2 not in rotated_joints]
                # just rotated this joint or this joint should not have been rotated
                joints_to_rotate = joints_to_rotate[1:]

    def update_flex(self):
        self.cumul_flex = self.new_cumul_flex

    def rollback_flex(self):
        self.new_cumul_flex = self.cumul_flex

    def has_bone(self, bid: str):
        return bid in [self.bone1, self.bone2]

class Skeleton:
    def __init__(self, skeleton_data: dict):
        self.joints = {
            joint_data['jid']: Joint(joint_data)
            for joint_data in skeleton_data['joints']
        }
        self.bones = {
            bone_data['bid']: Bone(bone_data)
            for bone_data in skeleton_data['bones']
        }
        self.muscles = {
            muscle_data['mid']: Muscle(muscle_data, self.bones, self.joints)
            for muscle_data in skeleton_data['muscles']
        }
        self.num_joints = len(skeleton_data['joints'])
        self.num_bones = len(skeleton_data['bones'])
        self.num_muscles = len(skeleton_data['muscles'])

        if self.num_bones > 0:
            self.fixed_bone = skeleton_data['bones'][0]['bid']
        else:
            self.fixed_bone = None
        
        if self.num_joints > 0:
            self.root_joint = skeleton_data['joints'][0]['jid']
        else:
            self.root_joint = None
    
    def reset_skeleton(self, skeleton_data: dict):
        for muscle in self.muscles.values():
            muscle.reset_angles()
        for joint_data in skeleton_data['joints']:
            self.joints[joint_data['jid']].rel_pos = joint_data['rel_pos']
            self.joints[joint_data['jid']].new_rel_pos = joint_data['rel_pos']

    # evo
    def add_extension(self, new_joint_pos: np.ndarray, existing_jid: str, existing_bid: str):
        '''
            Adds an extension to an existing bone and connects a muscle. The new bone will always have a depth
            value one greater than the bone it is extending from.
        '''
        # add joint
        new_jid = f'j{self.num_joints}'
        self.num_joints += 1
        self.joints[new_jid] = Joint({
            'rel_pos': new_joint_pos,
        })
        # find the depth of this bone
        bone_depth = self.bones[existing_bid].depth + 1
        # add bone
        new_bid = f'b{self.num_bones}'
        self.num_bones += 1
        self.bones[new_bid] = Bone({
            'joint1': new_jid,
            'joint2': existing_jid,
            'depth': bone_depth,
        })
        # add muscle
        new_mid = f'm{self.num_muscles}'
        self.num_muscles += 1
        self.muscles[new_mid] = Muscle({
            'bone1': existing_bid,
            'bone2': new_bid,
        }, self.bones, self.joints)
    
    def add_new_structure(self, new_joint_pos: np.ndarray):
        '''
            Adds a new branch structure from the root joint and adds a muscle to connect
            to the fixed bone unless the new structure is the fixed bone itself.
        '''
        # adds to the root joint
        new_jid = f'j{self.num_joints}'
        self.num_joints += 1
        self.joints[new_jid] = Joint({
            'rel_pos': new_joint_pos,
        })

        # find the depth of this bone
        # add bone
        new_bid = f'b{self.num_bones}'
        if self.fixed_bone is None:
            self.fixed_bone = new_bid
        self.num_bones += 1
        self.bones[new_bid] = Bone({
            'joint1': self.root_joint,
            'joint2': new_jid,
            'depth': 0,
        })

        # add muscle
        if self.fixed_bone != new_bid:
            new_mid = f'm{self.num_muscles}'
            self.num_muscles += 1
            self.muscles[new_mid] = Muscle({
                'bone1': self.fixed_bone,
                'bone2': new_bid,
            }, self.bones, self.joints)

    def add_new_muscle(self, bid1: str, bid2: str):
        new_mid = f'm{self.num_muscles}'
        self.num_muscles += 1
        self.muscles[new_mid] = Muscle({
            'bone1': bid1,
            'bone2': bid2,
        })

    def mutate(self):
        if random.uniform(0, 1) <= MUTATION_RATE:
            # structure
            new_joint_dir = np.random.uniform(0, 1, (3,))
            while np.linalg.norm(new_joint_dir) == 0:
                new_joint_dir = np.random.uniform(0, 1, (3,))
            new_joint_dir = new_joint_dir / np.linalg.norm(new_joint_dir)
            self.add_new_structure(50 * new_joint_dir)

        if random.uniform(0, 1) <= MUTATION_RATE and self.bones:
            # extension
            bid = random.choice(list(self.bones.keys()))
            jid = self.bones[bid].bone1 if random.uniform(0, 1) <= 0.5 else self.bones[bid].bone2
            bone_vec = -self.bones[bid].get_bone_vec(jid, self.joints)
            rotation_axis = np.random.uniform(0, 1, size=(3,))
            if np.linalg.norm(rotation_axis) == 0:
                rotation_axis = np.array([0,0,1])
            else:
                rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
            r_matrix = Rotation.from_quat(np.concatenate([rotation_axis * math.sin(0.1), np.array([math.cos(0.1)])])).as_matrix()
            new_rel_pos = r_matrix.dot(bone_vec) + self.joints[jid].rel_pos
            self.add_extension(new_rel_pos, jid, bid)

        if random.uniform(0, 1) <= MUTATION_RATE:
            # add muscle
            random_jid = random.choice(list(self.joints.keys()))
            bones_with_joint = [bid for bid, bone in self.bones if random_jid in [bone.joint1, bone.joint2]]
            if len(bones_with_joint) >= 2:
                # choose two random bones
                bindex1 = random.randint(0, len(bones_with_joint))
                bindex2 = random.randint(0, len(bones_with_joint) - 1)
                bid1 = bones_with_joint[bindex1]
                bones_with_joint.pop(bindex1)
                bid2 = bones_with_joint[bindex2]
                # check if this muscle already exists
                muscle_exists = [mid for mid, muscle in self.muscles if muscle.has_bone(bid1) and muscle.has_bone(bid2)]
                if not muscle_exists:
                    self.add_new_muscle(bid1, bid2)

    # functionality
    def fire_muscles(self, pos: np.ndarray, angle: float, up_matrix: np.ndarray, 
                     muscle_activations: dict, dt: float) -> tuple[np.ndarray, float]:
        for muscle_id, activation in muscle_activations.items():
            # a muscle flexes one bone out of the two it is connected with
            # it flexes the bone that is furthest away from the body
            muscle = self.muscles[muscle_id]
            bone_closer_to_body = None
            if self.bones[muscle.bone1].depth < self.bones[muscle.bone2].depth:
                bone_closer_to_body = muscle.bone1
            elif self.bones[muscle.bone2].depth < self.bones[muscle.bone1].depth:
                bone_closer_to_body = muscle.bone2
            
            self.muscles[muscle_id].flex(pos, 1 * activation * dt, self.joints, self.bones, bone_closer_to_body, self.fixed_bone)

        movement, turn_angle = np.zeros((3,)), 0
        dragging_joints = [joint for joint in self.joints.values() if joint.is_pivot(pos, angle, up_matrix)]
        if len(dragging_joints) == 1:
            # get the movement
            movement = (dragging_joints[0].new_rel_pos - dragging_joints[0].rel_pos)
            
            # move all of the joints pos and muscle flex
            [joint.update_movement() for joint in self.joints.values()]
            [muscle.update_flex() for muscle in self.muscles.values()]
        elif len(dragging_joints) > 1:
            through_joint_vec = dragging_joints[0].rel_pos - dragging_joints[1].rel_pos
            new_through_joint_vec = dragging_joints[0].new_rel_pos - dragging_joints[1].new_rel_pos
            other_dragging_joints = dragging_joints[2:]

            angle_between_through_vecs = angle_between(through_joint_vec, new_through_joint_vec)
            if angle_between_through_vecs < PARALLEL_TOLERANCE:
                # movement
                can_offset = True
                average_rel_pos = np.average(np.array([dragged_joint.rel_pos for dragged_joint in dragging_joints]), axis=0)
                average_new_rel_pos = np.average(np.array([dragged_joint.new_rel_pos for dragged_joint in dragging_joints]), axis=0)
                offset = average_new_rel_pos - average_rel_pos
                movement = offset
                for dragged_joint in other_dragging_joints:
                    if np.linalg.norm(dragged_joint.new_rel_pos - offset - dragged_joint.rel_pos) > DRAG_TOLERANCE:
                        can_offset = False
                        break
                
                if can_offset:
                    up_rotation = get_matrix_from_quat(up_matrix.dot(rotate_z(average_rel_pos, angle)), 
                                                       up_matrix.dot(rotate_z(average_new_rel_pos, angle)))
                    [joint.update_movement() for joint in self.joints.values()]
                    [muscle.update_flex() for muscle in self.muscles.values()]
                else:
                    [joint.rollback_movement() for joint in self.joints.values()]
                    [muscle.rollback_flex() for muscle in self.muscles.values()]
            else:
                # rotate
                rotation_pivot = find_poi(through_joint_vec, new_through_joint_vec, 
                                          dragging_joints[1].rel_pos, dragging_joints[1].new_rel_pos)
                rotation_axis = np.cross(through_joint_vec, new_through_joint_vec)
                rotation_angle = angle_between_through_vecs
                r_matrix = np.array([
                    [math.cos(rotation_angle), -math.sin(rotation_angle), 0],
                    [math.sin(rotation_angle),  math.cos(rotation_angle), 0],
                    [0,                         0,                        1]
                ])
                can_offset = True
                offset = r_matrix.dot(-rotation_pivot) + rotation_pivot
                for dragged_joint in other_dragging_joints:
                    if np.linalg.norm(dragged_joint.new_rel_pos + offset - dragged_joint.rel_pos) > DRAG_TOLERANCE:
                        can_offset = False
                        break
                
                if can_offset:
                    movement = -offset
                    turn_angle = rotation_angle
                [joint.update_movement() for joint in self.joints.values()]
                [muscle.update_flex() for muscle in self.muscles.values()]
        else:
            # no movement should occur
            # [joint.rollback_movement() for joint in self.joints.values()]
            # [muscle.rollback_flex() for muscle in self.muscles.values()]
            [joint.update_movement() for joint in self.joints.values()]
            [muscle.update_flex() for muscle in self.muscles.values()]

        movement[2] = 0
        return -movement, turn_angle

    def inv_dist_from_ground(self, pos: np.ndarray, angle: float, up_matrix: np.ndarray):
        return {jid: 1 / abs((joint.get_abs_z(pos, angle, up_matrix) + 1))
                for jid, joint in self.joints.items()}

    def get_muscle_flex_amt(self):
        return {mid: muscle.cumul_flex - muscle.relaxed_angle
                for mid, muscle in self.muscles.items()}

    def get_lowest_joint(self, pos: np.ndarray, angle: float, up_matrix: np.ndarray) -> float:
        return np.min(np.array([joint.get_abs_z(pos, angle, up_matrix) for joint in self.joints.values()]))

    def get_balance(self, pos: np.ndarray, angle: float, up_matrix: np.ndarray) -> np.ndarray | None:
        joints = np.array([joint.rel_pos for joint in self.joints.values() if joint.get_abs_z(pos, angle, up_matrix) <= PIVOT_TOLERANCE])
        if joints.size > 0:
            return np.average(joints, axis=0)
        return None

    def get_com(self) -> np.ndarray:
        return np.average(np.array([joint.rel_pos for joint in self.joints.values()]), axis=0)

    # render
    def render(self, display: pg.Surface, pos: np.ndarray, angle: float, up_matrix: np.ndarray, camera):
        joint_drawpos = {
            jid: camera.transform_to_screen(joint.get_abs_pos(pos, angle, up_matrix))
            for jid, joint in self.joints.items()
        }
        joint_color = {
            jid: (255, 0, 0) if joint.get_abs_z(pos, angle, up_matrix) <= PIVOT_TOLERANCE else (0, 255, 0)
            for jid, joint in self.joints.items()
        }
        [pg.draw.circle(display, joint_color[jid], joint_drawpos[jid], 2) 
         for jid in joint_drawpos]
        [pg.draw.line(display, (0, 255, 0), joint_drawpos[bone.joint1], joint_drawpos[bone.joint2]) 
         for bone in self.bones.values()]

    # data
    def get_df(self) -> dict:
        joints = {
            jid: tuple([float(c) for c in joint.rest_pos]) for jid, joint in self.joints.items()
        }
        bones = {
            bid: {
                'joint1': bone.joint1,
                'joint2': bone.joint2,
                'depth': bone.depth
            } for bid, bone in self.bones.items()
        }
        muscles = {
            mid: [muscle.bone1, muscle.bone2]
            for mid, muscle in self.muscles.items()
        }
        return {
            'joints': joints,
            'bones': bones,
            'muscles': muscles,
        }
