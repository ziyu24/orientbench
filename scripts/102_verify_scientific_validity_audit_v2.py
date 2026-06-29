#!/usr/bin/env python3
"""102_verify_scientific_validity_audit_v2.py — read-only verification of 033 P1 validity audit."""
import hashlib,json,os,subprocess,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REP=os.path.join(P,"outputs/bench_core/reports")
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    docs={"audit":f"{P}/docs/scientific_validity_audit.md","psc":f"{P}/docs/psc_miscalibration_mechanism_note.md",
          "track":f"{P}/docs/selection_score_three_track_definition.md"}
    for k,v in docs.items(): c(f"exists:{k}",os.path.isfile(v))
    for f in ("scientific_validity_audit_v2.json","scientific_validity_audit_v2.csv","tail_risk_analysis_v2.csv",
              "construct_validity_nrc_v2.csv","persistent_prediction_manifest_v2.json"):
        c(f"exists:{f}",os.path.isfile(os.path.join(REP,f)))
    # contradictions fixed in progress report
    pr=rd(f"{P}/docs/orientbench_project_progress_report.md")
    c("psc_wording_fixed","不是**要求每个 detector NRC" in pr or "不**要求每个 detector NRC" in pr)
    c("rtmdet32_noted","#32" in pr and "未进入" in pr)
    c("no_n3_independence","n=3 独立性 OK" not in pr and "独立性 OK" not in pr)
    # no chasing public mAP / trainval-test
    audit=rd(docs["audit"])
    c("dota_split_correct","train 训练" in audit and "val 验证" in audit)
    c("no_chase_public_map","不追" in audit and ("trainval/test" in audit or "非 trainval" in audit))
    # scope guards
    sj=json.load(open(os.path.join(REP,"scientific_validity_audit_v2.json")))
    c("full_project_false",sj["scope_guards"]["full_project_complete"] is False)
    c("non_dota_exploratory",sj["scope_guards"]["non_dota_exploratory"] is True)
    c("no_train",sj["scope_guards"]["no_train"] is True)
    # construct validity computed
    c("construct_validity_present","spearman_nrc_map" in sj["construct_validity"])
    c("tail_risk_present","unmasked_p99_range_deg" in sj["tail_risk"])
    # thresholds + git
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    # persistent artifacts gitignored
    gi=rd(f"{P}/.gitignore")
    c("persistent_gitignored","persistent_artifacts" in gi)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"checks":ch}
    json.dump(out,open(os.path.join(REP,"verification_scientific_validity_audit_v2.json"),"w"),indent=2,ensure_ascii=False)
    print(f"[verify-033] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
