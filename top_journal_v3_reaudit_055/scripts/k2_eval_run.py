"""k2_eval_run.py <run_id> <config> <ckpt> <head> <dataset> — instrumented eval of one K2 final run.
Native uncertainty per head (PSC phase_mod / CSL,DCL softmax margin / direct_regression none /
KLD not_emitted-or-variance). Masked main口径 = K4a derived-ar=2.1; sensitivity ar>=1.6, ar>=1.3.
Outputs masked NRC(native) + NRC(score) + AURC + Risk + bootstrap CI + AP50/AP75 to a per-run JSON.
Reuses the K1-validated evaluator + frozen nrc_auc. No training.
"""
import os, sys, json, math, csv, time
import numpy as np, torch
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench")
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055")
import orientbench_ext.instrumented_heads  # register instrumented AngleBranch
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
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports/k2_eval"
os.makedirs(REP, exist_ok=True)
iou_calc = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))
ANGLEBRANCH = {"PSC", "CSL", "DCL"}

def native_conf(head, enc, coder):
    if head == "PSC":
        ns = coder.num_step; cs = coder.coef_sin.to(enc); cc = coder.coef_cos.to(enc)
        return ((enc[:, :ns]*cc).sum(-1)**2 + (enc[:, :ns]*cs).sum(-1)**2)
    if head == "CSL":
        p = enc.softmax(-1); t2 = p.topk(2, dim=-1).values; return t2[:, 0]-t2[:, 1]
    if head == "DCL":
        pb = enc.sigmoid(); return (2*pb-1).abs().mean(-1)
    return None

def voc_ap(tp, sc, n_gt):
    if n_gt == 0: return float("nan")
    o = np.argsort(-sc, kind="stable"); tp = tp[o]
    ctp = np.cumsum(tp); cfp = np.cumsum(1-tp); rec = ctp/n_gt; prec = ctp/np.maximum(ctp+cfp, 1e-9)
    return float(sum((prec[rec >= t].max() if (rec >= t).any() else 0.0)/11 for t in np.linspace(0, 1, 11)))

def boot_ci(imgs, conf, err, n=800):
    imgs = np.asarray(imgs); conf = np.asarray(conf); err = np.asarray(err)
    uniq = np.unique(imgs); by = {u: np.where(imgs == u)[0] for u in uniq}
    rng = np.random.RandomState(12345); vals = []
    for _ in range(n):
        pick = rng.choice(uniq, len(uniq), replace=True); idx = np.concatenate([by[u] for u in pick])
        if idx.size < 50: continue
        try: vals.append(nrc_auc(conf[idx], err[idx])["nrc_auc"])
        except Exception: pass
    return (round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)) if vals else (float("nan"), float("nan"))

def main():
    rid, cfgp, ckpt, head, ds = sys.argv[1:6]
    cfg = Config.fromfile(cfgp)
    instrumented = head in ANGLEBRANCH
    if instrumented: cfg.model.bbox_head.type = "InstrumentedAngleBranchRetinaHead"
    model = MODELS.build(cfg.model); load_checkpoint(model, ckpt, map_location="cpu"); model.eval().cuda()
    coder = getattr(model.bbox_head, "angle_coder", None)
    dsobj = DATASETS.build(cfg.val_dataloader["dataset"])
    sc = []; cf = []; er = []; ar = []; nsq = []; img = []
    dets_by_cls = {}; gts_by_cls = {}
    n_img = len(dsobj)
    cap = int(os.environ.get("EVAL_MAX_IMAGES", "0"))
    if cap > 0: n_img = min(n_img, cap)
    with torch.no_grad():
        for i in range(n_img):
            d = dsobj[i]; iid = d["data_samples"].img_id
            gt = d["data_samples"].gt_instances
            gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).cpu(); gl = gt.labels.cpu()
            dd = model.data_preprocessor(dict(inputs=[d["inputs"].cuda()], data_samples=[d["data_samples"].cuda()]), False)
            pi = model.predict(dd["inputs"], dd["data_samples"])[0].pred_instances
            pb = (pi.bboxes.tensor if hasattr(pi.bboxes, "tensor") else pi.bboxes).cpu()
            ps = pi.scores.cpu(); pl = pi.labels.cpu()
            conf = None
            if instrumented and hasattr(pi, "angle_encoded"):
                conf = native_conf(head, pi.angle_encoded.float(), coder).cpu()
            for k in range(gb.shape[0]):
                gts_by_cls.setdefault(int(gl[k]), {}).setdefault(iid, []).append(gb[k])
            for k in range(pb.shape[0]):
                dets_by_cls.setdefault(int(pl[k]), []).append((float(ps[k]), iid, pb[k]))
            if pb.shape[0] and gb.shape[0]:
                order = torch.argsort(ps, descending=True); used = set(); gbc = gb.cuda()
                for k in order.tolist():
                    same = (gl == int(pl[k])).nonzero(as_tuple=True)[0]
                    if same.numel() == 0: continue
                    ious = iou_calc(pb[k:k+1].cuda(), gbc[same]).squeeze(0).cpu()
                    j = int(ious.argmax()); gj = int(same[j])
                    if float(ious[j]) < 0.5 or gj in used: continue
                    used.add(gj)
                    wp, hp, tp = float(pb[k, 2]), float(pb[k, 3]), float(pb[k, 4])
                    cc = angle_error_contract(wp, hp, tp, float(gb[gj, 2]), float(gb[gj, 3]), float(gb[gj, 4]))
                    e = cc["angle_error_canonical_longside"]
                    if not math.isfinite(e): continue
                    sc.append(float(ps[k])); er.append(e); ar.append(max(wp, hp)/max(min(wp, hp), 1e-6))
                    nsq.append(cc["near_square"]); img.append(iid)
                    cf.append(float(conf[k]) if conf is not None else float("nan"))
    # AP
    def ap_at(t):
        aps = {}
        for c, g in gts_by_cls.items():
            n = sum(len(v) for v in g.values())
            if n == 0: continue
            dl = sorted(dets_by_cls.get(c, []), key=lambda x: -x[0]); tp = np.zeros(len(dl)); s2 = np.zeros(len(dl)); us = {}
            for i2, (s, im, bx) in enumerate(dl):
                s2[i2] = s; gg = g.get(im, [])
                if not gg: continue
                iou = iou_calc(bx.unsqueeze(0).cuda(), torch.stack(gg).cuda()).squeeze(0).cpu(); j = int(iou.argmax())
                if float(iou[j]) >= t and (im, j) not in us: tp[i2] = 1; us[(im, j)] = 1
            aps[c] = voc_ap(tp, s2, n)
        return float(np.nanmean([v for v in aps.values() if v == v])) if aps else float("nan")
    sc = np.array(sc); cf = np.array(cf); er = np.array(er); ar = np.array(ar); nsq = np.array(nsq); img = np.array(img)
    res = dict(run_id=rid, head=head, dataset=ds, n_matched=len(er),
               AP50=round(ap_at(0.5), 4), AP75=round(ap_at(0.75), 4),
               native_signal={"PSC": "phase_mod", "CSL": "softmax_margin", "DCL": "softmax_margin"}.get(head, "not_emitted" if head == "KLD" else "none"))
    for lbl, thr in [("main_ar2.1", 2.1), ("sens_ar1.6", 1.6), ("sens_ar1.3", 1.3)]:
        m = (ar >= thr) & (~nsq) & np.isfinite(er)
        blk = dict(n=int(m.sum()))
        if int(m.sum()) >= 50:
            blk["NRC_score"] = round(nrc_auc(sc[m], er[m])["nrc_auc"], 4)
            blk["angle_err_mean"] = round(float(er[m].mean()), 3)
            blk["Risk70_score"] = round(risk_at_coverage(sc[m], er[m], 0.7), 3)
            if np.isfinite(cf[m]).sum() >= 50:
                mm = m & np.isfinite(cf)
                blk["NRC_native"] = round(nrc_auc(cf[mm], er[mm])["nrc_auc"], 4)
                blk["NRC_native_CI"] = boot_ci(img[mm], cf[mm], er[mm])
                blk["AURC_native"] = round(aurc(cf[mm], er[mm]), 4)
        res[lbl] = blk
    with open(f"{REP}/{rid}.json", "w") as f:
        json.dump(res, f, indent=2); f.flush()
    print("K2_EVAL_DONE", rid, "AP50", res["AP50"], "main_native", res["main_ar2.1"].get("NRC_native"),
          "main_score", res["main_ar2.1"].get("NRC_score"), flush=True)

if __name__ == "__main__":
    main()
