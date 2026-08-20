执行完毕
`dis/server_reports/orientbench-b-r049-cora-obb-native-risk-stagea-20260819/SERVER_EXECUTION_REPORT.md`

## r049 server receipt

- 正常结束：是。终止门为 `G2_SEED0_TWO_DATASET_SURVIVAL`，结论 `REJECT_CORA_METHOD`。
- 已完成：G0 parity、G1 真实 CORA/smoke 修复、DIOR-R seed0 的 CONT/VM-NLL/CORA 四卡 FP32 三臂、每 epoch full-val、三份 raw export、matched rows、冻结 G2 adjudication 与独立结构验证。
- DIOR G2：CORA AP50/AP75=`0.491/0.248`；strongest control=`0.496/0.275`。AP50 与 AP75 保真失败；相对最佳 control 的 AUGRC/Risk@70 改善仅 `0.000404/0.000223`，低于 `0.01/0.02`。
- 未完成且禁止：SODA-A seed0、CORA_NO_CF、seed1/2、G3 bootstrap、G4 efficiency、Stage B 与所有 clean endpoint；这不是异常中止，而是计划要求的正常科学早停。
- 禁止端点：未触碰 DOTA-v2.0、SODA-A official test 或未登记 clean endpoint。
- 期刊等级：CORA 不具备 Stage-B 资格，不可宣称可部署方法或顶刊路线；仅保留既有 benchmark/diagnostic 资产。

关键路径：`docs/paper_jprs_r049/r049_dior_g2_decision.md`；`audit_bundles/r049/gate.json`；`outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2/metrics/gate_dior_seed0.json`。
