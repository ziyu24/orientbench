"""Bounded r027 input qualification; comparison is impossible without an OBB package."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def records(path, include=None):
    all_rows, focus, axis, missing = Counter(), Counter(), Counter(), []
    for label in sorted(path.glob("*.txt")):
        if include is not None and label.stem not in include:
            continue
        count = 0
        for number, line in enumerate(label.read_text(errors="replace").splitlines(), 1):
            v = line.split()
            if len(v) < 10 or line.lower().startswith(("imagesource:", "gsd:", "acquisition date:")):
                continue
            try:
                p = [(float(v[i]), float(v[i + 1])) for i in range(0, 8, 2)]
            except ValueError:
                missing.append({"file": label.name, "line": number, "reason": "non_numeric"}); continue
            aligned = all(math.isclose(p[i][0], p[(i + 1) % 4][0], abs_tol=1e-6) or math.isclose(p[i][1], p[(i + 1) % 4][1], abs_tol=1e-6) for i in range(4))
            all_rows["objects"] += 1; axis["all_axis_aligned"] += aligned; count += 1
            if v[8] in {"plane", "ship"}:
                focus["objects"] += 1; axis["focus_axis_aligned"] += aligned
        all_rows["label_files"] += 1
        if count == 0: all_rows["empty_label_files"] += 1
    return {"counts": dict(all_rows), "focus": dict(focus), "geometry": dict(axis), "exceptions": missing}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, required=True); p.add_argument("--corrected", action="store_true"); a = p.parse_args()
    root = a.root.resolve(); cfg = json.loads((root / "configs/r027/protocol.json").read_text())
    out = root / "runs/r027/artifacts"
    if a.corrected: out.mkdir(parents=True, exist_ok=True)
    else: out.mkdir(parents=True, exist_ok=False)
    data = Path(cfg["dataset_root"]); v1, hbb = data / cfg["v1_labels"], data / cfg["current_v2_labels"]
    shared_images = {x.stem for x in (data / cfg["shared_v1_val_images"]).glob("*.png")}
    observed = records(hbb, shared_images)
    access = {"official_dataset_page": cfg["official_dataset_page"], "official_baidu_share": cfg["official_baidu_share"],
              "official_onedrive_share": cfg["official_onedrive_share"], "extraction_code": cfg["extraction_code"],
              "bytes_transferred": 0, "limit_bytes": cfg["max_download_bytes"],
              "baidu": "public share page reached; password-verification endpoint returned errno=2 and list endpoint returned errno=-9 (verification failed)",
              "onedrive": "official link redirects to Microsoft login; no authenticated download attempted",
              "conclusion": "OBB package not acquired from a verifiable public source within the permitted access."}
    cand = cfg["candidate_obb_label_dir"]
    package = {"configured_path": cand, "exists": bool(cand and Path(cand).is_dir())}
    result = {"status": "OBB_INPUT_NOT_ACQUIRED", "shared_image_count": len(shared_images),
              "v1_label_files": len(list(v1.glob("*.txt"))), "current_hbb_on_shared_458": observed,
              "access": access, "candidate_obb_package": package,
              "comparison": "NOT_RUN: no source-bound OBB validation label package; HBB must not be converted into pseudo-OBB.",
              "limitations": ["Local HBB-like labels are retained as evidence, not treated as OBB.", "No hidden test, images, training data, weights, inference or AP was accessed."]}
    (out / ("input_qualification_corrected.json" if a.corrected else "input_qualification.json")).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
