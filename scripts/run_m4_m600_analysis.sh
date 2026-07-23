#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG="$ROOT/top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
for slot in A B; do
  path="$PKG/annotator_${slot}/outputs_m600_plus_recheck/annotations_${slot}_m600_plus_recheck.csv"
  [[ -s "$path" ]] || { echo "${slot} 新任务尚未导出：$path" >&2; exit 2; }
done
python "$ROOT/scripts/finalize_m4_m600_tranche.py"
python "$ROOT/scripts/merge_m4_human_annotations.py" \
  --task-a "$PKG/annotator_A/m600_target/task_manifest.csv" \
  --task-b "$PKG/annotator_B/m600_target/task_manifest.csv" \
  --raw-a "$PKG/internal/m600_A_combined.csv" \
  --raw-b "$PKG/internal/m600_B_combined.csv" \
  --mapping "$PKG/internal/instance_id_mapping.csv" \
  --manifest "$PKG/internal/m600_sampling_manifest.csv" \
  --output "$ROOT/reports/m4_m600_pairs.csv" \
  --audit "$ROOT/reports/m4_m600_merge_audit.json" \
  --min-per-dataset 200
python "$ROOT/scripts/analyze_m4_human_disagreement.py" \
  --pairs "$ROOT/reports/m4_m600_pairs.csv" \
  --merge-audit "$ROOT/reports/m4_m600_merge_audit.json" \
  --output "$ROOT/reports/m4_m600_disagreement.csv" \
  --analysis-audit "$ROOT/reports/m4_m600_analysis_audit.json" \
  --proxy-output "$ROOT/reports/m4_m600_proxy_reference.csv"
python "$ROOT/scripts/summarize_m4_pilot200.py" \
  --pairs "$ROOT/reports/m4_m600_pairs.csv" \
  --output "$ROOT/reports/m4_m600_key_metrics.csv" \
  --audit "$ROOT/reports/m4_m600_key_metrics_audit.json"
