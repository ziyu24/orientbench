#!/usr/bin/env python3
"""94_verify_cross_dataset_multidetector.py — read-only verification of 023."""
import csv,hashlib,json,os,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FORBIDDEN=["all datasets covered","9-detector matrix complete","cross-dataset formal gate","ARS-DETR substituted RHINO","full benchmark complete"]
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for f in ("cross_dataset_multidetector_plan_023.csv","cross_dataset_schema_validation_023.csv","cross_dataset_metrics_023.csv","cross_dataset_fullval_status_023.csv"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    plan=list(csv.DictReader(open(os.path.join(REP,"cross_dataset_multidetector_plan_023.csv"))))
    valid={"ready_to_run","already_available","blocked_no_checkpoint","blocked_no_config","blocked_dependency",
           "blocked_oom","converter_failed","unsupported_dataset","weak_nonformal","not_applicable","blocked_config_mismatch"}
    c("plan_schema_valid",all(r["status"].split()[0] in valid for r in plan),[r["status"] for r in plan])
    met=list(csv.DictReader(open(os.path.join(REP,"cross_dataset_metrics_023.csv"))))
    c("multidetector_coverage",len({(m["dataset"],m["baseline_id"]) for m in met})>=7)
    c("dior_multi",sum(1 for m in met if m["dataset"]=="DIOR-R")>=3)
    c("all_exploratory",all("exploratory" in m["formal_scope"] for m in met))
    c("hrsc_angle_uncertain",any(m["dataset"]=="HRSC2016" and "uncertain" in m["angle_status"] for m in met))
    sv=list(csv.DictReader(open(os.path.join(REP,"cross_dataset_schema_validation_023.csv"))))
    c("schema_nonzero",all(int(s["n_schema"])>0 for s in sv))
    fv=list(csv.DictReader(open(os.path.join(REP,"cross_dataset_fullval_status_023.csv"))))
    c("fullval_no_silent_truncation",all("subset" in r["used"].lower() and r["reason"] for r in fv))
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    c("all_gpu_world_size_4",all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"]))
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    # no 032/C5 artifacts
    c("no_032_c5_artifacts",not any("032" in f or "source_teacher" in f.lower() or "c5" in f.lower()
                                     for f in os.listdir(REP)))
    bad=[]
    for f in ("cross_dataset_multidetector_plan_023.md","cross_dataset_metrics_023.md"):
        t=open(os.path.join(REP,f)).read().lower()
        for ph in FORBIDDEN:
            if ph.lower() in t: bad.append(f"{f}:{ph}")
    c("no_forbidden_overclaim",not bad,bad)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED",
         "n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"cross_dataset_status":"partial_exploratory_multidetector",
         "full_project_complete":False,"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_cross_dataset_multidetector_023.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Cross-Dataset Multi-Detector Verification 023","",f"> {out['time']}",f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+\
      [f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_cross_dataset_multidetector_023.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-023] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
