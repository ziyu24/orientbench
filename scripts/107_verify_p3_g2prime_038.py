#!/usr/bin/env python3
"""107_verify_p3_g2prime_038.py — read-only verification of 038 P3 G2' feasibility."""
import hashlib,os,subprocess,sys,time,json
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
MAIN=f"{P}/docs/p3_g2prime_feasibility_report.md"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]; t=rd(MAIN); tl=t.lower()
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("report_exists",os.path.isfile(MAIN))
    c("has_three_selectors",("score-only" in tl or "score_only" in tl) and ("score+ar" in tl or "score_ar" in tl or "score+aspect" in tl) and ("p3 selector" in tl or "p3_nonlinear" in tl or "非线性" in t))
    c("has_ar_primary_and_sens",("1.6" in t) and ("1.3" in t))
    c("has_dcal_daudit","d_cal" in tl and "d_audit" in tl and ("互斥" in t or "mutual" in tl))
    c("has_metrics",all(k in t.upper() for k in ("NRC","AURC")) and ("risk@70" in tl) and "bootstrap" in tl)
    c("has_verdict",any(v in t.upper() for v in ("G2′ PASS","G2' PASS","G2′ FAIL","G2' FAIL","INCONCLUSIVE")) or ("pass" in tl or "fail" in tl or "inconclusive" in tl))
    def forbidden(ph):
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","若","如果","pending")):
                return True
        return False
    c("no_p3_established",not forbidden("p3 已成立"))
    c("no_trackc_deployable",not forbidden("deployable method") or "upper-bound" in tl or "upper bound" in tl)
    c("no_near_square_main_gain","near-square" in tl and ("trivial" in tl or "排除" in t or "well-defined" in tl))
    c("no_venue",not any(v in tl for v in ("tgrs","cvpr","iccv","tpami","neurips","eccv")))
    c("thresholds_unchanged",hashlib.sha256(open(f"{P}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {P} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("p1_split_threshold_unmodified",not diff.strip(),diff.strip())
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    cc=rd(f"{P}/docs/cc_latest_report.md")
    c("cc_has_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{P}/outputs/bench_core/reports/verification_p3_g2prime_038.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-038] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
