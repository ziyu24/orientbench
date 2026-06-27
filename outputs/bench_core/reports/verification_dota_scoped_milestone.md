# DOTA-Scoped Milestone Verification (read-only)

> 2026-06-27 22:37:42 CST
> verdict: **VERIFIED** (21/21 checks)
> scoped_formal_gate_allowed=true_for_frozen_dota_c1_a4_scope_only; overall_project_complete=False; training_needed_now=False

| check | ok | detail |
|---|---|---|
| exists:configs/thresholds.yaml | ✓ |  |
| exists:outputs/training/rhino/best_dota_mAP_epoch_35.pth | ✓ |  |
| exists:outputs/training/a4_host/best_dota_mAP_epoch_70.pth | ✓ |  |
| exists:outputs/bench_core/reports/c1_formal_audit.csv | ✓ |  |
| exists:outputs/bench_core/reports/a4_formal_audit.csv | ✓ |  |
| exists:outputs/bench_core/reports/c1_a4_threshold_freeze_record.md | ✓ |  |
| exists:outputs/bench_core/reports/project_status_matrix.md | ✓ |  |
| exists:outputs/bench_core/reports/claim_ledger.md | ✓ |  |
| exists:outputs/bench_core/reports/reproducibility_manifest.json | ✓ |  |
| freeze_status_correct | ✓ | partial_frozen_dota_d2+host_orientation_gates+c1_a4_formal_thresholds |
| freeze_not_overclaimed | ✓ | partial_frozen_dota_d2+host_orientation_gates+c1_a4_formal_thresholds |
| rhino_sha256 | ✓ | 55a90abbace42927 |
| a4_sha256 | ✓ | 3e32fa11114ced82 |
| B_C1_host_match | ✓ |  |
| A_A4_host_match | ✓ |  |
| dcal_daudit_disjoint | ✓ | |cal|=529 |aud|=471 |
| calibration_split_dcal | ✓ |  |
| c1_formal_pass | ✓ |  |
| a4_formal_pass | ✓ |  |
| no_forbidden_assertions | ✓ | [] |
| status_codes_valid | ✓ |  |
