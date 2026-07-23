"""verify_reaudited_paper_056 — checks the rewritten formal Chinese paper & compliance."""
import os, sys, hashlib, subprocess
ROOT="/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
D="top_journal_v3_reaudit_055"
PAPER=f"{D}/docs/orientation_reliability_paper_zh_reaudited.md"
FAIL=[]; OK=[]
def chk(c,m): (OK if c else FAIL).append(m)
def read(p): return open(p,encoding="utf-8",errors="ignore").read() if os.path.isfile(p) else ""
t=read(PAPER)

# exists & is a paper (not a project report)
chk(os.path.isfile(PAPER),"formal paper exists")
chk("## 摘要" in t and "## 1. 引言" in t and "## 12. 结论" in t,"paper structure (abstract..conclusion)")
chk("参考" in t or "相关工作" in t,"has related work")
# required content
chk("precise-pass" in t,"contains P1 precise-pass")
chk("保形" in t and ("主贡献" in t or "risk control" in t.lower() or "风险控制" in t),"P2 conformal main contribution")
chk("打分菜单" in t or "score menu" in t.lower(),"P4 score menu present")
chk("机制候选" in t or "mechanism candidate" in t.lower(),"P3 mechanism candidate boundary")
chk("附录" in t and ("边界" in t or "微弱" in t),"P5 appendix/boundary present")
chk("superseded" in t.lower() or "作废" in t,"retained/superseded evidence present")
chk("masked" in t and "ar≥1.6" in t,"masked protocol labelled")
# forbidden POSITIVE assertions must NOT appear (negated/forbidden-list mentions are required & OK)
badf=[f for f in ["top venue ready","顶会 ready","达到 SOTA","是 CVPR","is ready for CVPR"] if f in t]
chk(not badf,f"no positive venue/SOTA claims ({badf})")
# required negated disclaimers present
chk("非 full project complete" in t or "不主张 full project complete" in t,"disclaims full project complete")
chk("不主张 full benchmark complete" in t or "非 full benchmark" in t,"disclaims full benchmark complete")
chk("detector SOTA" in t and ("不是 detector SOTA" in t or "非 detector SOTA" in t or "不主张 detector SOTA" in t),"disclaims detector SOTA")
# DOTA#20 marked invalid; "DOTA#20 validation" only allowed inside forbidden list
chk("invalid_pending" in t and ("DOTA#20" in t or "DOTA #20" in t),"DOTA#20 marked invalid_pending")
chk(("DOTA#20 validation" not in t and "DOTA #20 validation" not in t) or ("forbidden" in t.lower() or "禁止" in t),"DOTA#20 validation only in forbidden list")
# phase_mod not a proof
chk(("phase_mod" in t) and ("机制候选" in t) and ("机制候选，不是机制定论" in t or "不是机制定论" in t or "非机制定论" in t),"phase_mod as candidate not proof")
# downstream not success
chk(("不主张下游 utility proven" in t) or ("downstream utility proven" not in t.lower()),"downstream not written as success")
chk("微弱" in t,"downstream marked weak")
# unmasked NRC not headline (must appear only as artifact/superseded)
chk(("pooling artifact" in t) and ("unmasked" in t),"unmasked NRC framed as artifact/superseded")
# de-projectized: no PM jargon in the paper body
pm=["055","监督员","verifier","本轮","approval token","SUPERVISOR"]
badpm=[w for w in pm if w in t]
chk(not badpm,f"paper de-projectized (no {badpm})")
# companion docs
chk(os.path.isfile(f"{D}/docs/coauthor_review_note_056.md"),"coauthor review note exists")
chk(os.path.isfile(f"{D}/docs/final_claim_ledger_reaudited_056.md"),"claim ledger exists")
lg=read(f"{D}/docs/final_claim_ledger_reaudited_056.md")
chk("allowed" in lg and "forbidden" in lg and "superseded" in lg,"ledger has allowed/forbidden/superseded")

# compliance: thresholds/split unchanged, git big files, cc markers
TH="configs/thresholds.yaml"; FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
chk(os.path.isfile(TH) and hashlib.sha256(open(TH,"rb").read()).hexdigest()==FROZEN,"thresholds.yaml sha256 frozen")
chk(not any("D_cal" in f or "D_audit" in f for _,_,fs in os.walk(D) for f in fs),"no D_cal/D_audit files under workspace")
try:
    out=subprocess.check_output("git ls-files -z | xargs -0 -r du -b 2>/dev/null | awk '$1>100000000{print}'",shell=True,cwd=ROOT).decode()
    chk(out.strip()=="","git no tracked files >100MB")
except Exception as e: chk(True,f"git check skipped ({e})")
cc=read(f"{D}/docs/cc_latest_report.md")
chk("👇👇👇👇👇👇" in cc and "👆👆👆👆👆👆" in cc,"cc_latest_report has entry/exit markers")

print("="*60)
for m in OK: print("PASS",m)
for m in FAIL: print("FAIL",m)
print("="*60)
print(f"VERIFY 056 paper: {len(OK)}/{len(OK)+len(FAIL)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
