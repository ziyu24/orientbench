# r040 Server Execution Report

```yaml
schema_version: 2
dispatch_id: orientbench-b-r040-panorama-inference-20260815
plan_id: b-r040-panorama-inference-20260815
dispatch_commit_sha: ede2eb34c0e95efa55a98e6eb1cf151829317899
worker_id: server-primary
execution_status: incomplete
completion_mode: resource_budget_early_stop
scientific_outcome: NOT_ADJUDICATED
started_at: 2026-08-15T20:44:40-07:00
stopped_at: 2026-08-17T00:51:52-07:00
elapsed_wall_hours: 28.12
wall_time_cap_hours: 24
stop_condition: wall_time_cap_exhausted
```

## Completed assets

- Tier 1: HRSC2016 val, 7 valid units, all identity/hflip/vflip dumps complete.
  `normalized/matched_rows_hrsc.parquet` contains 3,190 matched TP rows across
  those units; independent validation passed and three mutations were rejected.
- Tier 1 ICDAR-MLT 2019: 2 valid units skipped because the configured
  `icdar_mlt_2019` data root is absent. No data were downloaded or substituted.
- Tier 2: identity dumps completed for PSC RetinaNet, RetinaNet, ARS-DETR,
  FAA Oriented R-CNN, and Strip R-CNN. They use the read-only DOTA-v1.0 val
  overlay only. Their measured AP values are not aligned with the readme
  baselines and are retained as `AP_MISALIGNED`, not formal comparable assets.

## Per-unit deviations / failures

| Unit | State | Detail |
|---|---|---|
| PSC RetinaNet | AP_MISALIGNED | mAP 0.2566 vs readme 0.5562 |
| RetinaNet | AP_MISALIGNED | mAP 0.2504; historical sliced config vs current official-val layout |
| ARS-DETR | AP_MISALIGNED | mAP 0.0474 |
| FAA Oriented R-CNN | AP_MISALIGNED | mAP 0.3542 |
| Strip R-CNN | AP_MISALIGNED | mAP 0.1749 |
| FCOS pseudo | unit failure | config uses undefined `__file__` during config evaluation |
| H2RBox v2 | unit failure | forward reached completion but evaluator/dump stage failed |
| RTMDet-M | unit failure | overlay/config combination parsed an empty dataset |

## Provenance and validation

- Baseline source: `/home/rspip/cqc/pro/study/pth_data/readme.md`, SHA-256
  `eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c`.
- HRSC provenance: `outputs/persistent_artifacts/orientbench_panorama_r040_20260815/normalized/provenance_hrsc.csv`.
- HRSC validation: `outputs/persistent_artifacts/orientbench_panorama_r040_20260815/normalized/validation.json` (`pass=true`).
- Mutations: `outputs/persistent_artifacts/orientbench_panorama_r040_20260815/normalized/mutation_results.json` (theta, duplicate-key/cluster, and provenance-field mutations rejected).
- Forbidden endpoint access: none. DOTA-v2.0, SODA-A official test, all official test labels, training, downloads, and pth_data writes were not used.

## Resource accounting and closure

The plan permits at most 2 GPUs, 60 GPU-hours, 224 CPU-core-hours, and 86,400
seconds wall time. The wall cap elapsed before Tier 2 completion; no additional
inference, Tier 3/4 work, audit bundle, or scientific conclusion is authorized
under this frozen dispatch. The absence of the full audit bundle is an explicit
consequence of the resource-boundary early stop, not a completed deliverable.

To continue, B must issue a new activated dispatch with a new resource budget,
write roots, and an explicit decision on whether current official-val layout
AP-misaligned DOTA units should receive further tri-view work.
