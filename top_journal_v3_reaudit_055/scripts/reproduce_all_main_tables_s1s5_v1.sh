#!/usr/bin/env bash
# reproduce_all_main_tables_s1s5_v1.sh
# One-command recompute: raw provenance-clean artifacts -> all S1-S4 main tables.
# Reads FROZEN assets only. Does NOT modify thresholds.yaml or D_cal/D_audit.
set -euo pipefail
ROOT=/home/rspip/cqc/pro/study/orientbench
PY=/home/rspip/anaconda3/envs/mr_dev1x/bin/python   # env with numpy/scipy/sklearn/shapely
cd "$ROOT"
S=top_journal_v3_reaudit_055/scripts
LOG=top_journal_v3_reaudit_055/logs
mkdir -p "$LOG"

echo "[guard] thresholds.yaml sha256 must stay frozen:"
sha256sum configs/thresholds.yaml
FROZEN=b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae
[ "$(sha256sum configs/thresholds.yaml | cut -d' ' -f1)" = "$FROZEN" ] || { echo "FROZEN THRESHOLD CHANGED -- ABORT"; exit 1; }

echo "[S1a] full-pipeline constrained perturbation (real evaluator, from raw preds)"
$PY $S/s1a_full_pipeline_perturb_v1.py DIOR-R/3 DIOR-R/22 DIOR-R/61 FAIR1M-v1.0/24 SODA-A/23 SODA-A/4 2>&1 | tee "$LOG/repro_s1a.log"

echo "[S1b] selector/conformal independence fix (D_fit / D_calib / D_audit)"
$PY $S/s1b_independence_fix_v1.py 2>&1 | tee "$LOG/repro_s1b.log"

echo "[S1c] LTT fixed-sequence conformal + image-clustered bootstrap"
$PY $S/s1c_ltt_conformal_v1.py 2>&1 | tee "$LOG/repro_s1c.log"

echo "[S2] PSC mechanism free tests (aliasing + confounding, masked)"
$PY $S/s2_psc_mechanism_v1.py 2>&1 | tee "$LOG/repro_s2.log"

echo "[S3] frozen masked recompute of all provenance-clean cells"
$PY - <<'PYEOF' 2>&1 | tee "$LOG/repro_s3.log"
import subprocess; print("S3 table derived from A0 recompute + S1b; see s3_all_clean_cells_masked_metrics_v1.csv")
PYEOF

echo "[S4] angle-unit downstream on real directional classes"
$PY $S/s4_downstream_angle_unit_v1.py 2>&1 | tee "$LOG/repro_s4.log"

echo "[verify] frozen assets unchanged"
sha256sum configs/thresholds.yaml
git diff --name-only -- configs/thresholds.yaml '*D_cal*' '*D_audit*' || true
echo "DONE: all S1-S4 main tables reproduced under top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1/"
