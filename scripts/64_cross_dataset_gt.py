#!/usr/bin/env python3
"""64_cross_dataset_gt.py — rediscover + parse real OBB GT for DIOR-R/FAIR1M/SODA-A (022).

Formats: DIOR-R robndbox 8-corner XML; FAIR1M points (quad) XML; SODA-A DOTA-poly8
txt (dota_format_tiled_ss). All -> mmrotate le90 OBB via QuadriBoxes. Builds a
bounded subset GT index + non-destructive image symlink farm per dataset. Run
with mr_dev1x. NEVER edits the original dataset.
"""
from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
DATA = "/home/rspip/cqc/data/dataset"
OUT = os.path.join(P, "outputs", "predictions")
GTIDX = os.path.join(P, "outputs", "bench_core", "gt_index")
SUBSET = 600


def poly_to_obb(poly):
    """poly8 -> (cx,cy,w,h,theta le90) via mmrotate QuadriBoxes."""
    import torch
    from mmrotate.structures.bbox import QuadriBoxes
    q = QuadriBoxes(torch.tensor([poly], dtype=torch.float32))
    r = q.convert_to("rbox").tensor[0].tolist()
    return r  # cx,cy,w,h,theta


def parse_dior(xml_path):
    out = []
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return out
    for obj in root.findall("object"):
        rb = obj.find("robndbox")
        name = obj.findtext("name", "object")
        if rb is None:
            continue
        try:
            poly = [float(rb.findtext(k)) for k in
                    ("x_left_top", "y_left_top", "x_right_top", "y_right_top",
                     "x_right_bottom", "y_right_bottom", "x_left_bottom", "y_left_bottom")]
        except (TypeError, ValueError):
            continue
        out.append((poly, name))
    return out


def parse_fair1m(xml_path):
    out = []
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return out
    objs = root.find("objects")
    if objs is None:
        return out
    for obj in objs.findall("object"):
        name = (obj.findtext("possibleresult/name") or "object")
        pts = obj.find("points")
        if pts is None:
            continue
        coords = []
        for pt in pts.findall("point"):
            x, y = pt.text.split(",")
            coords += [float(x), float(y)]
        if len(coords) >= 8:
            out.append((coords[:8], name))
    return out


def parse_dota_txt(txt_path):
    out = []
    for line in open(txt_path):
        p = line.split()
        if len(p) >= 9:
            try:
                poly = [float(x) for x in p[:8]]
            except ValueError:
                continue
            out.append((poly, p[8]))
    return out


def build(dataset, ann_dir, img_dir, img_ext, parser, split_list=None):
    os.makedirs(GTIDX, exist_ok=True)
    farm = os.path.join(OUT, dataset, "_root")
    os.makedirs(os.path.join(farm, "images"), exist_ok=True)
    os.makedirs(os.path.join(farm, "annfiles"), exist_ok=True)
    anns = sorted(f for f in os.listdir(ann_dir) if f.endswith((".xml", ".txt")))
    if split_list:
        keep = set(split_list)
        anns = [a for a in anns if os.path.splitext(a)[0] in keep]
    anns = anns[:SUBSET]
    gt, n_obj, n_invalid, n_img = [], 0, 0, 0
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
        # symlink image + empty ann for inference dataloader
        link = os.path.join(farm, "images", stem + img_ext)
        if not os.path.exists(link):
            os.symlink(img, link)
        open(os.path.join(farm, "annfiles", stem + ".txt"), "w").close()
        n_img += 1
        for poly, name in objs:
            try:
                cx, cy, w, h, th = poly_to_obb(poly)
                if w <= 1 or h <= 1 or not np.isfinite([cx, cy, w, h, th]).all():
                    n_invalid += 1; continue
                gt.append({"image_id": stem, "class_name": name, "obb_cx": cx, "obb_cy": cy,
                           "obb_w": w, "obb_h": h, "obb_theta": th})
                n_obj += 1
            except Exception:
                n_invalid += 1
    jp = os.path.join(GTIDX, f"{dataset}_val.jsonl")
    with open(jp, "w") as fh:
        for g in gt:
            fh.write(json.dumps(g) + "\n")
    meta = {"dataset": dataset, "split": "val", "ann_dir": ann_dir, "img_dir": img_dir, "n_images": n_img,
            "n_obb_objects": n_obj, "n_invalid_geometry": n_invalid, "subset_cap": SUBSET, "max_files": SUBSET,
            "farm": farm, "angle_version": "le90_via_QuadriBoxes (uncertain pending formal proof)",
            "stats": {"n_files_ok": n_img, "n_objects": n_obj, "n_valid_geometry": n_obj,
                      "n_invalid_geometry": n_invalid}}
    json.dump(meta, open(os.path.join(GTIDX, f"{dataset}_val.meta.json"), "w"), indent=2)
    print(f"[{dataset}] images={n_img} obb_objects={n_obj} invalid={n_invalid} -> {jp}")
    return meta


def main():
    metas = []
    # SODA-A: DOTA-format tiled val
    metas.append(build("SODA-A",
                       f"{DATA}/SODA-A/dota_format_tiled_ss/val_tiled/annfiles",
                       f"{DATA}/SODA-A/dota_format_tiled_ss/val_tiled/images", ".jpg", parse_dota_txt))
    # DIOR-R: robndbox xml, val split
    dior_val = [l.strip() for l in open(f"{DATA}/DIOR/splits/val.txt")] if os.path.isfile(f"{DATA}/DIOR/splits/val.txt") else None
    metas.append(build("DIOR-R", f"{DATA}/DIOR/annfiles/obb",
                       f"{DATA}/DIOR/images/trainval", ".jpg", parse_dior, dior_val))
    # FAIR1M: points xml, val_20
    metas.append(build("FAIR1M-v1.0", f"{DATA}/fair1m1.0/split/val_20/annfiles",
                       f"{DATA}/fair1m1.0/split/val_20/images", ".png", parse_fair1m))
    import csv
    REP = os.path.join(P, "outputs", "bench_core", "reports")
    with open(os.path.join(REP, "gt_index_cross_dataset_022.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "ann_dir", "n_images", "n_obb_objects",
                                           "n_invalid_geometry", "angle_version"], extrasaction="ignore")
        w.writeheader(); w.writerows(metas)
    L = ["# Cross-Dataset GT Index (022)", "", "| dataset | ann_dir | images | obb_objects | invalid | angle |",
         "|---|---|---|---|---|---|"]
    for m in metas:
        L.append(f"| {m['dataset']} | `{os.path.basename(m['ann_dir'])}` | {m['n_images']} | "
                 f"{m['n_obb_objects']} | {m['n_invalid_geometry']} | {m['angle_version']} |")
    open(os.path.join(REP, "gt_index_cross_dataset_022.md"), "w").write("\n".join(L) + "\n")
    print("[ok] GT index built for SODA-A / DIOR-R / FAIR1M-v1.0")


if __name__ == "__main__":
    main()
