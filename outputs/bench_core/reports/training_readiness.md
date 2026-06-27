# Training Readiness Check

> 生成时间: 2026-06-26 09:11:25 CST
> CHECK ONLY — 不启动训练; 明确何时才能训练。

- **training_allowed: False** / can_train_now: False (expected: False)
- reasons: ['thresholds not frozen', 'RHINO missing', 'A4 host pending', 'real predictions not yet formal', 'human approval required']
- blockers: ['training_allowed_default', 'R8_thresholds_frozen', 'host_baseline_selected', 'checkpoint_log_path_policy', 'lr_batch_schedule_alignment_plan', 'gpu_plan', 'real_predictions_formal', 'angle_version_verified', 'human_approval']

## Remaining before training
- R8 thresholds frozen (configs/thresholds.yaml freeze_time + freeze_status=frozen)
- D_cal/D_audit split policy ratified
- RHINO (C1/B) host ruling + A4 frozen host provided
- real predictions converted + angle_version verified (esp. HRSC)
- config/log/schedule/lr/batch alignment plan authored
- GPU plan (4xA30 default) confirmed

## Human decisions required
- approve threshold draft values
- rule on RHINO host (download/train/supply/approve-substitute)
- supply A4 hybrid-encoder frozen snapshot
- explicit approval to start training

## Files needed
- frozen thresholds.yaml (freeze_time set)
- RHINO checkpoint+config (or approved substitute)
- A4 hybrid-host frozen snapshot+config
- real detector prediction files in prediction schema

## Commands allowed AFTER approval
- (after approval only) training command aligned to official/valid baseline; 4xA30; per-epoch eval; save best-mAP+latest; logs to outputs/logs with full path

## First-epoch stop conditions
- first-epoch mAP clearly below baseline expectation -> STOP and report
- NaN/inf loss -> STOP and report
- OOM not resolved by documented fallback -> STOP and report

## Checklist items
| item | status | detail |
|---|---|---|
| training_allowed_default | **blocked** | training_allowed defaults to FALSE (监督 006) |
| R8_thresholds_frozen | **pending** | thresholds.yaml must complete R8 freeze before training |
| host_baseline_selected | **blocked** | RHINO (C1/B) missing; A4 host pending — host/baseline ruling required |
| config_path_exists | **ready** | baseline config paths exist (inventory config_exists all True) — alignment plan still required |
| checkpoint_log_path_policy | **pending** | policy: save only best-mAP + latest; logs full path — to be enacted at training time |
| dataset_path_exists | **ready** | 5 present datasets verified (DOTA10/15/DIOR/HRSC/FAIR1M) |
| split_policy_valid | **ready** | D_cal/D_audit mutually exclusive; train/val(test) per dataset policy |
| lr_batch_schedule_alignment_plan | **pending** | must align epoch/batch/lr/SyncBN/schedule to official/valid baseline (not yet authored) |
| gpu_plan | **pending** | 4xA30 default; fall back on OOM and log — plan to be confirmed |
| first_epoch_stop_rule | **ready** | first-epoch-low stop rule recorded: if first-epoch mAP clearly low -> stop & report |
| output_directory_policy | **ready** | self-built baselines -> orientbench/pth_data with baseline_ prefix; no root clutter |
| no_pollution_rule | **ready** | no writes outside study root; pth_data read-only |
| real_predictions_formal | **pending** | formal real detector predictions required before training is meaningful |
| angle_version_verified | **pending** | angle_version le90 sign consistency (esp. HRSC) must be verified |
| human_approval | **blocked** | explicit human/supervisor approval required to start training |
