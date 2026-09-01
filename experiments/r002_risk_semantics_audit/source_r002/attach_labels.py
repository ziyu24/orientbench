#!/usr/bin/env python3
"""Attach frozen evaluation labels after prediction-only assets are sealed.

This program is deliberately separate from feature extraction.  It uses labels
only to create evaluation/training outcome tables; it never writes labels into
the prediction-time feature registry and never fits a held-out dataset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from mmcv.ops import box_iou_rotated
from mmrotate.structures.bbox import qbox2rbox

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('${ORIENTBENCH_ROOT}')
import sys
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from orientbench.data.splits import assign_split
from m069_common import split_role
from derive_delta_theta_075 import load_interpolator

RUNTIME = ROOT / 'outputs/persistent_artifacts/orientbench_r002_gr_eqs_method_admission'
DTH = load_interpolator()
UNITS = {
    'A': ('DIOR-R', 'dior22', PROJECT / 'top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test'),
    'B': ('DIOR-R', 'dior3', PROJECT / 'top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test'),
    'C': ('DIOR-R', 'dior61', PROJECT / 'top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test'),
    'D': ('FAIR1M-v1.0', 'fair24', Path('${RUNTIME_DATA_ROOT}/fair1m-v1.0/val_annfiles_r002')),
    'E': ('SODA-A', 'soda23', Path('${RUNTIME_DATA_ROOT}/SODA-A/val_tiled_r002/annfiles')),
    'F': ('SODA-A', 'soda4', Path('${RUNTIME_DATA_ROOT}/SODA-A/val_tiled_r002/annfiles')),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def parse_gt(path: Path) -> tuple[torch.Tensor, torch.Tensor]:
    polys, labels = [], []
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        fields = line.split()
        if len(fields) < 9:
            continue
        try:
            coords = [float(x) for x in fields[:8]]
        except ValueError:
            continue
        if int(fields[-1]) != 0:
            continue
        # Dataset class IDs already agree with detector config ordering in the
        # frozen Core-6 units; file order cannot be trusted, so map by unit's
        # feature class externally only where names are present.
        # FAIR1M native class names contain spaces; the final field is DOTA
        # difficulty, so preserve the complete intervening class token span.
        polys.append(coords); labels.append(' '.join(fields[8:-1]))
    if not polys:
        return torch.empty((0, 5), dtype=torch.float32), np.asarray([], dtype=object)
    return qbox2rbox(torch.tensor(polys, dtype=torch.float32)), np.asarray(labels, dtype=object)


def class_names(unit: str) -> tuple[str, ...]:
    # All six frozen configs use their native DOTA class ordering.  Read the
    # generated config instead of any evaluation label table.
    # Config parsing would execute arbitrary config code; the static class order
    # is fixed by the respective datasets and written here for explicit audit.
    if UNITS[unit][0] == 'DIOR-R':
        # Labels are detector-indexed.  A/B and C were frozen from configs
        # with distinct (but internally valid) class orderings; preserve case
        # exactly as it appears in the DOTA-format annotations.
        ab = ('airplane','airport','baseballfield','basketballcourt','bridge',
              'chimney','dam','Expressway-Service-area','Expressway-toll-station',
              'golffield','groundtrackfield','harbor','overpass','ship','stadium',
              'storagetank','tenniscourt','trainstation','vehicle','windmill')
        c = ('airplane','airport','baseballfield','basketballcourt','bridge',
             'chimney','Expressway-Service-area','Expressway-toll-station','dam',
             'golffield','groundtrackfield','harbor','overpass','ship','stadium',
             'storagetank','tenniscourt','trainstation','vehicle','windmill')
        return c if unit == 'C' else ab
    if UNITS[unit][0] == 'SODA-A':
        return ('airplane','helicopter','small-vehicle','large-vehicle','ship','container','storage-tank','swimming-pool','windmill')
    return ('Passenger Ship','Liquid Cargo Ship','Dry Cargo Ship','Motorboat',
            'Fishing Boat','Warship','Engineering Ship','other-ship','Tugboat',
            'Small Car','Cargo Truck','Van','Trailer','other-vehicle','Dump Truck',
            'Bus','Tractor','Excavator','Truck Tractor','Boeing737','Boeing747',
            'Boeing777','Boeing787','other-airplane','C919','A220','A321','A330',
            'A350','ARJ21','Tennis Court','Football Field','Basketball Court',
            'Baseball Field','Intersection','Bridge','Roundabout')


def le90(a: float, b: float) -> float:
    d = abs((a - b) * 180.0 / math.pi) % 180.0
    return min(d, 180.0 - d)


def match_one(pred: dict, ann_path: Path, names: tuple[str, ...], dataset: str) -> list[dict]:
    image_id = str(pred['img_id'])
    inst = pred['pred_instances']
    pbox = inst['bboxes'].tensor if hasattr(inst['bboxes'], 'tensor') else inst['bboxes']
    pbox = pbox.detach().cpu().float()
    pscores = inst['scores'].detach().cpu().float().numpy()
    plabels = inst['labels'].detach().cpu().long().numpy()
    gbox, gnames = parse_gt(ann_path)
    result = []
    for cls in np.unique(plabels):
        pi = np.flatnonzero(plabels == cls)
        name = names[int(cls)] if 0 <= int(cls) < len(names) else ''
        gi = np.flatnonzero(gnames == name)
        if not len(pi) or not len(gi):
            continue
        iou = box_iou_rotated(pbox[pi], gbox[gi]).cpu().numpy()
        used: set[int] = set()
        for local in sorted(range(len(pi)), key=lambda j: (-float(pscores[pi[j]]), int(pi[j]))):
            candidates = [(float(iou[local, j]), j) for j in range(len(gi)) if j not in used]
            if not candidates:
                break
            value, g_local = max(candidates)
            if value < 0.5:
                continue
            used.add(g_local)
            pb, gb = pbox[pi[local]], gbox[gi[g_local]]
            gw, gh = float(gb[2]), float(gb[3])
            ar = max(gw, gh) / max(min(gw, gh), 1e-6)
            if ar < 2.1:
                continue
            cluster = image_id.split('__', 1)[0] if dataset == 'SODA-A' else image_id
            assigned = assign_split(image_id)
            role = 'D_audit' if assigned == 'D_audit' else f'D_cal-{split_role(image_id)}'
            angle = le90(float(pb[4]), float(gb[4]))
            result.append(dict(image_id=image_id, pred_id=int(pi[local]), class_id=int(cls),
                               cluster=cluster, role=role, gt_ar=ar, angle_error=angle,
                               risk=min(angle / max(float(DTH(ar)), 1.0), 3.0), iou=float(value)))
    return result


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument('--unit', choices=UNITS, required=True); args = p.parse_args()
    dataset, slug, ann_dir = UNITS[args.unit]
    raw = RUNTIME / 'raw' / slug / 'identity.pkl'
    with raw.open('rb') as f: records = sorted(pickle.load(f), key=lambda x: str(x['img_id']))
    if not ann_dir.is_dir() or len(records) != len(list(ann_dir.glob('*.txt'))):
        raise RuntimeError(f'universe mismatch for {args.unit}: records={len(records)} ann={len(list(ann_dir.glob("*.txt")))}')
    names = class_names(args.unit)
    rows = []
    for record in records:
        image_id = str(record['img_id']); rows.extend(match_one(record, ann_dir / f'{image_id}.txt', names, dataset))
    out = RUNTIME / 'labels'; out.mkdir(parents=True, exist_ok=True)
    path = out / f'{args.unit}.parquet'; pd.DataFrame(rows).to_parquet(path, index=False, compression='zstd')
    manifest = dict(unit=args.unit, dataset=dataset, images=len(records), matched_ar21=len(rows),
                    clusters=len({r['cluster'] for r in rows}), path=str(path), bytes=path.stat().st_size, sha256=sha256(path),
                    schema='r002_postseal_labels_v1', selector_feature_fields=[])
    (out / f'{args.unit}.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, sort_keys=True))


if __name__ == '__main__':
    main()
