from scipy.spatial.transform import Rotation
import numpy as np
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
        new_rel_pos = r_matrix * (self.rel_pos - pivot_point) + pivot_point
        rotation_offset = new_rel_pos - self.rel_pos
        self.rel_pos = new_rel_pos
        if np.abs(entity_pos[2] + self.rel_pos[2]) <= PIVOT_TOLERANCE:
            return rotation_offset
        return np.zeros(shape=(3,))

class Bone:
    def __init__(self, bone_data: dict):
        self.joint1 : int = bone_data['joint1']
        self.joint2 : int = bone_data['joint2']
        self.bone_length : int = bone_data['bone_length']

    def get_midpoint(self) -> np.ndarray:
        return (self.joint1.rel_pos + self.joint2.rel_pos) / 2

class Muscle:
    def __init__(self, muscle_data: dict):
        self.bone1 : int = muscle_data['bone1']
        self.bone2 : int = muscle_data['bone2']
    
    def update(self, flex_amt: float, joints: list[Joint], bones: list[Bone]) -> np.ndarray:
        amt_to_flex = flex_amt
        if amt_to_flex >= FLEX_TOLERANCE:
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
            rotation_offset = joint_to_rotate.rotate(pivot_point.rel_pos, amt_to_flex, rotation_axis)
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
            rotation_offset = joint_to_rotate.rotate(pivot_point.rel_pos, amt_to_flex, rotation_axis)
            if np.linalg.norm(rotation_offset) > np.linalg.norm(bone2_true_pivot):
                bone2_true_pivot = -rotation_offset
            # get the other joints attached to this joint
            for i, bone in enumerate(bones):
                if bone.joint1 == joint_index and i not in rotated_bones:
                    bone2_rotations.add(bone.joint2)
                elif bone.joint2 == joint_index and i not in rotated_bones:
                    bone2_rotations.add(bone.joint1)

        return bone1_true_pivot + bone2_true_pivot # the displacement of the entity itself based on real pivots

class Skeleton:
    def __init__(self, skeleton_data: dict):
        self.joints = [Joint(joint_data) 
                       for joint_data in skeleton_data['joints']]
        self.bones = [Bone(bone_data) 
                       for bone_data in skeleton_data['bones']]
        self.muscles = [Muscle(muscle_data)
                        for muscle_data in skeleton_data['muscles']]
    
    def fire_muscles(self, muscle_activations: np.ndarray, dt: float) -> np.ndarray:
        return np.sum(np.array([muscle.update(activation * dt, self.joints, self.bones) 
                                for activation, muscle in zip(muscle_activations, self.muscles)]), axis=0)
        
