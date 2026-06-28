#!/usr/bin/env python3
"""99_verify_full_matrix_finish_029.py — read-only verification of 029 finish."""
import csv,hashlib,json,os,subprocess,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FORB=["full project complete","all datasets covered","9-detector matrix complete","ARS-DETR substituted RHINO","cross-dataset formal gate"]
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for f in ("final_matrix_summary.csv","remaining_blockers.csv","heartbeat_029.json"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    # final matrix has cells across multiple datasets
    rows=list(csv.DictReader(open(os.path.join(REP,"final_matrix_summary.csv"))))
    ds=set(r["dataset"] for r in rows)
    c("matrix_multidataset",len(ds)>=5 and len(rows)>=15,f"{len(rows)} cells, {len(ds)} datasets")
    # non-DOTA all exploratory
    nd=[r for r in rows if r["dataset"] not in ("DOTA-v1.0","DOTA-v1.5")]
    c("non_dota_exploratory",all("exploratory" in r["scope"] for r in nd),len(nd))
    # ARS-DETR not RHINO
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    c("arsdetr_not_rhino",a["not_RHINO_replacement"] is True)
    # not over-claimed full project
    cov=json.load(open(os.path.join(REP,"full_project_coverage_report.json")))
    c("full_project_incomplete",cov.get("final_matrix",{}).get("full_project_complete") is False)
    # thresholds unchanged + no large files
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    # no large schema in project
    bigp=subprocess.run(["bash","-c",f"find {P}/outputs/predictions -name 'pred_b*.jsonl' -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_schema_in_project",not bigp.strip())
    # gpu policy world_size 4
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    c("all_gpu_world_size_4",all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"]))
    # remaining blockers documented
    bl=list(csv.DictReader(open(os.path.join(REP,"remaining_blockers.csv"))))
    c("blockers_documented",any("Strip" in b["item"] for b in bl) and any("point2rbox" in b["item"] for b in bl))
    # no forbidden overclaim in final reports
    bad=[]
    for f in ("final_matrix_summary.md","remaining_blockers.md"):
        t=open(os.path.join(REP,f)).read().lower()
        for ph in FORB:
            if ph.lower() in t: bad.append(f"{f}:{ph}")
    c("no_forbidden_overclaim",not bad,bad)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_full_matrix_finish_029.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Full-Matrix Finish Verification 029","",f"> {out['time']}",f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+[f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_full_matrix_finish_029.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-029] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
