#!/usr/bin/env python3
"""70_fullval_gt.py — build FULL-VAL OBB GT (no subset cap) to SCRATCH (024).

Reuses the 022 parsers (DIOR robndbox xml / FAIR1M points xml / SODA dota txt).
GT jsonl + image symlink farm -> SCRATCH (large); project keeps a meta (count,
sha256, paths). NEVER edits the original dataset. Run with mr_dev1x.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from scripts._cross_dataset_parsers import parse_dior, parse_fair1m, parse_dota_txt, poly_to_obb  # noqa: E402

import numpy as np  # noqa: E402

DATA = "/home/rspip/cqc/data/dataset"
SCRATCH = "/dev/shm/cqc/orientbench"
GTIDX = os.path.join(P, "outputs", "bench_core", "gt_index")


def build(dataset, ann_dir, img_dir, img_ext, parser, split_list=None):
    farm = os.path.join(SCRATCH, "predictions", dataset, "_root")
    os.makedirs(os.path.join(farm, "images"), exist_ok=True)
    os.makedirs(os.path.join(farm, "annfiles"), exist_ok=True)
    anns = sorted(f for f in os.listdir(ann_dir) if f.endswith((".xml", ".txt")))
    if split_list:
        keep = set(split_list); anns = [a for a in anns if os.path.splitext(a)[0] in keep]
    gt_path = os.path.join(SCRATCH, "predictions", dataset, f"{dataset}_fullval_gt.jsonl")
    n_obj = n_inv = n_img = 0
    with open(gt_path, "w") as out:
        for a in anns:
            stem = os.path.splitext(a)[0]
            img = os.path.join(img_dir, stem + img_ext)
            if not os.path.exists(img):
                for e in (".jpg", ".png", ".bmp", ".tif"):
                    if os.path.exists(os.path.join(img_dir, stem + e)):
                        img = os.path.join(img_dir, stem + e); img_ext = e; break
            if not os.path.exists(img):
                continue
            objs = parser(os.path.join(ann_dir, a))
            if not objs:
                continue
            link = os.path.join(farm, "images", stem + img_ext)
            if not os.path.exists(link):
                os.symlink(img, link)
            open(os.path.join(farm, "annfiles", stem + ".txt"), "w").close()
            n_img += 1
            for poly, name in objs:
                try:
                    cx, cy, w, h, th = poly_to_obb(poly)
                    if w <= 1 or h <= 1 or not np.isfinite([cx, cy, w, h, th]).all():
                        n_inv += 1; continue
                    out.write(json.dumps({"image_id": stem, "class_name": name, "obb_cx": cx, "obb_cy": cy,
                                          "obb_w": w, "obb_h": h, "obb_theta": th}) + "\n")
                    n_obj += 1
                except Exception:
                    n_inv += 1
    sha = hashlib.sha256(open(gt_path, "rb").read()).hexdigest()
    meta = {"dataset": dataset, "split": "fullval", "ann_dir": ann_dir, "n_images": n_img,
            "n_obb_objects": n_obj, "n_invalid_geometry": n_inv, "fullval": True, "not_fullval": False,
            "scratch_gt_path": gt_path, "scratch_farm": farm, "gt_sha256": sha, "max_files": None,
            "stats": {"n_files_ok": n_img, "n_objects": n_obj, "n_valid_geometry": n_obj, "n_invalid_geometry": n_inv},
            "angle_version": "le90_via_QuadriBoxes (uncertain)"}
    os.makedirs(GTIDX, exist_ok=True)
    json.dump(meta, open(os.path.join(GTIDX, f"{dataset}_fullval.meta.json"), "w"), indent=2)
    print(f"[{dataset}] FULLVAL images={n_img} obb={n_obj} invalid={n_inv} sha={sha[:12]} -> scratch")
    return meta


def main():
    dior_val = [l.strip() for l in open(f"{DATA}/DIOR/splits/val.txt")] if os.path.isfile(f"{DATA}/DIOR/splits/val.txt") else None
    metas = [
        build("SODA-A", f"{DATA}/SODA-A/dota_format_tiled_ss/val_tiled/annfiles",
              f"{DATA}/SODA-A/dota_format_tiled_ss/val_tiled/images", ".jpg", parse_dota_txt),
        build("DIOR-R", f"{DATA}/DIOR/annfiles/obb", f"{DATA}/DIOR/images/trainval", ".jpg", parse_dior, dior_val),
        build("FAIR1M-v1.0", f"{DATA}/fair1m1.0/split/val_20/annfiles",
              f"{DATA}/fair1m1.0/split/val_20/images", ".png", parse_fair1m),
    ]
    import csv
    REP = os.path.join(P, "outputs", "bench_core", "reports")
    with open(os.path.join(REP, "fullval_gt_index_024.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "n_images", "n_obb_objects", "n_invalid_geometry",
                                           "gt_sha256", "scratch_gt_path"], extrasaction="ignore")
        w.writeheader(); w.writerows(metas)
    print("[ok] full-val GT built to scratch")


if __name__ == "__main__":
    main()
