"""Dataset inventory — probe fixed dataset root for known OBB datasets.

Read-only. Records existence, annotation/image dirs, split candidates, notes,
and warnings for each known dataset. Missing datasets are recorded (not errors).
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

DATASET_ROOT_DEFAULT = "/home/rspip/cqc/data/dataset"

# Known datasets and where to look. Each entry lists candidate roots and the
# subdirs that, if present, identify annotation/image/split locations.
DATASET_PROBES: List[Dict[str, Any]] = [
    {
        "dataset_name": "DOTA-v1.0",
        "candidate_path": "dota/dota1.0",
        "ann_globs": ["split_ss_dota10/train/annfiles", "split_ss_dota10/val/annfiles",
                      "train/annfiles", "val/annfiles"],
        "img_globs": ["split_ss_dota10/train/images", "split_ss_dota10/val/images"],
        "split_dirs": [],
        "notes": "split_ss 1024x1024 tiles; ann = DOTA poly8 txt",
    },
    {
        "dataset_name": "DOTA-v1.5",
        "candidate_path": "dota/dota1.5",
        "ann_globs": ["split_ss_dota15/train/annfiles", "split_ss_dota15/val/annfiles",
                      "train/annfiles", "val/annfiles"],
        "img_globs": ["split_ss_dota15/train/images", "split_ss_dota15/val/images"],
        "split_dirs": [],
        "notes": "shares src images with v1.0; ann = DOTA poly8 txt",
    },
    {
        "dataset_name": "DIOR-R",
        "candidate_path": "DIOR",
        "ann_globs": ["annfiles/obb", "annfiles/hbb"],
        "img_globs": ["images/trainval", "images/test"],
        "split_dirs": ["splits"],
        "notes": "obb = robndbox XML; splits in splits/*.txt",
    },
    {
        "dataset_name": "HRSC2016",
        "candidate_path": "HRSC2016",
        "ann_globs": ["annfiles"],
        "img_globs": ["images"],
        "split_dirs": ["splits"],
        "notes": "XML mbox_cx/cy/w/h/ang(rad); bmp images",
    },
    {
        "dataset_name": "SODA-A",
        "candidate_path": "SODA-A",
        "ann_globs": ["annfiles", "Annotations"],
        "img_globs": ["images", "Images"],
        "split_dirs": ["splits"],
        "notes": "expected in readme baselines but probe to confirm presence",
    },
    {
        "dataset_name": "FAIR1M-v1.0",
        "candidate_path": "fair1m1.0",
        "ann_globs": ["split/train_80/annfiles", "split/val_20/annfiles"],
        "img_globs": ["split/train_80/images", "split/val_20/images"],
        "split_dirs": [],
        "notes": "XML points polygon; possibleresult/name class",
    },
    {
        "dataset_name": "ICDAR-MLT",
        "candidate_path": "ICDAR-MLT",
        "ann_globs": ["annfiles", "gt"],
        "img_globs": ["images"],
        "split_dirs": ["splits"],
        "notes": "cross-domain probe dataset; probe to confirm presence",
    },
]


def _existing(root: str, rels: List[str]) -> List[str]:
    out = []
    for rel in rels:
        p = os.path.join(root, rel)
        if os.path.isdir(p):
            out.append(p)
    return out


def _split_files(root: str, split_dirs: List[str]) -> List[str]:
    out = []
    for sd in split_dirs:
        p = os.path.join(root, sd)
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.endswith(".txt"):
                    out.append(os.path.join(p, f))
    return out


def build_dataset_inventory(dataset_root: str = DATASET_ROOT_DEFAULT) -> Dict[str, Any]:
    """Probe each known dataset under ``dataset_root``. Returns a result dict."""
    records: List[Dict[str, Any]] = []
    root_exists = os.path.isdir(dataset_root)
    for probe in DATASET_PROBES:
        cand = os.path.join(dataset_root, probe["candidate_path"])
        exists = os.path.isdir(cand)
        warnings: List[str] = []
        ann_dirs = img_dirs = split_files = []
        if exists:
            ann_dirs = _existing(cand, probe["ann_globs"])
            img_dirs = _existing(cand, probe["img_globs"])
            split_files = _split_files(cand, probe["split_dirs"])
            if not ann_dirs:
                warnings.append("no expected annotation dir found under candidate path")
            if not img_dirs:
                warnings.append("no expected image dir found under candidate path")
        else:
            warnings.append(f"candidate path missing: {cand}")
        records.append({
            "dataset_name": probe["dataset_name"],
            "candidate_path": cand,
            "exists": exists,
            "annotation_dirs": ann_dirs,
            "image_dirs": img_dirs,
            "split_candidates": split_files,
            "notes": probe["notes"],
            "warnings": warnings,
        })
    return {
        "dataset_root": dataset_root,
        "dataset_root_exists": root_exists,
        "n_known": len(records),
        "n_present": sum(1 for r in records if r["exists"]),
        "n_missing": sum(1 for r in records if not r["exists"]),
        "records": records,
    }
