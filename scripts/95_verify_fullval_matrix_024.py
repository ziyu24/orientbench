#!/usr/bin/env python3
"""95_verify_fullval_matrix_024.py — read-only verification of 024 full-val + storage."""
import csv,hashlib,json,os,subprocess,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
SCRATCH="/dev/shm/cqc/orientbench"; FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FORBIDDEN=["all datasets covered","9-detector matrix complete","cross-dataset formal gate","ARS-DETR substituted RHINO","full benchmark complete"]
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("scratch_exists",os.path.isdir(SCRATCH))
    for f in ("resource_startup_024.json","fullval_matrix_plan_024.csv","metrics_024.csv","env_network_unlock_024.json","adapter_manifest_024.json"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    # 024 full-val cells: raw+schema in scratch, manifest in project pointing to scratch
    for ds,b in (("DIOR-R","3"),("FAIR1M-v1.0","5"),("SODA-A","4")):
        mp=os.path.join(P,"outputs/predictions",ds,b,"manifest.json")
        if os.path.isfile(mp):
            m=json.load(open(mp))
            c(f"manifest_scratch:{ds}",m["raw_pkl_scratch"].startswith(SCRATCH) and m["schema_scratch"].startswith(SCRATCH))
            c(f"manifest_sha:{ds}",len(m.get("raw_pkl_sha256",""))==64 and len(m.get("schema_sha256",""))==64)
            c(f"fullval:{ds}",m.get("fullval") is True)
        else:
            c(f"manifest_scratch:{ds}",False,"no manifest")
    # no 024 large schema in project
    big=[f for f in subprocess.run(["bash","-c",f"find {P}/outputs/predictions -name 'pred_*fullval*.jsonl' 2>/dev/null"],
         capture_output=True,text=True).stdout.split() if f]
    c("no_fullval_schema_in_project",not big,big[:2])
    # git does not track large files
    tracked=subprocess.run(["git","-C",P,"ls-files"],capture_output=True,text=True).stdout
    c("git_no_large",not any(l.endswith(".pkl") or "fullval" in l and l.endswith(".jsonl") for l in tracked.splitlines()))
    # thresholds unchanged
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    # GPU world_size 4
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    c("all_gpu_world_size_4",all(t["world_size"]==4 and t["batch_override"] is False for t in gp["tasks"]))
    # full-val status recorded; non-DOTA exploratory
    met=list(csv.DictReader(open(os.path.join(REP,"metrics_024.csv"))))
    c("fullval_exploratory",all("exploratory" in m["formal_scope"] for m in met if m.get("n_used")))
    # ARS-DETR not RHINO; point2rbox weak_nonformal
    env=json.load(open(os.path.join(REP,"env_network_unlock_024.json")))
    c("arsdetr_not_rhino",env["arsdetr"]["not_RHINO_replacement"] is True)
    c("point2rbox_weak_nonformal",env["point2rbox"]["weak_nonformal"] is True)
    bad=[]
    for f in ("metrics_024.md","fullval_matrix_plan_024.md","env_network_unlock_024.md"):
        t=open(os.path.join(REP,f)).read().lower()
        for ph in FORBIDDEN:
            if ph.lower() in t: bad.append(f"{f}:{ph}")
    c("no_forbidden_overclaim",not bad,bad)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED",
         "n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"full_project_complete":False,"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_fullval_matrix_024.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Full-Val Matrix Verification 024","",f"> {out['time']}",f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+\
      [f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_fullval_matrix_024.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-024fv] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
