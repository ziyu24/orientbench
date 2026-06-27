#!/usr/bin/env python3
"""04_compute_sources.py — Bench-Core-1 source measurement (DRY-RUN).

Reads GT index jsonl(s) from outputs/bench_core/gt_index/, computes layout
sources (geometry-only, all objects) and background sources (real image annulus,
capped sample, parallel across images), and writes augmented per-object source
records to outputs/bench_core/cache/sources_<key>_<split>.jsonl.

Read-only on datasets. Not a formal experiment (thresholds unfrozen).
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import sys
from multiprocessing import Pool

import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.buckets.sources import (  # noqa: E402
    compute_background_for_object,
    compute_layout_for_image,
    precompute_gradients,
)
from orientbench.buckets.stress_buckets import aspect_ratio  # noqa: E402
from orientbench.io.reports import read_jsonl, write_jsonl, write_json  # noqa: E402
from orientbench.metrics.gv import gv_obliquity  # noqa: E402

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

GT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "gt_index")
CACHE_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core", "cache")
from orientbench.core.geometry import obb_to_corners  # noqa: E402


def _bg_worker(task):
    """task = (image_path, [objs]) -> list of (orig_index, bg_dict)."""
    image_path, objs = task
    if cv2 is None or not os.path.isfile(image_path):
        return [(o["_idx"], {"bg_status": "unavailable",
                             "bg_warnings": ["image missing or cv2 unavailable"]}) for o in objs]
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        return [(o["_idx"], {"bg_status": "unavailable",
                             "bg_warnings": ["cv2 failed to read"]}) for o in objs]
    gray = gray.astype(np.float64)
    mag, tcos, tsin = precompute_gradients(gray)
    corners = [obb_to_corners(o["obb_cx"], o["obb_cy"], o["obb_w"], o["obb_h"], o["obb_theta"])
               for o in objs]
    out = []
    for k, o in enumerate(objs):
        others = [corners[j] for j in range(len(objs)) if j != k]
        bg = compute_background_for_object(mag, tcos, tsin, o, others)
        out.append((o["_idx"], bg))
    return out


def process_index_file(path, max_bg_files, jobs):
    records = read_jsonl(path)
    n = len(records)
    if n == 0:
        return None
    # group by image_id, preserve first-seen order
    groups = {}
    for idx, r in enumerate(records):
        groups.setdefault(r["image_id"], []).append(idx)

    # ---- layout (all images) ----
    for img_id, idxs in groups.items():
        objs = [records[i] for i in idxs]
        lay = compute_layout_for_image(objs)
        for i, l in zip(idxs, lay):
            records[i].update(l)

    # ---- per-record geometry aux ----
    for r in records:
        g = gv_obliquity(r["obb_w"], r["obb_h"], r["obb_theta"])
        r["gv_ratio"] = g["gv_ratio"]
        r["gv_obb_needed"] = g["gv_obb_needed"]
        r["aspect_ratio"] = aspect_ratio(r["obb_w"], r["obb_h"])
        # default bg fields (overwritten if computed)
        r.setdefault("V_bg", 0)
        r.setdefault("A_bg", float("nan"))
        r.setdefault("E_bg", float("nan"))
        r.setdefault("bg_valid_ratio", float("nan"))
        r.setdefault("bg_status", "skipped_cap")

    # ---- background (capped subsample of images) ----
    img_ids = list(groups.keys())
    bg_ids = img_ids[:max_bg_files] if max_bg_files is not None and max_bg_files >= 0 else img_ids
    tasks = []
    for img_id in bg_ids:
        idxs = groups[img_id]
        objs = []
        for i in idxs:
            r = records[i]
            objs.append({"_idx": i, "obb_cx": r["obb_cx"], "obb_cy": r["obb_cy"],
                         "obb_w": r["obb_w"], "obb_h": r["obb_h"], "obb_theta": r["obb_theta"]})
        tasks.append((records[idxs[0]]["image_path"], objs))

    n_bg_ok = 0
    if tasks:
        if jobs > 1:
            with Pool(jobs) as pool:
                results = pool.map(_bg_worker, tasks)
        else:
            results = [_bg_worker(t) for t in tasks]
        for res in results:
            for orig_idx, bg in res:
                records[orig_idx].update(bg)
                if bg.get("bg_status") == "ok":
                    n_bg_ok += 1

    out_path = os.path.join(CACHE_DIR, "sources_" + os.path.basename(path))
    write_jsonl(out_path, records)

    # summary stats
    def finite(key):
        return [r[key] for r in records if isinstance(r.get(key), (int, float)) and math.isfinite(r[key])]
    stats = {
        "n_objects": n,
        "n_images": len(groups),
        "n_bg_images_attempted": len(tasks),
        "n_bg_objects_ok": n_bg_ok,
        "n_V_layout": sum(1 for r in records if r.get("V_layout") == 1),
        "n_V_bg": sum(1 for r in records if r.get("V_bg") == 1),
        "mean_E_layout": float(np.mean(finite("E_layout"))) if finite("E_layout") else float("nan"),
        "mean_E_bg": float(np.mean(finite("E_bg"))) if finite("E_bg") else float("nan"),
    }
    return {"file": out_path, "stats": stats}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", default="core1")
    ap.add_argument("--gt-dir", default=GT_DIR)
    ap.add_argument("--pattern", default="*.jsonl", help="glob within gt-dir")
    ap.add_argument("--max-bg-files", type=int, default=60,
                    help="cap images for background source (-1 = all). Recorded, not silent.")
    ap.add_argument("--jobs", type=int, default=max(1, min(12, (os.cpu_count() or 2) - 2)))
    args = ap.parse_args(argv)

    os.makedirs(CACHE_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(args.gt_dir, args.pattern)))
    files = [f for f in files if not f.endswith(".meta.json")]
    if not files:
        print(f"[warn] no GT index files in {args.gt_dir}/{args.pattern}")
        return 0

    max_bg = None if args.max_bg_files is not None and args.max_bg_files < 0 else args.max_bg_files
    print(f"[stage {args.stage}] sources over {len(files)} index files; "
          f"jobs={args.jobs} max_bg_files={max_bg}")
    summary = []
    for f in files:
        res = process_index_file(f, max_bg, args.jobs)
        if res is None:
            continue
        s = res["stats"]
        print(f"[ok] {os.path.basename(f)}: objs={s['n_objects']} imgs={s['n_images']} "
              f"V_layout={s['n_V_layout']} bg_ok={s['n_bg_objects_ok']}/{s['n_bg_images_attempted']}img "
              f"V_bg={s['n_V_bg']} meanE_layout={s['mean_E_layout']:.3f} meanE_bg={s['mean_E_bg']:.3f}")
        summary.append(res)

    write_json(os.path.join(CACHE_DIR, "sources_summary.json"),
               {"stage": args.stage, "max_bg_files": max_bg, "jobs": args.jobs,
                "files": [{"file": r["file"], "stats": r["stats"]} for r in summary]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
