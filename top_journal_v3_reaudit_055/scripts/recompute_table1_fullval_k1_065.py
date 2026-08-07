"""recompute_table1_fullval_k1_065.py <cell_key> — recompute one Table-1 cell on full-val GT.

Uses the K1-validated torch rotated AP (RBboxOverlaps2D, == DOTAMetric within 0.0014), NOT the
slow Shapely s1a loop. Reads persisted full-val predictions + the persistent full-val GT built by
build_k1_fullval_gt_065.py. Applies the same constrained angle perturbation as s1a (perturb only
TP@0.5 preds by their per-instance eps_max keeping rIoU>0.5 away from the matched GT), recomputes
AP + angle error. Emits base/perturbed AP50/AP75, ΔAP, FP@0.5, angle error, GT/pred sha256.
No training; inference-free (predictions already persisted).
"""
import os, sys, json, math, csv, hashlib, time
import numpy as np, torch
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench")
import mmrotate, mmrotate.models
from mmrotate.registry import TASK_UTILS
ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
GTD = f"{ROOT}/outputs/persistent_artifacts/k1_table1_fullval_065/gt"
iou_calc = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))
DEV = "cuda" if torch.cuda.is_available() else "cpu"

CELLS = {
    "DIOR-R/22": dict(pred=f"{ROOT}/outputs/persistent_artifacts/orientbench_v2/DIOR-R/22/schema/pred_b22_fullval.jsonl",
                      gt=f"{GTD}/DIOR-R_test_fullval_gt.jsonl", detector="rotated_retinanet_psc"),
    "DIOR-R/3":  dict(pred=f"{ROOT}/outputs/persistent_artifacts/orientbench_v2/DIOR-R/3/schema/pred_b3_fullval.jsonl",
                      gt=f"{GTD}/DIOR-R_test_fullval_gt.jsonl", detector="oriented_rcnn"),
    "SODA-A/23": dict(pred=f"{ROOT}/outputs/persistent_artifacts/orientbench_v2/SODA-A/23/schema/pred_b23_fullval.jsonl",
                      gt=f"{GTD}/SODA-A_val_tiled_fullval_gt.jsonl", detector="rotated_retinanet_psc"),
}

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def load(p):
    return [json.loads(l) for l in open(p)]

def rbox(o):
    return [o["obb_cx"], o["obb_cy"], o["obb_w"], o["obb_h"], o["obb_theta"]]

def long_axis(w, h, t):
    return t if w >= h else t + math.pi / 2

def ang_err(w1, h1, t1, w2, h2, t2):
    d = abs(long_axis(w1, h1, t1) - long_axis(w2, h2, t2)) % math.pi
    return math.degrees(min(d, math.pi - d))

def voc_ap(tp, scores, n_gt):
    if n_gt == 0: return float("nan")
    order = np.argsort(-np.asarray(scores), kind="stable"); tp = np.asarray(tp)[order]
    fp = 1 - tp; ctp = np.cumsum(tp); cfp = np.cumsum(fp)
    rec = ctp / n_gt; prec = ctp / np.maximum(ctp + cfp, 1e-9)
    ap = 0.0
    for t in np.linspace(0, 1, 11):
        p = prec[rec >= t].max() if (rec >= t).any() else 0.0
        ap += p / 11
    return ap

def eval_cell(preds, gts, return_tau_matches=False):
    """Return (mAP50, mAP75, fp50, angle_errs, tp_matches). Batched IoU per (image,class):
    compute the pred x GT IoU matrix once per image-class, then greedy-match in score order."""
    from collections import defaultdict
    P = defaultdict(list); G = defaultdict(list)
    for i, p in enumerate(preds):
        P[(p["image_id"], p["class_name"])].append((i, p))
    for g in gts:
        G[(g["image_id"], g["class_name"])].append(g)
    gt_count = defaultdict(int)
    for (img, c), l in G.items(): gt_count[c] += len(l)
    classes = set(c for _, c in P) | set(c for _, c in G)
    ap = {0.5: {}, 0.75: {}}; fp50 = 0; tp_matches = []; tp_matches75 = []; aerrs = []
    for cls in classes:
        # gather images with preds or gt for this class
        imgs = set(img for (img, c) in P if c == cls) | set(img for (img, c) in G if c == cls)
        # precompute IoU matrix per image (preds sorted by score within image)
        cache = {}  # img -> (pred_idx_list, pred_dicts, gt_list, iou[np NxM])
        for img in imgs:
            pl = sorted(P.get((img, cls), []), key=lambda x: -x[1]["score"])
            gl = G.get((img, cls), [])
            if pl and gl:
                pb = torch.tensor([rbox(p) for _, p in pl], dtype=torch.float32, device=DEV)
                gb = torch.tensor([rbox(g) for g in gl], dtype=torch.float32, device=DEV)
                iou = iou_calc(pb, gb).cpu().numpy()
            else:
                iou = None
            cache[img] = (pl, gl, iou)
        # global score order across images
        allp = [(img, k) for img in imgs for k in range(len(cache[img][0]))]
        allp.sort(key=lambda x: -cache[x[0]][0][x[1]][1]["score"])
        for tau in (0.5, 0.75):
            used = {img: [False] * len(cache[img][1]) for img in imgs}
            tp = np.zeros(len(allp)); sc = np.zeros(len(allp))
            for n, (img, k) in enumerate(allp):
                pl, gl, iou = cache[img]; i, p = pl[k]; sc[n] = p["score"]
                if iou is None: continue
                row = iou[k]; j = int(row.argmax()); best = float(row[j])
                if best >= tau and not used[img][j]:
                    used[img][j] = True; tp[n] = 1
                    if tau == 0.5:
                        g = gl[j]; tp_matches.append((i, g))
                        aerrs.append(ang_err(p["obb_w"], p["obb_h"], p["obb_theta"],
                                             g["obb_w"], g["obb_h"], g["obb_theta"]))
                    elif return_tau_matches:
                        tp_matches75.append((i, gl[j]))
                elif tau == 0.5:
                    fp50 += 1
            ap[tau][cls] = voc_ap(tp, sc, gt_count.get(cls, 0))
    mAP = {t: float(np.nanmean([v for v in ap[t].values() if v == v])) if ap[t] else float("nan") for t in ap}
    if return_tau_matches:
        return mAP[0.5], mAP[0.75], fp50, aerrs, tp_matches, tp_matches75
    return mAP[0.5], mAP[0.75], fp50, aerrs, tp_matches

def eps_max(p, g):
    grid = torch.arange(1.0, 70.0, 1.0)
    gb = torch.tensor([rbox(g)], dtype=torch.float32, device=DEV)
    # sign: away from matched gt long-axis
    s0 = ((long_axis(p["obb_w"], p["obb_h"], p["obb_theta"]) -
           long_axis(g["obb_w"], g["obb_h"], g["obb_theta"]) + math.pi / 2) % math.pi) - math.pi / 2
    d = 1.0 if s0 >= 0 else -1.0
    rb = torch.tensor([[p["obb_cx"], p["obb_cy"], p["obb_w"], p["obb_h"],
                        p["obb_theta"] + math.radians(d * float(dd))] for dd in grid],
                      dtype=torch.float32, device=DEV)
    ious = iou_calc(rb, gb).squeeze(1)
    ok = (ious > 0.5)
    best = 0.0
    for k in range(len(grid)):
        if ok[k]: best = float(grid[k])
        else: break
    return d, best

def main():
    key = sys.argv[1]; c = CELLS[key]
    t0 = time.time()
    preds = load(c["pred"]); gts = load(c["gt"])
    print(f"[{key}] n_pred={len(preds)} n_gt={len(gts)} loaded ({(time.time()-t0):.0f}s)", flush=True)
    b50, b75, fp0, be, tpm = eval_cell(preds, gts)
    print(f"[{key}] BASE AP50={b50:.4f} AP75={b75:.4f} FP@0.5={fp0} angle_mean={np.mean(be):.2f}", flush=True)
    # perturb TP@0.5
    pert = [dict(p) for p in preds]; pe = []
    for i, g in tpm:
        d, em = eps_max(preds[i], g)
        pert[i]["obb_theta"] = preds[i]["obb_theta"] + math.radians(d * em)
        pe.append(ang_err(pert[i]["obb_w"], pert[i]["obb_h"], pert[i]["obb_theta"],
                          g["obb_w"], g["obb_h"], g["obb_theta"]))
    p50, p75, pfp0, _, _ = eval_cell(pert, gts)
    print(f"[{key}] PERT AP50={p50:.4f} AP75={p75:.4f} FP@0.5={pfp0} angle_mean={np.mean(pe):.2f}", flush=True)
    row = dict(cell=key, detector=c["detector"], n_pred=len(preds), n_gt_fullval=len(gts),
               base_AP50=round(b50, 4), pert_AP50=round(p50, 4), dAP50=round(p50 - b50, 4),
               base_AP75=round(b75, 4), pert_AP75=round(p75, 4), dAP75=round(p75 - b75, 4),
               FP50_base=fp0, FP50_pert=pfp0,
               angle_err_base=round(float(np.mean(be)), 3), angle_err_pert=round(float(np.mean(pe)), 3),
               evaluator="torch_RBboxOverlaps2D_VOC11 (K1-validated == DOTAMetric)",
               gt_sha256=sha(c["gt"])[:16], pred_sha256=sha(c["pred"])[:16], can_recompute="yes",
               command=f"python recompute_table1_fullval_k1_065.py {key}")
    os.makedirs(f"{REP}/k1_table1", exist_ok=True)
    json.dump(row, open(f"{REP}/k1_table1/{key.replace('/','_')}.json", "w"), indent=2)
    print(f"[{key}] WROTE result ({(time.time()-t0)/60:.1f}min)", flush=True)

if __name__ == "__main__":
    main()
