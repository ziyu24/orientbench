#!/usr/bin/env python3
"""104_verify_p1_scientific_report_035.py — read-only verification of 035 single P1 report."""
import hashlib,os,subprocess,sys,time,json
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
MAIN=f"{P}/docs/orientbench_p1_scientific_report.md"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]; t=rd(MAIN); tl=t.lower()
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("main_report_exists",os.path.isfile(MAIN))
    # single human-read report: no scattered collaborator reports in docs/ root
    scattered=[f for f in os.listdir(f"{P}/docs") if f.startswith("collaborator_p1_") and f.endswith(".md")]
    c("single_report_no_scattered",not scattered,scattered)
    # contains required sections
    for kw in ("p99","cliff","construct","psc","aspect-ratio","reliability cliff"):
        c(f"contains:{kw}",kw in tl)
    # no overclaims (must be prefixed by ❌/不/未 if present)
    def forbidden(ph):
        # forbidden iff phrase appears on a line WITHOUT a negation marker
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","pending","PENDING")):
                return True
        return False
    c("no_full_project_complete",not forbidden("full project complete"))
    c("no_c1_multiview_solved",not forbidden("genuine physical multi-view solved") and not forbidden("c1 genuine multi-view"))
    c("no_a4_cross_host_proved",not forbidden("cross-host causal proved") and not forbidden("a4 cross-host causal"))
    c("no_psc_anglehead_proven",("不能说" in t) and ("psc angle head" in tl))
    c("no_complete_independence","完全独立" not in t or "不主张" in t)
    c("dota_train_val_noted","train 训练" in t and "val 验证" in t and "非 trainval" in t)
    c("catastrophic_corrected","纠正" in t and "near-square" in tl)
    # thresholds + split + git
    c("thresholds_unchanged",hashlib.sha256(open(f"{P}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    # D_cal/D_audit split code unchanged (splits.py present + freeze)
    c("split_module_present",os.path.isfile(f"{P}/orientbench/data/splits.py"))
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    cc=rd(f"{P}/docs/cc_latest_report.md")
    c("cc_has_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{P}/outputs/bench_core/reports/verification_p1_scientific_report_035.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-035] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
