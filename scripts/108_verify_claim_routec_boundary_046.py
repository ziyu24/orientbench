#!/usr/bin/env python3
"""108_verify_claim_routec_boundary_046.py — read-only verification of 046."""
import hashlib,os,subprocess,time,json
P="/home/rspip/cqc/pro/study/orientbench"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    docs=["claim_language_cleanup_report","route_c_dataflow_audit","diagnose_predicts_fix_boundary","real_tta_non_psc_extension","track_a_mechanism_boundary"]
    for d in docs: c(f"exists:{d}",os.path.isfile(f"{P}/docs/{d}.md"))
    # claim cleanup removed top-venue selling from MAIN draft (only negated/forbidden mentions remain)
    draft=rd(f"{P}/measure_fix_v2/docs/orientation_reliability_measure_diagnose_fix_draft.md")
    c("draft_no_topvenue_selling","顶刊点" not in draft)
    c("draft_no_strict_independence",("NRC 独立性" not in draft) and ("提供独立于 accuracy" not in draft))
    # route-c audit distinguishes source-supervised vs target GT-free
    rc=rd(f"{P}/docs/route_c_dataflow_audit.md")
    c("routec_source_supervised",("source-supervised" in rc) and ("target gt-free inference" in rc.lower()))
    c("routec_not_fully_gtfree",("不得写 fully GT-free" in rc) or ("非 fully GT-free" in rc))
    # predictive boundary: no D_audit circular claim (verdict not-established or guarded)
    pb=rd(f"{P}/docs/diagnose_predicts_fix_boundary.md")
    c("predboundary_circularity_flagged",("循环" in pb) and ("未成立" in pb or "parallel" in pb.lower()))
    c("predboundary_dota_limitation",("limitation" in pb.lower()) and ("validation" in pb.lower()))
    # real TTA extension: >=2 non-PSC families + >=2 datasets, or failure evidence
    ext=rd(f"{P}/docs/real_tta_non_psc_extension.md")
    c("nonpsc_two_families",("rtmdet" in ext.lower()) and ("orcnn" in ext.lower()))
    c("nonpsc_two_datasets",("dior" in ext.lower()) and ("fair1m" in ext.lower()))
    # track A as mechanism side-branch only
    ta=rd(f"{P}/docs/track_a_mechanism_boundary.md")
    c("trackA_sidebranch",("不决定主线" in ta or "非门控" in ta) and ("definitively broken" not in ta.lower() or "禁止" in ta))
    # frozen
    c("thresholds_unchanged",hashlib.sha256(open(f"{P}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {P} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    cc=rd(f"{P}/measure_fix_v2/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{P}/measure_fix_v2/reports/verification_claim_routec_boundary_046.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-046] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
