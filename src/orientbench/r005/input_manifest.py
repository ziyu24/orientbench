"""Hashes the frozen r004 prediction and image inputs used by r005."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    files = sorted(root.glob("inference/*/*/*/predictions.pkl"))
    payload = {"r004_root": str(root.resolve()), "prediction_files": [{"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256(path)} for path in files],
               "canonical_clean_images": "/home/rspip/cqc/data/dataset/HRSC2016/images",
               "intervention_roots": {split: str((root / "interventions" / split).resolve()) for split in ("trainval", "test")}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
