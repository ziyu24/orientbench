#!/usr/bin/env python3
"""105_verify_p1_chinese_paper_draft_036.py — read-only verification of 036 P1 Chinese paper draft."""
import hashlib,os,subprocess,sys,time,json
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
MAIN=f"{P}/docs/orientbench_p1_chinese_paper_draft.md"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]; t=rd(MAIN); tl=t.lower()
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("main_exists",os.path.isfile(MAIN))
    # no journal/conference names
    venues=["tgrs","isprs","jprs","cvpr","iccv","tpami","neurips","nature","aaai","eccv"]
    found=[v for v in venues if v in tl]
    c("no_venue_names",not found,found)
    c("has_23_cells",("23 real cells" in t or "23 个真实" in t) and ("6 datasets" in t or "6 个数据" in t or "6 datasets" in tl))
    c("has_bootstrap_ci","bootstrap" in tl and "ci" in tl and "[1.027" in t)
    for fig in ("fig1_reliability_cliff_data.csv","fig2_angle_error_cdf_data.csv","fig3_psc_nrc_ci_data.csv"):
        c(f"fig_data:{fig}",fig in t)
    c("three_track","track a" in tl and "track b" in tl and "track c" in tl)
    # negation-aware forbidden check
    def forbidden(ph):
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","pending","PENDING")):
                return True
        return False
    c("no_complete_independence","完全独立" not in t or "不主张" in t)
    c("no_catastrophic_failure",not forbidden("catastrophic failure") and not forbidden("detector catastrophic"))
    c("no_psc_anglehead_proven","不能说" in t and "angle head" in tl)
    c("no_full_project_complete",not forbidden("full project complete"))
    c("no_c1_multiview_solved",not forbidden("genuine physical multi-view solved") and not forbidden("c1 genuine multi-view"))
    c("no_a4_cross_host_proved",not forbidden("cross-host causal proved"))
    c("dota_train_val",("train 训练" in t and "val 验证" in t) and "非 trainval" in t)
    c("persistent_manifest",os.path.isfile(f"{P}/outputs/bench_core/reports/persistent_prediction_manifest_v2.json"))
    c("thresholds_unchanged",hashlib.sha256(open(f"{P}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    cc=rd(f"{P}/docs/cc_latest_report.md")
    c("cc_has_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{P}/outputs/bench_core/reports/verification_p1_chinese_paper_draft_036.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-036] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
