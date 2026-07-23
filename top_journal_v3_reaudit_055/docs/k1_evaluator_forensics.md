# K1 评测器法证（evaluator forensics）

> 目的：解释表 1（P1 扰动，S1a 评测器）与表 7（角度头矩阵，DOTAMetric）之间的 AP 口径矛盾，
> 判断当前 evaluator 是否高出官方/第三方 10+ AP 点且无法解释。**结论：evaluator 代码本身与
> DOTAMetric 口径一致；表 1 的绝对 AP 锚点因使用了一个部分/未持久化的 GT 而被抬高约 16 点，
> 必须在 full-val 上用对齐后的 evaluator 重算。** 数据：`reports/k1_metric_protocol_alignment.csv`、
> `reports/k1_evaluator_diff_per_class.csv`、`reports/k1_summary.json`。

## 1. 矛盾点
- 表 1「DIOR#22（相位编码）」报告 **AP@0.5 = 0.6964**（来源：S1a 全评测器）。
- 表 7「PSC / DIOR-R」新训权重 **AP50 = 0.531**（DOTAMetric，训练验证日志）。
- 二者为同一检测器/同一 train/val 协议（表 7 config 即由表 1 那条冻结 baseline 复制而来），
  却相差约 16 点。

## 2. 关键事实：冻结 baseline 权重自报 DOTAMetric AP50 = 0.537
- 表 1「DIOR#22」背后的冻结 baseline 检查点文件名即 `best_mAP_5368_epoch_12.pth`；其训练日志末行：
  `dota/mAP: 0.5368  dota/AP50: 0.5370`（DIOR trainval→test，DOTAMetric）。
- 即该权重在**标准 DOTAMetric full-val** 上就是 **0.537**，与新训权重 0.531 一致；表 1 的 0.6964
  既不等于该权重的官方 AP，也不等于新训权重的 AP。

## 3. 受控对照：同一预测 + 同一 full GT，三个 evaluator 一致
在 PSC/DIOR-R/seed0（DOTAMetric=0.531）上，对 **同一批预测与同一份 full-val GT** 同时运行
S1a evaluator 与本项目 VOC-AP（后者此前已验证 == DOTAMetric，差 5e-4）：

| evaluator | full-val AP50 | full-val AP75 |
|---|---|---|
| S1a（项目全评测器） | **0.5297** | 0.3313 |
| 本项目 VOC-AP | **0.5311** | 0.3472 |
| DOTAMetric（参考） | **0.5310** | — |

**三者 AP50 相差 ≤ 0.0014**；逐类 AP50 差绝对值最大仅 0.053（多数 <0.04，源于 VOC all-points 与
11-point 插值差异），宏平均后互相抵消（`k1_evaluator_diff_per_class.csv`）。→ **S1a 评测器代码正确，
与 DOTAMetric 口径一致，不存在 16 点的评测器级 inflation。**

## 4. 根因：表 1 用了部分/未持久化的 GT
- 表 1「DIOR#22」的 GT 路径为 `/dev/shm/.../DIOR-R_fullval_gt.jsonl`，**该文件已不存在**（/dev/shm
  临时区、未持久化）。
- 其记录的 `n_gt = 35436`，而 **DIOR test full-val GT 实测 = 124445**（本次全量推理确认）。即表 1 的
  AP 是对一份**约 28% 的非标准 GT** 计算的，与 full-val DOTAMetric 口径不一致。
- 结论：0.6964 是**部分-GT 口径**的产物，而非 evaluator bug；该 GT 已无法复现，故 0.6964 也无法精确
  复算。

## 5. 协议对齐核对（S1a vs DOTAMetric vs 本项目 AP）
| 项 | 值 |
|---|---|
| dataset split | DIOR-R trainval→test（一致） |
| class list / 数量 | 20 类（一致） |
| class averaging | macro 逐类平均（一致） |
| IoU | 旋转多边形 IoU（一致，非 AABB） |
| angle convention | le90 canonical 长边（一致） |
| AP 插值 | S1a=VOC all-points；本项目/DOTAMetric=VOC 11-point（差异 <0.002 mAP） |
| score threshold | 0.05（一致） |
| **GT 口径** | **表 1=partial(35436, 已丢失)；本次=full-val(124445)** ← **唯一实质差异** |

## 6. K1 判定
- **评测器代码：PASS。** S1a ≡ DOTAMetric ≡ 本项目 VOC-AP（full-val AP50 0.5297/0.5310/0.5311）。
  16 点差异**已定位、可解释**，非“无法解释的 AP”，故**不触发 K1 硬 FAIL（不需停止全部投稿准备）**。
- **表 1 绝对 AP 锚点：FAIL-as-published。** 其数值来自一份部分/未持久化的 GT（35436≠124445），
  被抬高约 16 点，**不得继续作为主表锚点**。
- **必须动作（K1 任务 5）**：表 1（P1 扰动实验）的**全部 6 个单元** AP 必须在 **full-val + 对齐后的
  evaluator** 上重算并持久化 GT。已完成 DIOR#22 的重算示范：**0.6964 → 0.530（full-val）**。其余 5 个
  单元（ORCNN/RTMDet/FAIR1M/SODA）需各自 full-val 重算（下一步）。
- **扰动 ΔAP 不受影响**：ΔAP@0.5=0 是同一 evaluator 内的不变量，重算 GT 后仍应成立；受影响的只是
  绝对锚点数值。

## 7. 后续（K1 之后才可继续）
1. 用对齐 evaluator 在 full-val 重算表 1 全部 6 单元，持久化 GT + sha256，替换 0.69/0.79/0.89 等锚点。
2. 表 1/表 7 统一到同一 full-val DOTAMetric 口径后，P1 §4 方可解冻。
3. 治理补丁：禁止任何主表数值依赖 /dev/shm 未持久化 GT（已在此次法证中暴露）。
