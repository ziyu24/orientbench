"""recompute_table1_by_inference_065.py — full-val re-inference recompute of Table-1 cells.

The frozen persisted predictions are on a wrong/partial image set (zero overlap with the full
test GT) and/or lost (/dev/shm), so Table-1 must be recomputed by re-running each frozen baseline
checkpoint on the CORRECT full-val split. Uses the K1-validated evaluator (torch RBboxOverlaps2D
VOC-AP == DOTAMetric within 0.0014) + gt_instances from the dataloader (exact convention). Adds
the constrained angle perturbation (perturb TP@0.5 by eps_max keeping rIoU>0.5). No training.
FAIR1M excluded (dataset dir split_ss_fair1m1.0 missing -> documented blocker). Robust per-cell:
logs blocker + continues. Writes per-cell JSON + a status CSV + heartbeat.
"""
import os, sys, json, math, csv, time
import numpy as np, torch
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench")
import mmrotate, mmrotate.models, mmrotate.datasets
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmengine.runner import load_checkpoint
from mmrotate.registry import MODELS, DATASETS, TASK_UTILS
init_default_scope("mmrotate")
ROOT = "/home/rspip/cqc/pro/study/orientbench"
PTH = "/home/rspip/cqc/pro/study/pth_data"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
LOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/k1_table1_fullval_recompute_065.log"
os.makedirs(f"{REP}/k1_table1", exist_ok=True)
iou_calc = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))

CELLS = [
    dict(cell="DIOR-R/22", det="rotated_retinanet_psc",
         cfg=f"{PTH}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py",
         ckpt=f"{PTH}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth"),
    dict(cell="DIOR-R/3", det="oriented_rcnn",
         cfg=f"{PTH}/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/cell03_orcnn_dior_sgd_lr020.py",
         ckpt=f"{PTH}/baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/best_dota_mAP_epoch_11.pth"),
    dict(cell="DIOR-R/61", det="rotated_rtmdet_s",
         cfg=f"{PTH}/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py",
         ckpt=f"{PTH}/baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/best_mAP_5489_epoch_32.pth"),
    dict(cell="SODA-A/23", det="rotated_retinanet_psc",
         cfg=f"{PTH}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py",
         ckpt=f"{PTH}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/best_mAP_5991_epoch_12.pth"),
    dict(cell="SODA-A/4", det="oriented_rcnn",
         cfg=f"{PTH}/baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/config.py",
         ckpt=f"{PTH}/baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/best_mAP_7295_epoch_09.pth"),
    dict(cell="FAIR1M-v1.0/24", det="rotated_retinanet_psc",
         cfg=f"{PTH}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py",
         ckpt=f"{PTH}/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/best_mAP_3462_epoch_12.pth",
         gt_jsonl=f"{ROOT}/outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl",
         img_root=f"{ROOT}/top_journal_v3_reaudit_055/data_prep/FAIR1M_val20"),
]

def lg(m): open(LOG, "a").write(f"[{time.strftime('%F %T')}] {m}\n"); print(m, flush=True)

def long_axis(w, h, t): return t if w >= h else t + math.pi / 2
def ang_err(w1, h1, t1, w2, h2, t2):
    d = abs(long_axis(w1, h1, t1) - long_axis(w2, h2, t2)) % math.pi
    return math.degrees(min(d, math.pi - d))
def voc_ap(tp, sc, n_gt):
    if n_gt == 0: return float("nan")
    o = np.argsort(-sc, kind="stable"); tp = tp[o]
    ctp = np.cumsum(tp); cfp = np.cumsum(1 - tp)
    rec = ctp / n_gt; prec = ctp / np.maximum(ctp + cfp, 1e-9)
    return float(sum((prec[rec >= t].max() if (rec >= t).any() else 0.0) / 11 for t in np.linspace(0, 1, 11)))

def eval_dets(dets_by_cls, gts_by_cls, tau, want_match=False):
    aps = {}; matches = []
    for c, gts in gts_by_cls.items():
        n_gt = sum(len(v) for v in gts.values())
        if n_gt == 0: continue
        dets = sorted(dets_by_cls.get(c, []), key=lambda d: -d[0])
        tp = np.zeros(len(dets)); sc = np.zeros(len(dets)); used = {}
        for i, (s, img, box, pidx) in enumerate(dets):
            sc[i] = s; gl = gts.get(img, [])
            if not gl: continue
            gb = torch.stack(gl); ious = iou_calc(box.unsqueeze(0).cuda(), gb.cuda()).squeeze(0).cpu()
            j = int(ious.argmax())
            if float(ious[j]) >= tau and (img, j) not in used:
                tp[i] = 1; used[(img, j)] = 1
                if want_match: matches.append((pidx, gl[j]))
        aps[c] = voc_ap(tp, sc, n_gt)
    mAP = float(np.nanmean([v for v in aps.values() if v == v])) if aps else float("nan")
    return mAP, matches

DIOR_PREP = f"{ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR"

def recompute(cell):
    cfg = Config.fromfile(cell["cfg"])
    model = MODELS.build(cfg.model); load_checkpoint(model, cell["ckpt"], map_location="cpu")
    model.eval().cuda()
    vd = cfg.val_dataloader["dataset"]
    # DIOR configs point to a shared annfiles_dotaformat/test that only exists in our data_prep;
    # repoint the eval split to the persistent data_prep (annfiles + symlinked images).
    if cell["cell"].startswith("DIOR-R"):
        vd["data_root"] = f"{DIOR_PREP}/"
        vd["ann_file"] = "annfiles_dotaformat/test/"
        vd["data_prefix"] = dict(img_path="dotaformat_images/test/")
        vd["img_suffix"] = "jpg"
    # FAIR1M: dataloader reads images from the val_20 prep (DOTA-txt for image listing);
    # GT is taken from the persistent jsonl (spaced class names -> metainfo index), bypassing
    # the DOTA-txt multi-word-class encoding problem.
    gt_from_jsonl = None
    if cell.get("gt_jsonl"):
        vd["data_root"] = f"{cell['img_root']}/"
        vd["ann_file"] = "annfiles_dotaformat/"
        vd["data_prefix"] = dict(img_path="images/")
        vd["img_suffix"] = "png"
        classes = list(cfg.val_dataloader["dataset"]["metainfo"]["classes"])
        cidx = {c: i for i, c in enumerate(classes)}
        gt_from_jsonl = {}
        for line in open(cell["gt_jsonl"]):
            o = json.loads(line); ci = cidx.get(o["class_name"])
            if ci is None: continue
            gt_from_jsonl.setdefault(o["image_id"], []).append(
                (ci, torch.tensor([o["obb_cx"], o["obb_cy"], o["obb_w"], o["obb_h"], o["obb_theta"]])))
    ds = DATASETS.build(vd)
    lg(f"{cell['cell']}: loaded, n_eval={len(ds)}")
    dets, gts = {}, {}; preds_store = {}
    t0 = time.time()
    with torch.no_grad():
        for i in range(len(ds)):
            d = ds[i]; img = d["data_samples"].img_id
            if gt_from_jsonl is not None:
                gl_list = gt_from_jsonl.get(img, [])
                gb = torch.stack([b for _, b in gl_list]) if gl_list else torch.zeros(0, 5)
                gl = torch.tensor([c for c, _ in gl_list], dtype=torch.long) if gl_list else torch.zeros(0, dtype=torch.long)
            else:
                gt = d["data_samples"].gt_instances
                gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).cpu(); gl = gt.labels.cpu()
            dd = model.data_preprocessor(dict(inputs=[d["inputs"].cuda()],
                                              data_samples=[d["data_samples"].cuda()]), False)
            pi = model.predict(dd["inputs"], dd["data_samples"])[0].pred_instances
            pb = (pi.bboxes.tensor if hasattr(pi.bboxes, "tensor") else pi.bboxes).cpu()
            ps = pi.scores.cpu(); pl = pi.labels.cpu()
            for k in range(gb.shape[0]):
                gts.setdefault(int(gl[k]), {}).setdefault(img, []).append(gb[k])
            for k in range(pb.shape[0]):
                pidx = len(preds_store)
                preds_store[pidx] = [float(pb[k,0]), float(pb[k,1]), float(pb[k,2]), float(pb[k,3]), float(pb[k,4])]
                dets.setdefault(int(pl[k]), []).append((float(ps[k]), img, pb[k], pidx))
            if (i+1) % 3000 == 0: lg(f"{cell['cell']}: infer {i+1}/{len(ds)} ({(time.time()-t0)/60:.1f}min)")
    n_gt = sum(len(v) for cls in gts.values() for v in cls.values())
    ap50, m50 = eval_dets(dets, gts, 0.5, want_match=True)
    ap75, _ = eval_dets(dets, gts, 0.75)
    # base angle error + perturbation
    grid = torch.arange(1.0, 70.0, 1.0)
    be = []; pert_theta = {}
    for pidx, g in m50:
        pcx, pcy, pw, ph, pt = preds_store[pidx]
        gw, gh, gt_ = float(g[2]), float(g[3]), float(g[4])
        be.append(ang_err(pw, ph, pt, gw, gh, gt_))
        s0 = ((long_axis(pw, ph, pt) - long_axis(gw, gh, gt_) + math.pi/2) % math.pi) - math.pi/2
        dsign = 1.0 if s0 >= 0 else -1.0
        # eps_max uses the PRED's OWN center/size vs the matched GT box (the actual IoU the
        # re-evaluation will see) -> keeps perturbed pred a genuine TP@0.5 (constrained perturbation).
        gb1 = torch.tensor([[float(g[0]), float(g[1]), gw, gh, gt_]], dtype=torch.float32).cuda()
        rb = torch.tensor([[pcx, pcy, pw, ph, pt + math.radians(dsign*float(dd))] for dd in grid],
                          dtype=torch.float32).cuda()
        ious = iou_calc(rb, gb1).squeeze(1).cpu()
        em = 0.0
        for kk in range(len(grid)):
            if float(ious[kk]) > 0.5: em = float(grid[kk])
            else: break
        pert_theta[pidx] = pt + math.radians(dsign*em)
        pert_theta[(pidx,'ae')] = ang_err(pw, ph, pert_theta[pidx], gw, gh, gt_)
    # perturbed AP: rebuild dets with perturbed theta
    pdets = {}
    for c, lst in dets.items():
        for (s, img, box, pidx) in lst:
            b2 = box.clone()
            if pidx in pert_theta: b2[4] = pert_theta[pidx]
            pdets.setdefault(c, []).append((s, img, b2, pidx))
    pap50, _ = eval_dets(pdets, gts, 0.5); pap75, _ = eval_dets(pdets, gts, 0.75)
    pe = [pert_theta[(p, 'ae')] for p, _ in m50 if (p, 'ae') in pert_theta]
    row = dict(cell=cell["cell"], detector=cell["det"], n_pred=len(preds_store), n_gt_fullval=n_gt,
               base_AP50=round(ap50, 4), pert_AP50=round(pap50, 4), dAP50=round(pap50-ap50, 4),
               base_AP75=round(ap75, 4), pert_AP75=round(pap75, 4), dAP75=round(pap75-ap75, 4),
               angle_err_base=round(float(np.mean(be)), 3) if be else None,
               angle_err_pert=round(float(np.mean(pe)), 3) if pe else None,
               evaluator="torch_RBboxOverlaps2D_VOC11 (K1-validated==DOTAMetric)",
               ckpt=os.path.basename(cell["ckpt"]), can_recompute="yes",
               command=f"recompute_table1_by_inference_065.py {cell['cell']}")
    with open(f"{REP}/k1_table1/{cell['cell'].replace('/','_')}.json", "w") as _jf:
        json.dump(row, _jf, indent=2); _jf.flush()
    lg(f"{cell['cell']}: DONE base_AP50={ap50:.4f} dAP50={pap50-ap50:.4f} n_gt={n_gt} ({(time.time()-t0)/60:.1f}min)")

def main():
    # single-cell mode: `... <cell_key>` runs only that cell (for GPU-parallel launcher)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    cells = [c for c in CELLS if c["cell"] == only] if only else CELLS
    open(LOG, "a").write(f"\n[{time.strftime('%F %T')}] recompute start ({len(cells)} cell(s){' '+only if only else ''})\n")
    status = []
    for c in cells:
        done = os.path.isfile(f"{REP}/k1_table1/{c['cell'].replace('/','_')}.json")
        if done: status.append((c["cell"], "complete")); lg(f"SKIP {c['cell']} (done)"); continue
        try:
            recompute(c); status.append((c["cell"], "complete"))
        except Exception as e:
            status.append((c["cell"], f"blocker:{type(e).__name__}:{str(e)[:120]}"))
            lg(f"BLOCKER {c['cell']}: {type(e).__name__}: {e}")
    if not only:
        status.append(("FAIR1M-v1.0/24", "blocker:dataset split_ss_fair1m1.0 missing (GT unbuildable)"))
        with open(f"{REP}/k1_table1_recompute_status_065.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["cell", "status"]); w.writerows(status)
    lg("RECOMPUTE 065 END" + (f" [{only}]" if only else "") + ": " + "; ".join(f"{c}={s}" for c, s in status))

if __name__ == "__main__":
    main()
