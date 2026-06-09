import json
from pathlib import Path

import bpy


# =========================
# CONFIG
# =========================

PROJECT_ROOT = Path(r"C:\Users\Windows User\Desktop\Project\nsakasa\nsakasa")

INPUT_JSON = PROJECT_ROOT / "animation_work" / "mediapipe_output" / "THANK_YOU_mediapipe_landmarks.json"

SCALE = 6.0
DEPTH_SCALE = 2.0

POSE_POINT_SIZE = 0.055
HAND_POINT_SIZE = 0.04

FRAME_STEP = 1


# =========================
# HELPERS
# =========================

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def mp_to_blender(point):
    """
    MediaPipe:
      x = left/right normalized image coordinate
      y = top/bottom normalized image coordinate
      z = relative depth

    Blender:
      X = left/right
      Y = depth
      Z = up/down
    """
    x = (point["x"] - 0.5) * SCALE
    y = -point["z"] * DEPTH_SCALE
    z = (0.5 - point["y"]) * SCALE
    return (x, y, z)


def create_sphere(name, radius, color):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=radius)
    obj = bpy.context.object
    obj.name = name

    mat = bpy.data.materials.new(name + "_mat")
    mat.diffuse_color = color
    obj.data.materials.append(mat)

    return obj


def make_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj, collection):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)


def get_landmark(frame_data, group_name, index):
    group = frame_data.get(group_name, [])

    if index >= len(group):
        return None

    return group[index]


# =========================
# MAIN
# =========================

def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"Could not find JSON file: {INPUT_JSON}")

    clear_scene()

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    frames = data["frames"]
    fps = data["video"]["fps"]

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = len(frames)
    bpy.context.scene.render.fps = int(fps)

    pose_collection = make_collection("Pose Landmarks")
    left_hand_collection = make_collection("Left Hand Landmarks")
    right_hand_collection = make_collection("Right Hand Landmarks")

    pose_objects = []
    left_hand_objects = []
    right_hand_objects = []

    # Create pose landmark dots.
    for index in range(33):
        obj = create_sphere(
            name=f"pose_{index}",
            radius=POSE_POINT_SIZE,
            color=(1.0, 0.85, 0.1, 1.0),
        )
        move_to_collection(obj, pose_collection)
        pose_objects.append(obj)

    # Create left hand landmark dots.
    for index in range(21):
        obj = create_sphere(
            name=f"left_hand_{index}",
            radius=HAND_POINT_SIZE,
            color=(0.1, 1.0, 0.2, 1.0),
        )
        move_to_collection(obj, left_hand_collection)
        left_hand_objects.append(obj)

    # Create right hand landmark dots.
    for index in range(21):
        obj = create_sphere(
            name=f"right_hand_{index}",
            radius=HAND_POINT_SIZE,
            color=(0.2, 0.6, 1.0, 1.0),
        )
        move_to_collection(obj, right_hand_collection)
        right_hand_objects.append(obj)

    # Animate all dots.
    for frame_index, frame_data in enumerate(frames):
        blender_frame = frame_index + 1
        bpy.context.scene.frame_set(blender_frame)

        # Pose points
        for index, obj in enumerate(pose_objects):
            landmark = get_landmark(frame_data, "pose", index)

            if landmark:
                obj.location = mp_to_blender(landmark)
                obj.scale = (1, 1, 1)
            else:
                obj.scale = (0, 0, 0)

            obj.keyframe_insert(data_path="location", frame=blender_frame)
            obj.keyframe_insert(data_path="scale", frame=blender_frame)

        # Left hand points
        for index, obj in enumerate(left_hand_objects):
            landmark = get_landmark(frame_data, "leftHand", index)

            if landmark:
                obj.location = mp_to_blender(landmark)
                obj.scale = (1, 1, 1)
            else:
                obj.scale = (0, 0, 0)

            obj.keyframe_insert(data_path="location", frame=blender_frame)
            obj.keyframe_insert(data_path="scale", frame=blender_frame)

        # Right hand points
        for index, obj in enumerate(right_hand_objects):
            landmark = get_landmark(frame_data, "rightHand", index)

            if landmark:
                obj.location = mp_to_blender(landmark)
                obj.scale = (1, 1, 1)
            else:
                obj.scale = (0, 0, 0)

            obj.keyframe_insert(data_path="location", frame=blender_frame)
            obj.keyframe_insert(data_path="scale", frame=blender_frame)

    # Add camera.
    bpy.ops.object.light_add(type="AREA", location=(0, -4, 5))
    light = bpy.context.object
    light.name = "Main Area Light"
    light.data.energy = 500
    light.data.size = 5

    bpy.ops.object.camera_add(location=(0, -8, 2.5), rotation=(1.25, 0, 0))
    bpy.context.scene.camera = bpy.context.object

    # Set view frame to start.
    bpy.context.scene.frame_set(1)

    print("DONE: ABOUT MediaPipe landmarks imported into Blender.")
    print(f"Frames imported: {len(frames)}")
    print(f"FPS: {fps}")
    print("Yellow = body pose")
    print("Green = left hand")
    print("Blue = right hand")


main()