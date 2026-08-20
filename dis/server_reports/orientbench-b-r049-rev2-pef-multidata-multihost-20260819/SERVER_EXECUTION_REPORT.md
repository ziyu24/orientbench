未执行完毕
`dis/server_reports/orientbench-b-r049-rev2-pef-multidata-multihost-20260819/SERVER_EXECUTION_REPORT.md`

## r049-rev2 server execution record

- 状态：`NOT_ADJUDICATED_IMPLEMENTATION`；最终 2×2 rotated-grid G1 已通过，但 G2 的 DIRECT_DIST 冻结对照在首轮异常低后暂停，尚不能做有效四臂裁决。
- 已核验：`server-primary` 绑定、冻结 plan commit/blob/SHA、四张 A30 可用、唯一报告路径和写入范围；DOTA/PSC 主资产与历史 checkpoint 的四卡全验证回放通过。
- 信息墙：尚未访问 DOTA-v2.0、SODA-A official test 或旧 `T_audit` 语义字段。
- G0 结论：DOTA PSC replay mAP/AP50=`0.5562/0.5560`，与 archived mAP=`0.5562` 一致；DIOR 与 SODA 的已登记扩展资产可用，FAIR1M 的已登记 transformed split 缺失并冻结为可跳过扩展 cell。
- 下一步：等待对 DIRECT_DIST operative inference 的冻结定义确认；确认前不启动 SCALAR_QUALITY/PEF，不运行 G3/G4。

## Final rotated-grid G1 and current G2 state

- 最终 PEF 实现以候选 `(w,h,theta,class)` 的局部矩形 2×2 rotated FPN grid 生成 candidate-conditioned field。四卡 500-iteration smoke 正常完成；独立全模型 probe 证明 backbone、neck、bbox、angle head、PEF sampler/scorer 五组均有非零有限梯度：`outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g1/dota_psc_pef_batched_rotated_grid_static_smoke_500/full_model_gradient.json`。
- 新 G2 使用隔离目录 `outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid/`。CONT 已正常完成 12 epoch，final full-val mAP/AP50=`0.5446/0.5450`。
- DIRECT_DIST 第 1 epoch full-val mAP/AP50=`0.0003/0.0000`，而同初始化 CONT 第 1 epoch 为 `0.0256/0.0260`。按项目首 epoch 显著偏低纪律已中断，保留 `dota_psc_direct_dist/train.log` 和 epoch-1 checkpoint；未继续盲跑。初步根因是初始近均匀 direct q 的 circular mean 在 inference 直接覆盖 host angle。把 direct q 改为 host-angle residual/mixed inference 会改变当前冻结对照语义，服务器未擅自改变。
- 信息墙未变：未触碰 DOTA-v2.0、SODA-A official test、旧 `T_audit`；未运行 G3/G4。该状态不是 `REJECT_PEF_METHOD`。

## Historical G1 completion (superseded for G2 admission)

- PEF 的 four-GPU 500-iteration 全参数 smoke 正常结束；候选采样、q、refined angle、native risk 与梯度有限性测试通过。
- DIRECT_DIST 和 SCALAR_QUALITY 均完成 four-GPU integration smoke；方法与控制配置已冻结。
- 复核发现该历史实现未把 candidate box 宽高编码到 sampling grid，故不能作为 G2 admission 证据；完整记录和已中止 CONT 被保留。

## Repaired per-candidate G1 admission (pre-G2)

- 修复后 PEF 四卡 500-iteration full-parameter smoke 正常结束，final validation 与 checkpoint 正常完成；7/7 PEF field tests 通过，并验证窄/宽 q 的 no-GT tail risk 单调性、轴向循环移位、候选宽高/类别变化及逐 anchor 非坍塌。
- 全模型反传 probe 正常结束：backbone、neck、bbox regression、PSC angle head、PEF sampler/scorer 均存在非零有限梯度，记录于 `outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g1/per_candidate_gradient_probe.log`。
- 修复实现以每个 FPN location 的每个 anchor template `(w,h,class)` 生成独立 evidence field，候选角是唯一变化的几何量；推理持久化 `pef_q`、`pef_native_risk`、原始及 refined angle。未改变数据、控制、K、loss weight、阈值或禁止端点。

## Superseded G2 engineering evidence

- CONT、DIRECT_DIST、SCALAR_QUALITY、PEF 均完成 DOTA-v1.0 train→val 12-epoch 四卡完整训练；final `epoch_12.pth` 的 frozen AP50/AP75 复评结果为 CONT=`0.561/0.299`、DIRECT_DIST=`0.508/0.265`、SCALAR_QUALITY=`0.559/0.294`、PEF=`0.500/0.258`。
- 原先相对 strongest CONT 的 PEF AP50/AP75 为 `-0.061/-0.041`，但 B 验收确认该 PEF 并非冻结的 per-candidate method、未导出 native risk/q，故这些数值仅保留为工程证据，不能构成 `REJECT_PEF_METHOD` 科学裁决。当前 dispatch 不关闭；未触碰禁止端点。
