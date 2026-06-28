#!/usr/bin/env python3
"""100_verify_final_push_030.py — read-only verification of 030 final push."""
import csv,hashlib,json,os,subprocess,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for f in ("final_push_030.md","final_push_030.csv","final_blocker_evidence_030.md","final_matrix_summary.csv"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    # Strip DIOR unblocked (manifest + in final matrix)
    c("strip_dior_manifest",os.path.isfile(os.path.join(P,"outputs/predictions/DIOR-R/47/manifest.json")))
    rows=list(csv.DictReader(open(os.path.join(REP,"final_matrix_summary.csv"))))
    c("strip_in_matrix",any(r["detector"]=="strip_rcnn" and r["dataset"]=="DIOR-R" for r in rows))
    # non-DOTA exploratory
    nd=[r for r in rows if r["dataset"] not in ("DOTA-v1.0","DOTA-v1.5")]
    c("non_dota_exploratory",all("exploratory" in r["scope"] for r in nd))
    # ARS-DETR not RHINO
    a=json.load(open(os.path.join(REP,"arsdetr_env_025.json")))
    c("arsdetr_not_rhino",a["not_RHINO_replacement"] is True)
    # point2rbox final blocker
    t=open(os.path.join(REP,"final_blocker_evidence_030.md")).read()
    c("point2rbox_final_blocked","blocked_upstream_artifact_unavailable_final" in t)
    # thresholds + storage
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    bigp=subprocess.run(["bash","-c",f"find {P}/outputs/predictions -name 'pred_*.jsonl' -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_in_project",not bigp.strip())
    # docs report exists
    c("docs_report",os.path.isfile(os.path.join(P,"docs/cc_latest_report.md")))
    # gpu policy
    gp=json.load(open(os.path.join(REP,"gpu_policy_record.json")))
    c("all_gpu_world_size_4",all(t2["world_size"]==4 and t2["batch_override"] is False for t2 in gp["tasks"]))
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_final_push_030.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Final Push Verification 030","",f"> {out['time']}",f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+[f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_final_push_030.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-030] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
