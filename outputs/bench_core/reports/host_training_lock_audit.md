# Host Training Lock Audit (014 evidence)

> 2026-06-27 20:01:06 CST

- freeze_status: **partial_frozen_dota_d2+host_orientation_gates** (allowed=True; 不得扩写 complete_B_C1/complete_A_A4)
- issues: NONE

| host | route/block | sha256(16) | matches | superseded | mix_guard |
|---|---|---|---|---|---|
| RHINO | C1/B/B_C1 | 55a90abbace42927 | True | superseded_2gpu_run;superseded_invalid_eval_ckpt | RHINO->C1/B/B_C1 only |
| O2-RTDETR | A4/A_A4 | 3e32fa11114ced82 | True | superseded_2gpu_run | O2-RTDETR->A4/A_A4 only |

## 核验
- RHINO best=55a90abb… → C1/B(B_C1)；O2-RTDETR best=3e32fa11… → A4(A_A4)；不混用。
- 旧 2+2 / eval-ckpt 不合规训练在 superseded_* 目录，标 superseded_invalid，不作输入。
- D_audit 未用于调阈值（B_C1/A_A4 calibration_split=D_cal；gate 阈值 NRC<=1.0 为 pre-registered）。
- 证据路径: outputs/training/{rhino,a4_host}/{manifest.json,SNAPSHOT_LOCK.json}, host_formal_audit.{md,csv}。
