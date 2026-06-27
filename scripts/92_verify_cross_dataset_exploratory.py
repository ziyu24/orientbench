#!/usr/bin/env python3
"""92_verify_cross_dataset_exploratory.py — read-only verification of 021 cross-dataset."""
import csv, hashlib, json, os, sys, time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FORBIDDEN=["full benchmark complete","all datasets covered","9-detector matrix complete","ARS-DETR substituted RHINO","cross-dataset formal gate"]
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for f in ("cross_dataset_execution_plan_021.csv","cross_dataset_metrics_021.csv","cross_dataset_probe_summary_021.csv","remaining_detector_blockers_021.csv"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    met=list(csv.DictReader(open(os.path.join(REP,"cross_dataset_metrics_021.csv"))))
    real=[m for m in met if m.get("dataset") not in (None,"none","")]
    c("all_cross_dataset_exploratory",all("exploratory" in m.get("formal_scope","") for m in real),[m.get("formal_scope") for m in real])
    c("hrsc_angle_uncertain",any(m["dataset"]=="HRSC2016" and m.get("angle_error_gate_status")=="blocked_angle_uncertain" for m in real))
    fails=list(csv.DictReader(open(os.path.join(REP,"cross_dataset_failures_021.csv"))))
    c("dior_fair1m_blocked",any("DIOR" in f["cell"] for f in fails) and any("FAIR1M" in f["cell"] for f in fails))
    bl={b["detector"]:b for b in csv.DictReader(open(os.path.join(REP,"remaining_detector_blockers_021.csv")))}
    c("arsdetr_not_rhino",bl.get("ARS-DETR",{}).get("confusable_with_rhino","").startswith("NO"))
    c("point2rbox_network_reason","YES" in bl.get("point2rbox_v2",{}).get("network_download",""))
    bad=[]
    for f in ("cross_dataset_metrics_021.md","cross_dataset_execution_plan_021.md","cross_dataset_probe_summary_021.md"):
        t=open(os.path.join(REP,f)).read().lower()
        for ph in FORBIDDEN:
            if ph.lower() in t: bad.append(f"{f}:{ph}")
    c("no_forbidden_overclaim",not bad,bad)
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    hrsc=[t for t in gp["tasks"] if "HRSC" in t["cell"]]
    c("hrsc_world_size_4",hrsc and all(t["world_size"]==4 and t["batch_override"] is False for t in hrsc))
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED",
         "n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"cross_dataset_status":"partial_exploratory",
         "full_project_complete":False,"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_cross_dataset_exploratory_021.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Cross-Dataset Exploratory Verification (read-only)","",f"> {out['time']}",
       f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']}); cross_dataset_status=partial_exploratory; full_project_complete=false","",
       "| check | ok | detail |","|---|---|---|"]+[f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_cross_dataset_exploratory_021.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-xds] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
