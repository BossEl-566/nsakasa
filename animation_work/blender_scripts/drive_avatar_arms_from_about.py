import json
from pathlib import Path
from math import radians

import bpy
from mathutils import Vector


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(
    r"C:\Users\Windows User\Desktop\Project\nsakasa\nsakasa"
)

INPUT_JSON = (
    PROJECT_ROOT
    / "animation_work"
    / "mediapipe_output"
    / "ABOUT_mediapipe_landmarks.json"
)

LEFT_ARM_SUFFIX = "LeftArm"
LEFT_FOREARM_SUFFIX = "LeftForeArm"
LEFT_HAND_SUFFIX = "LeftHand"

RIGHT_ARM_SUFFIX = "RightArm"
RIGHT_FOREARM_SUFFIX = "RightForeArm"
RIGHT_HAND_SUFFIX = "RightHand"

# MediaPipe pose landmark indexes
LEFT_SHOULDER_INDEX = 11
RIGHT_SHOULDER_INDEX = 12
LEFT_ELBOW_INDEX = 13
RIGHT_ELBOW_INDEX = 14
LEFT_WRIST_INDEX = 15
RIGHT_WRIST_INDEX = 16

TARGET_COLLECTION_NAME = "NSA_IK_TARGETS"

# Axis tuning
DEPTH_SIGN = -1.0
VERTICAL_SIGN = 1.0
POLE_FORWARD_SIGN = -1.0

# Small smoothing
SMOOTHING_RADIUS = 2

# ------------------------------------------------------------
# TEMP HAND ROTATION FIX
# These are only temporary offsets until we drive the hand
# from real hand landmarks.
# ------------------------------------------------------------
LEFT_HAND_ROT_X = 0
LEFT_HAND_ROT_Y = 0
LEFT_HAND_ROT_Z = 0

RIGHT_HAND_ROT_X = 0
RIGHT_HAND_ROT_Y = 0
RIGHT_HAND_ROT_Z = 180
# If this still looks wrong later, we will try:
# RIGHT_HAND_ROT_X = 180
# or RIGHT_HAND_ROT_Y = 180


# ============================================================
# LANDMARK HELPERS
# ============================================================

def get_pose_world_point(frame_data, landmark_index):
    landmarks = frame_data.get("poseWorld", [])

    for point in landmarks:
        if point.get("index") == landmark_index:
            return point

    raise ValueError(
        f"Missing poseWorld landmark {landmark_index} "
        f"in frame {frame_data.get('frameIndex')}"
    )


def mediapipe_to_blender_vector(point):
    """
    MediaPipe world coordinates:
      x = horizontal
      y = vertical
      z = depth

    Blender coordinates used here:
      X = horizontal
      Y = depth
      Z = vertical
    """
    return Vector(
        (
            float(point["x"]),
            DEPTH_SIGN * float(point["z"]),
            VERTICAL_SIGN * float(point["y"]),
        )
    )


def average_vectors(vectors):
    total = Vector((0.0, 0.0, 0.0))

    for vector in vectors:
        total += vector

    return total / len(vectors)


def smooth_vectors(vectors, radius):
    if radius <= 0:
        return vectors

    smoothed = []

    for index in range(len(vectors)):
        start = max(0, index - radius)
        end = min(len(vectors), index + radius + 1)

        smoothed.append(average_vectors(vectors[start:end]))

    return smoothed


# ============================================================
# BLENDER OBJECT HELPERS
# ============================================================

def get_or_create_collection(name):
    collection = bpy.data.collections.get(name)

    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)

    return collection


def clear_collection_objects(collection):
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def create_empty(name, collection, display_type="SPHERE", size=0.12):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = display_type
    empty.empty_display_size = size
    collection.objects.link(empty)
    return empty


# ============================================================
# ARMATURE AND BONE HELPERS
# ============================================================

def find_bone_name_by_suffix(armature, required_suffix):
    for bone in armature.pose.bones:
        clean_name = bone.name.split(".")[0]
        if clean_name.endswith(required_suffix):
            return bone.name
    return None


def find_correct_armature():
    armature_candidates = [
        obj for obj in bpy.data.objects if obj.type == "ARMATURE"
    ]

    print("\nArmature objects found:")

    for obj in armature_candidates:
        print(f"- {obj.name}")

        left_arm_name = find_bone_name_by_suffix(obj, LEFT_ARM_SUFFIX)
        left_forearm_name = find_bone_name_by_suffix(obj, LEFT_FOREARM_SUFFIX)
        left_hand_name = find_bone_name_by_suffix(obj, LEFT_HAND_SUFFIX)

        right_arm_name = find_bone_name_by_suffix(obj, RIGHT_ARM_SUFFIX)
        right_forearm_name = find_bone_name_by_suffix(obj, RIGHT_FOREARM_SUFFIX)
        right_hand_name = find_bone_name_by_suffix(obj, RIGHT_HAND_SUFFIX)

        if all([
            left_arm_name,
            left_forearm_name,
            left_hand_name,
            right_arm_name,
            right_forearm_name,
            right_hand_name,
        ]):
            print(f"\nUsing armature: {obj.name}")
            print(f"Left arm: {left_arm_name}")
            print(f"Left forearm: {left_forearm_name}")
            print(f"Left hand: {left_hand_name}")
            print(f"Right arm: {right_arm_name}")
            print(f"Right forearm: {right_forearm_name}")
            print(f"Right hand: {right_hand_name}")

            return (
                obj,
                left_arm_name,
                left_forearm_name,
                left_hand_name,
                right_arm_name,
                right_forearm_name,
                right_hand_name,
            )

    raise KeyError(
        "Could not find an armature containing recognizable "
        "left/right arm, forearm, and hand bones."
    )


def require_pose_bone(armature, bone_name):
    bone = armature.pose.bones.get(bone_name)

    if bone is None:
        raise KeyError(f"Could not find pose bone: {bone_name}")

    return bone


def remove_old_nsa_constraints(pose_bone):
    for constraint in list(pose_bone.constraints):
        if constraint.name.startswith("NSA_"):
            pose_bone.constraints.remove(constraint)


def reset_pose(armature):
    for pose_bone in armature.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_mode = "QUATERNION"
        pose_bone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)


def add_ik_constraint(forearm_bone, wrist_target, elbow_pole, name):
    remove_old_nsa_constraints(forearm_bone)

    constraint = forearm_bone.constraints.new(type="IK")
    constraint.name = name
    constraint.target = wrist_target
    constraint.pole_target = elbow_pole
    constraint.chain_count = 2

    if hasattr(constraint, "use_stretch"):
        constraint.use_stretch = False

    return constraint


def apply_static_hand_rotation(hand_bone, x_deg, y_deg, z_deg):
    hand_bone.rotation_mode = "XYZ"
    hand_bone.rotation_euler = (
        radians(x_deg),
        radians(y_deg),
        radians(z_deg),
    )


# ============================================================
# MAIN
# ============================================================

def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(
            f"Could not find JSON file: {INPUT_JSON}"
        )

    (
        armature,
        left_arm_bone_name,
        left_forearm_bone_name,
        left_hand_bone_name,
        right_arm_bone_name,
        right_forearm_bone_name,
        right_hand_bone_name,
    ) = find_correct_armature()

    # Remove imported animation so it does not fight our IK test.
    if armature.animation_data:
        armature.animation_data_clear()

    reset_pose(armature)

    left_forearm = require_pose_bone(armature, left_forearm_bone_name)
    right_forearm = require_pose_bone(armature, right_forearm_bone_name)

    left_hand = require_pose_bone(armature, left_hand_bone_name)
    right_hand = require_pose_bone(armature, right_hand_bone_name)

    with open(INPUT_JSON, "r", encoding="utf-8") as file:
        data = json.load(file)

    frames = data["frames"]
    fps = int(round(float(data["video"]["fps"])))

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = len(frames)
    scene.render.fps = fps

    # Rest-pose shoulder positions
    avatar_left_shoulder = Vector(
        armature.data.bones[left_arm_bone_name].head_local
    )

    avatar_right_shoulder = Vector(
        armature.data.bones[right_arm_bone_name].head_local
    )

    avatar_shoulder_center = (
        avatar_left_shoulder + avatar_right_shoulder
    ) * 0.5

    avatar_shoulder_width = (
        avatar_left_shoulder - avatar_right_shoulder
    ).length

    # Estimate signer shoulder width
    signer_shoulder_widths = []

    for frame_data in frames:
        signer_left_shoulder = mediapipe_to_blender_vector(
            get_pose_world_point(frame_data, LEFT_SHOULDER_INDEX)
        )

        signer_right_shoulder = mediapipe_to_blender_vector(
            get_pose_world_point(frame_data, RIGHT_SHOULDER_INDEX)
        )

        signer_shoulder_widths.append(
            (signer_left_shoulder - signer_right_shoulder).length
        )

    signer_shoulder_width = (
        sum(signer_shoulder_widths) / len(signer_shoulder_widths)
    )

    if signer_shoulder_width <= 0:
        raise ValueError("Invalid signer shoulder width.")

    scale_factor = avatar_shoulder_width / signer_shoulder_width

    print(f"Avatar shoulder width: {avatar_shoulder_width:.4f}")
    print(f"Signer shoulder width: {signer_shoulder_width:.4f}")
    print(f"Scale factor: {scale_factor:.4f}")

    left_wrist_positions = []
    right_wrist_positions = []
    left_elbow_positions = []
    right_elbow_positions = []

    for frame_data in frames:
        signer_left_shoulder = mediapipe_to_blender_vector(
            get_pose_world_point(frame_data, LEFT_SHOULDER_INDEX)
        )

        signer_right_shoulder = mediapipe_to_blender_vector(
            get_pose_world_point(frame_data, RIGHT_SHOULDER_INDEX)
        )

        signer_shoulder_center = (
            signer_left_shoulder + signer_right_shoulder
        ) * 0.5

        def map_relative_to_avatar(point_index):
            source_point = mediapipe_to_blender_vector(
                get_pose_world_point(frame_data, point_index)
            )

            relative = source_point - signer_shoulder_center

            return avatar_shoulder_center + (relative * scale_factor)

        left_elbow_positions.append(map_relative_to_avatar(LEFT_ELBOW_INDEX))
        right_elbow_positions.append(map_relative_to_avatar(RIGHT_ELBOW_INDEX))
        left_wrist_positions.append(map_relative_to_avatar(LEFT_WRIST_INDEX))
        right_wrist_positions.append(map_relative_to_avatar(RIGHT_WRIST_INDEX))

    left_elbow_positions = smooth_vectors(left_elbow_positions, SMOOTHING_RADIUS)
    right_elbow_positions = smooth_vectors(right_elbow_positions, SMOOTHING_RADIUS)
    left_wrist_positions = smooth_vectors(left_wrist_positions, SMOOTHING_RADIUS)
    right_wrist_positions = smooth_vectors(right_wrist_positions, SMOOTHING_RADIUS)

    target_collection = get_or_create_collection(TARGET_COLLECTION_NAME)
    clear_collection_objects(target_collection)

    left_wrist_target = create_empty(
        "NSA_LeftWristTarget",
        target_collection,
        "SPHERE",
        0.12,
    )

    right_wrist_target = create_empty(
        "NSA_RightWristTarget",
        target_collection,
        "SPHERE",
        0.12,
    )

    left_elbow_pole = create_empty(
        "NSA_LeftElbowPole",
        target_collection,
        "CUBE",
        0.10,
    )

    right_elbow_pole = create_empty(
        "NSA_RightElbowPole",
        target_collection,
        "CUBE",
        0.10,
    )

    for target in [
        left_wrist_target,
        right_wrist_target,
        left_elbow_pole,
        right_elbow_pole,
    ]:
        target.parent = armature

    pole_offset = Vector(
        (
            0.0,
            POLE_FORWARD_SIGN * avatar_shoulder_width * 2.0,
            0.0,
        )
    )

    for index in range(len(frames)):
        blender_frame = index + 1
        scene.frame_set(blender_frame)

        left_wrist_target.location = left_wrist_positions[index]
        right_wrist_target.location = right_wrist_positions[index]

        left_elbow_pole.location = (
            left_elbow_positions[index] + pole_offset
        )

        right_elbow_pole.location = (
            right_elbow_positions[index] + pole_offset
        )

        left_wrist_target.keyframe_insert(
            data_path="location",
            frame=blender_frame,
        )

        right_wrist_target.keyframe_insert(
            data_path="location",
            frame=blender_frame,
        )

        left_elbow_pole.keyframe_insert(
            data_path="location",
            frame=blender_frame,
        )

        right_elbow_pole.keyframe_insert(
            data_path="location",
            frame=blender_frame,
        )

        # keep hand direction consistent for now
        apply_static_hand_rotation(
            left_hand,
            LEFT_HAND_ROT_X,
            LEFT_HAND_ROT_Y,
            LEFT_HAND_ROT_Z,
        )

        apply_static_hand_rotation(
            right_hand,
            RIGHT_HAND_ROT_X,
            RIGHT_HAND_ROT_Y,
            RIGHT_HAND_ROT_Z,
        )

        left_hand.keyframe_insert(
            data_path="rotation_euler",
            frame=blender_frame,
        )

        right_hand.keyframe_insert(
            data_path="rotation_euler",
            frame=blender_frame,
        )

    add_ik_constraint(
        left_forearm,
        left_wrist_target,
        left_elbow_pole,
        "NSA_LeftArmIK",
    )

    add_ik_constraint(
        right_forearm,
        right_wrist_target,
        right_elbow_pole,
        "NSA_RightArmIK",
    )

    scene.frame_set(1)

    print("\nDONE: ABOUT landmark motion connected to avatar arms.")
    print("Press Play on the Blender timeline.")
    print("Expected: upper arms and forearms move.")
    print("Temporary hand rotation offset is applied.")
    print("Real wrist/hand landmark rotation is not included yet.")


main()