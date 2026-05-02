import json
from pathlib import Path
from label_cleaner import clean_label


RAW_DATASET_PATH = Path("data/raw/GSL_openpose_data")
PROCESSED_DATASET_PATH = Path("data/processed")

# Keep this false for now so we do not duplicate all videos and waste space.
COPY_VIDEOS = False


def get_frame_number(file_path: Path) -> int:
    parts = file_path.stem.split("_")

    for part in parts:
        if part.isdigit():
            return int(part)

    return 0


def convert_keypoints(flat_keypoints):
    points = []

    for i in range(0, len(flat_keypoints), 3):
        points.append({
            "x": flat_keypoints[i],
            "y": flat_keypoints[i + 1],
            "confidence": flat_keypoints[i + 2],
        })

    return points


def process_sign_folder(sign_folder: Path):
    sign_name = sign_folder.name
    cleaned_label = clean_label(sign_name)

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

    video_file_name = video_files[0].name if video_files else None

    pose_sequence_file_name = f"{sign_name}_pose_sequence.json"

    pose_sequence = {
        "gloss": sign_name.upper(),
        "english": sign_name.lower().replace("_", " "),
        "totalFrames": len(frames),
        "detectedFrames": detected_frames,
        "missingDetectionFrames": len(frames) - detected_frames,
        "frames": frames,
    }

    with open(output_folder / pose_sequence_file_name, "w", encoding="utf-8") as file:
        json.dump(pose_sequence, file, indent=2)

    metadata = {
        "gloss": sign_name.upper(),
        "displayName": cleaned_label["displayName"],
        "aliases": cleaned_label["aliases"],
        "baseWord": cleaned_label["baseWord"],
        "variant": cleaned_label["variant"],
        "english": sign_name.lower().replace("_", " "),
        "sourceFolder": str(sign_folder),
        "videoFile": video_file_name,
        "videoRawPath": str(sign_folder / video_file_name) if video_file_name else None,
        "poseSequenceFile": pose_sequence_file_name,
        "totalFrames": len(frames),
        "detectedFrames": detected_frames,
        "missingDetectionFrames": len(frames) - detected_frames,
        "bodyPointsPerFrame": 25,
        "handPointsPerFrame": 21,
        "facePointsAvailable": False,
        "status": "processed",
    }

    with open(output_folder / "metadata.json", "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    return metadata


def main():
    if not RAW_DATASET_PATH.exists():
        print(f"Raw dataset folder not found: {RAW_DATASET_PATH}")
        return

    PROCESSED_DATASET_PATH.mkdir(parents=True, exist_ok=True)

    sign_folders = [
        folder for folder in RAW_DATASET_PATH.iterdir()
        if folder.is_dir()
    ]

    print(f"Found {len(sign_folders)} sign folders.")
    print("Processing signs...\n")

    summary = []

    for index, sign_folder in enumerate(sign_folders, start=1):
        try:
            metadata = process_sign_folder(sign_folder)
            summary.append(metadata)

            print(
                f"{index}. {metadata['gloss']} - "
                f"{metadata['totalFrames']} frames, "
                f"{metadata['missingDetectionFrames']} missing"
            )

        except Exception as error:
            print(f"{index}. Failed to process {sign_folder.name}: {error}")

    summary_path = PROCESSED_DATASET_PATH / "dataset_summary.json"

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print("\nProcessing complete.")
    print(f"Processed signs: {len(summary)}")
    print(f"Summary created: {summary_path}")


if __name__ == "__main__":
    main()