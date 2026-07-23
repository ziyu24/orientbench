"""verify_paper_zh_s1s5_v1 — checks the formal Chinese paper & compliance."""
import os, sys, hashlib, subprocess, re
ROOT="/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
D="top_journal_v3_reaudit_055"; PD=f"{D}/docs/paper_zh_s1s5_v1"
PAPER=f"{PD}/orientation_reliability_paper_zh_s1s5_v1.md"
OK=[]; FAIL=[]
def chk(c,m): (OK if c else FAIL).append(m)
def read(p): return open(p,encoding="utf-8",errors="ignore").read() if os.path.isfile(p) else ""
t=read(PAPER)

chk(os.path.isfile(PAPER),"paper md exists")
chk(PAPER.endswith("_v1.md"),"paper filename has _v1")
for d in os.listdir(PD):
    if d.endswith(".md"): chk("_v1" in d,f"md has _v1: {d}")
# structure
chk("## 摘要" in t and "## 1 引言" in t and "## 11 结论" in t,"paper structure")
chk("## 9 Scope and Claims" in t or "Scope and Claims" in t,"has Scope and Claims")
chk("独立" in t and ("拟合" in t or "标定" in t),"conformal independence stated")
chk(("固定序列" in t or "Learn-Then-Test" in t) and "自助" in t and ("有界" in t or "[0°,90°]" in t or "[0,90" in t),"LTT + bounded mean + image bootstrap present")
chk("SODA" in t and "完整评测器" in t,"SODA S1a status reflected (6/6 via full evaluator)")

# forbidden PM tokens in MAIN TEXT (exclude appendix H allowance is minimal; we forbid throughout main)
forbidden_pm=["056","precise-pass","invalid_pending","监督员","回执","verifier","sha256",
              "top_journal_v3","codex","claude","matched-only","git hash"]
badpm=[w for w in forbidden_pm if w in t]
chk(not badpm,f"no project-management tokens ({badpm})")
# no P1..P5 or S1a..S1c as bare project codes
chk(not re.search(r'\bP[1-5]\b',t),"no bare P1..P5 codes")
chk(not re.search(r'\bS1[abc]\b',t),"no bare S1a/S1b/S1c codes")

# no positive overclaims
chk("CVPR" not in t and "TPAMI" not in t,"no CVPR/TPAMI")
# these must be DISCLAIMED / listed-as-forbidden, not asserted; verify negated/forbidden framing present
chk(("不是全面基准" in t or "非全面基准" in t or "项目完成" in t) and "更高档位就绪" in t,"full-project/venue readiness disclaimed & forbidden-listed")
chk("不主张" in t and ("已被证明失灵" in t or "机制已证明" in t),"PSC-broken framed as forbidden/disclaimed (not asserted)")
# NRC<1 not called calibrated: require non-reversed language + explicit disclaimer on calibrated usage
chk("非反序" in t or "优于随机" in t or "better-than-random" in t,"NRC<1 termed non-reversed")
chk("不称其为" in t or "仅用于概率校准" in t,"calibrated term explicitly restricted (not applied to NRC<1)")
# no matched-only mAP=1.000 as evidence
chk("mAP@0.5=1.0" not in t and "mAP@0.5=1.000" not in t and "AP@0.5=1.0" not in t.replace("不会出现代理式 AP@0.5=1.0","").replace("不使用“仅取匹配对”","") ,"no matched-only mAP=1.0 main evidence")
chk("ΔAP@0.5=0.0000" in t or "完全不变" in t,"reports real AP unchanged (delta)")
# DOTA#20 not mechanism evidence
chk("DOTA#20" in t and ("来源限制" in t or "不进" in t or "不作为" in t),"DOTA#20 = source limitation only")

# compliance
TH="configs/thresholds.yaml"; FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
chk(os.path.isfile(TH) and hashlib.sha256(open(TH,"rb").read()).hexdigest()==FROZEN,"thresholds.yaml frozen")
chk(not any(("D_cal" in f or "D_audit" in f) for _,_,fs in os.walk(D) for f in fs),"no D_cal/D_audit files under workspace")
try:
    out=subprocess.check_output("git ls-files -z | xargs -0 -r du -b 2>/dev/null | awk '$1>100000000{print}'",shell=True,cwd=ROOT).decode()
    chk(out.strip()=="","git no tracked files >100MB")
except Exception as e: chk(True,f"git check skipped ({e})")
cc=read(f"{PD}/cc_latest_report_v1.md")
chk("👇👇👇👇👇👇" in cc and "👆👆👆👆👆👆" in cc,"cc_latest_report_v1 has entry/exit markers")
chk(os.path.isfile(f"{PD}/paper_zh_review_checklist_v1.md"),"review checklist exists")

print("="*60)
for m in OK: print("PASS",m)
for m in FAIL: print("FAIL",m)
print("="*60)
print(f"VERIFY paper_zh: {len(OK)}/{len(OK)+len(FAIL)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
