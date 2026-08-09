#!/usr/bin/env python3
"""First r019 DOTA-label access, fresh matching, parity, and frozen bootstrap."""
from __future__ import annotations

import os
os.environ.update({"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})

import csv
import hashlib
import json
import math
import multiprocessing as mp
import pickle
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from mmcv.ops import box_iou_rotated
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmrotate.evaluation import eval_rbbox_map
from mmrotate.registry import DATASETS
from mmrotate.structures.bbox import QuadriBoxes

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.nrc_auc import nrc_auc
from scripts.m069_common import delta_theta_075

WORK = ROOT / "p3_selector/deployable_proxy_r019"
PRE = WORK / "prelabel"
RESULTS = WORK / "results"
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r019"
RUNPRE = RUNTIME / "prelabel"
RUNPOST = RUNTIME / "postlabel"
DOTA_VAL = Path("/home/rspip/cqc/data/dataset/dota/split_ss_dota10_dota15/val")
EXPECTED_AP = {"orcnn": (0.7061, 0.4517), "rtmdet": (0.7161, 0.4868)}
_BOOT = None


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def verify_timelock():
    receipt = RUNTIME / "post_commit_receipt.json"
    if not receipt.is_file():
        raise RuntimeError("prelabel remote receipt missing")
    value = json.loads(receipt.read_text())
    remote = subprocess.check_output(["git", "ls-remote", "https://github.com/ziyu24/orientbench.git", "refs/heads/main"], text=True).split()[0]
    if value.get("prelabel_commit_sha") != remote or value.get("remote_main_sha") != remote:
        raise RuntimeError("remote main is not sealed prelabel commit")
    manifest = PRE / "prelabel_seal_manifest_r019.json"
    if sha(manifest) != value.get("prelabel_manifest_sha256"):
        raise RuntimeError("prelabel manifest changed after remote seal")
    for row in json.loads(manifest.read_text())["runtime_files"]:
        path = ROOT / row["path"]
        if not path.is_file() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise RuntimeError(f"sealed runtime changed: {path}")
    return value


def load_gt(registry):
    """This function is the first allowed label-bearing operation in r019."""
    first = {"timestamp": time.time(), "operation": "DATASETS.build", "path": str(DOTA_VAL / "annfiles"),
             "remote_prelabel_verified": True, "historical_project_label_access_acknowledged": True}
    write_json(RUNPOST / "first_target_label_access.json", first)
    init_default_scope("mmrotate")
    cfg = Config.fromfile(registry["units"]["orcnn"]["config"])
    spec = cfg.val_dataloader.dataset
    spec["data_root"] = str(DOTA_VAL) + "/"; spec["ann_file"] = "annfiles/"
    spec["data_prefix"] = {"img_path": "images/"}; spec["img_suffix"] = "png"
    dataset = DATASETS.build(spec); dataset.full_init()
    by_id = {}
    total = 0
    for info in dataset.data_list:
        boxes, labels, ignored = [], [], []
        instances = info.get("instances", [])
        polys = [x["bbox"] for x in instances]
        rboxes = (QuadriBoxes(torch.tensor(polys, dtype=torch.float32)).convert_to("rbox").tensor.numpy()
                  if polys else np.empty((0, 5), dtype=np.float32))
        for index, instance in enumerate(instances):
            boxes.append(rboxes[index]); labels.append(int(instance["bbox_label"])); ignored.append(int(instance.get("ignore_flag", 0)))
        by_id[str(info["img_id"])] = {"boxes": np.asarray(boxes, np.float32).reshape(-1, 5),
                                      "labels": np.asarray(labels, np.int64),
                                      "ignored": np.asarray(ignored, np.int64)}
        total += len(boxes)
    expected = {x["stem"] for x in registry["tiles"]}
    if set(by_id) != expected or len(by_id) != 5297 or total != 55804:
        raise RuntimeError(f"GT universe mismatch images={len(by_id)} objects={total}")
    path = RUNPOST / "dota_gt_fresh.pkl"; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f: pickle.dump(by_id, f, protocol=4)
    return by_id, path


def load_identity(unit):
    with (RUNPRE / "raw" / unit / "identity.pkl").open("rb") as f:
        rows = pickle.load(f)
    rows = sorted(rows, key=lambda x: str(x["img_id"]))
    if len(rows) != 5297 or len({str(x["img_id"]) for x in rows}) != 5297:
        raise RuntimeError(f"identity raw incomplete {unit}")
    return rows


def official_ap(records, gt):
    detections, annotations = [], []
    for record in records:
        pred = record["pred_instances"]
        boxes = pred["bboxes"].detach().cpu().numpy().astype(np.float32)
        scores = pred["scores"].detach().cpu().numpy().astype(np.float32)
        labels = pred["labels"].detach().cpu().numpy()
        detections.append([np.concatenate([boxes[labels == cls], scores[labels == cls, None]], axis=1)
                           for cls in range(15)])
        item = gt[str(record["img_id"])]
        keep = item["ignored"] == 0; ignore = ~keep
        annotations.append({"bboxes": item["boxes"][keep], "labels": item["labels"][keep],
                            "bboxes_ignore": item["boxes"][ignore], "labels_ignore": item["labels"][ignore]})
    ap50, _ = eval_rbbox_map(detections, annotations, iou_thr=.5, use_07_metric=True, nproc=38, logger="silent")
    ap75, _ = eval_rbbox_map(detections, annotations, iou_thr=.75, use_07_metric=True, nproc=38, logger="silent")
    return float(ap50), float(ap75)


def attach(unit, records, gt, mother):
    rows = []
    for record in records:
        image_id = str(record["img_id"]); pred = record["pred_instances"]
        pb = pred["bboxes"].detach().cpu().float(); ps = pred["scores"].detach().cpu().numpy(); pl = pred["labels"].detach().cpu().numpy()
        item = gt[image_id]; keep = item["ignored"] == 0
        gb = torch.from_numpy(item["boxes"][keep]).float(); gl = item["labels"][keep]
        if len(pb) == 0 or len(gb) == 0: continue
        overlaps = box_iou_rotated(pb, gb).cpu().numpy(); used = set()
        pred_order = sorted(range(len(pb)), key=lambda k: (-float(ps[k]), k))
        for pred_id in pred_order:
            candidates = [(float(overlaps[pred_id, j]), j) for j in range(len(gb))
                          if j not in used and int(gl[j]) == int(pl[pred_id]) and float(overlaps[pred_id, j]) >= .5]
            if not candidates: continue
            _, gt_id = min(candidates, key=lambda x: (-x[0], x[1])); used.add(gt_id)
            gw, gh = float(gb[gt_id, 2]), float(gb[gt_id, 3]); gt_ar = max(gw, gh) / max(min(gw, gh), 1e-6)
            if gt_ar < 2.1: continue
            cc = angle_error_contract(float(pb[pred_id,2]), float(pb[pred_id,3]), float(pb[pred_id,4]), gw, gh, float(gb[gt_id,4]))
            angle = float(cc["angle_error_canonical_longside"])
            risk = min(angle / max(float(delta_theta_075(gt_ar)), 1.0), 3.0)
            rows.append({"unit": unit, "image_id": image_id, "mother": mother[image_id], "pred_id": pred_id,
                         "gt_id": gt_id, "match_iou": max(x[0] for x in candidates if x[1] == gt_id),
                         "gt_ar": gt_ar, "angle_error": angle, "risk": risk})
    return pd.DataFrame(rows)


def nrc(scores, risks):
    return float(nrc_auc(np.asarray(scores, float), np.asarray(risks, float))["nrc_auc"])


def _weighted_nrc(order, risks, multiplicity):
    m = multiplicity[order].astype(np.int32); active = m > 0
    expanded = np.repeat(risks[order][active], m[active])
    if len(expanded) < 2: return float("nan")
    model = float(np.mean(np.cumsum(expanded) / np.arange(1, len(expanded)+1)))
    oracle = np.sort(expanded, kind="stable")
    a_oracle = float(np.mean(np.cumsum(oracle) / np.arange(1, len(oracle)+1)))
    random = float(np.mean(expanded)); denom = random - a_oracle
    return float((model-a_oracle)/denom) if abs(denom) > 1e-12 else float("nan")


def _bootstrap_worker(rep):
    draw = _BOOT["draws"][rep]; counts = np.bincount(draw, minlength=_BOOT["mother_count"])
    values = []
    guards = []
    for unit in _BOOT["units"]:
        mult = counts[unit["mother_pos"]]
        lin = _weighted_nrc(unit["orders"]["linear"], unit["risk"], mult)
        eqs = _weighted_nrc(unit["orders"]["eqs"], unit["risk"], mult)
        sta = _weighted_nrc(unit["orders"]["standalone"], unit["risk"], mult)
        values.append(lin-eqs); guards.append(sta-eqs)
    return (rep, values[0], values[1], float(np.mean(values)), guards[0], guards[1], float(np.mean(guards)))


def summarize(point, reps):
    array = np.asarray(reps, float)
    return {"point": float(point), "ci_low": float(np.percentile(array, 2.5)), "ci_high": float(np.percentile(array, 97.5)),
            "p_one_sided": float((1 + np.sum((array-point) >= point)) / 10001)}


def main():
    receipt = verify_timelock(); registry = json.loads((RUNPRE / "image_only_registry.json").read_text())
    gt, gt_path = load_gt(registry); mother = {x["stem"]: x["mother"] for x in registry["tiles"]}
    parity_rows=[]; labeled={}; contexts=[]; point_rows=[]
    mothers=sorted(set(mother.values())); mother_pos={x:i for i,x in enumerate(mothers)}
    draws=np.load(RUNPRE / "draws/mother_draws.npy", mmap_mode="r")
    for unit in ("orcnn","rtmdet"):
        raw=load_identity(unit); ap50,ap75=official_ap(raw,gt); exp=EXPECTED_AP[unit]
        parity=abs(ap50-exp[0])<=.002 and abs(ap75-exp[1])<=.002
        parity_rows.append({"unit":unit,"images":len(raw),"gt":sum(len(x["boxes"]) for x in gt.values()),"ap50":ap50,"expected_ap50":exp[0],"ap50_abs_diff":abs(ap50-exp[0]),"ap75":ap75,"expected_ap75":exp[1],"ap75_abs_diff":abs(ap75-exp[1]),"tolerance":.002,"pass":parity})
        if not parity: raise RuntimeError(f"official AP parity failed {unit}: {ap50} {ap75}")
        labels=attach(unit,raw,gt,mother); scores=pd.read_parquet(RUNPRE/f"target_scores/{unit}.parquet")
        frame=labels.merge(scores,on=["image_id","pred_id"],validate="one_to_one")
        if len(frame)!=len(labels): raise RuntimeError(f"score join incomplete {unit}")
        path=RUNPOST/f"labeled/{unit}.parquet";path.parent.mkdir(parents=True,exist_ok=True);frame.to_parquet(path,index=False,compression="zstd");labeled[unit]=frame
        points={name:nrc(frame[col],frame.risk) for name,col in (("linear","linear_score"),("eqs","eqs_rc_score"),("standalone","standalone_score"))}
        point_rows.append({"unit":unit,"eligible":len(frame),**{f"nrc_{k}":v for k,v in points.items()},"delta_linear_eqs":points["linear"]-points["eqs"],"guard_standalone_eqs":points["standalone"]-points["eqs"]})
        contexts.append({"risk":frame.risk.to_numpy(float),"mother_pos":frame.mother.map(mother_pos).to_numpy(int),
                         "orders":{name:np.argsort(-frame[col].to_numpy(float),kind="stable") for name,col in (("linear","linear_score"),("eqs","eqs_rc_score"),("standalone","standalone_score"))}})
    global _BOOT
    _BOOT={"draws":draws,"mother_count":len(mothers),"units":contexts}
    with mp.get_context("fork").Pool(38) as pool:
        reps=pool.map(_bootstrap_worker,range(10000),chunksize=8)
    columns=["replicate","orcnn_delta","rtmdet_delta","aggregate_delta","orcnn_guard","rtmdet_guard","aggregate_guard"]
    repframe=pd.DataFrame(reps,columns=columns)
    if len(repframe)!=10000 or not np.isfinite(repframe.iloc[:,1:].to_numpy()).all() or repframe.replicate.tolist()!=list(range(10000)):
        raise RuntimeError("bootstrap replicate contract failed")
    rep_path=RUNPOST/"bootstrap/replicates.parquet";rep_path.parent.mkdir(parents=True,exist_ok=True);repframe.to_parquet(rep_path,index=False,compression="zstd")
    point={r["unit"]:r for r in point_rows}; agg_delta=(point["orcnn"]["delta_linear_eqs"]+point["rtmdet"]["delta_linear_eqs"])/2
    agg_guard=(point["orcnn"]["guard_standalone_eqs"]+point["rtmdet"]["guard_standalone_eqs"])/2
    summaries={
        "orcnn_delta":summarize(point["orcnn"]["delta_linear_eqs"],repframe.orcnn_delta),
        "rtmdet_delta":summarize(point["rtmdet"]["delta_linear_eqs"],repframe.rtmdet_delta),
        "aggregate_delta":summarize(agg_delta,repframe.aggregate_delta),
        "orcnn_guard":summarize(point["orcnn"]["guard_standalone_eqs"],repframe.orcnn_guard),
        "rtmdet_guard":summarize(point["rtmdet"]["guard_standalone_eqs"],repframe.rtmdet_guard),
        "aggregate_guard":summarize(agg_guard,repframe.aggregate_guard),
    }
    rawp=[summaries["orcnn_delta"]["p_one_sided"],summaries["rtmdet_delta"]["p_one_sided"]]
    order=np.argsort(rawp); holm=[0.,0.]; running=0.
    for rank,idx in enumerate(order): running=max(running,min(1.,rawp[idx]*(2-rank)));holm[idx]=running
    summaries["orcnn_delta"]["p_holm2"],summaries["rtmdet_delta"]["p_holm2"]=holm
    passed=(summaries["aggregate_delta"]["point"]>=.02 and summaries["aggregate_delta"]["ci_low"]>0 and summaries["aggregate_delta"]["p_one_sided"]<.05
            and all(summaries[f"{u}_delta"]["point"]>=.02 and summaries[f"{u}_delta"]["ci_low"]>0 and summaries[f"{u}_delta"]["p_holm2"]<.05 for u in ("orcnn","rtmdet"))
            and summaries["aggregate_guard"]["point"]>=0 and all(summaries[f"{u}_guard"]["point"]>=0 for u in ("orcnn","rtmdet")))
    failed=(summaries["aggregate_delta"]["ci_high"]<=0 or any(summaries[f"{u}_delta"]["ci_high"]<=0 for u in ("orcnn","rtmdet")) or summaries["aggregate_guard"]["ci_high"]<0)
    gate="PASS_EXTERNAL_DOTA_EQS_RC_R019" if passed else ("FAIL_EXTERNAL_DOTA_EQS_RC_R019" if failed else "INCONCLUSIVE_EXTERNAL_DOTA_EQS_RC_R019")
    RESULTS.mkdir(parents=True,exist_ok=True)
    write_csv(RESULTS/"official_detection_parity_r019.csv",parity_rows);write_csv(RESULTS/"unit_point_metrics_r019.csv",point_rows)
    write_json(RESULTS/"dota_endpoint_results_r019.json",{"gate":gate,"summaries":summaries,"replicates":10000,"mother_count":len(mothers),"unit_weighting":"equal","eligible":{u:len(f) for u,f in labeled.items()}})
    write_json(RESULTS/"label_attach_inventory_r019.json",{"first_access":json.loads((RUNPOST/"first_target_label_access.json").read_text()),"prelabel_commit":receipt["prelabel_commit_sha"],"gt":{"path":str(gt_path.relative_to(ROOT)),"bytes":gt_path.stat().st_size,"sha256":sha(gt_path),"images":len(gt),"objects":sum(len(x["boxes"]) for x in gt.values())},"labeled":{u:{"path":str((RUNPOST/f'labeled/{u}.parquet').relative_to(ROOT)),"bytes":(RUNPOST/f'labeled/{u}.parquet').stat().st_size,"sha256":sha(RUNPOST/f'labeled/{u}.parquet'),"rows":len(f)} for u,f in labeled.items()},"replicates":{"path":str(rep_path.relative_to(ROOT)),"bytes":rep_path.stat().st_size,"sha256":sha(rep_path),"rows":10000}})
    print(json.dumps({"gate":gate,"aggregate_delta":summaries["aggregate_delta"]}))


if __name__=="__main__": main()
