"""m_dota_dump.py <orcnn|rtmdet> — persist per-instance matched dump for a DOTA-v1.0 clean full-val cell
so M1/M4 can recompute at ar>=2.1 with image-level fields. Reuses the K1-validated evaluator + frozen
checkpoints (no training). Writes m_dota_clean_perinstance/DOTA_<det>.jsonl with load_cell-compatible schema.
"""
import os, sys, json, math, time
import numpy as np, torch
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench")
import mmrotate, mmrotate.models, mmrotate.datasets
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmengine.runner import load_checkpoint
from mmrotate.registry import MODELS, DATASETS, TASK_UTILS
from orientbench.metrics.angle_contract import angle_error_contract
init_default_scope("mmrotate")
ROOT = "/home/rspip/cqc/pro/study/orientbench"; PTH = "/home/rspip/cqc/pro/study/pth_data"
OUT = f"{ROOT}/top_journal_v3_reaudit_055/reports/m_dota_clean_perinstance"
LOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/m069/m_dota_dump.log"
DOTA_VAL = "/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/val"
os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.dirname(LOG), exist_ok=True)
iou_calc = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))
CELLS = {
    "orcnn": dict(det="oriented_rcnn", out="DOTA_orcnn.jsonl",
        cfg=f"{PTH}/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py",
        ckpt=f"{PTH}/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth"),
    "rtmdet": dict(det="rotated_rtmdet_m", out="DOTA_rtmdet.jsonl",
        cfg=f"{PTH}/baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/config.py",
        ckpt=f"{PTH}/baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/best_mAP_7161_epoch_31.pth"),
}


def lg(m):
    open(LOG, "a").write(f"[{time.strftime('%F %T')}] {m}\n"); print(m, flush=True)


def size_bin(area):
    s = math.sqrt(max(area, 0))
    return "small" if s < 32 else ("medium" if s < 96 else "large")


def main():
    which = sys.argv[1]; c = CELLS[which]
    outp = f"{OUT}/{c['out']}"
    if os.path.isfile(outp) and os.path.getsize(outp) > 1000:
        lg(f"{which}: exists -> skip"); return
    t0 = time.time()
    cfg = Config.fromfile(c["cfg"]); model = MODELS.build(cfg.model)
    load_checkpoint(model, c["ckpt"], map_location="cpu"); model.eval().cuda()
    vd = cfg.val_dataloader["dataset"]
    vd["data_root"] = f"{DOTA_VAL}/"; vd["ann_file"] = "annfiles/"
    vd["data_prefix"] = dict(img_path="images/"); vd["img_suffix"] = "png"
    ds = DATASETS.build(vd)
    lg(f"{which}: n_eval={len(ds)}")
    fout = open(outp + ".tmp", "w")
    nrows = 0
    with torch.no_grad():
        for i in range(len(ds)):
            d = ds[i]; img = str(d["data_samples"].img_id)
            gt = d["data_samples"].gt_instances
            gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).cpu(); gl = gt.labels.cpu()
            dd = model.data_preprocessor(dict(inputs=[d["inputs"].cuda()],
                                              data_samples=[d["data_samples"].cuda()]), False)
            pi = model.predict(dd["inputs"], dd["data_samples"])[0].pred_instances
            pb = (pi.bboxes.tensor if hasattr(pi.bboxes, "tensor") else pi.bboxes).cpu()
            ps = pi.scores.cpu(); pl = pi.labels.cpu()
            if pb.shape[0] == 0 or gb.shape[0] == 0:
                continue
            order = torch.argsort(ps, descending=True); used = set(); gbc = gb.cuda()
            for k in order.tolist():
                same = (gl == int(pl[k])).nonzero(as_tuple=True)[0]
                if same.numel() == 0:
                    continue
                ious = iou_calc(pb[k:k+1].cuda(), gbc[same]).squeeze(0).cpu()
                j = int(ious.argmax()); gj = int(same[j])
                if float(ious[j]) < 0.5 or gj in used:
                    continue
                used.add(gj)
                pw, ph, pt = float(pb[k, 2]), float(pb[k, 3]), float(pb[k, 4])
                gw, gh, gtt = float(gb[gj, 2]), float(gb[gj, 3]), float(gb[gj, 4])
                cc = angle_error_contract(pw, ph, pt, gw, gh, gtt)
                e = cc["angle_error_canonical_longside"]
                if not math.isfinite(e):
                    continue
                area = pw * ph; arv = max(pw, ph) / max(min(pw, ph), 1e-6)
                rec = dict(cell_id=f"DOTA-v1.0/{which}", dataset="DOTA-v1.0", detector=c["det"],
                           image_id=img, pred_id=int(k), gt_id=gj, score=float(ps[k]), phase_mod="",
                           pred_obb=dict(obb_cx=float(pb[k, 0]), obb_cy=float(pb[k, 1]), obb_w=pw, obb_h=ph, obb_theta=pt),
                           gt_obb=dict(obb_w=gw, obb_h=gh, obb_theta=gtt), match_iou=round(float(ious[j]), 4),
                           angle_error=e, **{"class": str(int(pl[k]))}, size=area, aspect_ratio=arv,
                           near_square=bool(cc["near_square"]), size_bin=size_bin(area), split="fullval",
                           d_cal_daudit_split_flag="D_audit", is_real_detector_output=True)
                fout.write(json.dumps(rec) + "\n"); nrows += 1
            if (i + 1) % 2000 == 0:
                lg(f"{which}: {i+1}/{len(ds)} rows={nrows} ({(time.time()-t0)/60:.1f}min)")
    fout.close(); os.replace(outp + ".tmp", outp)
    lg(f"{which}: DONE rows={nrows} ({(time.time()-t0)/60:.1f}min)")
    print(f"M_DOTA_DUMP_DONE {which} rows={nrows}", flush=True)


if __name__ == "__main__":
    main()
