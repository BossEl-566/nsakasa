import argparse
import json
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


def safe_float(value, default=None):
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def landmark_to_dict(landmark, index: int):
    data = {
        "index": index,
        "x": safe_float(landmark.x, 0.0),
        "y": safe_float(landmark.y, 0.0),
        "z": safe_float(landmark.z, 0.0),
    }

    visibility = getattr(landmark, "visibility", None)
    presence = getattr(landmark, "presence", None)

    if visibility is not None:
        data["visibility"] = safe_float(visibility)

    if presence is not None:
        data["presence"] = safe_float(presence)

    return data


def landmarks_to_dict_list(landmarks):
    if not landmarks:
        return []

    return [
        landmark_to_dict(landmark, index)
        for index, landmark in enumerate(landmarks)
    ]


def draw_pose_landmarks(frame, pose_landmarks):
    if not pose_landmarks:
        return

    height, width = frame.shape[:2]

    # Draw points.
    for landmark in pose_landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)


def draw_hand_landmarks(frame, hand_landmarks):
    if not hand_landmarks:
        return

    height, width = frame.shape[:2]

    # Basic MediaPipe hand connections.
    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20),
        (5, 9), (9, 13), (13, 17),
    ]

    points = []

    for landmark in hand_landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))
        cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

    for start, end in connections:
        if start < len(points) and end < len(points):
            cv2.line(frame, points[start], points[end], (0, 255, 0), 2)


def draw_face_landmarks(frame, face_landmarks):
    if not face_landmarks:
        return

    height, width = frame.shape[:2]

    # Drawing all 478 points is heavy, so draw every 8th point for preview.
    for index, landmark in enumerate(face_landmarks):
        if index % 8 != 0:
            continue

        x = int(landmark.x * width)
        y = int(landmark.y * height)
        cv2.circle(frame, (x, y), 1, (255, 0, 255), -1)


def create_pose_landmarker(model_path: Path):
    base_options = python.BaseOptions(model_asset_path=str(model_path))

    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    return vision.PoseLandmarker.create_from_options(options)


def create_hand_landmarker(model_path: Path):
    base_options = python.BaseOptions(model_asset_path=str(model_path))

    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    return vision.HandLandmarker.create_from_options(options)


def create_face_landmarker(model_path: Path):
    base_options = python.BaseOptions(model_asset_path=str(model_path))

    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    return vision.FaceLandmarker.create_from_options(options)


def get_hand_side(handedness_item):
    if not handedness_item:
        return "unknown"

    # MediaPipe returns categories like Left / Right.
    best_category = handedness_item[0]
    return best_category.category_name.lower()


def blendshapes_to_dict(face_blendshapes):
    if not face_blendshapes:
        return {}

    blendshape_dict = {}

    for category in face_blendshapes[0]:
        blendshape_dict[category.category_name] = float(category.score)

    return blendshape_dict


def process_video(
    input_path: Path,
    sign_name: str,
    output_json_path: Path,
    output_preview_path: Path,
    pose_model_path: Path,
    hand_model_path: Path,
    face_model_path: Path,
):
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    for model_path in [pose_model_path, hand_model_path, face_model_path]:
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_preview_path.parent.mkdir(parents=True, exist_ok=True)

    video = cv2.VideoCapture(str(input_path))

    if not video.isOpened():
        raise RuntimeError(f"Could not open input video: {input_path}")

    fps = video.get(cv2.CAP_PROP_FPS) or 30
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    preview_writer = cv2.VideoWriter(
        str(output_preview_path),
        fourcc,
        fps,
        (width, height),
    )

    frames = []

    pose_detected_count = 0
    left_hand_detected_count = 0
    right_hand_detected_count = 0
    face_detected_count = 0

    print("Creating MediaPipe landmarkers...")

    with create_pose_landmarker(pose_model_path) as pose_landmarker, \
         create_hand_landmarker(hand_model_path) as hand_landmarker, \
         create_face_landmarker(face_model_path) as face_landmarker:

        frame_index = 0

        while True:
            success, frame_bgr = video.read()

            if not success:
                break

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

            timestamp_ms = int((frame_index / fps) * 1000)

            pose_result = pose_landmarker.detect_for_video(
                mp_image,
                timestamp_ms,
            )

            hand_result = hand_landmarker.detect_for_video(
                mp_image,
                timestamp_ms,
            )

            face_result = face_landmarker.detect_for_video(
                mp_image,
                timestamp_ms,
            )

            pose_landmarks = (
                pose_result.pose_landmarks[0]
                if pose_result.pose_landmarks
                else []
            )

            pose_world_landmarks = (
                pose_result.pose_world_landmarks[0]
                if pose_result.pose_world_landmarks
                else []
            )

            left_hand = []
            right_hand = []
            unknown_hands = []

            if hand_result.hand_landmarks:
                for hand_index, hand_landmarks in enumerate(hand_result.hand_landmarks):
                    handedness = (
                        hand_result.handedness[hand_index]
                        if hand_result.handedness
                        and hand_index < len(hand_result.handedness)
                        else []
                    )

                    side = get_hand_side(handedness)

                    if side == "left":
                        left_hand = hand_landmarks
                    elif side == "right":
                        right_hand = hand_landmarks
                    else:
                        unknown_hands.append(hand_landmarks)

            face_landmarks = (
                face_result.face_landmarks[0]
                if face_result.face_landmarks
                else []
            )

            face_blendshapes = blendshapes_to_dict(face_result.face_blendshapes)

            if pose_landmarks:
                pose_detected_count += 1

            if left_hand:
                left_hand_detected_count += 1

            if right_hand:
                right_hand_detected_count += 1

            if face_landmarks:
                face_detected_count += 1

            preview_frame = frame_bgr.copy()

            draw_pose_landmarks(preview_frame, pose_landmarks)
            draw_hand_landmarks(preview_frame, left_hand)
            draw_hand_landmarks(preview_frame, right_hand)
            draw_face_landmarks(preview_frame, face_landmarks)

            preview_writer.write(preview_frame)

            frame_data = {
                "frameIndex": frame_index,
                "timeSeconds": frame_index / fps,
                "timestampMs": timestamp_ms,
                "pose": landmarks_to_dict_list(pose_landmarks),
                "poseWorld": landmarks_to_dict_list(pose_world_landmarks),
                "leftHand": landmarks_to_dict_list(left_hand),
                "rightHand": landmarks_to_dict_list(right_hand),
                "unknownHands": [
                    landmarks_to_dict_list(hand_landmarks)
                    for hand_landmarks in unknown_hands
                ],
                "face": landmarks_to_dict_list(face_landmarks),
                "faceBlendshapes": face_blendshapes,
                "detections": {
                    "pose": bool(pose_landmarks),
                    "leftHand": bool(left_hand),
                    "rightHand": bool(right_hand),
                    "face": bool(face_landmarks),
                },
            }

            frames.append(frame_data)

            frame_index += 1

            if frame_index % 30 == 0:
                print(f"Processed {frame_index}/{total_frames} frames...")

    video.release()
    preview_writer.release()

    output_data = {
        "sign": sign_name,
        "sourceVideo": str(input_path),
        "video": {
            "fps": fps,
            "width": width,
            "height": height,
            "totalFramesFromVideo": total_frames,
            "processedFrames": len(frames),
        },
        "modelFiles": {
            "pose": str(pose_model_path),
            "hand": str(hand_model_path),
            "face": str(face_model_path),
        },
        "landmarkInfo": {
            "posePoints": 33,
            "handPointsPerHand": 21,
            "facePoints": 478,
        },
        "detectionSummary": {
            "poseDetectedFrames": pose_detected_count,
            "leftHandDetectedFrames": left_hand_detected_count,
            "rightHandDetectedFrames": right_hand_detected_count,
            "faceDetectedFrames": face_detected_count,
        },
        "frames": frames,
    }

    with open(output_json_path, "w", encoding="utf-8") as file:
        json.dump(output_data, file, indent=2)

    print("\nDone.")
    print(f"Input video: {input_path}")
    print(f"Output JSON: {output_json_path}")
    print(f"Preview video: {output_preview_path}")
    print(f"Processed frames: {len(frames)}")
    print("\nDetection summary:")
    print(f"Pose frames: {pose_detected_count}/{len(frames)}")
    print(f"Left hand frames: {left_hand_detected_count}/{len(frames)}")
    print(f"Right hand frames: {right_hand_detected_count}/{len(frames)}")
    print(f"Face frames: {face_detected_count}/{len(frames)}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True, help="Path to input video")
    parser.add_argument("--sign", required=True, help="Sign gloss/name")
    parser.add_argument(
        "--output-dir",
        default="animation_work/mediapipe_output",
        help="Output folder",
    )
    parser.add_argument(
        "--models-dir",
        default="animation_work/models",
        help="Folder containing MediaPipe .task files",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    models_dir = Path(args.models_dir)

    safe_sign_name = args.sign.upper().replace(" ", "_")

    output_json_path = output_dir / f"{safe_sign_name}_mediapipe_landmarks.json"
    output_preview_path = output_dir / f"{safe_sign_name}_mediapipe_preview.mp4"

    pose_model_path = models_dir / "pose_landmarker.task"
    hand_model_path = models_dir / "hand_landmarker.task"
    face_model_path = models_dir / "face_landmarker.task"

    process_video(
        input_path=input_path,
        sign_name=safe_sign_name,
        output_json_path=output_json_path,
        output_preview_path=output_preview_path,
        pose_model_path=pose_model_path,
        hand_model_path=hand_model_path,
        face_model_path=face_model_path,
    )


if __name__ == "__main__":
    main()