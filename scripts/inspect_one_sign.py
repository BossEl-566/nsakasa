import json
from pathlib import Path

DATASET_PATH = Path("data/raw/GSL_openpose_data")

SIGN_NAME = "ABOUT"

sign_folder = DATASET_PATH / SIGN_NAME

if not sign_folder.exists():
    print(f"Sign folder not found: {sign_folder}")
    exit()

json_files = sorted(sign_folder.glob("*_keypoints.json"))
video_files = sorted(sign_folder.glob("*.mp4"))

print("Sign:", SIGN_NAME)
print("Folder:", sign_folder)
print("Number of JSON keypoint files:", len(json_files))
print("Number of video files:", len(video_files))

if video_files:
    print("Video file:", video_files[0].name)

if not json_files:
    print("No JSON files found.")
    exit()

first_json = json_files[0]

print("\nReading first JSON file:")
print(first_json.name)

with open(first_json, "r", encoding="utf-8") as file:
    data = json.load(file)

people = data.get("people", [])

print("OpenPose version:", data.get("version"))
print("People detected:", len(people))

if not people:
    print("No person detected in this frame.")
    exit()

person = people[0]

pose = person.get("pose_keypoints_2d", [])
left_hand = person.get("hand_left_keypoints_2d", [])
right_hand = person.get("hand_right_keypoints_2d", [])
face = person.get("face_keypoints_2d", [])

print("\nKeypoint sizes:")
print("Body pose values:", len(pose))
print("Left hand values:", len(left_hand))
print("Right hand values:", len(right_hand))
print("Face values:", len(face))

print("\nInterpreted counts:")
print("Body pose points:", len(pose) // 3)
print("Left hand points:", len(left_hand) // 3)
print("Right hand points:", len(right_hand) // 3)
print("Face points:", len(face) // 3)