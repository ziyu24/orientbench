#!/usr/bin/env python3
"""verify_track_a_psc_mechanism_043.py — read-only verification of 043 Track A."""
import hashlib,os,subprocess,sys,time,json
ROOT="/home/rspip/cqc/pro/study/orientbench"; V=f"{ROOT}/measure_fix_v2"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    rep=f"{V}/docs/track_a_psc_mechanism_report.md"; t=rd(rep); tl=t.lower()
    c("main_report",os.path.isfile(rep))
    c("protocol",os.path.isfile(f"{V}/docs/track_a_psc_mechanism_protocol.md"))
    c("dump_manifest",os.path.isfile(f"{V}/reports/track_a_dump_manifest_043.json"))
    c("route_status",os.path.isfile(f"{V}/docs/measure_fix_route_status.md"))
    for f in ("track_abc_results_043.csv","track_abc_results_043.md","track_a_schema_sample_043.json"):
        c(f"exists:{f}",os.path.isfile(f"{V}/reports/{f}"))
    # large dump not in git
    big=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    bigv=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files measure_fix_v2 | xargs -I{{}} find {ROOT}/{{}} -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_tracked_v2",not bigv.strip())
    # frozen
    c("thresholds_unchanged",hashlib.sha256(open(f"{ROOT}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {ROOT} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    # Track A NOT written as main gate
    c("track_a_not_main_gate",("不门控 p3" in tl or "不再门控" in tl or "仅机制解释" in tl or "不门控" in tl))
    # PSC angle head reverse-cal claim only as candidate WITH track A evidence
    mani=json.load(open(f"{V}/reports/track_a_dump_manifest_043.json"))
    has_evidence=len(mani.get("dumps",[]))>=1
    c("anglehead_claim_has_evidence",("mechanism candidate" in tl) and has_evidence)
    c("not_overclaim_proven",("未声称" in t) or ("candidate" in tl and "非最终定论" in t))
    cc=rd(f"{V}/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{V}/reports/verification_track_a_psc_mechanism_043.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-043] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
