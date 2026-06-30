#!/usr/bin/env python3
"""verify_paper_zh_full_048.py — read-only verification of 048 full Chinese paper."""
import hashlib,os,subprocess,time,json
P="/home/rspip/cqc/pro/study/orientbench"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
PAPER=f"{P}/measure_fix_v2/docs/orientation_reliability_paper_zh_full.md"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]; t=rd(PAPER); tl=t.lower()
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    c("paper_exists",os.path.isfile(PAPER))
    for sec in ("摘要","关键词","引言","相关工作","问题定义","实验结果","讨论","局限","结论","附录"):
        c(f"section:{sec}",sec in t)
    c("measure_diagnose_fix",("measure" in tl and "diagnose" in tl and "fix" in tl))
    c("supervision_spectrum","supervision spectrum" in tl or "监督光谱" in t)
    c("g2_double_prime","g2_double_prime" in tl)
    c("route_c","route-c" in tl)
    c("nonpsc_leave_star",("non-psc leave-" in tl) or ("non-psc leave-\\*" in tl) or ("leave-detector" in tl and "leave-dataset" in tl))
    c("track_a_candidate",("track a" in tl or "phase_mod" in tl) and "candidate" in tl)
    c("dota20_limitation",("dota #20" in tl) and ("limitation" in tl))
    c("why_no_gpu",("为何不大规模 gpu" in tl) or ("为何不大规模 GPU".lower() in tl) or ("混淆变量" in t))
    c("why_no_dota_map",("不追 dota public mAP".lower() in tl) or ("不追公开 mAP".lower() in tl) or ("不追 DOTA public".lower() in tl) or ("不追公开 map" in tl))
    # negatives
    def has_pos(ph):  # positive (non-negated) occurrence
        for line in t.splitlines():
            if ph in line.lower() and not any(m in line for m in ("不","未","非","❌","forbidden","禁止","limitation","candidate","不是")):
                return True
        return False
    c("no_venue_names",not any(v in tl for v in ("tgrs","isprs","jprs","cvpr","iccv","tpami","neurips","eccv","aaai")))
    c("no_venue_ready",not has_pos("top venue ready") and not has_pos("cvpr ready") and not has_pos("iccv ready") and not has_pos("顶刊点"))
    c("no_full_project_complete",not has_pos("full project complete"))
    c("no_p3_final_complete",not has_pos("p3 final method complete") and not has_pos("final deployable method complete"))
    c("no_strict_independent",not has_pos("strictly independent") and "strictly independent" not in tl.split("forbidden")[-1] if "forbidden" in tl else not has_pos("strictly independent"))
    c("no_angle_head_proven",not has_pos("finally proven broken") and not has_pos("最终证明反校准"))
    c("source_sup_not_fully_gtfree",("source-supervised" in tl) and ("不是 fully gt-free" in tl or "非 fully gt-free" in tl or "source-supervised = fully gt-free" in tl))
    # frozen
    c("thresholds_unchanged",hashlib.sha256(open(f"{P}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {P} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    cc=rd(f"{P}/measure_fix_v2/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{P}/measure_fix_v2/reports/verification_paper_zh_full_048.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-048] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
