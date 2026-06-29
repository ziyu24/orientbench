#!/usr/bin/env python3
"""verify_measure_fix_v2_039.py — read-only verification of 039 v2 measure->fix round."""
import hashlib,os,subprocess,sys,time,json
ROOT="/home/rspip/cqc/pro/study/orientbench"; V=f"{ROOT}/measure_fix_v2"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for d in ("docs","reports","scripts","data","figures","artifacts","logs","docs/input"):
        c(f"folder:{d}",os.path.isdir(f"{V}/{d}"))
    c("input_claude8",os.path.isfile(f"{V}/docs/input/CLAUDE (8).md"))
    c("input_exec_v2",os.path.isfile(f"{V}/docs/input/项目执行文件_v2_measure_fix.md"))
    main_rep=f"{V}/docs/g2_double_prime_and_deployable_report.md"; t=rd(main_rep); tl=t.lower()
    c("main_report",os.path.isfile(main_rep))
    c("protocol_doc",os.path.isfile(f"{V}/docs/g2_double_prime_protocol.md"))
    c("results_csv",os.path.isfile(f"{V}/reports/g2_double_prime_results_039.csv"))
    c("report_has_g2dp","g2_double_prime" in tl)
    c("report_has_size_bins",("fixed-size bin" in tl or "fixed box-size" in tl or "size bin" in tl) and "small" in tl)
    c("report_has_three_selectors",("score-only" in tl) and ("score+ar+size" in tl or "score + ar + size" in tl or "size linear" in tl) and ("nonlinear" in tl))
    c("report_has_verdict","pass" in tl or "fail" in tl or "partial" in tl)
    # all new products under measure_fix_v2: check no new top-level files created outside (heuristic: reports exist under V)
    c("products_under_v2",os.path.isdir(f"{V}/reports") and os.path.isfile(f"{V}/reports/g2_double_prime_results_039.csv"))
    # frozen invariants
    c("thresholds_unchanged",hashlib.sha256(open(f"{ROOT}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {ROOT} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    # if G2DP fail -> no deployable products; here G2DP pass so deployable allowed
    g2_pass="g2_double_prime 裁决：**pass" in tl or "g2_double_prime：**pass" in tl or ("g2_double_prime" in tl and "pass（明确" in t.lower())
    dep_exists=os.path.isfile(f"{V}/reports/deployable_results_039.csv")
    c("deploy_only_if_g2pass",(g2_pass and dep_exists) or (not dep_exists),f"g2pass={g2_pass} dep={dep_exists}")
    # if Deployable fail -> no Track A products; we did not create Track A
    tracka=any("track_a" in f.lower() or "forward_dump" in f.lower() for f in os.listdir(f"{V}/reports")) if os.path.isdir(f"{V}/reports") else False
    c("no_trackA_products",not tracka)
    # no full matrix / no host retrain markers in v2 (heuristic: no .pth produced)
    big=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    bigv=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files measure_fix_v2 | xargs -I{{}} find {ROOT}/{{}} -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_tracked_in_v2",not bigv.strip(),bigv.strip()[:80])
    cc=rd(f"{V}/docs/cc_latest_report.md")
    c("cc_has_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{V}/reports/verification_measure_fix_v2_039.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-039] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
