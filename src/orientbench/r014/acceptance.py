"""Read-only r014 acceptance checks; this never loads a classifier or opens test data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def crop(image: Image.Image, entry: dict[str, object]) -> np.ndarray:
    side = int(entry["canvas_side"])
    x, y = entry["center"]
    box = (int(x - side / 2), int(y - side / 2), int(x + side / 2), int(y + side / 2))
    return np.asarray(image.crop(box).convert("RGB"), dtype=np.uint8).copy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--g0", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--old-train", type=Path, required=True)
    parser.add_argument("--old-calibration", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise RuntimeError("acceptance output exists")

    metadata_path = args.dataset / "real/metadata_annotations/RarePlanes_Public_Metadata.csv"
    geojson_path = args.dataset / "real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson"
    with metadata_path.open(newline="") as stream:
        metadata = list(csv.DictReader(stream))
    # Deliberately rebuild this map from official metadata, rather than consuming source_records.
    sources = {(int(row["loc_id"]), row["image_id"].split("_", 1)[1]): row["image_id"] for row in metadata}
    if len(metadata) != 253 or len(sources) != 253:
        raise RuntimeError("official metadata identity is not unique")
    with geojson_path.open() as stream:
        features = json.load(stream)["features"]
    eligible = {row["object_id"]: row for row in json.load(open(args.g0.parent / "eligible_manifest.json"))}
    old_records = [json.loads(line) for line in open(args.audit / "source_records.jsonl")]
    records = {row["object_id"]: row for row in old_records}
    calibration = [row for row in old_records if row["partition"] == "calibration"]
    train = [row for row in old_records if row["partition"] == "train"]
    if len(calibration) != 7416 or len(train) != 4065 or set(records) != set(eligible):
        raise RuntimeError("frozen universe mismatch")

    train_dir = args.dataset / "real/imagery/train/PS-RGB_cog"
    calibration_dir = args.dataset / "real/imagery/calibration/PS-RGB_cog"
    image_cache: dict[str, Image.Image] = {}
    per_object: list[dict[str, object]] = []
    for record in calibration:
        object_id = int(record["object_id"])
        entry = eligible[object_id]
        props = features[object_id]["properties"]
        image_id = sources.get((int(props["loc_id"]), props["cat_id"]))
        if image_id is None or image_id != entry["source_cog"]:
            raise RuntimeError(f"independent source mismatch for {object_id}")
        path = train_dir / f"{image_id}.tif"
        if not path.exists():
            path = calibration_dir / f"{image_id}.tif"
        if not path.is_file():
            raise RuntimeError(f"missing source COG {image_id}")
        image_cache.setdefault(image_id, Image.open(path))
        actual = crop(image_cache[image_id], entry)
        stored = np.load(args.audit / "corrected_calibration_canvases" / f"{object_id}.npy", allow_pickle=False)
        old = np.load(args.old_calibration / f"{object_id}.npy", allow_pickle=False)
        if actual.shape != stored.shape or actual.shape != old.shape:
            raise RuntimeError(f"canvas shape mismatch for {object_id}")
        channels = int(np.count_nonzero(actual != stored))
        per_object.append({
            "object_id": object_id,
            "loc_id": int(props["loc_id"]),
            "cat_id": props["cat_id"],
            "image_id": image_id,
            "stored_canvas_sha256": sha256(args.audit / "corrected_calibration_canvases" / f"{object_id}.npy"),
            "independent_canvas_sha256": hashlib.sha256(actual.tobytes()).hexdigest(),
            "different_channels": channels,
            "old_canvas_different_channels": int(np.count_nonzero(actual != old)),
        })

    train_changed = 0
    for record in train:
        object_id = int(record["object_id"])
        entry = eligible[object_id]
        props = features[object_id]["properties"]
        image_id = sources[(int(props["loc_id"]), props["cat_id"])]
        path = train_dir / f"{image_id}.tif"
        if not path.is_file():
            raise RuntimeError(f"missing train source {image_id}")
        image_cache.setdefault(image_id, Image.open(path))
        train_changed += int(not np.array_equal(crop(image_cache[image_id], entry), np.load(args.old_train / f"{object_id}.npy", allow_pickle=False)))

    model_names = [f"{kind}_{seed}.pt" for kind in ("resnet50", "vit_b16") for seed in (1201, 1202, 1203)]
    model_files = [{"name": name, "exists": (args.models / name).is_file(), "sha256": sha256(args.models / name) if (args.models / name).is_file() else None} for name in model_names]
    original_records = {
        "r013_preflight": (args.models.parent / "artifacts/preflight.json").is_file(),
        "r013_fit_manifest": (args.models / "manifest.json").is_file(),
        "r013_train_canvas_manifest": (args.old_train / "manifest.json").is_file(),
        "r013_calibration_manifest": (args.old_calibration.parent / "manifest.json").is_file(),
    }
    args.out.mkdir(parents=True)
    (args.out / "pixel_records.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in per_object))
    summary = {
        "protocol": "r014-remaining-acceptance-v1",
        "test_opened": False,
        "model_forward": False,
        "calibration_rows": len(per_object),
        "calibration_pixel_nonzero_difference_count": sum(row["different_channels"] > 0 for row in per_object),
        "calibration_old_changed_rows": sum(row["old_canvas_different_channels"] > 0 for row in per_object),
        "train_rows": len(train),
        "train_old_changed_rows": train_changed,
        "models": model_files,
        "original_execution_records": original_records,
        "original_execution_identity_recoverable": all(original_records.values()),
        "metadata_sha256": sha256(metadata_path),
        "geojson_sha256": sha256(geojson_path),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
