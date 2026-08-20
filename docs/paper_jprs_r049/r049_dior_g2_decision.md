# r049 DIOR-R G2 决策报告

## 决策

`REJECT_CORA_METHOD`，正常科学早停。DIOR-R seed0 已足以否决 r049：计划明确规定任一数据集 G2 失败即停止，不补 seed、不启动 SODA-A，也不通过调阈值、融合 detection score 或改风险定义续命。

## 冻结证据（AR >= 2.1 matched TP）

| arm | AP50 | AP75 | AUGRC | Risk@70 | mean angle error (deg) |
| --- | ---: | ---: | ---: | ---: | ---: |
| CONT | 0.496 | 0.275 | 0.009783 | 0.020114 | 2.1050 |
| VM-NLL | 0.485 | 0.265 | 0.008165 | 0.015910 | 2.0260 |
| CORA | 0.491 | 0.248 | 0.007761 | 0.015687 | 1.9475 |

CORA 相对 strongest control 的 AP50 差为 `-0.005`（浮点精确值略低于门槛），AP75 差为 `-0.027`；两个均未通过。尽管角误差均值没有增加，CORA 相对最佳 control（VM-NLL）的 AUGRC 改善仅 `0.000404`（要求 `>=0.01`），Risk@70 改善仅 `0.000223`（要求 `>=0.02`）。因此可靠性门与 accuracy preservation 门均失败。

## 范围与禁止后续

- 正常结束：三臂训练、full-val、raw export、matched rows 和 frozen adjudication 均完成；早期 AMP `NaN` 已作为数值工程问题通过统一 FP32 修复，不计入科学失败。
- 未触碰 DOTA-v2.0、SODA-A official test 或任何 clean endpoint。
- SODA-A、CORA_NO_CF、seed1/2、G3 bootstrap、G4 efficiency 和 Stage B 均禁止启动。
- 期刊层级：CORA 不达合法 Stage-B 条件；该方法线停止，项目仍仅可保留此前 benchmark/diagnostic 资产，不能以 CORA 主张升级。

原始 receipt：`outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g2/metrics/gate_dior_seed0.json`。
