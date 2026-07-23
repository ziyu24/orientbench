"""eval_r1_run.py <run_id> — full instrumented evaluation of ONE healthy R1 run.

Pipeline: build instrumented AngleBranch head -> load checkpoint -> run inference on the eval
split -> per image match predictions to the SAME gt_instances the evaluator uses (rotated IoU,
greedy by score, per class) -> per matched det compute canonical long-side angle_error (reuse
orientbench.metrics.angle_contract), aspect_ratio, and the head's NATIVE uncertainty from the
captured angle_encoded vector -> masked ar>=1.6: nrc_auc(native, err) and nrc_auc(score, err) +
AURC + Risk@70/90 + image-clustered bootstrap CI -> AP50/AP75 (self rotated-AP, cross-checked
vs the val-log AP50). Writes JSON + appends CSVs. Reuses FROZEN metrics; no threshold/split change.

Native uncertainty (confidence; higher = more confident):
  PSC -> phase_mod ; CSL -> softmax margin (top1-top2) ; DCL -> mean per-bit sigmoid margin.
"""
import os, sys, json, math, csv, time
import numpy as np
import torch
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench")
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055")
import orientbench_ext.instrumented_heads  # register
import mmrotate, mmrotate.models, mmrotate.datasets
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmengine.runner import load_checkpoint
from mmrotate.registry import MODELS, DATASETS, TASK_UTILS
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage, aurc
init_default_scope("mmrotate")

ROOT = "/home/rspip/cqc/pro/study/orientbench"
CFGDIR = f"{ROOT}/top_journal_v3_reaudit_055/configs/r1_angle_coder"
WDROOT = f"{ROOT}/top_journal_v3_reaudit_055/work_dirs/r1"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
LOGD = f"{ROOT}/top_journal_v3_reaudit_055/logs/r1_angle_coder"
AR_MASK = 1.6
iou_calc = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))

def parse_run(rid):
    head = rid.split("__")[0]; ds = rid.split("__")[1]; seed = rid.split("__")[2].replace("seed", "")
    dss = "dior" if ds == "DIOR-R" else "soda"
    hp = {"PSC": "psc", "CSL": "csl", "DCL": "dcl"}[head]
    cfg = f"{CFGDIR}/{hp}_{dss}_seed{seed}.py"
    if not os.path.isfile(cfg): cfg = f"{CFGDIR}/{hp}_{dss}_seed0.py"
    return head, ds, seed, cfg

def native_conf(head, enc, coder):
    if head == "PSC":
        ns = coder.num_step; cs = coder.coef_sin.to(enc); cc = coder.coef_cos.to(enc)
        psin = (enc[:, :ns] * cs).sum(-1); pcos = (enc[:, :ns] * cc).sum(-1)
        return (pcos**2 + psin**2)                      # phase_mod
    if head == "CSL":
        p = enc.softmax(-1); top2 = p.topk(2, dim=-1).values
        return (top2[:, 0] - top2[:, 1])                # margin
    if head == "DCL":
        pb = enc.sigmoid()
        return (2 * pb - 1).abs().mean(-1)              # mean bit margin
    raise ValueError(head)

def rotated_ap(dets_by_cls, gts_by_cls, iou_thr):
    """VOC-area rotated AP averaged over classes present in GT."""
    aps = []
    for c, gts in gts_by_cls.items():
        n_gt = sum(len(v) for v in gts.values())
        if n_gt == 0: continue
        dets = dets_by_cls.get(c, [])
        dets = sorted(dets, key=lambda d: -d[0])         # (score, img, box_tensor)
        tp = np.zeros(len(dets)); fp = np.zeros(len(dets)); matched = {}
        for i, (sc, img, box) in enumerate(dets):
            gl = gts.get(img, [])
            if not gl: fp[i] = 1; continue
            gb = torch.stack([g for g in gl])
            ious = iou_calc(box.unsqueeze(0), gb).squeeze(0)
            j = int(ious.argmax()); best = float(ious[j])
            if best >= iou_thr and (img, j) not in matched:
                tp[i] = 1; matched[(img, j)] = True
            else: fp[i] = 1
        tpc = np.cumsum(tp); fpc = np.cumsum(fp)
        rec = tpc / (n_gt + 1e-9); prec = tpc / np.maximum(tpc + fpc, 1e-9)
        ap = 0.0
        for t in np.linspace(0, 1, 11):
            p = prec[rec >= t].max() if (rec >= t).any() else 0.0
            ap += p / 11
        aps.append(ap)
    return float(np.mean(aps)) if aps else 0.0

def val_log_ap50(rid):
    import re
    p = f"{LOGD}/{rid}.log"
    if not os.path.isfile(p): return None
    m = re.findall(r"dota/AP50: ([0-9.]+)", open(p, errors="ignore").read())
    return float(m[-1]) if m else None

def image_bootstrap_ci(img_ids, conf, err, n_boot=1000):
    """Image-level clustered bootstrap of nrc_auc(conf, err)."""
    img_ids = np.asarray(img_ids); conf = np.asarray(conf); err = np.asarray(err)
    uniq = np.unique(img_ids); by = {u: np.where(img_ids == u)[0] for u in uniq}
    rng = np.random.RandomState(12345)
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([by[u] for u in pick])
        if idx.size < 50: continue
        try: vals.append(nrc_auc(conf[idx], err[idx])["nrc_auc"])
        except Exception: pass
    if not vals: return (float("nan"), float("nan"))
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))

def main():
    rid = sys.argv[1]
    head, ds, seed, cfgp = parse_run(rid)
    wd = f"{WDROOT}/{rid}"
    ckpt = f"{wd}/epoch_12.pth"
    if not os.path.isfile(ckpt):
        cand = [f for f in os.listdir(wd) if f.startswith("best_") and f.endswith(".pth")]
        ckpt = f"{wd}/{cand[0]}" if cand else None
    assert ckpt and os.path.isfile(ckpt), f"no checkpoint in {wd}"
    log = open(f"{LOGD}/eval_063.log", "a")
    def lg(m): log.write(f"[{time.strftime('%F %T')}] {rid}: {m}\n"); log.flush(); print(m, flush=True)

    cfg = Config.fromfile(cfgp)
    cfg.model.bbox_head.type = "InstrumentedAngleBranchRetinaHead"
    model = MODELS.build(cfg.model); load_checkpoint(model, ckpt, map_location="cpu")
    model.eval().cuda()
    coder = model.bbox_head.angle_coder
    ds_obj = DATASETS.build(cfg.val_dataloader["dataset"])
    lg(f"loaded ckpt={os.path.basename(ckpt)} n_eval_images={len(ds_obj)}")

    rec_score = []; rec_conf = []; rec_err = []; rec_ar = []; rec_nsq = []; rec_img = []
    dets_by_cls = {}; gts_by_cls = {}
    t0 = time.time()
    n_img = len(ds_obj)
    cap = int(os.environ.get("EVAL_MAX_IMAGES", "0"))
    if cap > 0: n_img = min(n_img, cap); lg(f"SMOKE cap n_img={n_img}")
    with torch.no_grad():
        for i in range(n_img):
            d = ds_obj[i]
            gt = d["data_samples"].gt_instances
            img_id = d["data_samples"].img_id
            dd = model.data_preprocessor(dict(inputs=[d["inputs"].cuda()],
                                              data_samples=[d["data_samples"].cuda()]), False)
            pi = model.predict(dd["inputs"], dd["data_samples"])[0].pred_instances
            pb = (pi.bboxes.tensor if hasattr(pi.bboxes, "tensor") else pi.bboxes).cpu()
            ps = pi.scores.cpu(); pl = pi.labels.cpu()
            conf = native_conf(head, pi.angle_encoded.float(), coder).cpu()
            gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes)
            gl = gt.labels
            # accumulate for AP (per class, per image)
            for c in torch.unique(torch.cat([pl, gl.cpu()]) if gl.numel() else pl):
                c = int(c)
                gts_by_cls.setdefault(c, {}).setdefault(img_id, [])
                dets_by_cls.setdefault(c, [])
            for k in range(gb.shape[0]):
                gts_by_cls.setdefault(int(gl[k]), {}).setdefault(img_id, []).append(gb[k].cpu())
            for k in range(pb.shape[0]):
                dets_by_cls.setdefault(int(pl[k]), {})  # ensure key
                dets_by_cls[int(pl[k])] = dets_by_cls.get(int(pl[k]), [])
                dets_by_cls[int(pl[k])].append((float(ps[k]), img_id, pb[k]))
            # match pred->gt for reliability records (greedy by score, per class, IoU>0.5)
            if pb.shape[0] and gb.shape[0]:
                order = torch.argsort(ps, descending=True)
                used = set()
                gb_cuda = gb.cuda()
                for k in order.tolist():
                    same = (gl.cpu() == int(pl[k])).nonzero(as_tuple=True)[0]
                    if same.numel() == 0: continue
                    ious = iou_calc(pb[k:k+1].cuda(), gb_cuda[same]).squeeze(0).cpu()
                    j = int(ious.argmax()); gj = int(same[j])
                    if float(ious[j]) < 0.5 or gj in used: continue
                    used.add(gj)
                    wp, hp, tp = float(pb[k, 2]), float(pb[k, 3]), float(pb[k, 4])
                    wg, hg, tg = float(gb[gj, 2]), float(gb[gj, 3]), float(gb[gj, 4])
                    c = angle_error_contract(wp, hp, tp, wg, hg, tg)
                    err = c["angle_error_canonical_longside"]
                    if not math.isfinite(err): continue
                    ar = max(wp, hp) / max(min(wp, hp), 1e-6)
                    rec_score.append(float(ps[k])); rec_conf.append(float(conf[k]))
                    rec_err.append(err); rec_ar.append(ar); rec_nsq.append(c["near_square"])
                    rec_img.append(img_id)
            if (i + 1) % 500 == 0:
                lg(f"infer {i+1}/{len(ds_obj)} matched={len(rec_err)} ({(time.time()-t0)/60:.1f}min)")
    lg(f"inference done: matched_dets={len(rec_err)} in {(time.time()-t0)/60:.1f}min")

    sc = np.array(rec_score); cf = np.array(rec_conf); er = np.array(rec_err)
    ar = np.array(rec_ar); nsq = np.array(rec_nsq); img = np.array(rec_img)
    mask = (ar >= AR_MASK) & (~nsq) & np.isfinite(er) & np.isfinite(cf)
    n_masked = int(mask.sum())
    res = dict(run_id=rid, angle_head=head, dataset=ds, seed=seed, checkpoint=os.path.basename(ckpt),
               n_matched=len(er), n_masked_ar16=n_masked, native_signal=
               {"PSC": "phase_mod", "CSL": "softmax_margin", "DCL": "mean_bit_margin"}[head])
    if n_masked >= 50:
        res["masked_NRC_native"] = round(nrc_auc(cf[mask], er[mask])["nrc_auc"], 4)
        res["masked_NRC_score"] = round(nrc_auc(sc[mask], er[mask])["nrc_auc"], 4)
        res["masked_AURC_native"] = round(aurc(cf[mask], er[mask]), 4)
        res["masked_Risk70_native"] = round(risk_at_coverage(cf[mask], er[mask], 0.7), 3)
        res["masked_Risk90_native"] = round(risk_at_coverage(cf[mask], er[mask], 0.9), 3)
        lo, hi = image_bootstrap_ci(img[mask], cf[mask], er[mask])
        res["masked_NRC_native_CI"] = [round(lo, 4), round(hi, 4)]
        res["masked_angle_error_mean"] = round(float(er[mask].mean()), 4)
    else:
        res["note"] = f"insufficient masked dets ({n_masked})"
    # AP
    res["AP50_self"] = round(rotated_ap(dets_by_cls, gts_by_cls, 0.5), 4)
    res["AP75_self"] = round(rotated_ap(dets_by_cls, gts_by_cls, 0.75), 4)
    res["AP50_val_log"] = val_log_ap50(rid)
    os.makedirs(f"{REP}/r1_eval", exist_ok=True)
    json.dump(res, open(f"{REP}/r1_eval/{rid}.json", "w"), indent=2)
    lg(f"RESULT {json.dumps(res)}")
    print("DONE", rid)

if __name__ == "__main__":
    main()
