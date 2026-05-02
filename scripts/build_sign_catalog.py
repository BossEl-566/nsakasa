import json
from pathlib import Path


PROCESSED_DATASET_PATH = Path("data/processed")
CATALOG_OUTPUT_PATH = PROCESSED_DATASET_PATH / "sign_catalog.json"


def main():
    if not PROCESSED_DATASET_PATH.exists():
        print(f"Processed dataset folder not found: {PROCESSED_DATASET_PATH}")
        return

    catalog = []

    sign_folders = [
        folder for folder in PROCESSED_DATASET_PATH.iterdir()
        if folder.is_dir()
    ]

    for sign_folder in sign_folders:
        metadata_path = sign_folder / "metadata.json"

        if not metadata_path.exists():
            print(f"Skipping {sign_folder.name}: metadata.json not found")
            continue

        with open(metadata_path, "r", encoding="utf-8") as file:
            metadata = json.load(file)

        catalog_item = {
            "gloss": metadata["gloss"],
            "displayName": metadata["displayName"],
            "english": metadata["english"],
            "aliases": metadata["aliases"],
            "baseWord": metadata["baseWord"],
            "variant": metadata["variant"],
            "videoFile": metadata["videoFile"],
            "videoRawPath": metadata["videoRawPath"],
            "poseSequenceFile": metadata["poseSequenceFile"],
            "totalFrames": metadata["totalFrames"],
            "detectedFrames": metadata["detectedFrames"],
            "missingDetectionFrames": metadata["missingDetectionFrames"],
            "bodyPointsPerFrame": metadata["bodyPointsPerFrame"],
            "handPointsPerFrame": metadata["handPointsPerFrame"],
            "facePointsAvailable": metadata["facePointsAvailable"],
            "status": metadata["status"],
        }

        catalog.append(catalog_item)

    catalog = sorted(catalog, key=lambda item: item["displayName"].lower())

    with open(CATALOG_OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(catalog, file, indent=2)

    print("Sign catalog created successfully.")
    print(f"Total signs in catalog: {len(catalog)}")
    print(f"Output file: {CATALOG_OUTPUT_PATH}")

    print("\nFirst 5 signs:")
    for sign in catalog[:5]:
        print(f"- {sign['displayName']} ({sign['gloss']})")


if __name__ == "__main__":
    main()