#!/usr/bin/env python3
"""verify_p3_method_package_044.py — read-only verification of 044 method package."""
import hashlib,os,subprocess,sys,time,json
ROOT="/home/rspip/cqc/pro/study/orientbench"; V=f"{ROOT}/measure_fix_v2"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    rep=f"{V}/docs/p3_method_package_report.md"; t=rd(rep); tl=t.lower()
    c("main_report",os.path.isfile(rep))
    for f in ("p3_selector_method_spec.md","paper_outline_measure_diagnose_fix_v1.md","claim_ledger_measure_fix_v1.md","measure_fix_route_status.md"):
        c(f"doc:{f}",os.path.isfile(f"{V}/docs/{f}"))
    for f in ("real_tta_coverage_044.csv","real_tta_coverage_044.md","fig_g2doubleprime_size_control.csv",
              "fig_deployable_leave_dataset_detector.csv","fig_route_c_real_tta.csv","fig_track_a_psc_mechanism.csv",
              "table_main_results_measure_fix.csv","table_ablation_tracks_abc.csv","table_limitations_and_blockers.csv",
              "artifact_persistence_check_044.json","artifact_persistence_check_044.md"):
        c(f"report:{f}",os.path.isfile(f"{V}/reports/{f}"))
    # forbidden claims
    def forbidden(ph):
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","若","candidate","limited","next-step")):
                return True
        return False
    c("no_p3_final_complete",not forbidden("p3 final complete") and not forbidden("p3 最终完成"))
    c("no_top_venue",not forbidden("顶会 ready") and not forbidden("top venue ready"))
    c("no_trackA_final_proof",not forbidden("track a 为唯一") and ("candidate" in tl))
    c("has_real_tta_limitation","coverage" in tl and ("limited" in tl or "未含" in t or "next-step" in tl))
    c("artifact_manifest",os.path.isfile(f"{V}/reports/artifact_persistence_check_044.json"))
    # frozen
    c("thresholds_unchanged",hashlib.sha256(open(f"{ROOT}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {ROOT} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    # no detector training / no P2 restore (heuristic: no .pth in v2)
    pth=subprocess.run(["bash","-c",f"find {V} -name '*.pth' 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_training_artifacts",not pth.strip())
    big=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    bigv=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files measure_fix_v2 | xargs -I{{}} find {ROOT}/{{}} -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_tracked_v2",not bigv.strip())
    cc=rd(f"{V}/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{V}/reports/verification_p3_method_package_044.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-044] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
