"""Source and geometry qualification for the restarted r027 OBB input."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_labels(directory, include):
    counts, malformed = Counter(), []
    for label in sorted(directory.glob("*.txt")):
        if label.stem not in include:
            continue
        counts["label_files"] += 1
        for line_no, text in enumerate(label.read_text(errors="replace").splitlines(), 1):
            fields = text.split()
            if not fields or text.lower().startswith(("imagesource:", "gsd:", "acquisition date:")):
                continue
            if len(fields) != 10:
                malformed.append({"file": label.name, "line": line_no, "reason": "field_count"})
                continue
            try:
                points = [(float(fields[i]), float(fields[i + 1])) for i in range(0, 8, 2)]
            except ValueError:
                malformed.append({"file": label.name, "line": line_no, "reason": "non_numeric"})
                continue
            axis = all(
                math.isclose(points[i][0], points[(i + 1) % 4][0], abs_tol=1e-6)
                or math.isclose(points[i][1], points[(i + 1) % 4][1], abs_tol=1e-6)
                for i in range(4)
            )
            counts["objects"] += 1
            counts["axis_aligned"] += int(axis)
            if fields[8] in {"plane", "ship"}:
                counts["focus_objects"] += 1
                counts["focus_axis_aligned"] += int(axis)
    return dict(counts), malformed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output_dir.resolve()
    cfg = json.loads((root / "configs/r027/protocol.json").read_text())
    data = Path(cfg["dataset_root"])
    archive = Path(cfg["source_archive"])
    obb = Path(cfg["candidate_obb_label_dir"])
    hbb = data / cfg["current_v2_labels"]
    shared = {path.stem for path in (data / cfg["shared_v1_val_images"]).glob("*.png")}
    obb_names = {path.stem for path in obb.glob("*.txt")}
    hbb_names = {path.stem for path in hbb.glob("*.txt")}
    counts, malformed = read_labels(obb, shared)
    result = {
        "status": "OBB_INPUT_QUALIFIED" if not malformed and shared <= obb_names else "OBB_INPUT_REJECTED",
        "archive": {"path": str(archive), "exists": archive.is_file(), "bytes": archive.stat().st_size if archive.is_file() else None,
                    "sha256": sha256(archive) if archive.is_file() else None, "expected_bytes": cfg["source_archive_expected_bytes"],
                    "expected_sha256": cfg["source_archive_sha256"]},
        "official_source": {"dataset_page": cfg["official_dataset_page"], "baidu_share": cfg["official_baidu_share"],
                            "archive_name": archive.name},
        "shared_image_count": len(shared), "obb_label_file_count": len(obb_names), "hbb_label_file_count": len(hbb_names),
        "shared_missing_from_obb": sorted(shared - obb_names), "obb_extra_vs_hbb": len(obb_names - hbb_names),
        "obb_shared_geometry": counts, "malformed_records": malformed,
        "prior_hbb_fact": "The retained current_v2_labels are all axis-aligned on the 458 shared images; they are not used as v2 OBB input.",
    }
    result["archive"]["matches_expected"] = (result["archive"]["bytes"] == result["archive"]["expected_bytes"]
                                                    and result["archive"]["sha256"] == result["archive"]["expected_sha256"])
    if not result["archive"]["matches_expected"]:
        result["status"] = "OBB_INPUT_REJECTED"
    out.mkdir(parents=True, exist_ok=False)
    (out / "input_qualification.json").write_text(json.dumps(result, indent=2) + "\n")
    if result["status"] != "OBB_INPUT_QUALIFIED":
        raise SystemExit("r027 OBB input qualification failed")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
