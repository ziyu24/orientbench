#!/usr/bin/env python3
"""93_verify_cross_dataset_gt_and_runs.py — read-only verification of 022 GT+runs."""
import csv,hashlib,json,os,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
GTIDX=os.path.join(P,"outputs/bench_core/gt_index"); FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FORBIDDEN=["all datasets covered","9-detector matrix complete","cross-dataset formal gate","ARS-DETR substituted RHINO","full benchmark complete"]
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for f in ("dataset_gt_rediscovery_022.csv","gt_index_cross_dataset_022.csv","cross_dataset_metrics_022.csv","soda_a_status_022.csv"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    # GT index nonzero for DIOR/FAIR1M/SODA
    for ds in ("DIOR-R","FAIR1M-v1.0","SODA-A"):
        mp=os.path.join(GTIDX,f"{ds}_val.meta.json")
        n=json.load(open(mp))["n_obb_objects"] if os.path.isfile(mp) else 0
        c(f"gt_nonzero:{ds}",n>0,n)
    # 021 errors corrected
    rd={r["dataset"]:r for r in csv.DictReader(open(os.path.join(REP,"dataset_gt_rediscovery_022.csv")))}
    c("dior_obb_found","FOUND" in rd["DIOR-R"]["status"])
    c("fair1m_obb_found","FOUND" in rd["FAIR1M-v1.0"]["status"])
    c("soda_present","PRESENT" in rd["SODA-A"]["status"])
    # all cross-dataset exploratory
    met=list(csv.DictReader(open(os.path.join(REP,"cross_dataset_metrics_022.csv"))))
    c("all_exploratory",all("exploratory" in m["formal_scope"] for m in met),[m["formal_scope"] for m in met])
    c("cells_have_metrics",sum(1 for m in met if m["n_used"] not in (None,"","0"))>=4)
    # HRSC angle uncertain still
    c("hrsc_angle_uncertain",any(m["dataset"]=="HRSC2016" and "uncertain" in m["angle_status"] for m in met))
    # thresholds unchanged
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    # GPU world_size 4
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    xds=[t for t in gp["tasks"] if any(d in t["cell"] for d in ("DIOR","FAIR1M","SODA","HRSC"))]
    c("xds_world_size_4",xds and all(t["world_size"]==4 and t["batch_override"] is False for t in xds),len(xds))
    # no forbidden overclaim
    bad=[]
    for f in ("cross_dataset_metrics_022.md","dataset_gt_rediscovery_022.md","soda_a_status_022.md"):
        t=open(os.path.join(REP,f)).read().lower()
        for ph in FORBIDDEN:
            if ph.lower() in t: bad.append(f"{f}:{ph}")
    c("no_forbidden_overclaim",not bad,bad)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED",
         "n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"cross_dataset_status":"partial_exploratory_4_datasets",
         "full_project_complete":False,"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_cross_dataset_022.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Cross-Dataset 022 Verification (read-only)","",f"> {out['time']}",
       f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+\
      [f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_cross_dataset_022.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-022] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
