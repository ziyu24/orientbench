#!/usr/bin/env python3
"""verify_route_c_tta_proxy_041.py — read-only verification of 041 Route-C deployable check."""
import hashlib,os,subprocess,sys,time,json
ROOT="/home/rspip/cqc/pro/study/orientbench"; V=f"{ROOT}/measure_fix_v2"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    rep=f"{V}/docs/route_c_tta_proxy_report.md"; t=rd(rep); tl=t.lower()
    c("main_report",os.path.isfile(rep))
    c("protocol",os.path.isfile(f"{V}/docs/route_c_tta_proxy_protocol.md"))
    for f in ("route_c_tta_proxy_results_041.csv","route_c_tta_proxy_results_041.md","tta_proxy_features_041.csv",
              "tta_proxy_manifest_041.json","dota20_negative_control_041.md","route_c_summary_041.json"):
        c(f"exists:{f}",os.path.isfile(f"{V}/reports/{f}"))
    c("products_under_v2",os.path.isfile(f"{V}/reports/route_c_summary_041.json"))
    c("has_verdict",any(v in tl for v in ("stable-pass","partial-pass","fail")))
    c("distinguishes_upperbound_deployable",("upper-bound" in tl or "upper bound" in tl) and "deployable" in tl)
    c("has_dota_negctrl","negative control" in tl or "negative-control" in tl or "negative control" in rd(f"{V}/reports/dota20_negative_control_041.md").lower())
    # not claiming P3 finished
    def forbidden(ph):
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","若","candidate","pending","next-step","next step")):
                return True
        return False
    c("no_p3_final_complete",not forbidden("p3 最终方法完成") and not forbidden("p3 已完成"))
    c("no_topconf",not forbidden("顶会级别"))
    # not claiming upper-bound is deployable wrongly (must contain the distinction)
    c("upperbound_vs_deployable_distinct","calibration" in tl and "无目标 gt" in tl)
    # frozen invariants
    c("thresholds_unchanged",hashlib.sha256(open(f"{ROOT}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {ROOT} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    # no Track A products started
    tracka=any("forward_dump" in f.lower() for f in os.listdir(f"{V}/reports"))
    c("no_trackA_started",not tracka)
    # no detector training (no .pth in v2)
    pth=subprocess.run(["bash","-c",f"find {V} -name '*.pth' 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_detector_training_artifacts",not pth.strip())
    big=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    bigv=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files measure_fix_v2 | xargs -I{{}} find {ROOT}/{{}} -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_tracked_v2",not bigv.strip())
    cc=rd(f"{V}/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{V}/reports/verification_route_c_tta_proxy_041.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-041] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
