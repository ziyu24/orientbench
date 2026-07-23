#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG="$ROOT/top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
B_RESULT="$PKG/annotator_B/outputs_pilot_176_remaining/annotations_B_pilot176_remaining.csv"
B_COMBINED="$PKG/internal/pilot_200_B_combined.csv"

if [[ ! -s "$B_RESULT" ]]; then
  echo "B 的 200 条真人标注尚未导出：$B_RESULT" >&2
  exit 2
fi

python "$ROOT/scripts/snapshot_m4_a_pilot200.py"

python "$ROOT/scripts/assemble_m4_b_pilot200_result.py" \
  --tasks "$PKG/annotator_B/pilot_200/task_manifest.csv" \
  --initial "$PKG/internal/pilot_200_B_initial24_snapshot.csv" \
  --remaining "$B_RESULT" \
  --output "$B_COMBINED"

python "$ROOT/scripts/merge_m4_human_annotations.py" \
  --task-a "$PKG/annotator_A/pilot_200/task_manifest.csv" \
  --task-b "$PKG/annotator_B/pilot_200/task_manifest.csv" \
  --raw-a "$PKG/internal/pilot_200_A_snapshot.csv" \
  --raw-b "$B_COMBINED" \
  --mapping "$PKG/internal/instance_id_mapping.csv" \
  --manifest "$PKG/internal/pilot_200_sampling_manifest.csv" \
  --output "$ROOT/reports/m4_pilot200_pairs.csv" \
  --audit "$ROOT/reports/m4_pilot200_merge_audit.json" \
  --min-per-dataset 1

python "$ROOT/scripts/analyze_m4_human_disagreement.py" \
  --pairs "$ROOT/reports/m4_pilot200_pairs.csv" \
  --merge-audit "$ROOT/reports/m4_pilot200_merge_audit.json" \
  --output "$ROOT/reports/m4_pilot200_disagreement.csv" \
  --analysis-audit "$ROOT/reports/m4_pilot200_analysis_audit.json" \
  --proxy-output "$ROOT/reports/m4_pilot200_proxy_reference.csv"

python "$ROOT/scripts/summarize_m4_pilot200.py" \
  --pairs "$ROOT/reports/m4_pilot200_pairs.csv" \
  --output "$ROOT/reports/m4_pilot200_key_metrics.csv" \
  --audit "$ROOT/reports/m4_pilot200_key_metrics_audit.json"

echo "分析完成：$ROOT/reports/m4_pilot200_key_metrics.csv"
