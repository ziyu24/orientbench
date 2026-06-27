#!/usr/bin/env python3
"""00_env_check.py — fixed-path & environment check + dataset inventory.

Read-only. Checks the project's fixed paths, key python deps, and writes the
dataset inventory to outputs/bench_core/dataset_inventory.{json,csv}.
Does not move/modify any data.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.data.dataset_inventory import build_dataset_inventory  # noqa: E402

FIXED_PATHS = {
    "DATA_ROOT": "/home/rspip/cqc/data/dataset",
    "PTH_DATA": "/home/rspip/cqc/pro/study/pth_data",
    "PTH_DATA_README": "/home/rspip/cqc/pro/study/pth_data/readme.md",
    "PROJECT_ROOT": "/home/rspip/cqc/pro/study/orientbench",
    "THIRD_PARTY": "/home/rspip/cqc/pro/study/third_party",
}
DEFAULT_DATA_ROOT = "/home/rspip/cqc/data/dataset"
DEFAULT_OUT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")


def _dep(mod):
    try:
        m = __import__(mod)
        return getattr(m, "__version__", "present")
    except Exception as e:  # noqa: BLE001
        return f"MISSING ({e.__class__.__name__})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)

    print("=== fixed path check ===")
    path_status = {}
    for name, p in FIXED_PATHS.items():
        ok = os.path.exists(p)
        path_status[name] = {"path": p, "exists": ok}
        print(f"  [{'ok ' if ok else 'MISS'}] {name}: {p}")

    print("=== python deps ===")
    deps = {m: _dep(m) for m in ("numpy", "cv2", "shapely")}
    for m, v in deps.items():
        print(f"  {m}: {v}")
    print(f"  python: {sys.version.split()[0]}")

    inv = build_dataset_inventory(args.data_root)
    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "dataset_inventory.json")
    csv_path = os.path.join(args.out_dir, "dataset_inventory.csv")

    payload = {
        "fixed_paths": path_status,
        "deps": deps,
        "python": sys.version.split()[0],
        **inv,
    }
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    cols = ["dataset_name", "candidate_path", "exists", "annotation_dirs",
            "image_dirs", "split_candidates", "notes", "warnings"]
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in inv["records"]:
            row = dict(r)
            for k in ("annotation_dirs", "image_dirs", "split_candidates", "warnings"):
                row[k] = " | ".join(row.get(k) or [])
            w.writerow({k: row.get(k, "") for k in cols})

    print("=== dataset inventory ===")
    print(f"  known={inv['n_known']} present={inv['n_present']} missing={inv['n_missing']}")
    for r in inv["records"]:
        tag = "present" if r["exists"] else "MISSING"
        print(f"  [{tag}] {r['dataset_name']}  ann_dirs={len(r['annotation_dirs'])} "
              f"img_dirs={len(r['image_dirs'])} splits={len(r['split_candidates'])}")
    print(f"[ok] wrote {json_path}")
    print(f"[ok] wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
