# r003 B/C 科学裁决：轴向图像旋转可观测性

日期：2026-09-01
基线提交：`7f7f508a8a462a87c601ad2250a02fcf7c1bed47`

本文件记录本任务内 B 与 C 科学代理的证据化讨论摘要，不冒充由独立 C 工作树写入的正式 `coordination/dialogues` 事件。

## 结论

B/C 一致只准许 **AIRO（Axial Image Rotational Observability，轴向图像旋转可观测性）** 进入一次 CPU-only Stage-A 生死门。它当前只是可证伪的测量科学假设，不是已证方法、不是新 Fisher/CRLB 理论，也不改变项目仍为 JSTARS 对标的期刊判断。

最终复核状态：`C_FINAL_SIGNED`。该签字只确认假设身份、反例边界和 Stage-A 生死门已经闭合，不预先支持 AIRO，也不授权 Stage-B。

独立计划红队状态：`ASSET_FINAL_PASS`、`STATS_FINAL_PASS`。这里的 PASS 仅表示资产合同和统计裁决可执行、可复算，不是科学结果 PASS。

联合假设为：对遥感 OBB，预测中心和无方向尺度确定的圆形外观 crop 在 `RP1` 上具有两种可区分的可观测性。`M_15` 应在局部 `J_eff` 与经典基线之外预测盲人工方向歧义；在 detector 端，`J_eff` 和 `M_15` 必须各自在另一机制之外预测 raw axial angle error，并能跨数据集和 detector family 迁移。这样不会让“其中一个量完全无用”仍冒充双机制成立。

## 被排除的候选

1. **集合值方向预测 + conformal**：C 最初提出后自行追溯到 r035--r037 Q-SetOD。r037 已是 `G_SET=FAIL`、set witness `0/8`，禁止复活。
2. **场景内对象关系方向场**：仓库 r040/r041 已使用同图邻域方向一致性，核心信息源不是新路线；整幅场景共同旋转偏差又会使关系残差不变，无法识别 common-mode 错误。外部最近邻还包括 2025 年 Angle-Synchronized Graph、[OrientedFormer](https://arxiv.org/abs/2409.19648) 和 [Relational Matching](https://openaccess.thecvf.com/content/CVPR2024/papers/Wu_Relational_Matching_for_Weakly_Semi-Supervised_Oriented_Object_Detection_CVPR_2024_paper.pdf)。该方向不作为主线。

## B/C 的实质争论与收敛

- C 的第一反对是：AIRO 很可能只是预测 AR、边缘能量或经典 structure tensor 的换皮。因此强基线必须同时包含 score、predicted AR/area、class、`u_axis`、`missing_fraction`、`iou_loss`、mean gradient、boundary contrast 和结构张量 anisotropy；只与 detection score 比较无效。
- C 曾建议扫描固定中心/宽高的候选矩形边界能量。B 反对：r049rev2 PEF 已把“固定非角字段、扫描候选角、候选角改变视觉采样并形成周期能量场”作为核心，手工边界版本会被视为失败 PEF 的离线弱化。
- B 改为不扫描候选框的圆形 crop 自旋登记：crop 只由 predicted center 与方向无关半径 `R=max(48,0.90*max(pred_w,pred_h))` 决定，不读取 predicted theta；`J_eff` 把 rotation tangent 投影掉 translation、isotropic scale、gain 和 offset nuisance，`M_15` 测量至少相隔 15 度的全局轴向竞争 alias。
- C 接受该更正：它不输出 refined angle，不生成候选框能量，不调用 detector 再前向，因此与 PEF、CMR 和 OER 均有清楚边界；但必须通过 rotate--inverse、插值、边界和 intensity-affine fixtures。
- C 的第二轮反对是：原草案仍可能让 `M_15` 恒为零通过 fixtures，也没有唯一规定 `J_eff/E/M_15` 的单位、gain 域、秩亏投影和有效支持。B 因此固定 radian tangent、`rcond=1e-10` Moore--Penrose 投影、正 gain、同一 common-valid support 与绝对数值底 `tau=1e-4`，并要求非轴外对称图的 `M_15>=10*tau`。
- 统计红队指出 A/B/C 来自同一批 DIOR 图像，普通 leave-detector 会把同一像素同时放入 source fit 和 target test。最终方案改为固定 mother-image 五折 OOF；跨 unit 不能拼接分数重排，必须先算 unit delta、再等权聚合 dataset、最后等权聚合三数据集。
- 资产红队指出同名 M4 文件有 600 个正式目标与 1500 个 pending 候选两套，且 A--F 历史原图没有完整逐图 SHA。最终方案钉死 600-row manifest/label 的 bytes+SHA 和 r036 qset 515559-row universe；非 M4 重叠图只能标为本轮 SHA 已封存、历史像素身份未封存，故 Stage-A 仍是探索性证据。

## 外部先验边界

不能声称本项目发明了这些数学组件：

- 图像梯度结构张量与方向置信度已有 [Bigun et al., TPAMI 1991](https://ieeexplore.ieee.org/document/85668/)。
- 旋转/刚体配准 CRLB 已有 [Yetik and Nehorai, IEEE TSP 2006](https://doi.org/10.1109/TSP.2006.870552)。
- 低 SNR、多峰和全局误配已有 [Xu et al., IEEE TSP 2009](https://doi.org/10.1109/TSP.2008.2011822) 的 Ziv--Zakai bound。
- 连续变换 Lie derivative 与 aliasing 已由 [Gruver et al.](https://arxiv.org/abs/2210.02984) 讨论。
- [Structure Tensor Representation for Robust Oriented Object Detection](https://arxiv.org/abs/2411.10497) 已把 OBB 参数编码为 tensor；它不是由真实图像梯度构造，但标题和术语高度碰撞。
- [MessDet, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/papers/Wu_Measuring_the_Impact_of_Rotation_Equivariance_on_Aerial_Object_Detection_ICCV_2025_paper.pdf) 已量化 aerial detector 的 rotation-equivariance error。
- [AQE-Detector, Scientific Reports 2026](https://www.nature.com/articles/s41598-025-31034-w) 已由 detector RoI 特征学习周期角度方差并融入 NMS；因此“方向置信度”本身也不是新贡献。

因此唯一可守的新颖性是 **OBB 特有的人机共同实证命题**：经典局部/全局图像可辨识性量在盲多标注者、多个 detector family 和跨域条件下是否具有独立、可迁移的解释力。

## 联合硬裁决

- 先做合成真值、nuisance 与插值 fixtures。
- 人工门使用冻结的 M4 600 个双标目标；像素特征先封存，人工结局后挂接。
- detector 门只用 r036 qset A--F 的冻结 515559-row matched cohort，沿用六个 source/target 配置和 source-defined common support；G/H 只可描述，不进入门。A--F 不能再称完全 `provenance-clean`，未有历史像素 SHA 锚的行必须披露这一限制。
- 人工主端点固定为排除任一 `SKIP` 后的 576 行；至少一位 `AMBIGUOUS` 为阳性，冻结计数为 126 阳性、450 双 `LABELED` 阴性。600-row 正式 manifest/labels 与 1500-row pending 文件不得混用。
- 强基线不仅包含几何、score、全部可用 TTA、梯度、边界和结构张量，还包含无 nuisance 的旋转 tangent `J_raw` 与普通自旋 gap `M_raw`；只有对这些近邻的增量才算 AIRO 信号。
- 主风险固定为 `clip(le90_deg/90, 0, 1)`，禁止 `delta_0.75`、GT-AR normalized risk 或 r002 risk rows 替代独立重建。
- detector 见证至少 `4/6`，覆盖三个数据集和两个 detector family；`AUGRC(B1)-AUGRC(B2) >= max(0.005, 0.05*AUGRC(B1))`，cluster CI 下界大于零，Holm-6 `p<=0.05`，且 `Delta Spearman>=0.02`。AUGRC 固定为预测风险升序、whole-tie generalized risk-mass 的注册公式。
- `M_15` 相对“强基线 + J”以及 `J_eff` 相对“强基线 + M”都必须在至少两个数据集上有非微小增量、CI 下界大于零，并各自通过固定 Holm-3。只有一个机制有效，整条 AIRO 仍 KILL，不得改名续命。
- 机制方向同样是必要条件：人工三折中 `log M_15` 系数必须全为负；detector 的 J/M 增量模型强制相应 monotonic constraint 为 `-1`。反向关联即使改善 loss 也不能冒充 observability。J、M 各自的条件见证还必须分别覆盖至少两种 target detector family，并通过自己的 Holm-6 unit family。
- 10000 次 bootstrap 只对封存的 target predictions 做 mother-scene multiplicity 重权，不重拟合；所以 CI 必须明确称为 `conditional-on-frozen-source-fit`，不能冒充整个学习流程的不确定性。
- 即使全部通过，也只授予 `ADMIT_AIRO_CAUSAL_STAGE_B`：下一轮才允许受控模糊、降采样、噪声和小旋转再推理来检验因果顺序。当前不授权 GPU、训练、推理或论文改写。

裁决优先级也已固定：先判 M4 asset/实现/synthetic，再判人工门；只有人工 PASS 后，detector asset 缺失才可给 `INCONCLUSIVE_DETECTOR_ASSET`，不能用尚非必要的 detector 文件遮蔽已成立的人工 KILL。两套实现、seal、复算或 mutation 不一致只能 `INCONCLUSIVE_IMPLEMENTATION`；数学实现一致但注册的 synthetic、人工、detector、双机制或真实 specificity 门失败则必须进入相应 `KILL`。不得用 `INCONCLUSIVE` 给科学失败续命。

## 最强拒稿理由

最强审稿意见会是：“这是 1991 structure tensor、2006 registration CRLB、2009 global bound 与已有 OBB reliability 指标的遥感拼装；相关性来自 AR、像素尺寸、背景边缘或 detector score，没有盲人工证据、跨域不变性或受控成像干预。”r003 的每个门都针对这一拒稿理由；任何关键门失败即止损。
