"""k1_evaluator_forensics.py — K1 evaluator forensics on PSC/DIOR-R/seed0 (full DIOR test).

Runs ONE prediction set through both evaluators to isolate the Table-1 (S1a) vs Table-7
(DOTAMetric) AP口径 gap:
  (a) DOTAMetric reference: AP50=0.531 from the training val log (authoritative, MMRotate).
  (b) project S1a evaluator: import evaluate() from s1a_full_pipeline_perturb_v1 and run on the
      SAME (preds, full-val gts) records.
  (c) our rotated VOC-AP (eval_r1_run.rotated_ap), already validated == DOTAMetric (diff 5e-4).
Reports per-class AP diff + a protocol-alignment table. Also reports the FULL DIOR test GT count
vs the DIOR#22 frozen n_gt=35436 (the Table-1 cell used a partial/ephemeral GT now missing).
Single GPU. Writes reports/k1_* + docs/k1_evaluator_forensics inputs.
"""
import os, sys, json, math, csv, time, importlib.util
import numpy as np, torch
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench")
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055")
import mmrotate, mmrotate.models, mmrotate.datasets
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmengine.runner import load_checkpoint
from mmrotate.registry import MODELS, DATASETS, TASK_UTILS
init_default_scope("mmrotate")
ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"

# import s1a evaluate()
spec = importlib.util.spec_from_file_location(
    "s1a", f"{ROOT}/top_journal_v3_reaudit_055/scripts/s1a_full_pipeline_perturb_v1.py")
# s1a imports FMT from a csv at module load; guard cwd
os.chdir(ROOT)
s1a = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(s1a)
except Exception as e:
    print("note: s1a module load side-effect:", e)

def our_rotated_ap(dets_by_cls, gts_by_cls, iou_thr, iou_calc):
    aps = {}
    for c, gts in gts_by_cls.items():
        n_gt = sum(len(v) for v in gts.values())
        if n_gt == 0: continue
        dets = sorted(dets_by_cls.get(c, []), key=lambda d: -d[0])
        tp = np.zeros(len(dets)); fp = np.zeros(len(dets)); matched = {}
        for i, (sc, img, box) in enumerate(dets):
            gl = gts.get(img, [])
            if not gl: fp[i] = 1; continue
            gb = torch.stack(gl); ious = iou_calc(box.unsqueeze(0), gb).squeeze(0)
            j = int(ious.argmax()); best = float(ious[j])
            if best >= iou_thr and (img, j) not in matched: tp[i] = 1; matched[(img, j)] = True
            else: fp[i] = 1
        tpc = np.cumsum(tp); fpc = np.cumsum(fp)
        rec = tpc / (n_gt + 1e-9); prec = tpc / np.maximum(tpc + fpc, 1e-9)
        ap = 0.0
        for t in np.linspace(0, 1, 11):
            p = prec[rec >= t].max() if (rec >= t).any() else 0.0
            ap += p / 11
        aps[c] = ap
    return aps

def main():
    cfg = Config.fromfile(f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder/psc_dior_seed0.py")
    classes = cfg.val_dataloader["dataset"]["metainfo"]["classes"]
    model = MODELS.build(cfg.model)
    wd = f"{ROOT}/top_journal_v3_reaudit_055/work_dirs/r1/PSC__DIOR-R__seed0"
    load_checkpoint(model, f"{wd}/epoch_12.pth", map_location="cpu"); model.eval().cuda()
    ds = DATASETS.build(cfg.val_dataloader["dataset"])
    iou_calc = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))
    preds_rec, gts_rec = [], []
    dets_by_cls, gts_by_cls = {}, {}
    cap = int(os.environ.get("K1_MAX_IMAGES", "0"))
    n_img = len(ds) if cap == 0 else min(cap, len(ds))
    t0 = time.time()
    with torch.no_grad():
        for i in range(n_img):
            d = ds[i]; img_id = d["data_samples"].img_id
            gt = d["data_samples"].gt_instances
            gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).cpu()
            gl = gt.labels.cpu()
            dd = model.data_preprocessor(dict(inputs=[d["inputs"].cuda()],
                                              data_samples=[d["data_samples"].cuda()]), False)
            pi = model.predict(dd["inputs"], dd["data_samples"])[0].pred_instances
            pb = (pi.bboxes.tensor if hasattr(pi.bboxes, "tensor") else pi.bboxes).cpu()
            ps = pi.scores.cpu(); pl = pi.labels.cpu()
            for k in range(gb.shape[0]):
                c = int(gl[k])
                gts_rec.append(dict(image_id=img_id, class_name=classes[c],
                    obb_cx=float(gb[k,0]), obb_cy=float(gb[k,1]), obb_w=float(gb[k,2]),
                    obb_h=float(gb[k,3]), obb_theta=float(gb[k,4])))
                gts_by_cls.setdefault(c, {}).setdefault(img_id, []).append(gb[k])
            for k in range(pb.shape[0]):
                c = int(pl[k])
                preds_rec.append(dict(image_id=img_id, class_name=classes[c], score=float(ps[k]),
                    obb_cx=float(pb[k,0]), obb_cy=float(pb[k,1]), obb_w=float(pb[k,2]),
                    obb_h=float(pb[k,3]), obb_theta=float(pb[k,4])))
                dets_by_cls.setdefault(c, []).append((float(ps[k]), img_id, pb[k]))
            if (i+1) % 2000 == 0: print(f"infer {i+1}/{n_img} ({(time.time()-t0)/60:.1f}min)", flush=True)
    print(f"inference done: n_pred={len(preds_rec)} n_gt_FULL={len(gts_rec)} ({(time.time()-t0)/60:.1f}min)", flush=True)

    # (b) s1a evaluator on SAME records
    ap_s1a, mAP_s1a, _, fp_s1a = s1a.evaluate(preds_rec, gts_rec)
    # (c) our rotated AP
    ap50_ours = our_rotated_ap(dets_by_cls, gts_by_cls, 0.5, iou_calc)
    ap75_ours = our_rotated_ap(dets_by_cls, gts_by_cls, 0.75, iou_calc)
    mAP50_ours = float(np.mean(list(ap50_ours.values()))); mAP75_ours = float(np.mean(list(ap75_ours.values())))

    print(f"\n=== AP50: s1a={mAP_s1a[0.5]:.4f}  ours(VOC)={mAP50_ours:.4f}  DOTAMetric_ref=0.5310")
    print(f"=== AP75: s1a={mAP_s1a[0.75]:.4f}  ours(VOC)={mAP75_ours:.4f}")
    print(f"=== full-val GT count={len(gts_rec)} vs DIOR#22 frozen n_gt=35436 (Table-1 partial GT)")

    # per-class diff CSV
    name = {i: c for i, c in enumerate(classes)}
    rows = []
    allc = set(ap_s1a[0.5]) | set(ap50_ours) | set(name)
    for c in sorted(ap50_ours):
        s = ap_s1a[0.5].get(classes[c], float("nan"))
        rows.append(dict(cls=classes[c], AP50_s1a=round(s, 4), AP50_ours=round(ap50_ours[c], 4),
                         diff=round(s - ap50_ours[c], 4)))
    with open(f"{REP}/k1_evaluator_diff_per_class.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cls", "AP50_s1a", "AP50_ours", "diff"]); w.writeheader(); w.writerows(rows)
    # protocol alignment
    align = [
        dict(item="dataset_split", value="DIOR-R trainval->test (both)"),
        dict(item="n_classes", value=len(classes)),
        dict(item="class_averaging", value="macro (per-class mean) both"),
        dict(item="IoU", value="rotated polygon IoU both"),
        dict(item="angle_convention", value="le90 canonical long-side both"),
        dict(item="AP_interpolation", value="s1a=VOC all-points; ours=VOC 11-point; DOTAMetric=VOC 11-point"),
        dict(item="full_val_GT_count", value=len(gts_rec)),
        dict(item="DIOR22_frozen_n_gt", value=35436),
        dict(item="DOTAMetric_ref_AP50", value=0.5310),
        dict(item="checkpoint_baseline_ownAP50", value=0.5370),
        dict(item="AP50_s1a_on_fullval", value=round(mAP_s1a[0.5], 4)),
        dict(item="AP50_ours_on_fullval", value=round(mAP50_ours, 4)),
        dict(item="Table1_DIOR22_reported", value=0.6964),
    ]
    with open(f"{REP}/k1_metric_protocol_alignment.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["item", "value"]); w.writeheader(); w.writerows(align)
    json.dump(dict(mAP50_s1a=mAP_s1a[0.5], mAP75_s1a=mAP_s1a[0.75], mAP50_ours=mAP50_ours,
                   mAP75_ours=mAP75_ours, n_pred=len(preds_rec), n_gt_full=len(gts_rec)),
              open(f"{REP}/k1_summary.json", "w"), indent=2)
    print("WROTE k1 reports")

if __name__ == "__main__":
    main()
