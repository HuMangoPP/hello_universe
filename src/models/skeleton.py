from scipy.spatial.transform import Rotation
import numpy as np
import pygame as pg
import math

FLEX_TOLERANCE = 0.01
RELAXATION_RATE = 0.1
PIVOT_TOLERANCE = 0.1

class Joint:
    def __init__(self, joint_data: dict):
        self.rel_pos : np.ndarray = joint_data['rel_pos'] # relative position of joint to body
    
    def rotate(self, entity_pos: np.ndarray, pivot_point: np.ndarray, 
               angle: float, rotation_axis: np.ndarray) -> np.ndarray:
        r_matrix = Rotation.from_quat(np.concatenate([math.sin(angle/2) * rotation_axis, np.array([math.cos(angle/2)])])).as_matrix()
        new_rel_pos = r_matrix.dot(self.rel_pos - pivot_point) + pivot_point
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
    def __init__(self, muscle_data: dict, bones: dict, joints: dict):
        self.bone1 : str = muscle_data['bone1']
        self.bone2 : str = muscle_data['bone2']
        self.min_bend = muscle_data['min_bend']
        self.max_bend = muscle_data['max_bend']

        # find the current bend
        bone1 = bones[self.bone1]
        bone2 = bones[self.bone2]
        pivot_joint = bone1.joint1
        if bone1.joint2 in [bone2.joint1, bone2.joint2]:
            pivot_joint = bone1.joint2
        bone1_vec = bone1.get_bone_vec(pivot_joint, joints)
        bone2_vec = bone2.get_bone_vec(pivot_joint, joints)
        angle = math.acos(bone1_vec.dot(-bone2_vec) / np.linalg.norm(bone1_vec) / np.linalg.norm(bone2_vec))
        self.cumul_flex = angle

    def flex(self, pos: np.ndarray, flex_amt: float, joints: dict, bones: dict, 
             stationary_bone: str | None, fixed_bone: str) -> tuple[np.ndarray, float]:
        angle = flex_amt if stationary_bone is not None else flex_amt * 2
        if self.cumul_flex + angle < self.max_bend:
            self.cumul_flex += angle
            return self.rotate_bones(pos, flex_amt, joints, bones, stationary_bone, fixed_bone)
        return np.zeros((3,)), 0

    def relax(self, pos: np.ndarray, dt: float, joints: dict, bones: dict, 
              stationary_bone: str | None, fixed_bone: str) -> tuple[np.ndarray, float]:
        angle = dt if stationary_bone is not None else dt * 2
        if self.cumul_flex - angle > self.min_bend:
            self.cumul_flex -= angle
            return self.rotate_bones(pos, -dt, joints, bones, stationary_bone, fixed_bone)
        return np.zeros((3,)), 0

    def rotate_bones(self, pos: np.ndarray, angle: float, joints: dict, bones: dict, 
                     stationary_bone: str | None, fixed_bone: str) -> tuple[np.ndarray, float]:
        pivot_joint = bones[self.bone1].joint1
        if bones[self.bone1].joint2 in [bones[self.bone2].joint1, bones[self.bone2].joint2]:
            pivot_joint = bones[self.bone1].joint2
        bone1_vec = bones[self.bone1].get_bone_vec(pivot_joint, joints)
        bone2_vec = bones[self.bone2].get_bone_vec(pivot_joint, joints)

        # check fixed bone
        entity_should_turn = False
        if fixed_bone in [self.bone1, self.bone2]:
            entity_should_turn = True
            angle *= 2

        # set up the joints that have been rotated and which joints need to be rotated
        rotated_joints = set([pivot_joint])
        # rotate bone1
        joints_to_rotate = [bones[self.bone1].joint1, bones[self.bone1].joint2]
        rotation_axis = np.cross(bone1_vec, bone2_vec)
        rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
        bone1_rotation_drag = np.zeros((3,))
        if self.bone1 != stationary_bone and self.bone1 != fixed_bone:
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
        if self.bone2 != stationary_bone and self.bone2 != fixed_bone:
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
        
        if entity_should_turn:
            return -(bone1_rotation_drag + bone2_rotation_drag), angle/2
        else:
            return -(bone1_rotation_drag + bone2_rotation_drag), 0

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
        if self.fixed_bone is None:
            self.fixed_bone = new_bid
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
            'bone2': new_bid,
            'min_bend': 0.1,
            'max_bend': math.pi - 0.1
        }, self.bones, self.joints)
    
    def add_new_muscle(self, bid1: str, bid2: str):
        new_mid = f'm_{self.num_muscles}'
        self.num_muscles += 1
        self.muscles[new_mid] = Muscle({
            'bone1': bid1,
            'bone2': bid2,
            'min_bend': 0.1,
            'max_bend': math.pi - 0.1
        },
        self.bones, self.joints)

    def mutate(self):
        ...

    def fire_muscles(self, pos: np.ndarray, muscle_activations: dict, dt: float) -> tuple[np.ndarray, float]:
        net_movement, net_angle = np.zeros((3,)), 0
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
                movement, angle = self.muscles[muscle_id].flex(pos, activation * dt, self.joints, self.bones, bone_closer_to_body, self.fixed_bone)
            else:
                movement, angle = self.muscles[muscle_id].relax(pos, dt, self.joints, self.bones, bone_closer_to_body, self.fixed_bone)
            net_movement = net_movement + movement
            net_angle += angle
        
        return net_movement, angle

    def get_joint_touching(self, pos: np.ndarray):
        return {jid: int(np.linalg.norm(pos + joint.rel_pos) <= PIVOT_TOLERANCE)
                for jid, joint in self.joints.items()}

    def get_muscle_flex_amt(self):
        return {mid: muscle.cumul_flex
                for mid, muscle in self.muscles.items()}

    def render(self, display: pg.Surface, pos: np.ndarray, angle: np.ndarray, camera):
        joint_drawpos = {
            jid: camera.transform_to_screen(joint.get_abs_pos(pos, angle)) for jid, joint in self.joints.items()}
        [pg.draw.circle(display, (0, 255, 0), drawpos, 2) for drawpos in joint_drawpos.values()]
        [pg.draw.line(display, (0, 255, 0), joint_drawpos[bone.joint1], joint_drawpos[bone.joint2]) for bone in self.bones.values()]
