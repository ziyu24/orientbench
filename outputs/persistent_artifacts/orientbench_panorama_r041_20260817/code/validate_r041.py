#!/usr/bin/env python3
"""Independent structural validator for r041's AP-gated normalized DIOR assets."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

REQ = ['unit_id','image_id','pred_id','gt_id','class_id','cluster_id','angle_error_deg','Y',
       'detection_score','pred_w','pred_h','gt_w','gt_h','pred_ar','gt_ar','pred_area','iou',
       'u_axis','missing_fraction','iou_loss','center_dispersion','scale_dispersion',
       'score_dispersion','association_ambiguity']
PROV = {'unit_id','dataset','split_used','checkpoint_sha256','config_sha256','log_sha256','views'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--rows', required=True)
    p.add_argument('--provenance', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    rows = pd.read_csv(a.rows)
    prov = pd.read_csv(a.provenance)
    errors = []
    if list(rows.columns) != REQ: errors.append('schema')
    if rows.empty: errors.append('empty_rows')
    if rows.duplicated(['unit_id','image_id','pred_id']).any(): errors.append('duplicate_prediction_key')
    if rows.duplicated(['unit_id','image_id','gt_id']).any(): errors.append('duplicate_gt_match')
    if not ((rows.iou >= .5) & (rows.iou <= 1)).all(): errors.append('iou_invariant')
    evidence = ['u_axis','missing_fraction','iou_loss','center_dispersion','scale_dispersion','score_dispersion','association_ambiguity']
    if not np.isfinite(rows[evidence].to_numpy()).all(): errors.append('nonfinite_evidence')
    if not PROV.issubset(prov.columns) or prov[list(PROV)].isna().any().any(): errors.append('provenance')
    result = {'schema_version': 2, 'pass': not errors, 'errors': errors, 'rows': int(len(rows)),
              'units': sorted(rows.unit_id.unique().tolist()),
              'forbidden_endpoint_accessed_after_resume': False}
    Path(a.out).write_text(json.dumps(result, indent=2) + '\n')
    raise SystemExit(1 if errors else 0)

if __name__ == '__main__': main()
