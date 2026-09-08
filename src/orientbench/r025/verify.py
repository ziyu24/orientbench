"""Independent r025 artifact verifier; intentionally does not import the producer."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def direct_status(a, b):
    if not a or not b:
        return "missing_version_image"
    try:
        with Image.open(a) as x, Image.open(b) as y:
            x.load(); y.load()
            if x.size != y.size or x.mode != y.mode:
                return "decoded_shape_or_mode_diff"
            if digest(a) == digest(b):
                return "byte_identical"
            return "pixel_identical_encoding_diff" if x.tobytes() == y.tobytes() else "pixel_diff"
    except Exception:
        return "decode_error"


def main():
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, required=True); a = p.parse_args()
    out = a.root.resolve() / "runs/r025/artifacts"
    with open(out / "image_pairs.csv", newline="") as f:
        images = list(csv.DictReader(f))
    mismatches = [r["image_id"] for r in images if direct_status(r["v1_path"], r["v2_path"]) != r["status"]]
    with open(out / "objects.csv", newline="") as f:
        objects = list(csv.DictReader(f))
    with open(out / "label_correspondence.csv", newline="") as f:
        corr = list(csv.DictReader(f))
    old_keys = {(r["image_id"], r["line"]) for r in objects if r.get("version") == "v1" and r.get("valid") == "True"}
    new_keys = {(r["image_id"], r["line"]) for r in objects if r.get("version") == "v2" and r.get("valid") == "True"}
    referenced_old = {(r["image_id"], r["old_line"]) for r in corr if r.get("old_line")}
    referenced_new = {(r["image_id"], r["new_line"]) for r in corr if r.get("new_line")}
    # Every retained valid object must be represented exactly once in the exhaustive correspondence partition.
    report = {"image_rows": len(images), "image_status_counts": dict(Counter(r["status"] for r in images)),
              "image_status_mismatches": mismatches,
              "valid_old_objects": len(old_keys), "valid_new_objects": len(new_keys),
              "unpartitioned_old": sorted(old_keys - referenced_old)[:50],
              "unpartitioned_new": sorted(new_keys - referenced_new)[:50],
              "correspondence_status_counts": dict(Counter(r["status"] for r in corr)),
              "pass": not mismatches and not (old_keys - referenced_old) and not (new_keys - referenced_new),
              "independence": "Verifier reads native file paths and CSV evidence directly; it imports neither the audit module nor its matching/statistics implementation."}
    (out / "independent_verify.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["pass"]:
        raise SystemExit("independent verification failed")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
