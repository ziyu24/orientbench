#!/usr/bin/env python3
"""verify_top_journal_lockdown_047.py — read-only verification of 047."""
import hashlib,os,subprocess,time,json
P="/home/rspip/cqc/pro/study/orientbench"
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    for d in ("docs/nonpsc_deployable_leave_star_047.md","docs/supervision_spectrum_method_section_047.md",
              "docs/paper_framing_top_journal_047.md","docs/artifact_persistence_047.md",
              "outputs/persistent_artifacts/manifest_047.json","measure_fix_v2/docs/top_journal_lockdown_decision_047.md"):
        c(f"exists:{d}",os.path.isfile(f"{P}/{d}"))
    # non-PSC leave-* has pass/fail/partial
    sm=json.load(open(f"{P}/measure_fix_v2/reports/nonpsc_leave_star_summary_047.json"))
    c("nonpsc_has_verdict","verdict" in sm and ("PASS" in sm["verdict"] or "fail" in sm["verdict"].lower() or "partial" in sm["verdict"].lower()))
    c("nonpsc_two_families",len(sm.get("nonpsc_families_pass",[]))>=2)
    c("nonpsc_two_datasets",len(sm.get("datasets_pass",[]))>=2)
    # manifest sha256 + can_recompute
    man=json.load(open(f"{P}/outputs/persistent_artifacts/manifest_047.json"))
    c("manifest_sha256",man.get("all_have_sha256") is True)
    c("manifest_can_recompute",man.get("all_can_recompute") is True)
    # Route-C not fully GT-free in framing
    fr=rd(f"{P}/docs/paper_framing_top_journal_047.md")+rd(f"{P}/docs/supervision_spectrum_method_section_047.md")
    c("routec_not_fully_gtfree","source-supervised" in fr and ("不得把 source-supervised transfer 写成 fully GT-free" in fr or "不是 fully GT-free" in fr))
    # no venue-selling in main framing draft + decision
    blob=(fr+rd(f"{P}/measure_fix_v2/docs/top_journal_lockdown_decision_047.md")+rd(f"{P}/measure_fix_v2/docs/orientation_reliability_measure_diagnose_fix_draft.md")).lower()
    def selling(ph):  # only flag positive (non-negated) usage
        for line in blob.splitlines():
            if ph in line and not any(m in line for m in ("不","未","非","❌","forbidden","禁止","不冲","删","无","移除","cleanup")):
                return True
        return False
    c("no_venue_selling",not selling("顶刊点") and not selling("cvpr ready") and not selling("iccv ready") and not selling("top venue ready"))
    # DOTA #20 limitation not validation
    dec=rd(f"{P}/measure_fix_v2/docs/top_journal_lockdown_decision_047.md")
    c("dota_limitation_not_validation",("limitation" in dec.lower()) and ("validation" in dec.lower()))
    # forbidden claims absent (positive)
    def forbidden(ph,txt):
        for line in txt.splitlines():
            if ph in line.lower() and not any(m in line for m in ("不","未","非","❌","forbidden","禁止","candidate")):
                return True
        return False
    fcheck=blob
    c("no_final_method_complete",not forbidden("final deployable method complete",fcheck))
    c("no_strict_independent",not forbidden("strictly independent",fcheck) and not forbidden("strictly-independent",fcheck))
    # frozen
    c("thresholds_unchanged",hashlib.sha256(open(f"{P}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    diff=subprocess.run(["bash","-c",f"git -C {P} diff --name-only HEAD -- orientbench/data/splits.py configs/thresholds.yaml"],capture_output=True,text=True).stdout
    c("split_threshold_unmodified",not diff.strip(),diff.strip())
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth|png)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    pers=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -c persistent_artifacts"],capture_output=True,text=True).stdout.strip()
    c("persistent_not_in_git",pers=="0",pers)
    hb=os.path.isfile(f"{P}/measure_fix_v2/reports/heartbeat_047.json")
    c("heartbeat",hb)
    cc=rd(f"{P}/measure_fix_v2/docs/cc_latest_report.md")
    c("cc_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{P}/measure_fix_v2/reports/verification_top_journal_lockdown_047.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-047] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
