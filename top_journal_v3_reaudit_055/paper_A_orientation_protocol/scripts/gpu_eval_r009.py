#!/usr/bin/env python3
"""GPU full-evaluator kernel for r009 (no Shapely).

Uses the K1-validated mmrotate RBboxOverlaps2D implementation and rematches
the complete prediction/GT universe at each dose. This is intentionally a
small kernel used by the r009 driver; it does not alter NMS or prediction IDs.
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'top_journal_v3_reaudit_055/scripts'))
from recompute_table1_fullval_k1_065 import eval_cell

CELLS = {
    'DIOR-R/22': ('outputs/persistent_artifacts/orientbench_v2/DIOR-R/22/schema/pred_b22_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
    'DIOR-R/3': ('outputs/persistent_artifacts/orientbench_v2/DIOR-R/3/schema/pred_b3_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
    'DIOR-R/61': ('outputs/persistent_artifacts/orientbench_v2/DIOR-R/61/schema/pred_b61_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
    'FAIR1M-v1.0/24': ('outputs/persistent_artifacts/orientbench_v2/FAIR1M-v1.0/24/schema/pred_b24_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl'),
    'SODA-A/23': ('outputs/persistent_artifacts/orientbench_v2/SODA-A/23/schema/pred_b23_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl'),
    'SODA-A/4': ('outputs/persistent_artifacts/orientbench_v2/SODA-A/4/schema/pred_b4_fullval.jsonl', 'outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl'),
}

def load(rel):
    with (ROOT / rel).open() as f: return [json.loads(x) for x in f]

def run(cell, dose):
    pp, gp = CELLS[cell]; preds, gts = load(pp), load(gp)
    if dose:
        preds = [dict(p, obb_theta=float(p['obb_theta']) + math.radians(dose)) for p in preds]
    ap50, ap75, fp, errs, _ = eval_cell(preds, gts)
    return {'cell': cell, 'dose_deg': dose, 'AP50': float(ap50), 'AP75': float(ap75), 'fp50': int(fp), 'angle_error_mean': float(np.mean(errs)) if errs else None, 'n_pred': len(preds), 'n_gt': len(gts), 'evaluator': 'GPU_RBboxOverlaps2D_K1'}

if __name__ == '__main__':
    cell = sys.argv[1]; doses = [int(x) for x in (sys.argv[2:] or ['0'])]
    for d in doses:
        print(json.dumps(run(cell, d), ensure_ascii=False), flush=True)
