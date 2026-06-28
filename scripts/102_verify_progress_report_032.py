#!/usr/bin/env python3
"""102_verify_progress_report_032.py — read-only verification of 032 progress report."""
import hashlib,json,os,sys,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
MAIN=os.path.join(P,"docs/orientbench_project_progress_report.md")
COPY=os.path.join(P,"outputs/releases/orientbench_final_current_scope/orientbench_project_progress_report.md")
SUMM=os.path.join(P,"docs/orientbench_project_progress_report.summary.json")
FORB=["full project complete","all datasets covered","9-detector matrix complete","genuine physical multi-view solved","cross-host causal proved","ARS-DETR substituted RHINO"]
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("main_exists",os.path.isfile(MAIN))
    c("release_copy_exists",os.path.isfile(COPY))
    c("summary_json_exists",os.path.isfile(SUMM))
    txt=open(MAIN).read().lower() if os.path.isfile(MAIN) else ""
    bad=[ph for ph in FORB if ph.lower() in txt and ("❌" not in txt.split(ph.lower())[0][-4:] if ph.lower() in txt else False)]
    # robust: forbidden phrases only appear in the 禁止 section prefixed with ❌; check they're not asserted positively
    c("no_forbidden_overclaim",all(("❌" in txt[max(0,txt.find(ph.lower())-6):txt.find(ph.lower())]) for ph in FORB if ph.lower() in txt),"")
    c("states_full_project_false","full_project_complete=false" in txt or "full project 完成 = 否" in txt)
    c("states_non_dota_exploratory","exploratory" in txt and "non-dota" in txt.replace("非 dota","non-dota") or "非 dota" in txt or "exploratory" in txt)
    c("states_scratch_non_persistent","非持久" in open(MAIN).read() or "non-persistent" in txt)
    if os.path.isfile(SUMM):
        s=json.load(open(SUMM))
        c("summary_scope_flags",s["current_approved_scope_complete"] is True and s["full_project_complete"] is False)
        c("summary_required_fields",all(k in s for k in ("formal_scope","exploratory_cells","datasets","detector_coverage","formal_gates","blocked_items","release_path","git_head","git_tag","thresholds_sha256","pytest_passed","verifiers")))
    cur=hashlib.sha256(open(os.path.join(P,"configs/thresholds.yaml"),"rb").read()).hexdigest()
    c("thresholds_unchanged",cur==FROZEN,cur[:16])
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_checks":len(ch),"n_pass":sum(x["ok"] for x in ch),"checks":ch}
    json.dump(out,open(os.path.join(P,"outputs/bench_core/reports/verification_progress_report_032.json"),"w"),indent=2,ensure_ascii=False)
    print(f"[verify-032] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
