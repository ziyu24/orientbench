未执行完毕
`dis/server_reports/orientbench-b-r049-rev2-pef-multidata-multihost-20260819/SERVER_EXECUTION_REPORT.md`

## r049-rev2 server execution record

- 状态：`G1_GEOMETRY_REPAIR_PASS`；此前 G2 CONT 已判为无效，不进入任何科学结论。
- 已核验：`server-primary` 绑定、冻结 plan commit/blob/SHA、四张 A30 可用、唯一报告路径和写入范围；DOTA/PSC 主资产与历史 checkpoint 的四卡全验证回放通过。
- 信息墙：尚未访问 DOTA-v2.0、SODA-A official test 或旧 `T_audit` 语义字段。
- G0 结论：DOTA PSC replay mAP/AP50=`0.5562/0.5560`，与 archived mAP=`0.5562` 一致；DIOR 与 SODA 的已登记扩展资产可用，FAIR1M 的已登记 transformed split 缺失并冻结为可跳过扩展 cell。
- 下一步：从零开始 CONT、DIRECT_DIST、SCALAR_QUALITY、PEF 四臂 G2；只在四臂完整结束后进行冻结联合裁决。

## Historical G1 completion (superseded for G2 admission)

- PEF 的 four-GPU 500-iteration 全参数 smoke 正常结束；候选采样、q、refined angle、native risk 与梯度有限性测试通过。
- DIRECT_DIST 和 SCALAR_QUALITY 均完成 four-GPU integration smoke；方法与控制配置已冻结。
- 复核发现该历史实现未把 candidate box 宽高编码到 sampling grid，故不能作为 G2 admission 证据；完整记录和已中止 CONT 被保留。

## Geometry-repaired G1 admission

- 修复后 PEF 四卡 500-iteration full-parameter smoke 正常结束，final validation 与 checkpoint 正常完成；5/5 PEF field tests 通过。
- 修复实现以每 FPN level 的 fixed anchor candidate box 宽高决定 rotated sampling axes，候选角是唯一变化的几何量；未改变数据、控制、K、loss weight、阈值或禁止端点。
