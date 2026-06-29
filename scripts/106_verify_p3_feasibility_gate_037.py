#!/usr/bin/env python3
"""106_verify_p3_feasibility_gate_037.py — read-only verification of 037 P3 feasibility gate."""
import hashlib,os,subprocess,sys,time,json
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
MAIN=f"{P}/docs/p3_feasibility_gate_report.md"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]; t=rd(MAIN); tl=t.lower()
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("gate_report_exists",os.path.isfile(MAIN))
    for f in ("psc_track_a_signal_audit_037.md","psc_trackabc_control_037.md","psc_trackabc_control_037.csv","p3_reliability_cliff_feasibility_037.md"):
        c(f"exists:{f}",os.path.isfile(f"{P}/outputs/bench_core/reports/{f}"))
    def forbidden(ph):
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","pending","若","如果","exploratory")):
                return True
        return False
    c("no_p3_established",not forbidden("p3 已成立"))
    # Track A unavailable -> must NOT claim PSC angle head reverse-calibrated
    a_unavail="unavailable" in tl and "track a" in tl
    c("track_a_unavailable_noted",a_unavail)
    c("no_anglehead_proven",("不能声称" in t or "不能" in t) and "intrinsic" in tl)
    c("no_full_matrix",not forbidden("full matrix 扩展"))
    c("dota_train_val_or_frozen","frozen" in tl and ("d_cal" in tl or "d_audit" in tl))
    c("thresholds_unchanged",hashlib.sha256(open(f"{P}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    # splits.py unchanged (in git, no diff)
    diff=subprocess.run(["bash","-c",f"git -C {P} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_files_unmodified",not diff.strip(),diff.strip())
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    cc=rd(f"{P}/docs/cc_latest_report.md")
    c("cc_has_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{P}/outputs/bench_core/reports/verification_p3_feasibility_gate_037.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-037] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
