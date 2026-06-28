#!/usr/bin/env python3
"""101_verify_final_release_031.py — read-only verification of 031 final release."""
import csv,hashlib,json,os,subprocess,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for f in ("final_orientbench_report.md","final_orientbench_summary.csv","final_claim_ledger.md","final_limitations.md",
              "final_artifact_manifest.json","final_reproducibility_guide.md","final_release_notes.md",
              "final_coverage_matrix.md","final_blocker_evidence.md"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    rel=os.path.join(P,"outputs/releases/orientbench_final_current_scope")
    for f in ("RELEASE_MANIFEST.json","SHA256SUMS.txt","thresholds.yaml.copy"):
        c(f"release:{f}",os.path.isfile(os.path.join(rel,f)))
    # all 23 cells have manifest
    rows=list(csv.DictReader(open(os.path.join(REP,"final_matrix_summary.csv"))))
    miss=[r for r in rows if not os.path.isfile(os.path.join(P,"outputs/predictions",r["dataset"],r["baseline_id"],"manifest.json"))]
    c("all_cells_have_manifest",not miss,len(miss))
    # scope flags
    am=json.load(open(os.path.join(REP,"final_artifact_manifest.json")))
    c("current_scope_complete",am["current_approved_scope_complete"] is True)
    c("full_project_incomplete",am["full_project_complete"] is False)
    # non-DOTA exploratory
    nd=[r for r in rows if r["dataset"] not in ("DOTA-v1.0","DOTA-v1.5")]
    c("non_dota_exploratory",all("exploratory" in r["scope"] for r in nd))
    # formal claims only DOTA frozen scope (claim ledger forbidden list present)
    cl=open(os.path.join(REP,"final_claim_ledger.md")).read()
    c("forbidden_claims_listed","ARS-DETR substituted RHINO" in cl and "9-detector matrix complete" in cl)
    # thresholds + storage
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    bigp=subprocess.run(["bash","-c",f"find {P}/outputs/predictions -name 'pred_*.jsonl' -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_in_project",not bigp.strip())
    c("docs_report",os.path.isfile(os.path.join(P,"docs/cc_latest_report.md")))
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_final_release_031.json"),"w"),indent=2,ensure_ascii=False)
    L=["# Final Release Verification 031","",f"> {out['time']}",f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})","","| check | ok | detail |","|---|---|---|"]+[f"| {x['check']} | {'✓' if x['ok'] else '✗'} | {x['detail']} |" for x in ch]
    open(os.path.join(REP,"verification_final_release_031.md"),"w").write("\n".join(L)+"\n")
    print(f"[verify-031] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
