"""k4a_derive_mask_threshold_066.py — principle-derived masked ar threshold.

Geometry: for a centered rectangle of aspect ratio ar rotated by dtheta, compute IoU(dtheta;ar)
and the angle tolerance dtheta_tau(ar) = max dtheta keeping IoU>tau. Frozen engineering criterion
(set BEFORE running): an angle is "resolvable" at tau=0.75 iff a dtheta* = 15 deg perturbation
drops IoU below 0.75. The derived critical ar is the smallest ar whose dtheta_0.75(ar) <= 15 deg.
Reports dtheta_tau(ar) curve, derived ar*, and mask ratio (fraction ar>=thr) per dataset from the
persistent GT jsonls (ar>=1.3, ar>=1.6, derived-ar). No frozen asset is modified (analysis only).
"""
import os, json, glob, csv, math
import numpy as np
from shapely.geometry import Polygon
from shapely import affinity

ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
GTD = f"{ROOT}/outputs/persistent_artifacts/k1_table1_fullval_065/gt"
LOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/k4a_mask_threshold_principle_066.log"
DELTA_STAR_DEG = 15.0   # FROZEN engineering criterion at tau=0.75
TAU = 0.75

def lg(m): open(LOG, "a").write(m + "\n"); print(m, flush=True)

def rect(w, h):
    return Polygon([(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)])

def iou_rot(ar, dtheta_deg):
    w = math.sqrt(ar); h = 1.0/math.sqrt(ar)  # area=1, aspect ratio ar
    a = rect(w, h); b = affinity.rotate(rect(w, h), dtheta_deg, origin=(0, 0))
    inter = a.intersection(b).area; union = a.area + b.area - inter
    return inter/union if union > 0 else 0.0

def dtheta_tau(ar, tau):
    # largest integer-ish dtheta (0.5 deg grid) keeping IoU>tau
    best = 0.0
    for d in np.arange(0.5, 90.0, 0.5):
        if iou_rot(ar, float(d)) > tau: best = float(d)
        else: break
    return best

def main():
    open(LOG, "w").close()
    ars = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0]
    curve = []
    for ar in ars:
        d50 = dtheta_tau(ar, 0.5); d75 = dtheta_tau(ar, TAU)
        curve.append(dict(ar=ar, dtheta_tol_tau0_5_deg=d50, dtheta_tol_tau0_75_deg=d75))
    with open(f"{REP}/k4a_ar_threshold_sensitivity_066.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(curve[0].keys())); w.writeheader(); w.writerows(curve)
    # derived ar*: smallest ar with dtheta_0.75(ar) <= DELTA_STAR_DEG
    derived = None
    for ar in np.arange(1.0, 8.01, 0.05):
        if dtheta_tau(float(ar), TAU) <= DELTA_STAR_DEG:
            derived = round(float(ar), 2); break
    lg(f"FROZEN criterion: at tau={TAU}, angle resolvable iff dtheta_tol <= {DELTA_STAR_DEG} deg")
    lg(f"derived ar* = {derived}  (dtheta_0.75(ar*) <= {DELTA_STAR_DEG} deg)")
    lg("dtheta tolerance curve:")
    for c in curve: lg(f"  ar={c['ar']:<4} dtheta_tol@0.5={c['dtheta_tol_tau0_5_deg']:>5} deg  @0.75={c['dtheta_tol_tau0_75_deg']:>5} deg")

    # mask ratio per dataset from persistent GT jsonls
    thrs = {"ar>=1.3": 1.3, "ar>=1.6": 1.6, f"derived ar>={derived}": derived}
    rows = []
    for gt in sorted(glob.glob(f"{GTD}/*_fullval_gt.jsonl")):
        name = os.path.basename(gt).replace("_fullval_gt.jsonl", "")
        ar_all = []
        for line in open(gt):
            o = json.loads(line); w, h = o["obb_w"], o["obb_h"]
            if min(w, h) > 1e-6: ar_all.append(max(w, h)/min(w, h))
        ar_all = np.array(ar_all); n = len(ar_all)
        row = dict(dataset=name, n_gt=n,
                   frac_near_square_ar_lt_1_6=round(float((ar_all < 1.6).mean()), 4))
        for lbl, t in thrs.items():
            row[f"kept_{lbl}"] = round(float((ar_all >= t).mean()), 4)
            row[f"masked_out_{lbl}"] = round(float((ar_all < t).mean()), 4)
        rows.append(row)
    with open(f"{REP}/k4a_mask_ratio_by_dataset.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    lg("mask ratio by dataset:")
    for r in rows:
        lg(f"  {r['dataset']:22s} n={r['n_gt']:>7} kept@1.3={r['kept_ar>=1.3']} kept@1.6={r['kept_ar>=1.6']} "
           f"kept@derived({derived})={r.get(f'kept_derived ar>={derived}')}")
    print("DERIVED_AR", derived)

if __name__ == "__main__":
    main()
