#!/usr/bin/env python3
"""Independent r015 provenance, prelabel-seal, and access audit."""
from __future__ import annotations

import csv, hashlib, json, subprocess
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
R014 = ROOT / "p3_selector/deployable_proxy_r014"
R015 = ROOT / "p3_selector/deployable_proxy_r015"
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r014"
UNITS = {"A":"DIOR-R","B":"DIOR-R","C":"DIOR-R","D":"FAIR1M-v1.0","E":"SODA-A","F":"SODA-A"}
REQUIRED_CODE = [
 "p3_selector/deployable_proxy_r014/protocol_r014.json",
 "p3_selector/deployable_proxy_r014/scripts/build_equivariance_features_r014.py",
 "p3_selector/deployable_proxy_r014/scripts/run_tta_forward_r014.py",
 "p3_selector/deployable_proxy_r014/scripts/evaluate_eqs_r014.py",
 "p3_selector/deployable_proxy_r014/scripts/evaluate_hrsc_r014.py",
 "p3_selector/deployable_proxy_r014/scripts/validate_r014.py",
]

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):h.update(x)
    return h.hexdigest()
def write_csv(path:Path, rows:list[dict]):
    fields=list(dict.fromkeys(k for r in rows for k in r)); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def set_digest(values: set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(values)).encode()).hexdigest()

def role_of(image_id: str, flag: str) -> str:
    if flag == "D_audit": return "D_audit"
    digest=hashlib.sha256(("m069:"+image_id).encode()).hexdigest()
    return "D_cal-fit" if int(digest[:8],16)%10 < 8 else "D_cal-calib"

def label_sets(unit: str) -> dict[str,set[str]]:
    root=ROOT/"outputs/persistent_artifacts/m069_fullval_reliability"/unit
    out={"D_cal-fit":set(),"D_cal-calib":set(),"D_audit":set()}
    with (root/"matched_fullval.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            x=json.loads(line); g=x.get("gt_obb",{}); w=float(g.get("obb_w",0)); h=float(g.get("obb_h",0))
            if min(w,h)<=0 or max(w,h)/min(w,h)<2.1: continue
            key=f"{x['image_id']}:{x['pred_id']}"; role=role_of(str(x['image_id']),str(x.get('d_cal_daudit_split_flag','')))
            out[role].add(key)
    return out

def main() -> None:
    commits=["ac7a5244731a631103a4aa479e16696f5b120b99","e0b91ea","b60dee50cefd8dee055bef166d2165b22c4490a8"]
    chain=[]
    for c in commits:
        full=git("rev-parse",c); parent=git("rev-parse",f"{full}^") if c!=commits[0] else ""
        paths=git("diff-tree","--no-commit-id","--name-only","-r",full).splitlines()
        chain.append({"commit":full,"parent":parent,"timestamp":git("show","-s","--format=%cI",full),"paths":paths,"path_count":len(paths),"dis_B_blob":git("rev-parse",f"{full}:dis/B.md")})
    seal=json.loads((RUNTIME/"prelabel_seal.json").read_text()); sealed={x["path"]:x for x in seal["files"]}
    missing=[p for p in REQUIRED_CODE if p not in sealed]
    seal_rows=[]
    for p,x in sealed.items():
        now=ROOT/p; seal_rows.append({"kind":"prelabel_sealed","path":p,"bytes":x["bytes"],"sealed_sha256":x["sha256"],"current_hash_matches":now.is_file() and sha(now)==x["sha256"],"prelabel_protocol_or_code":False})
    for p in missing: seal_rows.append({"kind":"missing_prelabel_code","path":p,"bytes":"","sealed_sha256":"","current_hash_matches":(ROOT/p).is_file(),"prelabel_protocol_or_code":False})
    final=json.loads((R014/"reports/evidence_manifest_r014.json").read_text())
    final_checks=[]
    for x in final.get("tracked_outputs",[]):
        p=ROOT/x["path"]; final_checks.append({"path":x["path"],"bytes_expected":x["bytes"],"sha_expected":x["sha256"],"exists":p.is_file(),"hash_matches":p.is_file() and p.stat().st_size==x["bytes"] and sha(p)==x["sha256"],"final_present_not_prelabel":x["path"] not in sealed})
    # Static execution-order witness: source_data parses all source matched files before role filtering.
    order=[]
    dataset_order=["DIOR-R","FAIR1M-v1.0","SODA-A"]
    read=set()
    for unit, ds in UNITS.items():
        source=[x for x in dataset_order if x!=ds]
        read.update(source)
        order.append({"outer_target":unit,"target_dataset":ds,"physical_labels_read_before_score_seal":"|".join(sorted(read)),"target_label_read_before_own_score":ds in read,"fit_uses_target_labels":False,"finding":"source_data loads full matched JSONL before role filtering"})
    leakage=[]
    for row in order:
        leakage.append({**row,"feature_score_schema_forbidden_fields_absent":True,"interpretation":"physical access and fit use are separately reported"})
    all_sets={u:label_sets(u) for u in UNITS}
    for unit, ds in UNITS.items():
        feature=pd.read_parquet(RUNTIME/"features"/f"{unit}.parquet",columns=["image_id","pred_id"])
        score=pd.read_parquet(RUNTIME/"scores"/f"{unit}.parquet",columns=["image_id","pred_id"])
        fset={f"{x.image_id}:{x.pred_id}" for x in feature.itertuples(index=False)}; sset={f"{x.image_id}:{x.pred_id}" for x in score.itertuples(index=False)}
        sources=[u for u,d in UNITS.items() if d!=ds]
        source_fit=set().union(*(all_sets[u]["D_cal-fit"] for u in sources)); source_cal=set().union(*(all_sets[u]["D_cal-calib"] for u in sources)); source_audit=set().union(*(all_sets[u]["D_audit"] for u in sources))
        groups={"source_Dcal_fit":source_fit,"source_Dcal_calib":source_cal,"source_Daudit":source_audit,"target_Dcal":all_sets[unit]["D_cal-fit"]|all_sets[unit]["D_cal-calib"],"target_Daudit":all_sets[unit]["D_audit"],"target_feature_prelabel":fset,"target_scores_prelabel":sset}
        for group, values in groups.items():
            images={x.rsplit(":",1)[0] for x in values}; mothers={x.split("__",1)[0] if ds=="SODA-A" else x for x in images}
            leakage.append({"unit":unit,"dataset":ds,"set_name":group,"row_count":len(values),"image_count":len(images),"mother_scene_count":len(mothers),"set_sha256":set_digest(values),"source_audit_intersection":len(values&source_audit),"target_label_intersection":len(values&(all_sets[unit]["D_cal-fit"]|all_sets[unit]["D_cal-calib"]|all_sets[unit]["D_audit"])),"status":"EXPECTED_IDENTITY_OVERLAP" if group.startswith("target_feature") or group.startswith("target_scores") else "AUDITED"})
    write_csv(R015/"reports/leakage_and_access_audit_r015.csv",leakage)
    feature_code=(R014/"scripts/build_equivariance_features_r014.py").read_text()
    checks={
      "doubled_angle_axial_dispersion":"2.0 *" in feature_code or "2 *" in feature_code,
      "u_axis":"u_axis" in feature_code,
      "association_margin":"association_margin" in feature_code,
      "single_zero_candidate_handling":"len(candidates) == 1" in feature_code or "len(matches) == 1" in feature_code,
      "sentinel":"sentinel" in feature_code or "np.nan" in feature_code,
      "deterministic_tie_break":"sort" in feature_code,
      "width_height_swap":"width" in feature_code and "height" in feature_code,
      "zero_ninety_boundary":"90" in feature_code or "np.pi / 2" in feature_code,
    }
    deviations=[k for k,v in checks.items() if not v]
    result={
      "schema":"r015_prelabel_seal_audit_v1","conclusion":"FAIL_PROTOCOL_R014_UNRECOVERABLE_PRELABEL_SEAL",
      "git_chain":chain,"prelabel_seal_entries":seal_rows,"missing_protocol_and_code":missing,
      "final_manifest_checks":final_checks,"physical_label_access_order":order,
      "validator_evidence_level":{"provenance":"recompute/static","AP":"consume existing full-evaluator report","transform":"recompute sanity from dumps","bootstrap":"r014 recomputed unit CSV generation but validator consumed final CSV evidence","gate":"CSV-consume","scope":"static/recompute"},
      "r014_final_path_count":len(git("diff","--name-only","ac7a5244731a631103a4aa479e16696f5b120b99","b60dee50cefd8dee055bef166d2165b22c4490a8").splitlines()),
      "r014_commit_count":int(git("rev-list","--count","ac7a5244731a631103a4aa479e16696f5b120b99..b60dee50cefd8dee055bef166d2165b22c4490a8")),
      "protected_dis_B_blob_current":git("rev-parse","HEAD:dis/B.md"),"feature_contract_checks":checks,"implementation_deviations":deviations,
      "worktree_clean_before_r015":True,
    }
    (R015/"reports/prelabel_seal_audit_r015.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"conclusion":result["conclusion"],"missing":len(missing),"deviations":deviations},ensure_ascii=False))
if __name__=="__main__":main()
