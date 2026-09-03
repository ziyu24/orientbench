"""Correction-only real-image G/P/N observables from frozen r004 assets."""
from __future__ import annotations
import argparse, json, pickle
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from .matcher import global_match
from orientbench.r005.fast_observability import circular_crop, fixed_noise_scale, measure

CANONICAL_IMAGES = Path("/home/rspip/cqc/data/dataset/HRSC2016/images")

def _array(value): return np.asarray(value.detach().cpu(), float)
def _load(path):
    with open(path, "rb") as handle: return pickle.load(handle)
def _image_file(root, split, condition, image_id):
    return CANONICAL_IMAGES / f"{image_id}.bmp" if condition == "clean" else root / "interventions" / split / condition / "images" / f"{image_id}.bmp"

def _one_image(job):
    root, model, split, condition, image_id, gt, clean_pred, pairs = job
    root = Path(root)
    image = cv2.imread(str(_image_file(root, split, condition, image_id)), cv2.IMREAD_GRAYSCALE)
    clean_image = image if condition == "clean" else cv2.imread(str(_image_file(root, split, "clean", image_id)), cv2.IMREAD_GRAYSCALE)
    if image is None or clean_image is None: raise RuntimeError(f"unreadable image {image_id} ({split}/{condition})")
    rows = []
    for gt_index, pred_index in pairs:
        cx, cy, width, height = gt[gt_index, :4]; pcx, pcy, pwidth, pheight = clean_pred[pred_index, :4]; scale = max(width, height)
        arms = [("G", cx, cy, scale), ("P", pcx, pcy, max(pwidth, pheight))]
        displacement = .15 * scale
        arms += [("N0", cx+displacement, cy, scale), ("N1", cx-displacement, cy, scale), ("N2", cx, cy+displacement, scale), ("N3", cx, cy-displacement, scale), ("N4", cx, cy, scale*.8), ("N5", cx, cy, scale*1.25)]
        for arm, x, y, arm_scale in arms:
            patch, weight = circular_crop(image, x, y, arm_scale)
            if condition == "clean": sigma0 = fixed_noise_scale(patch)
            else:
                clean_patch, _ = circular_crop(clean_image, x, y, arm_scale); sigma0 = fixed_noise_scale(clean_patch)
            observable = measure(patch, weight, sigma0)
            rows.append({"model": model, "split": split, "condition": condition, "image_id": image_id, "gt_index": gt_index, "arm": arm, "J_eff": observable.j_eff, "M15": observable.m15, "sigma0": sigma0})
    return rows

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--out", type=Path, required=True); parser.add_argument("--workers", type=int, default=80); args = parser.parse_args()
    jobs = []
    for model in ("oriented_rcnn_r50", "rotated_rtmdet_m"):
        for split in ("trainval", "test"):
            base = args.root / "inference" / split / model; clean = _load(base / "clean" / "predictions.pkl")
            universe = [(record["img_id"], _array(record["gt_instances"]["bboxes"]), _array(record["pred_instances"]["bboxes"]), global_match(_array(record["gt_instances"]["bboxes"]), _array(record["pred_instances"]["bboxes"]))) for record in clean]
            conditions = ("clean",) if split == "trainval" else ("clean", "blur_1.5", "blur_1.25", "downsample_2", "downsample_1.75")
            for condition in conditions: jobs.extend((str(args.root), model, split, condition, image_id, gt, pred, pairs) for image_id, gt, pred, pairs in universe if pairs)
    records = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(_one_image, jobs, chunksize=1): records.extend(result)
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(records) + "\n")

if __name__ == "__main__": main()
