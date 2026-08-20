未执行完毕
`dis/server_reports/orientbench-b-r049-rev2-pef-multidata-multihost-20260819/SERVER_EXECUTION_REPORT.md`

## r049-rev2 server execution record

- 状态：`G0_PASS`；当前进入 `G1_REAL_PEF_AND_FULL_DETECTOR_SMOKE`。
- 已核验：`server-primary` 绑定、冻结 plan commit/blob/SHA、四张 A30 可用、唯一报告路径和写入范围；DOTA/PSC 主资产与历史 checkpoint 的四卡全验证回放通过。
- 信息墙：尚未访问 DOTA-v2.0、SODA-A official test 或旧 `T_audit` 语义字段。
- G0 结论：DOTA PSC replay mAP/AP50=`0.5562/0.5560`，与 archived mAP=`0.5562` 一致；DIOR 与 SODA 的已登记扩展资产可用，FAIR1M 的已登记 transformed split 缺失并冻结为可跳过扩展 cell。
- 下一步：实现冻结的 candidate-conditioned PEF、DIRECT_DIST、SCALAR_QUALITY，并进行结构测试与四卡 500-iteration 全参数 smoke。
