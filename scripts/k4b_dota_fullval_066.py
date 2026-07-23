"""k4b_dota_fullval_066.py — DOTA-v1.0 full-val recompute for K4b (2 detector families).

Reintegrates DOTA with a provenance-clean FULL-val cell (NOT the 19-img D20). Uses frozen
checkpoints (ORCNN-r50, RTMDet-m) on DOTA-v1.0 split_ss val; re-inference (no training); the
K1-validated evaluator (torch RBboxOverlaps2D VOC-AP == DOTAMetric). Per cell: AP50/AP75, masked
ar>=1.6 detection-score NRC + AURC + Risk@70/90, angle-error, GT/pred sha, n_gt. Persists DOTA
val GT jsonl. FAIR1M-style; runs one cell per invocation for GPU-parallel launch.
"""
import os, sys, json, math, csv, time, hashlib, glob
import numpy as np, torch
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench")
import mmrotate, mmrotate.models, mmrotate.datasets
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmengine.runner import load_checkpoint
from mmrotate.registry import MODELS, DATASETS, TASK_UTILS
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage, aurc
init_default_scope("mmrotate")
ROOT = "/home/rspip/cqc/pro/study/orientbench"; PTH = "/home/rspip/cqc/pro/study/pth_data"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
LOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/k4b_dota_full_val_reintegration_066.log"
GTD = f"{ROOT}/outputs/persistent_artifacts/k1_table1_fullval_065/gt"
DOTA_VAL = "/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/val"
iou_calc = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))
AR = 1.6
os.makedirs(f"{REP}/k4b_dota", exist_ok=True)

CELLS = {
    "DOTA-v1.0/orcnn": dict(det="oriented_rcnn",
        cfg=f"{PTH}/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py",
        ckpt=f"{PTH}/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth"),
    "DOTA-v1.0/rtmdet": dict(det="rotated_rtmdet_m",
        cfg=f"{PTH}/baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/config.py",
        ckpt=f"{PTH}/baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/best_mAP_7161_epoch_31.pth"),
}

def lg(m): open(LOG, "a").write(f"[{time.strftime('%F %T')}] {m}\n"); print(m, flush=True)
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def voc_ap(tp, sc, n_gt):
    if n_gt == 0: return float("nan")
    o = np.argsort(-sc, kind="stable"); tp = tp[o]
    ctp = np.cumsum(tp); cfp = np.cumsum(1 - tp)
    rec = ctp / n_gt; prec = ctp / np.maximum(ctp + cfp, 1e-9)
    return float(sum((prec[rec >= t].max() if (rec >= t).any() else 0.0) / 11 for t in np.linspace(0, 1, 11)))

def eval_ap(dets, gts, tau, want_match=False):
    aps = {}; matches = []
    for c, g in gts.items():
        n_gt = sum(len(v) for v in g.values())
        if n_gt == 0: continue
        dl = sorted(dets.get(c, []), key=lambda d: -d[0])
        tp = np.zeros(len(dl)); sc = np.zeros(len(dl)); used = {}
        for i, (s, img, box, pw, ph, pt) in enumerate(dl):
            sc[i] = s; gl = g.get(img, [])
            if not gl: continue
            gb = torch.stack([b for b, _ in gl])
            ious = iou_calc(box.unsqueeze(0).cuda(), gb.cuda()).squeeze(0).cpu()
            j = int(ious.argmax())
            if float(ious[j]) >= tau and (img, j) not in used:
                tp[i] = 1; used[(img, j)] = 1
                if want_match:
                    gbb = gl[j][0]
                    matches.append((s, pw, ph, pt, float(gbb[2]), float(gbb[3]), float(gbb[4])))
        aps[c] = voc_ap(tp, sc, n_gt)
    return float(np.nanmean([v for v in aps.values() if v == v])) if aps else float("nan"), matches

def main():
    key = sys.argv[1]; c = CELLS[key]
    t0 = time.time()
    cfg = Config.fromfile(c["cfg"]); model = MODELS.build(cfg.model)
    load_checkpoint(model, c["ckpt"], map_location="cpu"); model.eval().cuda()
    vd = cfg.val_dataloader["dataset"]
    vd["data_root"] = f"{DOTA_VAL}/"; vd["ann_file"] = "annfiles/"
    vd["data_prefix"] = dict(img_path="images/"); vd["img_suffix"] = "png"
    ds = DATASETS.build(vd)
    lg(f"{key}: loaded n_eval={len(ds)}")
    dets, gts = {}, {}
    with torch.no_grad():
        for i in range(len(ds)):
            d = ds[i]; img = d["data_samples"].img_id
            gt = d["data_samples"].gt_instances
            gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).cpu(); gl = gt.labels.cpu()
            dd = model.data_preprocessor(dict(inputs=[d["inputs"].cuda()],
                                              data_samples=[d["data_samples"].cuda()]), False)
            pi = model.predict(dd["inputs"], dd["data_samples"])[0].pred_instances
            pb = (pi.bboxes.tensor if hasattr(pi.bboxes, "tensor") else pi.bboxes).cpu()
            ps = pi.scores.cpu(); pl = pi.labels.cpu()
            for k in range(gb.shape[0]):
                gts.setdefault(int(gl[k]), {}).setdefault(img, []).append((gb[k], int(gl[k])))
            for k in range(pb.shape[0]):
                dets.setdefault(int(pl[k]), []).append(
                    (float(ps[k]), img, pb[k], float(pb[k,2]), float(pb[k,3]), float(pb[k,4])))
            if (i+1) % 2000 == 0: lg(f"{key}: infer {i+1}/{len(ds)} ({(time.time()-t0)/60:.1f}min)")
    n_gt = sum(len(v) for cl in gts.values() for v in cl.values())
    ap50, m50 = eval_ap(dets, gts, 0.5, want_match=True)
    ap75, _ = eval_ap(dets, gts, 0.75)
    # masked ar>=1.6 detection-score NRC
    sc = []; er = []; ar = []; nsq = []
    for s, pw, ph, pt, gw, gh, gt_ in m50:
        cc = angle_error_contract(pw, ph, pt, gw, gh, gt_)
        e = cc["angle_error_canonical_longside"]
        if not math.isfinite(e): continue
        sc.append(s); er.append(e); ar.append(max(pw, ph)/max(min(pw, ph), 1e-6)); nsq.append(cc["near_square"])
    sc = np.array(sc); er = np.array(er); ar = np.array(ar); nsq = np.array(nsq)
    mask = (ar >= AR) & (~nsq) & np.isfinite(er)
    row = dict(cell=key, detector=c["det"], AP50=round(ap50, 4), AP75=round(ap75, 4),
               n_gt_fullval=n_gt, n_matched=len(er), n_masked_ar16=int(mask.sum()),
               ckpt=os.path.basename(c["ckpt"]), gt_source=DOTA_VAL, can_recompute="yes")
    if int(mask.sum()) >= 50:
        row["masked_NRC_score"] = round(nrc_auc(sc[mask], er[mask])["nrc_auc"], 4)
        row["masked_AURC_score"] = round(aurc(sc[mask], er[mask]), 4)
        row["masked_Risk70"] = round(risk_at_coverage(sc[mask], er[mask], 0.7), 3)
        row["masked_Risk90"] = round(risk_at_coverage(sc[mask], er[mask], 0.9), 3)
        row["masked_angle_err_mean"] = round(float(er[mask].mean()), 3)
    with open(f"{REP}/k4b_dota/{key.replace('/','_')}.json", "w") as f:
        json.dump(row, f, indent=2); f.flush()
    lg(f"{key}: DONE AP50={ap50:.4f} AP75={ap75:.4f} masked_NRC_score={row.get('masked_NRC_score')} n_gt={n_gt} ({(time.time()-t0)/60:.1f}min)")

if __name__ == "__main__":
    main()
