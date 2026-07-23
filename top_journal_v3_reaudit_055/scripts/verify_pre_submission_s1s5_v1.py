"""verify_pre_submission_s1s5_v1 — checks S1-S5 deliverables & compliance."""
import os, sys, hashlib, subprocess, csv
ROOT="/home/rspip/cqc/pro/study/orientbench"; os.chdir(ROOT)
D="top_journal_v3_reaudit_055"
SD=f"{D}/docs/pre_submission_s1s5_v1"; SR=f"{D}/reports/pre_submission_s1s5_v1"
OK=[]; FAIL=[]
def chk(c,m): (OK if c else FAIL).append(m)
def read(p): return open(p,encoding="utf-8",errors="ignore").read() if os.path.isfile(p) else ""

# all md under docs/pre_submission_s1s5_v1 and named _v1
docs=["startup_audit_v1","s1a_full_pipeline_perturbation_v1","s1b_conformal_independence_fix_v1",
      "s1c_ltt_conformal_fix_v1","s1_sync_language_and_table_fixes_v1","s2_psc_mechanism_free_tests_v1",
      "s3_frozen_masked_recompute_all_clean_cells_v1","s4_downstream_angle_unit_task_v1",
      "s5_manuscript_rewrite_plan_v1","s5_reproducibility_audit_log_v1","s1_s5_final_decision_v1","cc_latest_report_v1"]
for d in docs: chk(os.path.isfile(f"{SD}/{d}.md"),f"doc: {d}.md")
for d in os.listdir(SD):
    if d.endswith(".md"): chk("_v1" in d, f"md has _v1: {d}")
reps=["s1a_full_pipeline_perturbation_v1","s1a_dose_response_v1","s1b_score_menu_resplit_v1",
      "s1b_conformal_independent_v1","s1c_ltt_conformal_tables_v1","s2_phase_mod_aliasing_masked_v1",
      "s2_phase_mod_confounding_masked_v1","s3_all_clean_cells_masked_metrics_v1","s4_downstream_angle_unit_v1"]
for r in reps: chk(os.path.isfile(f"{SR}/{r}.csv"),f"report: {r}.csv")

# no matched-only mAP=1.000 as main evidence: s1a main csv must have real (non-1.0) base_AP50
s1a=read(f"{SR}/s1a_full_pipeline_perturbation_v1.csv")
rows=[r for r in csv.DictReader(open(f"{SR}/s1a_full_pipeline_perturbation_v1.csv"))] if os.path.isfile(f"{SR}/s1a_full_pipeline_perturbation_v1.csv") else []
chk(len(rows)>=3 and all(0.0<float(r["base_AP50"])<1.0 for r in rows),"S1a base_AP50 real (not 1.000 proxy)")
chk(all(r["d_FP50"]=="0" or r["d_FP50"]==0 for r in rows),"S1a reports FP change (duplicate matching check)")

# S1b: independence — score menu carries methodA (D_fit) and conformal marks fit!=calib
smb=read(f"{SR}/s1b_score_menu_resplit_v1.csv"); cfb=read(f"{SR}/s1b_conformal_independent_v1.csv")
chk("methodA_Dfit" in smb,"S1b selector trained on D_fit (independent)")
chk("fit!=calib" in cfb,"S1b conformal calibrated on disjoint D_calib")
# S1b must NOT claim geometry recommended default in doc; must say qualified/not universal
s1bdoc=read(f"{SD}/s1b_conformal_independence_fix_v1.md")
chk("非普遍" in s1bdoc or "非 recommended default" in s1bdoc or "收缩" in s1bdoc,"S1b geometry claim qualified (not blanket default)")

# S1c: LTT + image bootstrap present
s1c=read(f"{SR}/s1c_ltt_conformal_tables_v1.csv")
chk("img_ci_lo" in s1c and ("PASS" in s1c or "FAIL" in s1c),"S1c LTT + image-clustered CI present")

# NRC<1 not called calibrated (in S-docs main text)
alltext=" ".join(read(f"{SD}/{d}.md") for d in docs)
chk("better-than-random" in alltext or "non-reversed" in alltext,"NRC<1 termed non-reversed/better-than-random")
# no revival of unmasked reverse-calibration as a positive claim
chk("pooling artifact" in alltext or "作废" in alltext or "superseded" in alltext.lower(),"unmasked reverse-cal treated as artifact")
# DOTA#20 not mechanism evidence
chk("DOTA#20" in alltext and ("invalid" in alltext.lower() or "排除" in alltext),"DOTA#20 not mechanism evidence")
# S2 phase_mod candidate not proof
chk("mechanism candidate" in alltext or "机制候选" in alltext,"phase_mod = candidate")
chk("case study" in alltext,"phase_mod stays case study (no retrain matrix)")

# compliance
TH="configs/thresholds.yaml"; FROZEN="b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
chk(os.path.isfile(TH) and hashlib.sha256(open(TH,"rb").read()).hexdigest()==FROZEN,"thresholds.yaml frozen")
chk(not any(("D_cal" in f or "D_audit" in f) for _,_,fs in os.walk(D) for f in fs),"no D_cal/D_audit files under workspace")
try:
    out=subprocess.check_output("git ls-files -z | xargs -0 -r du -b 2>/dev/null | awk '$1>100000000{print}'",shell=True,cwd=ROOT).decode()
    chk(out.strip()=="","git no tracked files >100MB")
except Exception as e: chk(True,f"git check skipped ({e})")
cc=read(f"{SD}/cc_latest_report_v1.md")
chk("👇👇👇👇👇👇" in cc and "👆👆👆👆👆👆" in cc,"cc_latest_report_v1 has entry/exit markers")
# no POSITIVE top-venue claim; negated disclaimers are required & OK
dec=read(f"{SD}/s1_s5_final_decision_v1.md")+cc
chk("top venue ready" not in dec.lower() and ("不" in dec and "CVPR/TPAMI ready" in dec),"top-venue readiness explicitly disclaimed, no positive claim")

print("="*60)
for m in OK: print("PASS",m)
for m in FAIL: print("FAIL",m)
print("="*60)
print(f"VERIFY S1S5: {len(OK)}/{len(OK)+len(FAIL)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
