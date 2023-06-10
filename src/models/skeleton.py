from scipy.spatial.transform import Rotation
import numpy as np
import pygame as pg
import math

FLEX_TOLERANCE = 0.01
RELAXATION_RATE = 0.1
PIVOT_TOLERANCE = 0.1
MIN_BEND_ANGLE = 0.1
MAX_BEND_ANGLE = math.pi - 0.1

class Joint:
    def __init__(self, joint_data: dict):
        self.rel_pos : np.ndarray = joint_data['rel_pos'] # relative position of joint to body
    
    def rotate(self, entity_pos: np.ndarray, pivot_point: np.ndarray, 
               angle: float, rotation_axis: np.ndarray) -> np.ndarray:
        r_matrix = Rotation.from_quat(np.concatenate([math.sin(angle/2) * rotation_axis, np.array([math.cos(angle/2)])])).as_matrix()
        new_rel_pos = r_matrix * (self.rel_pos - pivot_point) + pivot_point
        rotation_offset = new_rel_pos - self.rel_pos
        self.rel_pos = new_rel_pos
        if np.abs(entity_pos[2] + self.rel_pos[2]) <= PIVOT_TOLERANCE:
            return rotation_offset
        return np.zeros(shape=(3,))

    def get_abs_pos(self, pos: np.ndarray, angle: float):
        r_matrix = np.array([
            [math.cos(angle), -math.sin(angle), 0],
            [math.sin(angle),  math.cos(angle), 0],
            [0,                0,               1]
        ])
        return r_matrix.dot(self.rel_pos) + pos

class Bone:
    def __init__(self, bone_data: dict):
        self.joint1 : str = bone_data['joint1']
        self.joint2 : str = bone_data['joint2']
        self.depth : int = bone_data['depth']
    
    def get_bone_vec(self, pivot_joint: str, joints: dict):
        if pivot_joint == self.joint1:
            return joints[self.joint2].rel_pos - joints[self.joint1].rel_pos
        else:
            return joints[self.joint1].rel_pos - joints[self.joint2].rel_pos

class Muscle:
    def __init__(self, muscle_data: dict):
        self.bone1 : str = muscle_data['bone1']
        self.bone2 : str = muscle_data['bone2']
        self.cumul_flex = MIN_BEND_ANGLE
    
    def update(self, flex_amt: float, joints: list[Joint], bones: list[Bone]) -> np.ndarray:
        self.amt_to_flex = flex_amt
        if self.amt_to_flex >= FLEX_TOLERANCE:
            # flex
            flex_dir = 1
        else:
            # relax
            flex_dir = -1
        
        # find the shared joint from bone1 and bone2
        if bones[self.bone1].joint1 in [bones[self.bone2].joint1, bones[self.bone2].joint2]:
                shared_joint = bones[self.bone1].joint1 
        else:
            shared_joint = bones[self.bone1].joint2
        # get the pivot point
        pivot_point = joints[shared_joint].rel_pos
        # get the rotation axis for bone1
        if bones[self.bone1].joint1 == shared_joint:
            bone1_vec = joints[bones[self.bone1].joint2].rel_pos - joints[shared_joint].rel_pos
        else:
            bone1_vec = joints[bones[self.bone1].joint1].rel_pos - joints[shared_joint].rel_pos

        if bones[self.bone2].joint1 == shared_joint:
            bone2_vec = joints[bones[self.bone2].joint2].rel_pos - joints[shared_joint].rel_pos
        else:
            bone2_vec = joints[bones[self.bone2].joint1].rel_pos - joints[shared_joint].rel_pos
        rotation_axis = bone1_vec.cross(bone2_vec) * flex_dir
        
        # rotate bone1 and its connections
        rotated_bones = set([self.bone1])
        bone1_rotations = set([bones[self.bone1].joint1, bones[self.bone1].joint2])
        bone1_rotations.remove(shared_joint)
        bone1_true_pivot = np.zeros(shape=(3,))
        while bone1_rotations:
            # get the joint to rotate, treat the list like a queue
            joint_index = bone1_rotations[0]
            bone1_rotations.remove(joint_index)
            joint_to_rotate = joints[joint_index]
            rotation_offset = joint_to_rotate.rotate(pivot_point.rel_pos, self.amt_to_flex, rotation_axis)
            if np.linalg.norm(rotation_offset) > np.linalg.norm(bone1_true_pivot):
                bone1_true_pivot = -rotation_offset
            # get the other joints attached to this joint
            for i, bone in enumerate(bones):
                if bone.joint1 == joint_index and i not in rotated_bones:
                    bone1_rotations.add(bone.joint2)
                elif bone.joint2 == joint_index and i not in rotated_bones:
                    bone1_rotations.add(bone.joint1)

        # rotate bone2 and its connnections
        rotation_axis = -rotation_axis # rotation is in the other direction for bone2
        rotated_bones = set([self.bone2])
        bone2_rotations = set([bones[self.bone2].joint1, bones[self.bone2].joint2])
        bone2_rotations.remove(shared_joint)
        bone2_true_pivot = np.zeros(shape=(3,))
        while bone2_rotations:
            # get the joint to rotate, treat the list like a queue
            joint_index = bone1_rotations[0]
            bone2_rotations.remove(joint_index)
            joint_to_rotate = joints[joint_index]
            rotation_offset = joint_to_rotate.rotate(pivot_point.rel_pos, self.amt_to_flex, rotation_axis)
            if np.linalg.norm(rotation_offset) > np.linalg.norm(bone2_true_pivot):
                bone2_true_pivot = -rotation_offset
            # get the other joints attached to this joint
            for i, bone in enumerate(bones):
                if bone.joint1 == joint_index and i not in rotated_bones:
                    bone2_rotations.add(bone.joint2)
                elif bone.joint2 == joint_index and i not in rotated_bones:
                    bone2_rotations.add(bone.joint1)

        return bone1_true_pivot + bone2_true_pivot # the displacement of the entity itself based on real pivots

    def flex(self, pos: np.ndarray, flex_amt: float, joints: dict, bones: dict, stationary_bone: str | None):
        if self.cumul_flex + flex_amt < MAX_BEND_ANGLE:
            self.cumul_flex += flex_amt
            self.rotate_bones(pos, flex_amt, joints, bones, stationary_bone)

    def relax(self, pos: np.ndarray, dt: float, joints: dict, bones: dict, stationary_bone: str | None):
        if self.cumul_flex - dt > MIN_BEND_ANGLE:
            self.cumul_flex -= dt
            self.rotate_bones(pos, -dt, joints, bones, stationary_bone)

    def rotate_bones(self, pos: np.ndarray, angle: float, joints: dict, bones: dict, stationary_bone: str | None):
        pivot_joint = bones[self.bone1].joint1
        if bones[self.bone1].joint2 in [bones[self.bone2].joint1, bones[self.bone2].joint2]:
            pivot_joint = bones[self.bone1].joint2
        bone1_vec = bones[self.bone1].get_bone_vec(pivot_joint, joints)
        bone2_vec = bones[self.bone2].get_bone_vec(pivot_joint, joints)

        # set up the joints that have been rotated and which joints need to be rotated
        rotated_joints = set([pivot_joint])
        # rotate bone1
        joints_to_rotate = [bones[self.bone1].joint1, bones[self.bone1].joint2]
        rotation_axis = bone1_vec.cross(bone2_vec)
        rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
        bone1_rotation_drag = np.zeros((3,))
        if stationary_bone != self.bone1:
            while joints_to_rotate:
                joint_to_rotate = joints_to_rotate[0]
                if joint_to_rotate not in rotated_joints:
                    # rotate the joint
                    rotation_drag = joints[joint_to_rotate].rotate(pos, joints[pivot_joint].rel_pos, angle,
                                                                   rotation_axis)
                    # keep track of the drag of this joint
                    if np.linalg.norm(rotation_drag) > np.linalg.norm(bone1_rotation_drag):
                        bone1_rotation_drag = rotation_drag
                    # keep track of all rotated joints
                    rotated_joints.add(joint_to_rotate)
                    # update the list of joints to rotate to include children of this 
                    # joint away from the body
                    joints_to_rotate = joints_to_rotate[1:]
                    joints_to_rotate = joints_to_rotate + [bone.joint1 for bone in bones.values() if bone.joint2 == joint_to_rotate and bone.joint1 not in rotated_joints]
                    joints_to_rotate = joints_to_rotate + [bone.joint2 for bone in bones.values() if bone.joint1 == joint_to_rotate and bone.joint2 not in rotated_joints]
                joints_to_rotate = joints_to_rotate[1:]
        
        # rotate bone2
        rotated_joints = set([pivot_joint])
        joints_to_rotate = [bones[self.bone2].joint1, bones[self.bone2].joint2]
        rotation_axis = -rotation_axis
        bone2_rotation_drag = np.zeros((3,))
        if stationary_bone != self.bone2:
            while joints_to_rotate:
                joint_to_rotate = joints_to_rotate[0]
                if joint_to_rotate not in rotated_joints:
                    # rotate the joint
                    rotation_drag = joints[joint_to_rotate].rotate(pos, joints[pivot_joint].rel_pos, angle,
                                                                   rotation_axis)
                    # keep track of the drag of this joint
                    if np.linalg.norm(rotation_drag) > np.linalg.norm(bone2_rotation_drag):
                        bone2_rotation_drag = rotation_drag
                    # keep track of all rotated joints
                    rotated_joints.add(joint_to_rotate)
                    # update the list of joints to rotate to include children of this 
                    # joint away from the body
                    joints_to_rotate = joints_to_rotate[1:]
                    joints_to_rotate = joints_to_rotate + [bone.joint1 for bone in bones.values() if bone.joint2 == joint_to_rotate and bone.joint1 not in rotated_joints]
                    joints_to_rotate = joints_to_rotate + [bone.joint2 for bone in bones.values() if bone.joint1 == joint_to_rotate and bone.joint2 not in rotated_joints]
                # just rotated this joint or this joint should not have been rotated
                joints_to_rotate = joints_to_rotate[1:]

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
            muscle_data['jid']: Muscle(muscle_data)
            for muscle_data in skeleton_data['muscles']
        }
        self.num_joints = len(skeleton_data['joints'])
        self.num_bones = len(skeleton_data['bones'])
        self.num_muscles = len(skeleton_data['muscles'])
    
    def add_new_structure(self, new_joint_pos: np.ndarray, existing_jid: str, existing_bid: str):
        # add joint
        new_jid = f'j_{self.num_joints}'
        self.num_joints += 1
        self.joints[new_jid] = Joint({
            'rel_pos': new_joint_pos,
        })
        # find the depth of this bone
        bone_depths = np.array([bone.depth for bone in self.bones.values() if existing_jid in [bone.joint1, bone.joint2]])
        if bone_depths.size > 0:
            bone_depth = np.min(bone_depths) + 1
        else:
            bone_depth = 0
        # add bone
        new_bid = f'b_{self.num_bones}'
        self.num_bones += 1
        self.bones[new_bid] = Bone({
            'joint1': new_jid,
            'joint2': existing_jid,
            'depth': bone_depth,
        })
        # add muscle
        new_mid = f'm_{self.num_muscles}'
        self.num_muscles += 1
        self.muscles[new_mid] = Muscle({
            'bone1': existing_bid,
            'bone2': new_bid
        })
    
    def add_new_muscle(self, bid1: str, bid2: str):
        new_mid = f'm_{self.num_muscles}'
        self.num_muscles += 1
        self.muscles[new_mid] = Muscle({
            'bone1': bid1,
            'bone2': bid2
        })

    def mutate(self):
        ...

    def fire_muscles(self, pos: np.ndarray, muscle_activations: dict, dt: float) -> np.ndarray:
        for muscle_id, activation in muscle_activations.items():
            # a muscle flexes one bone out of the two it is connected with
            # it flexes the bone that is furthest away from the body
            muscle = self.muscles[muscle_id]
            bone_closer_to_body = None
            if self.bones[muscle.bone1].depth < self.bones[muscle.bone2].depth:
                bone_closer_to_body = muscle.bone1
            elif self.bones[muscle.bone2].depth < self.bones[muscle.bone1].depth:
                bone_closer_to_body = muscle.bone2
            if activation > 0:
                self.muscles[muscle_id].flex(pos, activation * dt, self.joints, self.bones, bone_closer_to_body)
            else:
                self.muscles[muscle_id].relax(pos, dt, self.joints, self.bones, bone_closer_to_body)
    
    def render(self, display: pg.Surface, pos: np.ndarray, angle: np.ndarray, camera):
        joint_drawpos = {
            jid: camera.transform_to_screen(joint.get_abs_pos(pos, angle)) for jid, joint in self.joints.items()}
        [pg.draw.circle(display, (0, 255, 0), drawpos, 2) for drawpos in joint_drawpos.values()]
        [pg.draw.line(display, (0, 255, 0), joint_drawpos[bone.joint1], joint_drawpos[bone.joint2]) for bone in self.bones.values()]