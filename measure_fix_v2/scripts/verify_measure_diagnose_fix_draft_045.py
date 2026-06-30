#!/usr/bin/env python3
"""verify_measure_diagnose_fix_draft_045.py — read-only verification of 045 paper draft."""
import hashlib,os,subprocess,time,json
ROOT="/home/rspip/cqc/pro/study/orientbench"; V=f"{ROOT}/measure_fix_v2"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
DRAFT=f"{V}/docs/orientation_reliability_measure_diagnose_fix_draft.md"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]; t=rd(DRAFT); tl=t.lower()
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("draft_exists",os.path.isfile(DRAFT))
    c("no_venue",not any(v in tl for v in ("tgrs","isprs","jprs","cvpr","iccv","tpami","neurips","eccv","aaai")))
    c("explains_no_training",("为什么" in t and "重训" in t) and ("混淆变量" in t or "后处理" in t))
    c("has_measure_diagnose_fix",("measure" in tl and "diagnose" in tl and "fix" in tl))
    c("has_g2double",("g2_double_prime" in tl))
    c("has_deployable_routec",("deployable" in tl and "route-c" in tl))
    c("has_trackA_candidate",("track a" in tl and "candidate" in tl))
    c("has_dota20_limitation",("dota #20" in tl) and ("limitation" in tl or "negative control" in tl or "不调参" in t))
    c("has_real_tta_limitation",("real tta coverage limited" in tl) or ("coverage limited" in tl) or ("非全覆盖" in t))
    # forbidden claims (must be negated)
    def forbidden(ph):
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","candidate","limited","forbidden","pending")):
                return True
        return False
    c("no_full_project_complete",not forbidden("full project complete"))
    c("no_p3_final_complete",not forbidden("p3 final complete") and not forbidden("p3 final method 完成"))
    c("no_top_venue",not forbidden("top venue ready") and not forbidden("顶会 ready"))
    c("no_psc_finally_broken",not forbidden("finally proven broken") and not forbidden("最终证明反校准"))
    # frozen
    c("thresholds_unchanged",hashlib.sha256(open(f"{ROOT}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {ROOT} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    big=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    cc=rd(f"{V}/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{V}/reports/verification_measure_diagnose_fix_draft_045.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-045] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
