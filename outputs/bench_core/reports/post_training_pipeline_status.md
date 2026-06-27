# Post-Training Pipeline Status

> RHINO->C1/B, O2-RTDETR->A4（不混用）；R1/R3/R4/R6/R8 守卫；训练未完成则 pending_training。

- **RHINO (C1/B, B_C1)**: pending_training
- **O2-RTDETR (A4, A_A4)**: pending_training

checkpoint 完成后阶段：ckpt 完整性→D_cal inference→schema→angle contract→matching/orientation risk→阈值候选(仅 D_cal)→完整性检查→冻结 B_C1/A_A4→D_audit 正式 gate→报告。
