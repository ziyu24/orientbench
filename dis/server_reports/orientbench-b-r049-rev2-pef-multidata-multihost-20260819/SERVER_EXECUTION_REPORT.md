执行完毕
`dis/server_reports/orientbench-b-r049-rev2-pef-multidata-multihost-20260819/SERVER_EXECUTION_REPORT.md`

## r049-rev2 server execution record

- 执行状态：`complete`（G2 科学早停）。`server-primary`、精确 dispatch/plan、DOTA-v1.0 train→val 主资产和四卡训练均已核验；G1 修复后真实 PEF 的 500-iteration 全参数 smoke 正常结束，backbone、neck、bbox、angle head、sampler/scorer 梯度均非零且有限。
- G2：CONT、DIRECT_DIST、SCALAR_QUALITY、PEF 均从合法同初始化完成 12 epoch、每 epoch full-val，并以 epoch-12 checkpoint 重新导出原始预测、PEF `q`/native-risk、matched rows、manifest 与 bootstrap。
- 决策：`REJECT_PEF_METHOD`。相对 strongest control CONT，PEF mAP/AP50/AP75 分别为 `0.4137/0.5450/0.2820` 对 `0.4171/0.5450/0.2900`；AR>=2.1 angle MAE 为 `1.9419` 对 `1.8581`，native-risk AUGRC/Risk@70 为 `0.009659/0.019360` 对 `0.009795/0.019692`。严格合取中 mAP tolerance、AP75、angle-error、两项15% risk reduction 和两项 bootstrap CI 均未满足。
- 早停：按冻结 G2 规则，未启动 G3 多数据/多架构或 G4 多种子/零目标 GT 扩展；该负结果仅保留内部研发台账，不进入目标论文、补充、附录或消融。
- 禁止端点：未访问 DOTA-v2.0、SODA-A official test 或旧 `T_audit` 语义字段。

## Authoritative artifacts

- G1 gradients: `outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g1/dota_psc_pef_host_residual_smoke_500/full_model_gradient.json`
- Full training logs: `outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid/dota_psc_{cont,direct_dist_residual,scalar_quality,pef}/train.log`
- Final raw exports and metrics: `outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid/evaluation/` and `outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid/metrics/`
- Frozen decision: `audit_bundles/r049_rev2/G2_GATE_DECISION.json`; human table: `audit_bundles/r049_rev2/G2_GATE_REPORT.md`

## Integrity

- `manifest.json` sha256: `3f5ba00fef5b297abc4de05152fb4d755dba23932b31819a7524430d07ede678`
- `risk_metrics.csv` sha256: `9c36667e3d6fc13225bcf50f7024fc55355f50ec817e98080e80d6856a41a30b`
- `gate_dota_psc_repaired.json` sha256: `74725665000e82474c94a1c14861c3b746f804ee1c2e05c67f95a5440a32720d`
