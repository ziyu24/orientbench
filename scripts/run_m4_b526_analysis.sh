#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG="$ROOT/top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
A_NEW="$PKG/annotator_A/outputs_b526_remaining/annotations_A_b526_remaining.csv"
A_COMBINED="$PKG/internal/b526_A_combined.csv"

if [[ ! -s "$A_NEW" ]]; then
  echo "A 的 331 条真人标注尚未导出：$A_NEW" >&2
  exit 2
fi

python "$ROOT/scripts/assemble_m4_tranche_result.py" \
  --tasks "$PKG/annotator_A/b526_target/task_manifest.csv" \
  --initial "$PKG/internal/b526_A_initial195_snapshot.csv" \
  --remaining "$A_NEW" \
  --output "$A_COMBINED"

python "$ROOT/scripts/merge_m4_human_annotations.py" \
  --task-a "$PKG/annotator_A/b526_target/task_manifest.csv" \
  --task-b "$PKG/annotator_B/b526_target/task_manifest.csv" \
  --raw-a "$A_COMBINED" \
  --raw-b "$PKG/internal/b526_B_frozen_snapshot.csv" \
  --mapping "$PKG/internal/instance_id_mapping.csv" \
  --manifest "$PKG/internal/b526_sampling_manifest.csv" \
  --output "$ROOT/reports/m4_b526_pairs.csv" \
  --audit "$ROOT/reports/m4_b526_merge_audit.json" \
  --min-per-dataset 1

python "$ROOT/scripts/analyze_m4_human_disagreement.py" \
  --pairs "$ROOT/reports/m4_b526_pairs.csv" \
  --merge-audit "$ROOT/reports/m4_b526_merge_audit.json" \
  --output "$ROOT/reports/m4_b526_disagreement.csv" \
  --analysis-audit "$ROOT/reports/m4_b526_analysis_audit.json" \
  --proxy-output "$ROOT/reports/m4_b526_proxy_reference.csv"

python "$ROOT/scripts/summarize_m4_pilot200.py" \
  --pairs "$ROOT/reports/m4_b526_pairs.csv" \
  --output "$ROOT/reports/m4_b526_key_metrics.csv" \
  --audit "$ROOT/reports/m4_b526_key_metrics_audit.json"
