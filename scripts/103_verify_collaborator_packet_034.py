#!/usr/bin/env python3
"""103_verify_collaborator_packet_034.py — read-only verification of 034 collaborator packet."""
import hashlib,os,subprocess,sys,time,json
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
def rd(p): return open(p).read() if os.path.isfile(p) else ""
def main():
    ch=[]
    def c(n,ok,d=""): ch.append({"check":n,"ok":bool(ok),"detail":str(d)})
    docs=[f"{P}/docs/collaborator_p1_scientific_validity_packet.md",
          f"{P}/docs/collaborator_p1_decision_form.md",
          f"{P}/docs/collaborator_p1_one_page_summary.md"]
    for d in docs: c(f"exists:{os.path.basename(d)}",os.path.isfile(d))
    form=rd(f"{P}/docs/collaborator_p1_decision_form.md")
    c("decision_form_D1_D7",all(f"**{x}**" in form or f"| {x} " in form or f"{x} " in form for x in ("D1","D2","D3","D4","D5","D6","D7")))
    cc=rd(f"{P}/docs/cc_latest_report.md")
    c("cc_has_wrappers",cc.count("👇")>=1 and cc.count("👆")>=1)
    # no overclaim across the 3 docs + cc
    blob=(rd(docs[0])+rd(docs[1])+rd(docs[2])+cc).lower()
    bad=[]
    for ph in ("full_project_complete=true","full project complete","genuine physical multi-view solved","cross-host causal proved","cross-host a4 causal proved"):
        # allow if prefixed by ❌/不/non within 6 chars
        i=blob.find(ph)
        if i>=0 and "❌" not in blob[max(0,i-6):i] and "不" not in blob[max(0,i-6):i] and "non-" not in blob[max(0,i-6):i] and "未" not in blob[max(0,i-6):i]:
            bad.append(ph)
    c("no_overclaim",not bad,bad)
    c("thresholds_unchanged",hashlib.sha256(open(f"{P}/configs/thresholds.yaml","rb").read()).hexdigest()==FROZEN)
    big=subprocess.run(["bash","-c",f"git -C {P} ls-files | grep -E '\\.(pkl|pth)$'"],capture_output=True,text=True).stdout
    c("git_no_large",not big.strip())
    ok=all(x["ok"] for x in ch)
    out={"time":time.strftime("%Y-%m-%d %H:%M:%S %Z"),"verdict":"VERIFIED" if ok else "FAILED","n_pass":sum(x["ok"] for x in ch),"n_checks":len(ch),"checks":ch}
    json.dump(out,open(f"{P}/outputs/bench_core/reports/verification_collaborator_packet_034.json","w"),indent=2,ensure_ascii=False)
    print(f"[verify-034] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    for x in ch:
        if not x["ok"]: print("  FAIL",x["check"],x["detail"])
    return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
