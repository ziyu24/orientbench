#!/usr/bin/env python3
"""verify_real_tta_deployability_042.py — read-only verification of 042 real-TTA proof."""
import hashlib,os,subprocess,sys,time,json
ROOT="/home/rspip/cqc/pro/study/orientbench"; V=f"{ROOT}/measure_fix_v2"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FARMSCRIPT=f"{V}/scripts/build_dior_farm_042.py"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    rep=f"{V}/docs/real_tta_deployability_report.md"; t=rd(rep); tl=t.lower()
    c("main_report",os.path.isfile(rep))
    for f in ("real_tta_inference_manifest_042.json","real_tta_feature_table_042.csv","real_tta_selector_results_042.csv",
              "real_tta_selector_results_042.md","tta_transform_sanity_042.md","tta_transform_sanity_042.csv","dior_farm_manifest_042.json"):
        c(f"exists:{f}",os.path.isfile(f"{V}/reports/{f}"))
    c("has_verdict",any(v in tl for v in ("stable-pass","partial-pass","fail")))
    c("distinguishes_offline_vs_real",("offline proxy" in tl or "offline" in tl) and "real tta" in tl)
    c("has_shadow_farm","shadow farm" in tl and os.path.isfile(f"{V}/reports/dior_farm_manifest_042.json"))
    c("has_transform_sanity","sanity" in tl and os.path.isfile(f"{V}/reports/tta_transform_sanity_042.csv"))
    # original dataset NOT modified
    fm=json.load(open(f"{V}/reports/dior_farm_manifest_042.json"))
    c("dataset_not_modified",fm.get("original_dataset_modified") is False)
    dnew=subprocess.run(["bash","-c",f"find /home/rspip/cqc/data/dataset/DIOR -newer {FARMSCRIPT} -type f 2>/dev/null | head -1"],capture_output=True,text=True).stdout
    c("dataset_dir_untouched",not dnew.strip(),dnew.strip()[:60])
    # not claiming P3 final
    def forbidden(ph):
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("❌","不","未","非","若","candidate","next-step","limited")):
                return True
        return False
    c("no_p3_final",not forbidden("p3 最终完成"))
    c("no_topconf",not forbidden("顶会 ready") and not forbidden("顶会级别"))
    # frozen invariants
    c("thresholds_unchanged",hashlib.sha256(open(f"{ROOT}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {ROOT} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    tracka=any("forward_dump" in f.lower() for f in os.listdir(f"{V}/reports"))
    c("no_trackA",not tracka)
    big=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    bigv=subprocess.run(["bash","-c",f"git -C {ROOT} ls-files measure_fix_v2 | xargs -I{{}} find {ROOT}/{{}} -size +1M 2>/dev/null"],capture_output=True,text=True).stdout
    c("no_large_tracked_v2",not bigv.strip())
    cc=rd(f"{V}/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{V}/reports/verification_real_tta_deployability_042.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-042] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
