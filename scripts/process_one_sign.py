import json
import shutil
from pathlib import Path


RAW_DATASET_PATH = Path("data/raw/GSL_openpose_data")
PROCESSED_DATASET_PATH = Path("data/processed")

SIGN_NAME = "ABOUT"


def get_frame_number(file_path: Path) -> int:
    """
    Extracts frame number from filename like:
    ABOUT_000000000000_keypoints.json
    """
    parts = file_path.stem.split("_")

    for part in parts:
        if part.isdigit():
            return int(part)

    return 0


def convert_keypoints(flat_keypoints):
    """
    Converts OpenPose flat array:
    [x, y, confidence, x, y, confidence, ...]

    Into cleaner objects:
    [
      { "x": 473.871, "y": 131.476, "confidence": 0.903182 },
      ...
    ]
    """
    points = []

    for i in range(0, len(flat_keypoints), 3):
        points.append({
            "x": flat_keypoints[i],
            "y": flat_keypoints[i + 1],
            "confidence": flat_keypoints[i + 2],
        })

    return points


def process_one_sign(sign_name: str):
    sign_folder = RAW_DATASET_PATH / sign_name

    if not sign_folder.exists():
        print(f"Sign folder not found: {sign_folder}")
        return

    output_folder = PROCESSED_DATASET_PATH / sign_name
    output_folder.mkdir(parents=True, exist_ok=True)

    json_files = sorted(
        sign_folder.glob("*_keypoints.json"),
        key=get_frame_number
    )

    video_files = sorted(sign_folder.glob("*.mp4"))

    frames = []
    detected_frames = 0

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        people = data.get("people", [])

        if people:
            detected_frames += 1
            person = people[0]

            frame_data = {
                "frameNumber": get_frame_number(json_file),
                "sourceFile": json_file.name,
                "detected": True,
                "body": convert_keypoints(person.get("pose_keypoints_2d", [])),
                "leftHand": convert_keypoints(person.get("hand_left_keypoints_2d", [])),
                "rightHand": convert_keypoints(person.get("hand_right_keypoints_2d", [])),
                "face": convert_keypoints(person.get("face_keypoints_2d", [])),
            }
        else:
            frame_data = {
                "frameNumber": get_frame_number(json_file),
                "sourceFile": json_file.name,
                "detected": False,
                "body": [],
                "leftHand": [],
                "rightHand": [],
                "face": [],
            }

        frames.append(frame_data)

    pose_sequence = {
        "gloss": sign_name.upper(),
        "english": sign_name.lower().replace("_", " "),
        "totalFrames": len(frames),
        "detectedFrames": detected_frames,
        "missingDetectionFrames": len(frames) - detected_frames,
        "frames": frames,
    }

    pose_output_path = output_folder / f"{sign_name}_pose_sequence.json"

    with open(pose_output_path, "w", encoding="utf-8") as file:
        json.dump(pose_sequence, file, indent=2)

    video_file_name = None

    if video_files:
        video_file = video_files[0]
        video_file_name = video_file.name

        shutil.copy(
            video_file,
            output_folder / video_file.name
        )

    metadata = {
        "gloss": sign_name.upper(),
        "english": sign_name.lower().replace("_", " "),
        "sourceFolder": str(sign_folder),
        "videoFile": video_file_name,
        "poseSequenceFile": pose_output_path.name,
        "totalFrames": len(frames),
        "detectedFrames": detected_frames,
        "missingDetectionFrames": len(frames) - detected_frames,
        "bodyPointsPerFrame": 25,
        "handPointsPerFrame": 21,
        "facePointsAvailable": False,
        "status": "processed",
    }

    metadata_output_path = output_folder / "metadata.json"

    with open(metadata_output_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    print(f"Processed sign: {sign_name}")
    print(f"Total frames: {len(frames)}")
    print(f"Detected frames: {detected_frames}")
    print(f"Missing detection frames: {len(frames) - detected_frames}")
    print(f"Output folder: {output_folder}")
    print(f"Created: {pose_output_path}")
    print(f"Created: {metadata_output_path}")


if __name__ == "__main__":
    process_one_sign(SIGN_NAME)