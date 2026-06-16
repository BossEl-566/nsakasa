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
DEPTH_SIGN = 1.0

# MediaPipe Y increases downward, while Blender Z increases upward.
VERTICAL_SIGN = 1.0

POLE_FORWARD_SIGN = -1.0

# Reduce forward/backward motion so the avatar does not lean
# or stretch its arms too far toward the camera.
DEPTH_MOTION_SCALE = 0.25

# Use the first few frames as the relaxed calibration pose.
CALIBRATION_FRAMES = 5

# Small moving-average smoothing.
SMOOTHING_RADIUS = 2
# ------------------------------------------------------------
# IDLE POSE AND ELBOW-SPACING TUNING
# ------------------------------------------------------------

# ------------------------------------------------------------
# MANUALLY CALIBRATED IDLE POSE
# ------------------------------------------------------------
# These values were positioned manually in Blender.
# They are armature-local coordinates.

IDLE_HOLD_FRAMES = 12
IDLE_TRANSITION_FRAMES = 12
CALIBRATION_FRAMES = 5

MANUAL_IDLE_LEFT_WRIST = Vector(
    (35.636559, -68.657333, 34.475868)
)

MANUAL_IDLE_RIGHT_WRIST = Vector(
    (-41.415791, -164.087494, 74.855721)
)

MANUAL_IDLE_LEFT_ELBOW_POLE = Vector(
    (52.948975, 86.997810, -27.076185)
)

MANUAL_IDLE_RIGHT_ELBOW_POLE = Vector(
    (-52.945328, 86.997887, -27.975361)
)

# Begin with arms naturally lowered before moving into the sign.
IDLE_HOLD_FRAMES = 10
IDLE_TRANSITION_FRAMES = 12

# Push elbow pole targets outward so elbows do not enter the torso.
ELBOW_POLE_OUTWARD_RATIO = 0.75

# Keep the elbows bending in front of the body.
ELBOW_POLE_FORWARD_RATIO = 1.40

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
RIGHT_HAND_ROT_Z = 0
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

    Blender coordinates:
      X = horizontal
      Y = depth
      Z = vertical
    """

    return Vector(
        (
            float(point["x"]),
            DEPTH_SIGN
            * DEPTH_MOTION_SCALE
            * float(point["z"]),
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

def average_first_vectors(vectors, count):
    """
    Average the first few tracked frames.
    This becomes the source video's reference pose.
    """

    if not vectors:
        raise ValueError("Cannot average an empty vector list.")

    usable_count = min(count, len(vectors))

    return average_vectors(
        vectors[:usable_count]
    )


def apply_manual_baseline(
    tracked_positions,
    manual_idle_position,
    calibration_frames,
):
    """
    Preserve the tracked motion, but shift its baseline so that
    frame 1 begins from the manually calibrated avatar pose.
    """

    tracked_reference = average_first_vectors(
        tracked_positions,
        calibration_frames,
    )

    return [
        manual_idle_position
        + (position - tracked_reference)
        for position in tracked_positions
    ]


def prepend_idle_transition(
    positions,
    idle_position,
    hold_frames,
    transition_frames,
):
    """
    Hold the manual idle pose briefly, then smoothly transition
    into the extracted sign motion.
    """

    if not positions:
        return []

    result = []

    for _ in range(hold_frames):
        result.append(
            idle_position.copy()
        )

    first_motion_position = positions[0]

    for index in range(transition_frames):
        amount = (
            (index + 1)
            / transition_frames
        )

        result.append(
            idle_position.lerp(
                first_motion_position,
                amount,
            )
        )

    result.extend(positions)

    return result

def prepend_idle_transition(
    positions,
    idle_position,
    hold_frames,
    transition_frames,
):
    """
    Add an arms-down idle pose before the sign starts.

    First:
      hold the relaxed pose

    Then:
      smoothly blend into the first tracked sign pose
    """

    if not positions:
        return []

    result = []

    for _ in range(hold_frames):
        result.append(idle_position.copy())

    first_sign_position = positions[0]

    for index in range(transition_frames):
        amount = (index + 1) / transition_frames

        result.append(
            idle_position.lerp(
                first_sign_position,
                amount,
            )
        )

    result.extend(positions)

    return result


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


def add_ik_constraint(
    forearm_bone,
    wrist_target,
    elbow_pole,
    name,
    pole_angle_degrees=0,
):
    remove_old_nsa_constraints(forearm_bone)

    constraint = forearm_bone.constraints.new(type="IK")
    constraint.name = name
    constraint.target = wrist_target
    constraint.pole_target = elbow_pole

    # Upper arm + forearm.
    constraint.chain_count = 2

    # Correct the roll/twist direction of the arm chain.
    constraint.pole_angle = radians(pole_angle_degrees)

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

        # --------------------------------------------------------
    # CREATE A NATURAL ARMS-DOWN IDLE POSE
    # --------------------------------------------------------

    down_direction = Vector((0.0, 0.0, -1.0))

    left_outward_direction = (
        avatar_left_shoulder
        - avatar_shoulder_center
    ).normalized()

    right_outward_direction = (
        avatar_right_shoulder
        - avatar_shoulder_center
    ).normalized()

    avatar_left_upper_arm_length = (
        armature.data.bones[left_arm_bone_name].length
    )

    avatar_right_upper_arm_length = (
        armature.data.bones[right_arm_bone_name].length
    )

    avatar_left_forearm_length = (
        armature.data.bones[left_forearm_bone_name].length
    )

    avatar_right_forearm_length = (
        armature.data.bones[right_forearm_bone_name].length
    )

    # Lower the elbows beside the torso.
    idle_left_elbow_position = (
        avatar_left_shoulder
        + left_outward_direction
        * avatar_left_upper_arm_length
        * 0.12
        + down_direction
        * avatar_left_upper_arm_length
        * 0.92
    )

    idle_right_elbow_position = (
        avatar_right_shoulder
        + right_outward_direction
        * avatar_right_upper_arm_length
        * 0.12
        + down_direction
        * avatar_right_upper_arm_length
        * 0.92
    )

    # Place the wrists lower beside the avatar's body.
    idle_left_wrist_position = (
        idle_left_elbow_position
        + left_outward_direction
        * avatar_left_forearm_length
        * 0.08
        + down_direction
        * avatar_left_forearm_length
        * 0.95
    )

    idle_right_wrist_position = (
        idle_right_elbow_position
        + right_outward_direction
        * avatar_right_forearm_length
        * 0.08
        + down_direction
        * avatar_right_forearm_length
        * 0.95
    )

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

    # --------------------------------------------------------
    # AVATAR ARM LENGTHS
    # --------------------------------------------------------
    # The avatar FBX is in a T-pose, but we do not use that
    # pose as the animation baseline.
    #
    # Instead, we use the avatar's arm lengths and reconstruct
    # the arm pose from the signer's tracked directions:
    #
    # shoulder -> elbow -> wrist
    # --------------------------------------------------------

    avatar_left_upper_arm_length = (
        armature.data.bones[left_arm_bone_name].length
    )

    avatar_left_forearm_length = (
        armature.data.bones[left_forearm_bone_name].length
    )

    avatar_right_upper_arm_length = (
        armature.data.bones[right_arm_bone_name].length
    )

    avatar_right_forearm_length = (
        armature.data.bones[right_forearm_bone_name].length
    )

    avatar_left_shoulder_position = Vector(
        armature.data.bones[left_arm_bone_name].head_local
    )

    avatar_right_shoulder_position = Vector(
        armature.data.bones[right_arm_bone_name].head_local
    )

    def safe_normalized(vector, fallback):
        if vector.length < 0.000001:
            return fallback.copy()

        return vector.normalized()

    # Fallback directions only apply if MediaPipe produces
    # an invalid frame.
    fallback_left_upper_direction = Vector(
        (-0.15, 0.0, -1.0)
    ).normalized()

    fallback_right_upper_direction = Vector(
        (0.15, 0.0, -1.0)
    ).normalized()

    fallback_left_forearm_direction = Vector(
        (-0.05, 0.0, -1.0)
    ).normalized()

    fallback_right_forearm_direction = Vector(
        (0.05, 0.0, -1.0)
    ).normalized()

    for frame_data in frames:
        signer_left_shoulder = mediapipe_to_blender_vector(
            get_pose_world_point(
                frame_data,
                LEFT_SHOULDER_INDEX,
            )
        )

        signer_right_shoulder = mediapipe_to_blender_vector(
            get_pose_world_point(
                frame_data,
                RIGHT_SHOULDER_INDEX,
            )
        )

        signer_left_elbow = mediapipe_to_blender_vector(
            get_pose_world_point(
                frame_data,
                LEFT_ELBOW_INDEX,
            )
        )

        signer_right_elbow = mediapipe_to_blender_vector(
            get_pose_world_point(
                frame_data,
                RIGHT_ELBOW_INDEX,
            )
        )

        signer_left_wrist = mediapipe_to_blender_vector(
            get_pose_world_point(
                frame_data,
                LEFT_WRIST_INDEX,
            )
        )

        signer_right_wrist = mediapipe_to_blender_vector(
            get_pose_world_point(
                frame_data,
                RIGHT_WRIST_INDEX,
            )
        )

        left_upper_direction = safe_normalized(
            signer_left_elbow - signer_left_shoulder,
            fallback_left_upper_direction,
        )

        right_upper_direction = safe_normalized(
            signer_right_elbow - signer_right_shoulder,
            fallback_right_upper_direction,
        )

        left_forearm_direction = safe_normalized(
            signer_left_wrist - signer_left_elbow,
            fallback_left_forearm_direction,
        )

        right_forearm_direction = safe_normalized(
            signer_right_wrist - signer_right_elbow,
            fallback_right_forearm_direction,
        )

        avatar_left_elbow_position = (
            avatar_left_shoulder_position
            + left_upper_direction
            * avatar_left_upper_arm_length
        )

        avatar_right_elbow_position = (
            avatar_right_shoulder_position
            + right_upper_direction
            * avatar_right_upper_arm_length
        )

        avatar_left_wrist_position = (
            avatar_left_elbow_position
            + left_forearm_direction
            * avatar_left_forearm_length
        )

        avatar_right_wrist_position = (
            avatar_right_elbow_position
            + right_forearm_direction
            * avatar_right_forearm_length
        )

        left_elbow_positions.append(
            avatar_left_elbow_position
        )

        right_elbow_positions.append(
            avatar_right_elbow_position
        )

        left_wrist_positions.append(
            avatar_left_wrist_position
        )

        right_wrist_positions.append(
            avatar_right_wrist_position
        )
    left_elbow_positions = smooth_vectors(left_elbow_positions, SMOOTHING_RADIUS)
    right_elbow_positions = smooth_vectors(right_elbow_positions, SMOOTHING_RADIUS)
    left_wrist_positions = smooth_vectors(left_wrist_positions, SMOOTHING_RADIUS)
    right_wrist_positions = smooth_vectors(right_wrist_positions, SMOOTHING_RADIUS)

        # --------------------------------------------------------
    # ADD IDLE POSE BEFORE THE SIGN MOTION
    # --------------------------------------------------------

    left_elbow_positions = prepend_idle_transition(
        left_elbow_positions,
        idle_left_elbow_position,
        IDLE_HOLD_FRAMES,
        IDLE_TRANSITION_FRAMES,
    )

    right_elbow_positions = prepend_idle_transition(
        right_elbow_positions,
        idle_right_elbow_position,
        IDLE_HOLD_FRAMES,
        IDLE_TRANSITION_FRAMES,
    )

    left_wrist_positions = prepend_idle_transition(
        left_wrist_positions,
        idle_left_wrist_position,
        IDLE_HOLD_FRAMES,
        IDLE_TRANSITION_FRAMES,
    )

    right_wrist_positions = prepend_idle_transition(
        right_wrist_positions,
        idle_right_wrist_position,
        IDLE_HOLD_FRAMES,
        IDLE_TRANSITION_FRAMES,
    )

    animation_frame_count = len(
        left_wrist_positions
    )

    scene.frame_end = animation_frame_count

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

        # --------------------------------------------------------
    # PUSH ELBOWS OUTWARD AND FORWARD
    # --------------------------------------------------------

        # --------------------------------------------------------
    # USE THE MANUALLY CALIBRATED IDLE POSE AS THE BASELINE
    # --------------------------------------------------------
    #
    # Wrist targets:
    #   manual idle position + tracked wrist movement delta
    #
    # Elbow poles:
    #   manual idle pole position + tracked elbow movement delta
    #
    # This avoids guessing the avatar's front/back orientation.

    left_wrist_positions = apply_manual_baseline(
        left_wrist_positions,
        MANUAL_IDLE_LEFT_WRIST,
        CALIBRATION_FRAMES,
    )

    right_wrist_positions = apply_manual_baseline(
        right_wrist_positions,
        MANUAL_IDLE_RIGHT_WRIST,
        CALIBRATION_FRAMES,
    )

    left_elbow_pole_positions = apply_manual_baseline(
        left_elbow_positions,
        MANUAL_IDLE_LEFT_ELBOW_POLE,
        CALIBRATION_FRAMES,
    )

    right_elbow_pole_positions = apply_manual_baseline(
        right_elbow_positions,
        MANUAL_IDLE_RIGHT_ELBOW_POLE,
        CALIBRATION_FRAMES,
    )

    # --------------------------------------------------------
    # ADD A SHORT IDLE HOLD BEFORE THE SIGN STARTS
    # --------------------------------------------------------

    left_wrist_positions = prepend_idle_transition(
        left_wrist_positions,
        MANUAL_IDLE_LEFT_WRIST,
        IDLE_HOLD_FRAMES,
        IDLE_TRANSITION_FRAMES,
    )

    right_wrist_positions = prepend_idle_transition(
        right_wrist_positions,
        MANUAL_IDLE_RIGHT_WRIST,
        IDLE_HOLD_FRAMES,
        IDLE_TRANSITION_FRAMES,
    )

    left_elbow_pole_positions = prepend_idle_transition(
        left_elbow_pole_positions,
        MANUAL_IDLE_LEFT_ELBOW_POLE,
        IDLE_HOLD_FRAMES,
        IDLE_TRANSITION_FRAMES,
    )

    right_elbow_pole_positions = prepend_idle_transition(
        right_elbow_pole_positions,
        MANUAL_IDLE_RIGHT_ELBOW_POLE,
        IDLE_HOLD_FRAMES,
        IDLE_TRANSITION_FRAMES,
    )

    animation_frame_count = len(
        left_wrist_positions
    )

    scene.frame_end = animation_frame_count

    # --------------------------------------------------------
    # INSERT IK TARGET KEYFRAMES
    # --------------------------------------------------------

    for index in range(animation_frame_count):
        blender_frame = index + 1
        scene.frame_set(blender_frame)

        left_wrist_target.location = (
            left_wrist_positions[index]
        )

        right_wrist_target.location = (
            right_wrist_positions[index]
        )

        left_elbow_pole.location = (
            left_elbow_pole_positions[index]
        )

        right_elbow_pole.location = (
            right_elbow_pole_positions[index]
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

        # Keep the current neutral wrist settings for now.
        # Real wrist direction will be added later using
        # the MediaPipe hand landmarks.
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
    pole_angle_degrees=0,
)

    add_ik_constraint(
        right_forearm,
        right_wrist_target,
        right_elbow_pole,
        "NSA_RightArmIK",
        pole_angle_degrees=180,
    )

    scene.frame_set(1)

    print("\nDONE: ABOUT landmark motion connected to avatar arms.")
    print("Press Play on the Blender timeline.")
    print("Expected: upper arms and forearms move.")
    print("Temporary hand rotation offset is applied.")
    print("Real wrist/hand landmark rotation is not included yet.")


main()