#!/usr/bin/env python3
"""Build GT index for a DOTA annfiles dir using mmrotate's OWN poly->rbox
conversion (canonical le90), so GT angles match detector predictions exactly.
Run with the mmrotate-1.x interpreter (mr_dev1x). Writes a jsonl.
"""
import argparse
import json
import os
import sys

import numpy as np
import torch
from mmrotate.structures.bbox import QuadriBoxes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orientbench.data.dota import parse_dota_txt  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annfiles", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset", default="DOTA-v1.0")
    ap.add_argument("--split", default="val")
    args = ap.parse_args()

    rows = []
    for f in sorted(os.listdir(args.annfiles)):
        if not f.endswith(".txt"):
            continue
        image_id = f[:-4]
        objs, _ = parse_dota_txt(os.path.join(args.annfiles, f))
        polys = [o["poly"] for o in objs if len(o["poly"]) == 8]
        names = [o["class_name"] for o in objs if len(o["poly"]) == 8]
        if not polys:
            continue
        qb = QuadriBoxes(torch.tensor(polys, dtype=torch.float32))
        rb = qb.convert_to("rbox").tensor.numpy()  # (N,5) cx,cy,w,h,theta(le90 rad)
        for i, name in enumerate(names):
            cx, cy, w, h, th = [float(x) for x in rb[i]]
            rows.append({"dataset": args.dataset, "split": args.split, "image_id": image_id,
                         "class_name": name, "obb_cx": cx, "obb_cy": cy, "obb_w": w,
                         "obb_h": h, "obb_theta": th, "angle_version": "mmrotate_le90",
                         "valid_geometry": bool(w > 0 and h > 0)})
    with open(args.out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"[ok] wrote {len(rows)} mmrotate-le90 GT objects -> {args.out}")


if __name__ == "__main__":
    main()
