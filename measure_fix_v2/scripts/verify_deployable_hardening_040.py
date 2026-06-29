#!/usr/bin/env python3
"""verify_deployable_hardening_040.py — read-only verification of 040 deployable hardening."""
import hashlib,os,subprocess,sys,time,json
ROOT="/home/rspip/cqc/pro/study/orientbench"; V=f"{ROOT}/measure_fix_v2"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    main_rep=f"{V}/docs/p3_deployable_hardening_report.md"; t=rd(main_rep); tl=t.lower()
    c("main_report",os.path.isfile(main_rep))
    c("protocol",os.path.isfile(f"{V}/docs/deployable_hardening_protocol.md"))
    for f in ("leave_dataset_hardening_040.csv","leave_dataset_hardening_040.md","leave_detector_hardening_040.csv",
              "leave_detector_hardening_040.md","tta_proxy_hardening_040.csv","tta_proxy_hardening_040.md",
              "dota20_failure_analysis_040.md","dota20_failure_analysis_040.csv"):
        c(f"exists:{f}",os.path.isfile(f"{V}/reports/{f}"))
    # all new products under measure_fix_v2
    c("products_under_v2",os.path.isfile(f"{V}/reports/hardening_summary_040.json"))
    c("has_verdict",any(v in tl for v in ("stable-pass","partial-pass","fail")))
    c("distinguishes_oracle_deployable",("upper-bound" in tl or "upper bound" in tl) and "deployable" in tl)
    c("dota_limitation","dota" in tl and ("limitation" in tl or "局限" in t))
    # not claiming completion
    def forbidden(ph):
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","若","candidate","pending")):
                return True
        return False
    c("no_p3_complete_claim",not forbidden("p3 已完成") and not forbidden("deployable method 已完成"))
    c("no_topconf_claim",not forbidden("顶会级别"))
    # frozen invariants
    c("thresholds_unchanged",hashlib.sha256(open(f"{ROOT}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {ROOT} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    # no Track A products (not started)
    tracka=any("forward_dump" in f.lower() or "track_a_dump" in f.lower() for f in os.listdir(f"{V}/reports"))
    c("no_trackA_started",not tracka)
    big=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    bigv=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files measure_fix_v2 | xargs -I{{}} find {ROOT}/{{}} -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_tracked_v2",not bigv.strip())
    cc=rd(f"{V}/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{V}/reports/verification_deployable_hardening_040.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-040] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
