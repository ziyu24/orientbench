"""k3_gt_angle_noise_proxy_audit_066.py — GT angle-noise floor via corner-jitter refit proxy.

No human double-annotation available -> proxy: for each sampled GT box, reconstruct its 4 corners,
add Gaussian corner jitter of sigma=JITTER_PX pixels (annotation precision), refit the OBB angle
(cv2.minAreaRect, le90 long-side), repeat N times; the std of the refit angle = per-instance angle
noise floor sigma_gt(px-precision). Reports mean/std/median/p90/p95 + P(noise>2 deg), P(noise>5 deg)
by dataset and by ar/size/class, and specifically the masked ar>=1.6 region. Frozen assets untouched.

Interpretation: this is the angle uncertainty implied by a fixed ~JITTER_PX annotation precision; it
is a lower-bound-style proxy for the true label-noise floor (真人双标为后续 blocker).
"""
import os, json, glob, csv, math, sys
import numpy as np
import cv2

ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
GTD = f"{ROOT}/outputs/persistent_artifacts/k1_table1_fullval_065/gt"
LOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/k3_gt_angle_noise_audit_066.log"
JITTER_PX = 2.0
N_JIT = 30
SAMPLE = 500
RNG = np.random.RandomState(20260708)

def lg(m): open(LOG, "a").write(m + "\n"); print(m, flush=True)

def corners(cx, cy, w, h, t):
    c, s = math.cos(t), math.sin(t)
    dx = [-w/2, w/2, w/2, -w/2]; dy = [-h/2, -h/2, h/2, h/2]
    return np.array([[cx + dx[i]*c - dy[i]*s, cy + dx[i]*s + dy[i]*c] for i in range(4)], dtype=np.float32)

def le90_angle(pts):
    (_, _), (w, h), ang = cv2.minAreaRect(pts.astype(np.float32))
    # long-side angle in radians, le90
    if w >= h: a = math.radians(ang)
    else: a = math.radians(ang + 90)
    # wrap to [-pi/2, pi/2)
    a = (a + math.pi/2) % math.pi - math.pi/2
    return a

def ang_diff(a, b):
    d = abs(a - b) % math.pi
    return math.degrees(min(d, math.pi - d))

def sigma_gt(cx, cy, w, h, t):
    base = corners(cx, cy, w, h, t)
    a0 = le90_angle(base)
    diffs = []
    for _ in range(N_JIT):
        jit = base + RNG.normal(0, JITTER_PX, base.shape).astype(np.float32)
        try: diffs.append(ang_diff(le90_angle(jit), a0))
        except Exception: pass
    return float(np.std(diffs)) if diffs else float("nan"), float(np.mean(diffs)) if diffs else float("nan")

def size_bin(area):
    if area < 32**2: return "small"
    if area < 96**2: return "medium"
    return "large"

def stats(vals):
    v = np.array([x for x in vals if x == x])
    if len(v) == 0: return {}
    return dict(n=len(v), mean=round(float(v.mean()), 3), std=round(float(v.std()), 3),
                median=round(float(np.median(v)), 3), p90=round(float(np.percentile(v, 90)), 3),
                p95=round(float(np.percentile(v, 95)), 3),
                P_gt2=round(float((v > 2).mean()), 4), P_gt5=round(float((v > 5).mean()), 4))

def main():
    open(LOG, "w").close()
    lg(f"K3 proxy: corner jitter sigma={JITTER_PX}px, N={N_JIT}, sample={SAMPLE}/dataset")
    by_ds = []; by_group = []
    for gt in sorted(glob.glob(f"{GTD}/*_fullval_gt.jsonl")):
        name = os.path.basename(gt).replace("_fullval_gt.jsonl", "")
        recs = [json.loads(l) for l in open(gt)]
        if not recs: continue
        idx = RNG.choice(len(recs), min(SAMPLE, len(recs)), replace=False)
        rows = [recs[i] for i in idx]
        per = []; masked = []; groups = {}
        for o in rows:
            w, h, t = o["obb_w"], o["obb_h"], o["obb_theta"]
            if min(w, h) < 1e-3: continue
            sg, mn = sigma_gt(o["obb_cx"], o["obb_cy"], w, h, t)
            if sg != sg: continue
            ar = max(w, h)/min(w, h); area = w*h
            per.append(sg)
            if ar >= 1.6: masked.append(sg)
            arb = "ar<1.6" if ar < 1.6 else ("1.6<=ar<2.1" if ar < 2.1 else "ar>=2.1")
            for key in [("ar", arb), ("size", size_bin(area)), ("class", o["class_name"])]:
                groups.setdefault(key, []).append(sg)
        st = stats(per); stm = stats(masked)
        by_ds.append(dict(dataset=name, **{f"all_{k}": v for k, v in st.items()},
                          **{f"masked_ar1.6_{k}": v for k, v in stm.items()}))
        lg(f"[{name}] all: mean={st.get('mean')} p90={st.get('p90')} P(>2)={st.get('P_gt2')} P(>5)={st.get('P_gt5')} "
           f"| masked ar>=1.6: mean={stm.get('mean')} p90={stm.get('p90')} P(>5)={stm.get('P_gt5')}")
        for (dim, val), vals in sorted(groups.items()):
            s = stats(vals); by_group.append(dict(dataset=name, dim=dim, group=val, **s))
    with open(f"{REP}/k3_gt_angle_noise_by_dataset.csv", "w", newline="") as f:
        cols = sorted(set().union(*[r.keys() for r in by_ds]))
        w = csv.DictWriter(f, fieldnames=["dataset"] + [c for c in cols if c != "dataset"], extrasaction="ignore")
        w.writeheader(); w.writerows(by_ds)
    with open(f"{REP}/k3_gt_angle_noise_by_ar_size_class_066.csv", "w", newline="") as f:
        cols = sorted(set().union(*[r.keys() for r in by_group]))
        w = csv.DictWriter(f, fieldnames=["dataset", "dim", "group"] + [c for c in cols if c not in ("dataset","dim","group")], extrasaction="ignore")
        w.writeheader(); w.writerows(by_group)
    lg("WROTE k3 reports")

if __name__ == "__main__":
    main()
