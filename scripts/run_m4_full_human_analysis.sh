#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG="$ROOT/top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
A_NEW="$PKG/annotator_A/outputs_full_remaining/annotations_A_full_remaining.csv"
B_NEW="$PKG/annotator_B/outputs_full_remaining/annotations_B_full_remaining.csv"

for path in "$A_NEW" "$B_NEW"; do
  if [[ ! -s "$path" ]]; then
    echo "真人标注尚未全部导出：$path" >&2
    exit 2
  fi
done

python "$ROOT/scripts/assemble_m4_full_annotation_result.py" \
  --slot A \
  --tasks "$PKG/annotator_A/task_manifest.csv" \
  --completed "$PKG/internal/full_A_completed_snapshot.csv" \
  --remaining "$A_NEW" \
  --output "$PKG/internal/full_A_combined.csv"

python "$ROOT/scripts/assemble_m4_full_annotation_result.py" \
  --slot B \
  --tasks "$PKG/annotator_B/task_manifest.csv" \
  --completed "$PKG/internal/full_B_completed_snapshot.csv" \
  --remaining "$B_NEW" \
  --output "$PKG/internal/full_B_combined.csv"

python "$ROOT/scripts/merge_m4_human_annotations.py" \
  --task-a "$PKG/annotator_A/task_manifest.csv" \
  --task-b "$PKG/annotator_B/task_manifest.csv" \
  --raw-a "$PKG/internal/full_A_combined.csv" \
  --raw-b "$PKG/internal/full_B_combined.csv" \
  --mapping "$PKG/internal/instance_id_mapping.csv" \
  --manifest "$ROOT/reports/m4_human_annotation_sampling_manifest.csv" \
  --output "$ROOT/reports/m4_human_annotation_pairs.csv" \
  --audit "$ROOT/reports/m4_human_annotation_merge_audit.json" \
  --min-per-dataset 200

python "$ROOT/scripts/analyze_m4_human_disagreement.py" \
  --pairs "$ROOT/reports/m4_human_annotation_pairs.csv" \
  --merge-audit "$ROOT/reports/m4_human_annotation_merge_audit.json" \
  --output "$ROOT/reports/m4_human_annotation_disagreement.csv" \
  --analysis-audit "$ROOT/reports/m4_human_annotation_analysis_audit.json" \
  --proxy-output "$ROOT/reports/m4_gt_jitter_proxy_reference.csv"
