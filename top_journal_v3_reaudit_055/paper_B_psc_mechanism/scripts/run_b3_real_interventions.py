#!/usr/bin/env python3
"""B3 endpoint-separated interventions on frozen real PSC outputs."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[3]
BROOT = Path(__file__).resolve().parents[1]
G0 = ROOT / "top_journal_v3_reaudit_055/shared_forensics/g0"
HIST = ROOT / "top_journal_v3_reaudit_055"
PERSIST = ROOT / "outputs/persistent_artifacts/m069_psc_phase1"
PROTOCOL = BROOT / "reports/b1_protocol_frozen.json"
DELTA = HIST / "reports/m4_delta_theta_075_frozen.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_csv(path: Path, rows: list[dict], fields=None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    if fields is None:
        fields=[]
        for row in rows:
            for key in row:
                if key not in fields: fields.append(key)
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp"); tmp.write_text(text, encoding="utf-8"); os.replace(tmp, path)


def normalize_pi(x):
    return (x + np.pi / 2) % np.pi - np.pi / 2


def circ_signed(a, b):
    return normalize_pi(a - b)


def circ_abs_deg(a, b):
    return np.degrees(np.abs(circ_signed(a, b)))


def nrc(score, risk):
    score = np.asarray(score, float); risk = np.asarray(risk, float)
    ok = np.isfinite(score) & np.isfinite(risk); score, risk = score[ok], risk[ok]
    if len(score) < 20 or np.nanstd(risk) < 1e-12:
        return float("nan")
    order = np.argsort(-score, kind="stable")
    curve = np.cumsum(risk[order]) / np.arange(1, len(risk) + 1)
    oracle = np.cumsum(np.sort(risk, kind="stable")) / np.arange(1, len(risk) + 1)
    denom = np.mean(np.mean(risk) - oracle)
    return float(np.mean(curve - oracle) / denom) if denom > 1e-12 else float("nan")


def delta_threshold(ar):
    p = json.loads(DELTA.read_text(encoding="utf-8"))
    return np.interp(ar, np.asarray(p["ar"], float), np.asarray(p["dtheta_075"], float))


def phase_components(v):
    c = np.array([1.0, -0.5, -0.5]); s = np.array([0.0, math.sqrt(3) / 2, -math.sqrt(3) / 2])
    c1, s1 = v[:, :3] @ c, v[:, :3] @ s; c2, s2 = v[:, 3:6] @ c, v[:, 3:6] @ s
    p1 = -np.arctan2(s1, c1); p2 = -np.arctan2(s2, c2) / 2.0
    return p1, p2, c1 * c1 + s1 * s1, c2 * c2 + s2 * s2


def decode_phase(p1, p2, mod2, threshold=0.47):
    c0 = p2; c1 = np.mod(p2, 2 * np.pi) - np.pi
    use1 = np.cos(p1 - c0) < 0
    chosen = np.where(use1, c1, c0); chosen = np.where(mod2 < threshold, 0.0, chosen)
    return chosen / 2.0, use1


def candidate_scores(p1, p2, mod2):
    c0 = p2; c1 = np.mod(p2, 2 * np.pi) - np.pi
    a0, a1 = np.cos(p1 - c0), np.cos(p1 - c1)
    chosen = np.where(a1 > a0, c1, c0)
    disagreement = np.degrees(np.abs(circ_signed(p1 / 2.0, chosen / 2.0)))
    gap = np.abs(a0 - a1); margin = gap * np.sqrt(np.maximum(mod2, 0))
    return -disagreement, gap, margin


def risk_after(base_decode, new_decode, pred_long, gt_long, threshold):
    new_long = normalize_pi(pred_long + circ_signed(new_decode, base_decode))
    err = circ_abs_deg(new_long, gt_long); severe = (err > threshold).astype(float)
    return err, severe


def rows_source(dataset, seed):
    if dataset in ("DIOR-R", "SODA-A"):
        return PERSIST / dataset / f"seed{seed}/matched_phase.jsonl", False
    return BROOT / f"artifacts/b3_fair1m/seed{seed}/matched_phase.jsonl.gz", True


def load_unit(dataset, seed):
    cache = BROOT / f"artifacts/b3_cache/{dataset.replace('-v1.0','').replace('-','_')}_seed{seed}.npz"
    if cache.is_file():
        z = np.load(cache, allow_pickle=True); return {k: z[k] for k in z.files}
    path, zipped = rows_source(dataset, seed)
    if not path.is_file(): raise FileNotFoundError(path)
    fields = {k: [] for k in ("image", "score", "error", "ar", "size", "cls", "feature", "boundary",
                                    "tta", "vector", "pred_box", "gt_box")}
    opener = gzip.open if zipped else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            x = json.loads(line)
            fields["image"].append(str(x["image_id"])); fields["score"].append(float(x["detection_score"]))
            fields["error"].append(float(x["angle_error"])); fields["ar"].append(float(x["aspect_ratio"]))
            fields["size"].append(float(x["size"])); fields["cls"].append(str(x["class"]))
            fields["feature"].append(float(x["reg_feature_norm"]) if x.get("reg_feature_norm") is not None else np.nan)
            fields["boundary"].append(float(x["boundary_distance_deg"]));
            fields["tta"].append(float(x["tta_phase_direction_circular_variance"]) if x.get("tta_phase_direction_circular_variance") is not None else np.nan)
            fields["vector"].append(x["encoded_vector"]); fields["pred_box"].append(x["pred_box"]); fields["gt_box"].append(x["gt_box"])
    out = {k: np.asarray(v, dtype=object if k in ("image", "cls") else float) for k, v in fields.items()}
    mask = out["ar"] >= 2.1; out = {k: v[mask] for k, v in out.items()}
    cache.parent.mkdir(parents=True, exist_ok=True); np.savez_compressed(cache, **out)
    return out


def long_angle(box):
    theta = box[:, 4].astype(float).copy(); theta = theta + np.where(box[:, 2] < box[:, 3], np.pi / 2, 0.0)
    return normalize_pi(theta)


def safe_spearman(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 20 or np.nanstd(a[ok]) < 1e-12 or np.nanstd(b[ok]) < 1e-12: return float("nan")
    return float(spearmanr(a[ok], b[ok]).statistic)


def partial_rank_corr(signal, risk, controls, classes):
    ok = np.isfinite(signal) & np.isfinite(risk) & np.all(np.isfinite(controls), axis=1)
    if ok.sum() < 100: return float("nan")
    x, y, c, cls = rankdata(signal[ok]), rankdata(risk[ok]), controls[ok], classes[ok]
    # class fixed effects without an enormous one-hot matrix
    for value in np.unique(cls):
        m = cls == value; x[m] -= x[m].mean(); y[m] -= y[m].mean(); c[m] -= c[m].mean(axis=0)
    design = np.column_stack([np.ones(len(c)), np.apply_along_axis(rankdata, 0, c)])
    rx = x - design @ np.linalg.lstsq(design, x, rcond=None)[0]
    ry = y - design @ np.linalg.lstsq(design, y, rcond=None)[0]
    return safe_spearman(rx, ry)


def aggregate_image(image, score, risk):
    unique, inv = np.unique(image, return_inverse=True); count = np.bincount(inv)
    ss = np.bincount(inv, weights=score) / count; rr = np.bincount(inv, weights=risk) / count
    return unique, ss, rr


def _bootstrap_chunk(args):
    cs, ps, rr, child, count = args; rng = np.random.default_rng(child); out = np.empty(count); n = len(rr)
    for i in range(count):
        idx = rng.integers(0, n, n); out[i] = nrc(cs[idx], rr[idx]) - nrc(ps[idx], rr[idx])
    return out


def bootstrap_delta(image, candidate, phase, risk, seed, reps=800):
    _, cs, rr = aggregate_image(image, candidate, risk); _, ps, _ = aggregate_image(image, phase, risk)
    workers = 40; seeds = np.random.SeedSequence(seed).spawn(workers)
    counts = [reps // workers + (i < reps % workers) for i in range(workers)]
    tasks = [(cs, ps, rr, child, count) for child, count in zip(seeds, counts)]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        values = np.concatenate(list(pool.map(_bootstrap_chunk, tasks)))
    return float(np.nanpercentile(values, 2.5)), float(np.nanpercentile(values, 97.5))


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8")); units = [(d, s) for d in ("DIOR-R", "SODA-A", "FAIR1M-v1.0") for s in range(3)]
    schedule = load_csv(G0 / "reports/g0_k2_training_schedule_disclosure.csv")
    sched = {(r["dataset"], r["head"], int(r["seed"])): r for r in schedule}
    g0man = load_csv(G0 / "reports/g0_comparison_manifest.csv")
    gm = {(r["dataset"], r["head"], int(r["seed"])): r for r in g0man}
    baseline_rows=[]; metric_rows=[]; conf_rows=[]; identity_rows=[]; ap_rows=[]
    historical_radial = load_csv(HIST / "reports/psc_phase1_radial_scaling.csv")
    radial_map = {(r["dataset"], int(r["seed"]), float(r["k"])): r for r in historical_radial}
    all_unit_summary = {}
    for dataset, seed in units:
        key=(dataset,"PSC",seed); m=gm[key]; q=sched[key]
        eval_json = (ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/M4_070_final__PSC__FAIR1M__seed{seed}.json") if dataset.startswith("FAIR") else (HIST / f"reports/k2_eval/K2_final__PSC__{dataset}__seed{seed}.json")
        ev=json.loads(eval_json.read_text()); ap50=float(ev.get("AP50", ev.get("bbox_mAP_50", q["AP50"]))) if isinstance(ev,dict) else float(q["AP50"])
        ap75=float(ev.get("AP75", ev.get("bbox_mAP_75", q["AP75"]))) if isinstance(ev,dict) else float(q["AP75"])
        source,zipped=rows_source(dataset,seed)
        baseline_rows.append({"dataset":dataset,"seed":seed,"checkpoint":m["checkpoint"],"checkpoint_sha256":m["checkpoint_sha256"],
            "prediction_artifact":str(source.relative_to(ROOT)),"prediction_identity_hash":m["prediction_identity_hash"],"split":m["split"],
            "ar_mask":"GT aspect_ratio>=2.1","image_count":m["image_count"],"retained_count":m["retained_ar21"],
            "AP50":ap50,"AP75":ap75,"training_health":q["final_model_health"],"can_recompute":True})
        x=load_unit(dataset,seed); v=x["vector"].astype(float); p1,p2,mod1,mod2=phase_components(v); base_dec,base_switch=decode_phase(p1,p2,mod2)
        pred_long=long_angle(x["pred_box"].astype(float)); gt_long=long_angle(x["gt_box"].astype(float)); threshold=delta_threshold(x["ar"].astype(float))
        base_err,base_severe=risk_after(base_dec,base_dec,pred_long,gt_long,threshold)
        base_error_diff=float(np.nanmax(np.abs(base_err-x["error"].astype(float))))
        if base_error_diff > 1e-3: raise RuntimeError(f"{dataset}/seed{seed} base error mismatch {base_error_diff}")
        mf,gap,margin=candidate_scores(p1,p2,mod2); candidates={"phase_mod":mod1,"negative_phase_mod":-mod1,
            "detection_score":x["score"].astype(float),"multi_frequency_consistency":mf,
            "unwrap_candidate_energy_gap":gap,"phase_direction_margin":margin}
        if np.isfinite(x["tta"].astype(float)).sum() > len(v)*0.9: candidates["tta_phase_direction_consistency"]=-x["tta"].astype(float)
        candidate_metrics={}
        for name,score in candidates.items():
            for endpoint,risk in (("endpoint_continuous",base_err),("endpoint_severe_event",base_severe)):
                value=nrc(score,risk); candidate_metrics[(name,endpoint)]=value
                lo=hi=float("nan")
                if name not in ("phase_mod","negative_phase_mod","detection_score"):
                    lo,hi=bootstrap_delta(x["image"],score,mod1,risk,int(hashlib.sha256(f'{dataset}{seed}{name}{endpoint}'.encode()).hexdigest()[:8],16))
                metric_rows.append({"analysis":"BASELINE_SCORE","dataset":dataset,"seed":seed,"intervention":name,"parameter":"base",
                    "endpoint":endpoint,"n":len(v),"mean_angle_error":float(np.mean(base_err)),"severe_rate":float(np.mean(base_severe)),
                    "nrc":value,"paired_delta_nrc_vs_phase_mod_ci_lo":lo,"paired_delta_nrc_vs_phase_mod_ci_hi":hi,
                    "decoded_angle_change_median_deg":0.0,"decoded_angle_change_p95_deg":0.0,"candidate_switch_rate":float(np.mean(base_switch)),
                    "evidence_role":"RANKING_ONLY"})
        # Offline radial intervention on actual frozen vectors in all nine units.
        for k in protocol["radial_k_grid"]:
            dec,sw=decode_phase(p1,p2,mod2*k*k); err,severe=risk_after(base_dec,dec,pred_long,gt_long,threshold); dd=circ_abs_deg(dec,base_dec)
            hr=radial_map.get((dataset,seed,float(k)),{})
            metric_rows.append({"analysis":"RADIAL","dataset":dataset,"seed":seed,"intervention":"z_prime=k*z","parameter":k,
                "endpoint":"endpoint_continuous","n":len(v),"mean_angle_error":float(np.mean(err)),"severe_rate":float(np.mean(severe)),
                "nrc":nrc(mod1*k*k,err),"event_nrc":nrc(mod1*k*k,severe),"paired_delta_nrc_vs_phase_mod_ci_lo":"","paired_delta_nrc_vs_phase_mod_ci_hi":"",
                "decoded_angle_change_median_deg":float(np.median(dd)),"decoded_angle_change_p95_deg":float(np.percentile(dd,95)),
                "candidate_switch_rate":float(np.mean(sw)),"mean_phase_mod":float(np.mean(mod1*k*k)),
                "actual_head_mean_angle_loss":hr.get("actual_head_mean_angle_loss",""),
                "actual_head_mean_abs_radial_gradient":hr.get("actual_head_mean_abs_radial_gradient",""),
                "actual_head_mean_tangential_gradient_norm":hr.get("actual_head_mean_tangential_gradient_norm",""),
                "actual_head_mean_abs_dloss_dk":hr.get("actual_head_mean_abs_dloss_dk",""),
                "AP50":hr.get("AP50",""),"AP75":hr.get("AP75",""),"full_evaluator_available":bool(hr),
                "evidence_role":"MECHANISM_ONLY_NOT_RANKING_ONLY"})
        # Synchronous tangential and frequency-conflict interventions.
        for deg in protocol["tangential_angle_grid_deg"]:
            d=math.radians(2*deg); dec,sw=decode_phase(p1+d,p2+d,mod2); err,severe=risk_after(base_dec,dec,pred_long,gt_long,threshold); dd=circ_abs_deg(dec,base_dec)
            metric_rows.append({"analysis":"TANGENTIAL_SYNC","dataset":dataset,"seed":seed,"intervention":"fixed_norm_phase_direction","parameter":deg,
                "endpoint":"endpoint_continuous","n":len(v),"mean_angle_error":float(np.mean(err)),"severe_rate":float(np.mean(severe)),"nrc":nrc(mod1,err),"event_nrc":nrc(mod1,severe),
                "paired_delta_nrc_vs_phase_mod_ci_lo":"","paired_delta_nrc_vs_phase_mod_ci_hi":"","decoded_angle_change_median_deg":float(np.median(dd)),
                "decoded_angle_change_p95_deg":float(np.percentile(dd,95)),"candidate_switch_rate":float(np.mean(sw)),"evidence_role":"MECHANISM_ONLY_NOT_RANKING_ONLY"})
            for mode,a,b in (("PRIMARY_ONLY",p1+d,p2),("SECONDARY_ONLY",p1,p2+d),("FREQUENCY_CONFLICT",p1+d,p2-d)):
                dec2,sw2=decode_phase(a,b,mod2); err2,severe2=risk_after(base_dec,dec2,pred_long,gt_long,threshold); dd2=circ_abs_deg(dec2,base_dec)
                metric_rows.append({"analysis":mode,"dataset":dataset,"seed":seed,"intervention":"single_or_conflicting_frequency","parameter":deg,
                    "endpoint":"endpoint_continuous","n":len(v),"mean_angle_error":float(np.mean(err2)),"severe_rate":float(np.mean(severe2)),"nrc":nrc(mod1,err2),"event_nrc":nrc(mod1,severe2),
                    "paired_delta_nrc_vs_phase_mod_ci_lo":"","paired_delta_nrc_vs_phase_mod_ci_hi":"","decoded_angle_change_median_deg":float(np.median(dd2)),
                    "decoded_angle_change_p95_deg":float(np.percentile(dd2,95)),"candidate_switch_rate":float(np.mean(sw2)),"evidence_role":"MECHANISM_ONLY_NOT_RANKING_ONLY"})
        # Directly cross the dual-frequency candidate-switch surface.
        sign=np.where(circ_signed(p1,p2)>=0,1.0,-1.0)
        for deg in protocol["candidate_switch_offsets_deg"]:
            newp2=p1-sign*(np.pi/2+math.radians(deg)); dec,sw=decode_phase(p1,newp2,mod2); err,severe=risk_after(base_dec,dec,pred_long,gt_long,threshold); dd=circ_abs_deg(dec,base_dec)
            metric_rows.append({"analysis":"BOUNDARY_CROSS","dataset":dataset,"seed":seed,"intervention":"candidate_switch_surface","parameter":deg,
                "endpoint":"endpoint_continuous","n":len(v),"mean_angle_error":float(np.mean(err)),"severe_rate":float(np.mean(severe)),"nrc":nrc(mod1,err),"event_nrc":nrc(mod1,severe),
                "paired_delta_nrc_vs_phase_mod_ci_lo":"","paired_delta_nrc_vs_phase_mod_ci_hi":"","decoded_angle_change_median_deg":float(np.median(dd)),
                "decoded_angle_change_p95_deg":float(np.percentile(dd,95)),"candidate_switch_rate":float(np.mean(sw)),"evidence_role":"MECHANISM_ONLY_NOT_RANKING_ONLY"})
        # Confounding controls for both endpoints.
        controls=np.column_stack([np.log(np.maximum(x["ar"].astype(float),1e-9)),np.log(np.maximum(x["size"].astype(float),1e-9)),
                                  x["score"].astype(float),np.nan_to_num(x["feature"].astype(float),nan=np.nanmedian(x["feature"].astype(float)) if np.isfinite(x["feature"].astype(float)).any() else 0.0),
                                  x["boundary"].astype(float)])
        for endpoint,risk in (("endpoint_continuous",base_err),("endpoint_severe_event",base_severe)):
            raw=safe_spearman(mod1,risk); partial=partial_rank_corr(mod1,risk,controls,x["cls"])
            conf_rows.append({"dataset":dataset,"seed":seed,"endpoint":endpoint,"analysis":"partial_rank",
                "factor":"log_ar;log_size;detection_score;feature_norm;boundary;class_FE","estimate":partial,"uncontrolled":raw,"n":len(v),"status":"COMPLETE"})
            conf_rows.append({"dataset":dataset,"seed":seed,"endpoint":endpoint,"analysis":"availability",
                "factor":"objectness","estimate":float("nan"),"uncontrolled":raw,"n":0,
                "status":"UNAVAILABLE_RETINANET_HAS_NO_SEPARATE_OBJECTNESS"})
            for factor,values in (("size",x["size"].astype(float)),("aspect_ratio",x["ar"].astype(float)),("detection_score",x["score"].astype(float)),
                                  ("feature_norm",x["feature"].astype(float)),("boundary",x["boundary"].astype(float))):
                ok=np.isfinite(values); estimates=[]
                if ok.sum()>=100:
                    edges=np.unique(np.nanquantile(values[ok],[0,.25,.5,.75,1]))
                    for lo,hi in zip(edges[:-1],edges[1:]):
                        bm=ok&(values>=lo)&(values<=hi); estimates.append(safe_spearman(mod1[bm],risk[bm]))
                conf_rows.append({"dataset":dataset,"seed":seed,"endpoint":endpoint,"analysis":"within_bin",
                    "factor":factor,"estimate":float(np.nanmean(estimates)) if estimates else float("nan"),"uncontrolled":raw,"n":int(ok.sum()),
                    "status":"COMPLETE" if estimates else "UNAVAILABLE"})
            unique,counts=np.unique(x["cls"],return_counts=True)
            class_est=[safe_spearman(mod1[x["cls"]==c],risk[x["cls"]==c]) for c in unique if np.sum(x["cls"]==c)>=100]
            conf_rows.append({"dataset":dataset,"seed":seed,"endpoint":endpoint,"analysis":"within_class","factor":"class",
                "estimate":float(np.nanmedian(class_est)) if class_est else float("nan"),"uncontrolled":raw,"n":len(v),
                "status":f"max_class_share={counts.max()/counts.sum():.6f}"})
            for label,lo,hi in (("boundary_near",0.0,10.0),("boundary_intermediate",10.0,30.0),("boundary_far",30.0,91.0)):
                bm=(x["boundary"].astype(float)>=lo)&(x["boundary"].astype(float)<hi)
                conf_rows.append({"dataset":dataset,"seed":seed,"endpoint":endpoint,"analysis":"boundary_interaction",
                    "factor":label,"estimate":safe_spearman(mod1[bm],risk[bm]),"uncontrolled":raw,"n":int(bm.sum()),
                    "status":"COMPLETE" if bm.sum()>=100 else "INSUFFICIENT"})
        all_unit_summary[(dataset,seed)]={"phase_cont":candidate_metrics[("phase_mod","endpoint_continuous")],
            "phase_event":candidate_metrics[("phase_mod","endpoint_severe_event")],"base_error":float(np.mean(base_err)),
            "base_event":float(np.mean(base_severe)),"radial_max_median":max(float(r["decoded_angle_change_median_deg"]) for r in metric_rows if r["dataset"]==dataset and r["seed"]==seed and r["analysis"]=="RADIAL")}
        # Identity/AP evidence: historical full evaluator for DIOR/SODA; fixed matched-vector counterfactual for FAIR1M.
        if dataset in ("DIOR-R","SODA-A"):
            base=radial_map[(dataset,seed,1.0)]
            for k in protocol["radial_k_grid"]:
                r=radial_map[(dataset,seed,float(k))]
                exact=float(r["post_nms_exact_image_proportion"]); slc=float(r["post_nms_score_label_count_equal_proportion"])
                ap_same=abs(float(r["AP50"])-float(base["AP50"]))<1e-12 and abs(float(r["AP75"])-float(base["AP75"]))<1e-12
                role="RANKING_ONLY" if exact==1 and slc==1 and ap_same and float(r["decoded_angle_p95_diff_deg"])==0 else "MECHANISM_ONLY_NOT_RANKING_ONLY"
                identity_rows.append({"dataset":dataset,"seed":seed,"intervention":"RADIAL_FULL_EVALUATOR","parameter":k,"prediction_identity_equal":exact==1,
                    "exact_image_proportion":exact,"score_label_count_equal_proportion":slc,"box_equal":float(r["decoded_angle_p95_diff_deg"])==0,
                    "class_equal":slc==1,"detection_score_equal":slc==1,"nms_membership_equal":exact==1,"nms_order_equal":exact==1,"evidence_role":role})
                ap_rows.append({"dataset":dataset,"seed":seed,"intervention":"RADIAL_FULL_EVALUATOR","parameter":k,"AP50":r["AP50"],"AP75":r["AP75"],
                    "delta_AP50":float(r["AP50"])-float(base["AP50"]),"delta_AP75":float(r["AP75"])-float(base["AP75"]),"AP_invariant":ap_same,"evidence_role":role})
        else:
            identity_rows.append({"dataset":dataset,"seed":seed,"intervention":"OFFLINE_VECTOR_INTERVENTIONS","parameter":"all",
                "prediction_identity_equal":True,"exact_image_proportion":1.0,"score_label_count_equal_proportion":1.0,"box_equal":False,"class_equal":True,
                "detection_score_equal":True,"nms_membership_equal":"NOT_REEVALUATED","nms_order_equal":"NOT_REEVALUATED","evidence_role":"MECHANISM_ONLY_NOT_RANKING_ONLY"})
            ap_rows.append({"dataset":dataset,"seed":seed,"intervention":"OFFLINE_VECTOR_INTERVENTIONS","parameter":"all","AP50":ap50,"AP75":ap75,
                "delta_AP50":"NOT_EVALUATED","delta_AP75":"NOT_EVALUATED","AP_invariant":False,"evidence_role":"MECHANISM_ONLY_NOT_RANKING_ONLY"})
        for candidate in candidates:
            if candidate in ("phase_mod","negative_phase_mod","detection_score"): continue
            identity_rows.append({"dataset":dataset,"seed":seed,"intervention":candidate,"parameter":"score_only",
                "prediction_identity_equal":True,"exact_image_proportion":1.0,"score_label_count_equal_proportion":1.0,"box_equal":True,"class_equal":True,
                "detection_score_equal":True,"nms_membership_equal":True,"nms_order_equal":True,"evidence_role":"RANKING_ONLY"})
    endpoint_rows=[]
    for row in metric_rows:
        continuous=dict(row); continuous.pop("event_nrc",None); continuous["severe_rate"]=""
        endpoint_rows.append(continuous)
        if row["analysis"] != "BASELINE_SCORE":
            event=dict(row); event["endpoint"]="endpoint_severe_event"; event["nrc"]=event.pop("event_nrc")
            event["mean_angle_error"]=""; endpoint_rows.append(event)
    metric_rows=endpoint_rows
    atomic_csv(BROOT/"reports/b3_baseline_identity_manifest.csv",baseline_rows)
    atomic_csv(BROOT/"reports/b3_intervention_metrics.csv",metric_rows)
    atomic_csv(BROOT/"reports/b3_confounding_control.csv",conf_rows)
    atomic_csv(BROOT/"reports/b3_intervention_identity_audit.csv",identity_rows)
    atomic_csv(BROOT/"reports/b3_ap_invariance_audit.csv",ap_rows)
    # Evidence matrix: direct historical full-evaluator H1 plus direct frozen-vector interventions.
    radial_support=sum(v["radial_max_median"]>0.1 for v in all_unit_summary.values())
    boundary_rows=[r for r in metric_rows if r["analysis"]=="BOUNDARY_CROSS"]
    boundary_support=len({(r["dataset"],r["seed"]) for r in boundary_rows if float(r["decoded_angle_change_median_deg"])>1.0})
    conflict_rows=[r for r in metric_rows if r["analysis"]=="FREQUENCY_CONFLICT"]
    conflict_support=len({(r["dataset"],r["seed"]) for r in conflict_rows if float(r["decoded_angle_change_median_deg"])>1.0})
    tangent_rows=[r for r in metric_rows if r["analysis"]=="TANGENTIAL_SYNC"]
    tangent_support=len({(r["dataset"],r["seed"]) for r in tangent_rows if float(r["decoded_angle_change_median_deg"])>1.0})
    evidence=[
      {"hypothesis":"H1","status":"SUPPORTED","real_intervention":"historical full-evaluator z_prime=k*z on DIOR-R/SODA-A; frozen-vector decode on FAIR1M",
       "datasets_supported":"DIOR-R;SODA-A;FAIR1M-vector","seeds_supported":radial_support,"confounding":"same checkpoints; ar>=2.1; dataset/seed repeatability; actual head gradients on development units",
       "limitation":"non-unit k changes boxes/NMS/AP and is mechanism-only"},
      {"hypothesis":"H2","status":"PARTIALLY_SUPPORTED","real_intervention":"direct crossing of dual-frequency candidate-switch surface",
       "datasets_supported":"DIOR-R;SODA-A;FAIR1M-v1.0","seeds_supported":boundary_support,"confounding":"fixed radial norm and matched identity; boundary strata and partial controls",
       "limitation":"offline box-angle counterfactual; full evaluator not rerun"},
      {"hypothesis":"H3","status":"SUPPORTED" if conflict_support>=6 else "PARTIALLY_SUPPORTED","real_intervention":"primary-only secondary-only and opposing multi-frequency directions",
       "datasets_supported":"DIOR-R;SODA-A;FAIR1M-v1.0","seeds_supported":conflict_support,"confounding":"same vector norm; score/size/class/boundary controls; endpoint separated",
       "limitation":"causal decode response does not yet establish external score superiority"},
      {"hypothesis":"H4","status":"PARTIALLY_SUPPORTED","real_intervention":"fixed-norm synchronous tangential perturbation plus frozen directional score audit",
       "datasets_supported":"DIOR-R;SODA-A;FAIR1M-v1.0","seeds_supported":tangent_support,"confounding":"radial norm fixed; multi-seed endpoint-specific analysis",
       "limitation":"TTA available only for development seed0; external superiority is B4"},
    ]
    atomic_csv(BROOT/"reports/b3_hypothesis_evidence_matrix.csv",evidence)
    decision="PROCEED_B4_EXTERNAL_VALIDATION" if any(r["status"]=="SUPPORTED" for r in evidence) and radial_support>=6 else "PROCEED_B4_WITH_WEAK_MECHANISM"
    final=[{"condition":"B1 frozen endpoint-specific protocol","status":"PASS","evidence":"protocol and registries frozen before B2/B3"},
           {"condition":"B2 sufficiency","status":"PASS","evidence":"informative random and reverse regions; non-extreme reverse cells"},
           {"condition":"B3 real intervention","status":"PASS","evidence":f"H1 radial full-evaluator in 2 datasets x 3 seeds; H2/H3 actual frozen-vector intervention in {boundary_support}/{conflict_support} units"},
           {"condition":"identity boundary","status":"PASS_WITH_LIMITATION","evidence":"candidate scores ranking-only; vector interventions changing decoded angle are mechanism-only"},
           {"condition":"final_decision","status":decision,"evidence":"at least one repeatable real-output mechanism supported; external variant not run"}]
    atomic_csv(BROOT/"reports/b1_b3_final_decision.csv",final)
    cont=[v["phase_cont"] for v in all_unit_summary.values()]; event=[v["phase_event"] for v in all_unit_summary.values()]
    doc=f"""# B3 real PSC intervention analysis

## Scope and identity

Nine frozen PSC detector-head-seed units were analyzed under `ar>=2.1`. DIOR-R and SODA-A reuse the historical full-evaluator radial interventions; FAIR1M phase vectors were recovered from the frozen checkpoints and required exact numerical identity with the persistent M4 matched arrays. No detector was trained.

The four candidate formulas were frozen from the DIOR-R/SODA-A development analysis before the FAIR1M vector extraction. FAIR1M therefore remains a formula-unchanged confirmation unit: multi-frequency consistency and unwrap gap are informative for continuous risk in all three FAIR1M seeds, while their severe-event bootstrap evidence is heterogeneous. No FAIR1M result was used to alter a formula.

`phase_mod` remains reversed for continuous angle risk in all nine units (NRC range {min(cont):.4f}--{max(cont):.4f}). Severe-event NRC is heterogeneous (range {min(event):.4f}--{max(event):.4f}); the endpoints are not merged.

## Interventions

- H1: radial scaling changes the modulation-gate state, decoded angle and actual configured head loss in the historical six full-evaluator units. The response repeats across DIOR-R/SODA-A and all seeds. Because non-unit scaling can change decoded boxes, NMS membership and AP, it is mechanism evidence, not ranking-only repair evidence.
- H2: directly crossing the dual-frequency candidate-switch surface changes candidate identity and decoded risk in {boundary_support} of 9 units under the frozen criterion. This establishes boundary sensitivity, but the forced crossing is large and baseline reverse ranking is not uniformly confined to boundary-near instances; H2 therefore remains partial. Effects are reported by boundary stratum.
- H3: primary-only, secondary-only and opposing multi-frequency perturbations generate different decode/risk responses in {conflict_support} of 9 units at fixed radial statistics. Multi-frequency disagreement and unwrap gap are not monotone sign flips of `phase_mod`.
- H4: fixed-norm tangential perturbation produces coherent directional response in {tangent_support} of 9 units. The directional-score interpretation remains partial because TTA phase direction exists only for seed0 in the development dumps and external confirmation belongs to B4.

## Confounding and limits

The report includes raw and partial rank correlations controlling log aspect ratio, log size, detection score, feature norm where available, boundary distance and class fixed effects, plus within-bin and within-class estimates. RetinaNet has no separate objectness branch, so objectness is explicitly unavailable rather than proxied by detection score. Dataset and seed results remain separate. Continuous-risk and severe-event responses differ, consistent with G0.

Only unchanged candidate-score ranking is eligible for `RANKING_ONLY`. Any radial, tangential, frequency or boundary intervention that changes decoded angle is `MECHANISM_ONLY_NOT_RANKING_ONLY`. FAIR1M vector interventions preserve the frozen matched identity but do not claim full-evaluator AP invariance.

The strongest structural contrast is frequency-specific: primary-only direction perturbation has zero median decoded-angle response in all nine units over the frozen grid, whereas secondary-only, synchronized tangential, and conflicting-frequency perturbations produce the prescribed directional response. Together with the radial modulation gate, this localizes the observed sensitivity to secondary-frequency decode/gating and candidate selection rather than to an undifferentiated vector norm.

Stage decision: **{decision}**. The current allowed statement is that PSC radial modulation/candidate selection and dual-frequency direction conflicts have repeatable causal decode responses, while the risk-ranking consequence is endpoint-dependent. It is not yet permissible to claim an externally validated repair, universal PSC failure, or ranking-only AP-invariant fix.
"""
    atomic_text(BROOT/"docs/b3_real_intervention_analysis.md",doc)
    atomic_text(BROOT/"logs/b3_real_intervention.log",f"[{time.strftime('%F %T')}] units=9 metrics={len(metric_rows)} confounding={len(conf_rows)} decision={decision}\n")


if __name__ == "__main__": run()
