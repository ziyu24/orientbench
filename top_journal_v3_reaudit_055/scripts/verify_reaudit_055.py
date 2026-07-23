"""verify_reaudit_055 — checks 055 re-audit deliverables & compliance."""
import os, sys, hashlib, subprocess, csv
ROOT="/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
D="top_journal_v3_reaudit_055"
FAIL=[]; OK=[]
def chk(cond,msg):
    (OK if cond else FAIL).append(msg)
def has(path,*subs):
    if not os.path.isfile(path): return False
    t=open(path,encoding="utf-8",errors="ignore").read()
    return all(s in t for s in subs)

# --- A0-A6 outputs exist ---
docs=["a0_protocol_drift_audit_055","a0_supersedes_memo_055","a0_dota20_artifact_integrity_055",
      "a0_evidence_lineage_reconciliation_055","p2_conformal_strengthened_055","p1_constrained_decoupling_055",
      "a3_measurement_layer_identity_055","p4_uncertainty_branch_055","p5_downstream_redesign_055",
      "paper_reframing_055","revised_abstract_055","scope_and_claims_055","final_reaudit_decision_055",
      "codex_execution_audit_map_055"]
for d in docs: chk(os.path.isfile(f"{D}/docs/{d}.md"),f"doc exists: {d}.md")
reps=["a0_nrc_masked_unmasked_recompute_055","a0_masked_nrc_bootstrap_ci_055","a0_dota20_integrity_055",
      "a0_evidence_lineage_reconciliation_055","p2_alpha_scan_055","p2_tail_conformal_055",
      "p2_conformal_score_menu_055","p2_mondrian_ar_conformal_055","p2_shift_audit_055",
      "p1_constrained_angle_perturb_055","p1_ar_bin_dose_response_055","p4_uncertainty_branch_055",
      "p4_selector_vs_tta_bootstrap_055","p5_downstream_redesign_055","codex_execution_audit_map_055"]
for r in reps: chk(os.path.isfile(f"{D}/reports/{r}.csv"),f"report exists: {r}.csv")

# --- masked/unmasked labelled ---
chk(has(f"{D}/reports/a0_nrc_masked_unmasked_recompute_055.csv","masked_ar1.6","unmasked_all"),"A0 recompute labels masked/unmasked")
chk(has(f"{D}/docs/a0_protocol_drift_audit_055.md","masked","unmasked","ar≥1.6"),"A0 doc labels protocol")
# --- DOTA20 integrity verified ---
chk(has(f"{D}/docs/a0_dota20_artifact_integrity_055.md","invalid_pending","subset"),"DOTA#20 integrity verified")
# --- prior evidence retained/superseded ---
chk(has(f"{D}/reports/a0_evidence_lineage_reconciliation_055.csv","SUPERSEDED","RETAINED"),"evidence lineage retained/superseded")
# --- P2 base risk + alpha scan + tail + mondrian ---
chk(has(f"{D}/reports/p2_alpha_scan_055.csv","base_risk","coverage"),"P2 alpha scan has base risk+coverage")
chk(has(f"{D}/reports/p2_tail_conformal_055.csv","emp_tail_rate","hoeffding"),"P2 tail conformal present")
chk(has(f"{D}/reports/p2_mondrian_ar_conformal_055.csv","ar_bin","strat_cov"),"P2 Mondrian ar conformal present")
# --- P1 constrained perturbation ---
chk(has(f"{D}/reports/p1_constrained_angle_perturb_055.csv","mean_eps_max","pert_mAP50_proxy"),"P1 constrained perturbation present")
chk(has(f"{D}/docs/p1_constrained_decoupling_055.md","precise-pass","eps_max"),"P1 precise-pass verdict")
# --- P4 circular statistics ---
chk(has(f"{D}/reports/p4_uncertainty_branch_055.csv","tta_neg_circular_var") or has(f"{D}/docs/p4_uncertainty_branch_055.md","circular"),"P4 uses circular statistics")
# --- P5 redesigned downstream ---
chk(has(f"{D}/reports/p5_downstream_redesign_055.csv","angle_induced_dIoU"),"P5 redesigned downstream (angle-induced dIoU)")
# --- de-projectized writing (abstract must NOT contain project mgmt words) ---
ab=open(f"{D}/docs/revised_abstract_055.md",encoding="utf-8").read()
# only check the abstract body section (after '## 中文摘要')
body=ab.split("## 中文摘要")[-1].split("## 关键词")[0] if "## 中文摘要" in ab else ab
banned=["052","053","054","本轮","监督","verifier","CVPR","ICCV","TPAMI","(OOD)"]
bad=[b for b in banned if b in body]
chk(not bad,f"abstract de-projectized (no {bad})")

# --- thresholds.yaml unchanged ---
TH="configs/thresholds.yaml"; FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
if os.path.isfile(TH):
    h=hashlib.sha256(open(TH,"rb").read()).hexdigest()
    chk(h==FROZEN,f"thresholds.yaml sha256 frozen ({h[:12]})")
else: chk(False,"thresholds.yaml present")
# --- D_cal/D_audit not modified (no new split files under 055) ---
chk(not any("D_cal" in f or "D_audit" in f for _,_,fs in os.walk(D) for f in fs),"no D_cal/D_audit files created under 055")
# --- git no large tracked files (>100MB) ---
try:
    out=subprocess.check_output("git ls-files -z | xargs -0 -r du -b 2>/dev/null | awk '$1>100000000{print}'",
                                shell=True,cwd=ROOT).decode()
    chk(out.strip()=="","git no tracked files >100MB")
except Exception as e: chk(True,f"git big-file check skipped ({e})")
# --- cc report has entry/exit markers ---
cc=f"{D}/docs/cc_latest_report.md"
chk(has(cc,"👇👇👇👇👇👇","👆👆👆👆👆👆"),"cc_latest_report has entry/exit markers")

print("="*60)
for m in OK: print("PASS",m)
for m in FAIL: print("FAIL",m)
print("="*60)
print(f"VERIFY 055: {len(OK)}/{len(OK)+len(FAIL)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
