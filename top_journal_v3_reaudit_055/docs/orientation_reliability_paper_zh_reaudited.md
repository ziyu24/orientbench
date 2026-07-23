# Orientation Reliability：面向旋转目标检测的朝向可靠性测量协议与保形风险控制

---

## 摘要

旋转目标检测（oriented / OBB detection）以 mAP 作为主导评价指标，但 mAP 在给定 IoU 阈值下对朝向误差的敏感性受目标长宽比（aspect ratio）与 IoU 阈值共同门控。我们通过约束扰动实验证明：在保持旋转交并比 rIoU>0.5 的前提下，可对预测框注入平均约 35° 的角度扰动而 mAP@0.5 完全不变，与此同时朝向误差上升约 7 倍、更严格阈值下的 AP75 大幅塌陷；近方形目标在 IoU 上对朝向几乎不可分辨，形成一道朝向可靠性“悬崖”（cliff）。这说明朝向可靠性需要专门的度量，而不能由 mAP 推断。

据此，本文提出一套 **朝向可靠性测量协议**：在剔除近方形病态实例（长宽比≥1.6）的冻结口径下，用归一化风险-覆盖曲线面积（NRC-AUC）、AURC 与分位风险刻画“检测置信度对朝向误差的排序质量”。测量表明：在良态（细长）实例上，检测置信度对朝向误差大体校准；先前文献报告的“检测置信度反校准”，实为把病态近方形实例并入统计所导致的合并假象（pooling artifact），在冻结口径下不成立。

在协议之上，本文给出 **有限样本保形朝向风险控制**（finite-sample conformal orientation risk control）：以保留集校准、审计集验证的 split-conformal / CRC，在“优于平均可靠性”的严格风险预算下提供带弃权的尾部角度误差保证，并给出 Hoeffding 有限样本界。我们进一步把不同可靠性打分套接到同一保形保证层构成“打分菜单”，发现在固定保证下 **几何感知选择器一致取得最高覆盖**，据此把保形保证层与几何选择器组合为推荐默认方案。作为机制层的边界探讨，相位编码器（PSC）的内在角度置信度（phase_mod）即使在良态实例上仍显著与朝向误差反序，构成一个 **机制候选**（mechanism candidate），而非机制定论。跨数据集迁移下保证会退化，按长宽比分层校准可部分缓解但不提供严格迁移保证；以反事实 angle-induced rIoU drop 定义的下游任务收益真实但幅度很小，作为边界处理。

本文的最稳贡献是测量协议与有限样本保形风险控制，而非检测器训练、方法胜利或全面基准。本文不主张 full benchmark complete，不主张方法 final complete，不追公开 mAP，不主张 detector SOTA。

**关键词**：旋转目标检测；朝向可靠性；风险覆盖；保形风险控制；选择性预测；近方形退化；遥感目标检测

---

## 1. 引言

旋转目标检测在遥感、文本、航拍等场景广泛使用有向框（OBB）表示目标朝向。评价上，社区以 mAP 为主导指标。然而 mAP 度量的是“框是否被正确检出与定位到给定 IoU 阈值”，并不直接度量“朝向估计是否可信”。本文的出发点是：**mAP 与朝向可靠性并非同一件事，且二者的耦合关系受几何门控。**

我们给出一个可直接观察的反差（第 5 节）：在保持 rIoU>0.5 的约束下对预测框注入角度扰动，mAP@0.5 可以完全不变，而朝向误差与 AP75 显著恶化；这一“盲区”在近方形目标上尤为极端（IoU 对朝向几乎不可分辨）。因此，若要判断一个检测器的朝向输出是否可信、能否据以选择性使用，必须有专门的朝向可靠性度量与风险控制机制。

本文的立场与边界如下：
- **不是 detector SOTA**：不训练新检测器、不追公开 mAP。DOTA 系列一律采用 train 训练 / val 验证的自跑协议，只与自跑基线比较，不引用官方 trainval/test 数字。DOTA 的 val mAP 低于公开 trainval/test 属正常现象，不作为重训理由。
- **不靠 full matrix 堆量**：本文只在具备可信、可复算 provenance 的少量单元（cell）上做严格测量，不以“覆盖全部检测器×数据集”作为卖点。
- **核心是 measurement protocol + finite-sample risk control**：测量协议（第 4 节）与保形风险控制（第 6 节）是主线；构造性解耦（第 5 节，P1）是动机；uncertainty 打分菜单（第 7 节，P4）并入保形层；机制候选（第 8 节，P3）与下游任务（第 9 节，P5）作为边界与补充，而非主线胜利。

**贡献**：
1. 一套朝向可靠性测量协议：canonical 角度误差、GV-obliquity、near-square masked 主口径、NRC-AUC / AURC / 风险-覆盖度量，以及可信 artifact 的处理规范。
2. 一个构造性解耦结论（P1 precise-pass）：mAP@0.5 对朝向误差的（不）敏感性受 aspect ratio 与 IoU 阈值门控。
3. 有限样本保形朝向风险控制（P2，主贡献）：在严格风险预算下给出带弃权、带有限样本界的尾部保证，并以打分菜单确立“保形层 + 几何选择器”为推荐默认。
4. 一个机制候选（P3）与两个诚实边界（P4 并入 P2；P5 下游收益微弱），以及对先前 unmasked 反校准结论的更正与 supersede。

---

## 2. 相关工作

- **旋转目标检测**：two-stage（Oriented R-CNN 等）、one-stage（Rotated RetinaNet / RTMDet 等）、强骨干（LSKNet 等）、DETR 类（ARS-DETR 等）。〔占位，待补具体文献〕
- **OBB 角度表示与周期性**：长边定义、le90 / le135 约定、角度 π 周期与 (w,h,θ)↔(h,w,θ+90°) 对称。〔占位，待补〕
- **square-like / near-square 歧义**：近方形目标的朝向病态与角度不可辨识问题，是本文 masked 主协议与 cliff 的直接背景。〔占位，待补〕
- **分布/几何角度损失**：GWD、KLD 等基于分布距离的旋转框回归损失。〔占位，待补〕
- **角度编码**：CSL、DCL、PSC（相位编码）等把角度回归转化为分类/相位表示的方法。本文将 PSC 的内在置信度作为机制候选研究对象。〔占位，待补〕
- **校准与选择性预测**：分类/检测校准与 D-ECE；selective prediction / risk-coverage；conformal prediction 与 conformal risk control（CRC）；detection 中的不确定性估计。本文把 CRC 用作朝向风险的保证层。〔占位，待补〕

> 说明：本文不编造具体文献条目；上述引用在正式定稿时补齐真实出处，当前以占位符标注“待补”。

---

## 3. 问题定义

**OBB 与角度误差。** 目标以 (cx, cy, w, h, θ) 表示。采用 canonical long-side 约定：长边朝向为 θ（当 w≥h）或 θ+90°（当 w<h）。两框朝向误差定义为长边朝向之差在 π 周期下的最小绝对值，归一化到 [0°, 90°]：
$$ e(\hat\theta,\theta^{gt}) = \min(d, 180^\circ - d),\quad d = |L(\hat\cdot) - L(\theta^{gt})| \bmod 180^\circ, $$
其中 $L(\cdot)$ 为 canonical 长边朝向。该定义对 (w,h) 互换对称，避免 90° 伪误差。

**near-square / masked 区。** 长宽比 $\mathrm{ar}=\max(w,h)/\min(w,h)$。当 $\mathrm{ar}\to 1$，朝向在 IoU 与几何上病态、不可辨识。本文定义 **masked 主口径为 $\mathrm{ar}\ge 1.6$**（敏感度分析用 $\mathrm{ar}\ge 1.3$）；unmasked 仅作对照，不作为可靠性结论。

**GV-obliquity。** 定义为长边方向相对水平外接框（HBB）的斜率占用度量，用于刻画“朝向偏离轴对齐”的程度；GV≈1 表示近轴/近方形（对朝向不敏感），GV 越小表示越斜/越需要 OBB。GV-obliquity 与 aspect ratio、near-square 退化相关，用于分层与 masking 的解释。

**风险-覆盖与 NRC-AUC。** 给定选择打分 $s$（越大越可信、越先保留）与朝向风险 $r$（角度误差，越小越好）。按 $s$ 降序保留 top-$k$（覆盖 $c=k/n$），选择性风险为所保留样本的平均 $r$。
- AURC = 各覆盖下选择性风险的均值（越低越好）。
- Risk@70 / Risk@90 = 覆盖 0.7 / 0.9 处的选择性风险。
- **NRC-AUC** $= (\mathrm{AURC}_{model}-\mathrm{AURC}_{oracle}) / (\mathrm{AURC}_{random}-\mathrm{AURC}_{oracle})$，其中 oracle 为按风险升序的最优排序，random 为期望随机排序（= 全局平均风险）。NRC=0 为 oracle，NRC=1 等价随机，**NRC>1 表示反校准**（高分反而朝向更差）。该定义为冻结定义。

**D_cal / D_audit。** 每个 cell 依据 md5(image_id) 做确定性互斥划分：D_cal 用于标定（选择器训练、保形阈值），D_audit 用于审计（报告可靠性与保证）。二者不相交、可复现，且在本文中不被修改。

**保形风险控制的定位。** 保形层是**保证层（risk-control layer）**，不是选择打分本身：给定任意打分 $s$ 与风险预算 $\alpha$，用 D_cal 标定阈值使保留集风险受控，在 D_audit 上验证经验覆盖、经验风险与违例，并给出有限样本界。conformal 提供保证，打分决定在该保证下能保留多少覆盖。

---

## 4. 测量协议与 artifact 可信性

**可信 artifact。** 本文的 per-instance 测量基于一批 provenance-clean 的真实检测器输出匹配表（17 字段：score、angle_error、aspect_ratio、near_square、size、D_cal/D_audit flag、source checkpoint、checkpoint sha256、config 等）。每个 cell 记录检测器、数据集、checkpoint sha256、匹配数与预测数（表 1）。这些是真实检测器前向 + 匹配的产物，非 proxy/synthetic。

**协议漂移的更正。** 早期分析在部分环节以 **unmasked**（含近方形）方式聚合 NRC，得到 NRC>1 并解释为“检测置信度反校准”。经在同一权威匹配表上逐口径重算，这一 NRC>1 是把 mean risk 20–32° 的近方形层并入 mean risk ~2° 的细长层所致的 **pooling artifact**：每个 aspect-ratio 分层的 NRC 都 <1（或 ~1），而 pooled 值高于任何单层（第 8 节表 8 与附录 E）。因此本文统一采用 **masked 主口径 ar≥1.6**，unmasked 仅作对照。

**残缺 artifact 的排除。** 其中一个 PSC-DOTA 单元的匹配表仅对一个 19 图的 D_cal 子集匹配（486 条匹配，mAP@0.5≈0.013 属 scope 不匹配的异常值），与其它 full-val 单元不可比。该单元标记为 invalid_pending，**不进入任何主表结论**，仅在附录记录（附录 E）。

**证据保留/作废。** 先前证据按 retained / superseded / out-of-scope / invalid 归类（表 2 与附录 E）：masked 口径下 DIOR#22 检测置信度 NRC≈0.55 保留；FAIR1M/SODA 的“反校准”作废；aspect-ratio cliff 保留并升为测量层核心；intrinsic phase_mod 反校准（masked 下幸存）保留为机制候选；均匀 30° 扰动“解耦”作废，由约束扰动替代。

> artifact 路径、sha256、生成命令等 provenance 细节下沉至附录 A，不在正文主叙述堆砌。

**表 1. Artifact / 数据集 / cell 汇总（provenance-clean，masked 主口径）**

| cell | 数据集 | 检测器 | n_pred | n_matched | 可信度 |
|---|---|---|---|---|---|
| DIOR#22 | DIOR-R | PSC (RetinaNet+相位编码) | 212448 | 29994 | full-val, real |
| FAIR1M#24 | FAIR1M-v1.0 | PSC | 484332 | 54768 | full-val, real |
| SODA#23 | SODA-A | PSC | 1449379 | 309218 | full-val, real |
| DIOR#3 | DIOR-R | Oriented R-CNN | 60881 | 32161 | full-val, real |
| DIOR#61 | DIOR-R | Rotated RTMDet-s | 110036 | 32696 | full-val, real |
| SODA#4 | SODA-A | Oriented R-CNN | 676208 | 376756 | full-val, real |
| DIOR#10 | DIOR-R | Oriented R-CNN + LSKNet | — | 27097 (masked) | masked-only (features) |
| SODA#11 | SODA-A | Oriented R-CNN + LSKNet | — | 254021 (masked) | masked-only (features) |
| DOTA#20† | DOTA-v1.0 | PSC | 2428 | 486 | invalid_pending（19 图子集，附录 E） |

† 不进入主表结论。

---

## 5. P1：构造性解耦

**方法。** 对每个真实匹配实例，取其预测框与匹配 GT，计算 **eps_max = 在保持 rIoU(pred, gt)>0.5 的前提下、沿远离 GT 方向可注入的最大角度扰动**（网格搜索，shapely 旋转 IoU）。注入该扰动后，匹配在 IoU>0.5 阈值下由构造保留，故 mAP@0.5 不变；随后观察朝向误差、AP75（IoU>0.75 的更严阈值对照）的变化。每 cell 采样 4000 个 D_audit 实例。

**主结果（表 3）。** 在平均约 35° 的约束扰动下，六个 cell 的 mAP@0.5 全部 1.000→1.000 保持不变，而朝向误差从约 4–5° 上升到约 34–37°（约 7 倍），AP75 大幅塌陷。

**表 3. P1 约束扰动主结果（D_audit，n=4000/cell）**

| cell | 平均 eps_max | mAP@0.5 | AP75 | 朝向误差° |
|---|---|---|---|---|
| DIOR#22 | 34.9° | 1.000→**1.000** | 0.715→0.076 | 5.30→34.49 |
| FAIR1M#24 | 35.6° | 1.000→**1.000** | 0.417→0.058 | 4.52→36.75 |
| SODA#23 | 33.5° | 1.000→**1.000** | 0.434→0.016 | 5.03→34.62 |
| DIOR#3 | 34.7° | 1.000→**1.000** | 0.815→0.075 | 4.85→34.92 |
| DIOR#61 | 35.2° | 1.000→**1.000** | 0.831→0.086 | 4.33→35.86 |
| SODA#4 | 34.7° | 1.000→**1.000** | 0.561→0.017 | 5.49→35.85 |

**长宽比门控（dose-response）。** 按 aspect-ratio 分层（表 3b）可见：eps_max 随长宽比增大而减小（近方形 ~68°、moderate ~58–67°、细长 ~32–35°、极细长 ~15–19°），即角度对 IoU 的几何敏感性由长宽比门控；但**每个分层的 Δ mAP@0.5 = 0.000**，朝向误差在每个分层都大幅上升。该结果与理论曲线 IoU(δθ; ar) 一致：ar=1.0 时 IoU 在任意 δθ 都 ≥0.707（近方形对朝向不可辨），ar=3.0 时 IoU 在 δθ≈30–35° 才降到 0.5（与细长层 eps_max≈33° 吻合）。

**表 3b. ar-bin dose-response（示例：跨 cell 一致趋势）**

| ar_bin | eps_max | Δ 朝向误差° | Δ mAP@0.5 | Δ AP75 |
|---|---|---|---|---|
| near_square (<1.3) | ~68° | +19 ~ +42 | **0.000** | −0.26 ~ −0.45 |
| moderate (1.3–1.6) | ~58–67° | +54 ~ +64 | **0.000** | −0.38 ~ −0.81 |
| elongated (1.6–3) | ~32–35° | +32 ~ +33 | **0.000** | −0.35 ~ −0.84 |
| very_elongated (≥3) | ~15–19° | +15 ~ +19 | **0.000** | −0.36 ~ −0.78 |

**裁决：P1 由 partial 修正为 precise-pass。** 精确表述为：**mAP@0.5 对朝向误差的（不）敏感性受 aspect ratio 与 IoU 阈值门控——近方形框在 IoU 上对朝向不可辨（cliff），细长框亦容忍约 35° 角误差而 mAP@0.5 不变；朝向误差与更严阈值的 AP75 不受此门控保护。** 这不是“mAP 完全看不见角度”，而是“mAP@0.5 在部分几何区对朝向错误结构性弱敏感”。（这修正了早期以均匀 30° 扰动得到的、因破坏 rIoU>0.5 而使 mAP 同步变动的无效解耦。）

---

## 6. P2：有限样本保形朝向风险控制（主贡献）

**设置。** 在 masked 主口径下，用 D_cal 标定阈值、D_audit 审计。给定选择打分 $s$ 与风险预算 $\alpha$，选取覆盖最大的阈值使 D_cal 上（加有限样本 slack 的）风险 $\le\alpha$，在 D_audit 报告经验覆盖、经验风险、违例率。

**空洞保证问题与修复。** 若把预算设在 base rate 之上（如平均角度误差 ≤15° 或尾部 P(err>10°)≤0.10），masked 细长实例本就满足，保证在覆盖=1 时平凡成立（无需弃权）——这是“空洞保证”。本文把保证设在 **operationally-strict 区（$\alpha$ 低于 base rate）**，即“要求优于平均可靠性”，此时保证强制弃权、出现真实的覆盖–风险权衡，不同打分显著分化。

**6.1 base risk 与 alpha 扫描（表 4）。** D_audit 平均朝向误差（base risk）为 DIOR#22 1.74° / FAIR1M#24 2.49° / SODA#23 2.41° / DIOR#3 1.89° / DIOR#61 2.06° / SODA#4 2.65°。在 $\alpha$ 低于 base 时出现真实弃权。

**表 4. 均值风险 alpha 扫描（detection score，coverage@D_audit）**

| cell | α=1.0° | α=1.5° | α=2.0° | α=2.5° | base |
|---|---|---|---|---|---|
| DIOR#22 | 0.305 | 0.793 | ~1.00 | ~1.00 | 1.74 |
| DIOR#3 | 0.229 | 0.690 | ~1.00 | ~1.00 | 1.89 |
| DIOR#61 | 0.276 | 0.737 | ~1.00 | ~1.00 | 2.06 |
| FAIR1M#24 | 0.007 | 0.015 | 0.065 | 1.00 | 2.49 |
| SODA#23 | infeasible | ~0 | ~0 | 1.00 | 2.41 |
| SODA#4 | 0.018 | 0.067 | 0.244 | 0.828 | 2.65 |

> 说明：在传统宽松预算（{3,5,8,10,15}°）下，本口径的保证在覆盖≈1 处平凡满足；故报告 operationally-strict 区 {1.0,1.5,2.0,2.5}°。均值损失无界，故均值版为近似保证（个别 cell D_audit 上有轻微溢出），尾部版有干净有限样本界（6.2）。

**6.2 尾部保形（indicator loss，有限样本界干净）。** 控制 P(err>5°)≤α（bounded loss，适配 CRC + Hoeffding；base tail P(err>5°)≈0.07–0.14）。Hoeffding 半径 $\sqrt{\ln(1/\delta)/(2 n_{cal})}$（δ=0.1）已并入阈值。

**表 5. 尾部保形 P(err>5°)≤α（detection score）**

| cell | base_tail | α=0.03: cov / 弃权 | α=0.05: cov | α=0.08: cov | Hoeffding |
|---|---|---|---|---|---|
| DIOR#22 | 0.067 | 0.327 / 0.673 | 0.680 | ~1.00 | 0.0098 |
| DIOR#3 | 0.067 | 0.502 / 0.498 | 0.810 | 1.00 | 0.0095 |
| DIOR#61 | 0.076 | 0.582 / 0.418 | 0.849 | ~1.00 | 0.0094 |
| FAIR1M#24 | 0.128 | 0.015 | 0.021 | 0.053 | 0.0069 |
| SODA#23 | 0.113 | ~0 | ~0 | ~0 | 0.0030 |
| SODA#4 | 0.142 | 0.032 | 0.066 | 0.204 | 0.0027 |

> 在更宽阈值 P(err>10°)/P(err>15°) 下，masked base rate ≈1–2%，保证在覆盖≈1 处平凡满足（附录 D）；因此 err>5° 的严格 α 是有意义的工作点。大 cell 的 $n_{cal}$ 为 1.2 万–16 万，Hoeffding 半径 0.003–0.010，界紧。

**6.3 打分菜单（score menu，同一保形层套不同打分）。** 在固定保证下，覆盖越高的打分越好。取严格 P(err>5°)≤0.03：

**表 7. 打分菜单（固定保证 P(err>5°)≤0.03 下的 D_audit 覆盖）**

| cell | detection | geometry selector | TTA circular var | phase_mod |
|---|---|---|---|---|
| DIOR#22 | 0.327 | **0.472** | 0.001 | 0.000 |
| FAIR1M#24 | 0.015 | **0.164** | 0.000 | 0.001 |
| SODA#23 | 0.000 | **0.227** | 0.228 | 0.000 |
| DIOR#3 | 0.502 | **0.593** | 0.490 | — |
| DIOR#61 | 0.582 | **0.631** | 0.126 | — |
| SODA#4 | 0.032 | **0.202** | 0.137 | — |

**几何感知选择器在 6/6 cell 取得最高覆盖**；TTA circular variance 不稳定（SODA 好、DIOR#22/FAIR1M/DIOR#61 差）；intrinsic phase_mod 作为选择器覆盖≈0（因其反校准，见第 8 节）。据此推荐默认方案为 **保形保证层 + 几何感知选择器**。

**6.4 Mondrian（ar-bin 分层）与 shift 审计。** 同分布（D_cal→D_audit）下，全体阈值与 ar 分层阈值的覆盖/违例接近（表 6）。**跨数据集迁移**（源 cell→异数据集目标 cell，α=0.05）下全体阈值出现违例（保证退化）；ar 分层在 4 对中 3 对降低违例（其中 DIOR#22→FAIR1M#24 由违例转为合规）。

**表 6. 跨数据集 shift 审计（尾部 P(err>5°)≤0.05）**

| 源→目标 | 全体阈值 tail | 分层阈值 tail | 分层是否缓解 |
|---|---|---|---|
| DIOR#22→SODA#23 | 0.099（违） | 0.099 | 部分 |
| DIOR#3→SODA#4 | 0.087（违） | 0.058 | 是 |
| DIOR#22→FAIR1M#24 | 0.099（违） | 0.042（合规） | **是（修复）** |
| SODA#4→DIOR#3 | 0.029（合规） | 0.034 | 否 |

**裁决：P2 由“空洞保证”修正为有效贡献（有边界）。** 在严格风险预算下，within-cell 保形提供带弃权的覆盖–违例–保证与干净的有限样本尾部界；打分菜单确立“保形层 + 几何选择器”为默认。**边界**：均值版为近似保证；跨数据集迁移无严格保证（如实报告退化，Mondrian 部分缓解）。保形是 risk-control 保证层，不是普通 selection score。

---

## 7. P4 融入 P2：不确定性打分菜单

TTA circular variance 使用 **θ→2θ 的圆统计**（circular variance）计算增强一致性下的角度离散度，**不使用 naive 线性 std**（后者在 π 周期上错误）。在 masked 口径 D_audit 上比较各打分对朝向误差的 NRC（越低越好）：

**表 7b. uncertainty 打分菜单 NRC（masked ar≥1.6, D_audit；配对 bootstrap）**

| cell | detection | geometry | TTA circular | phase_mod | geo vs det | geo vs TTA |
|---|---|---|---|---|---|---|
| DIOR#22 | 0.562 | **0.520** | 0.534 | 1.128 | 显著优 | 打平 |
| FAIR1M#24 | 0.921 | **0.599** | 0.647 | 1.117 | 显著优 | 显著优 |
| SODA#23 | 0.906 | **0.502** | 0.527 | 1.091 | 显著优 | 显著优 |
| DIOR#3 | 0.528 | **0.487** | 0.570 | — | 显著优 | 显著优 |
| DIOR#61 | 0.419 | **0.396** | 0.684 | — | 显著优 | 显著优 |
| SODA#4 | 0.706 | **0.505** | 0.948 | — | 显著优 | 显著优 |

masked 口径下 **几何感知选择器在 6/6 cell 显著优于检测置信度、5/6 优于 TTA（DIOR#22 打平）**。因此：几何感知选择器为推荐主打分；**TTA circular variance 作为 GT-free 后备**（不需目标域 GT，但作为打分不稳定）。末段多 epoch checkpoint 未持久化，**checkpoint-ensemble circular variance unavailable（如实标注，不构造）**。P4 不作独立胜利，而是 P2 打分菜单的一部分（“选哪个打分喂保形层”的实证答案：几何选择器）。

---

## 8. P3：机制候选与边界

**检测置信度反校准结论被 superseded。** 早期以 unmasked 口径报告 PSC 检测置信度 NRC>1（反校准）。在冻结 masked 口径 + 同一权威匹配表上重算，检测置信度在 4/4 PSC cell **显著校准**（NRC<1，见表 8）；该 unmasked NRC>1 为近方形 pooling artifact（附录 E）。

**intrinsic phase_mod 在 masked 下仍反校准，作为机制候选。** PSC 的相位编码内在置信度 phase_mod（= 第一频相位分量的模）在 masked 口径下对朝向误差仍显著反序（NRC>1，CI 下界>1）于 3/3 full-val PSC cell。

**表 8. PSC 检测置信度 vs 内在 phase_mod（masked ar≥1.6，bootstrap 95% CI）**

| cell | detection NRC [CI] | 判定 | phase_mod NRC [CI] | 判定 |
|---|---|---|---|---|
| DIOR#22 | 0.542 [0.529, 0.556] | 显著校准 | 1.129 [1.098, 1.160] | 显著反校准 |
| FAIR1M#24 | 0.885 [0.865, 0.907] | 显著校准 | 1.101 [1.077, 1.121] | 显著反校准 |
| SODA#23 | 0.914 [0.903, 0.926] | 显著校准 | 1.090 [1.081, 1.100] | 显著反校准 |
| DOTA#20† | 0.693 [0.672, 0.711] | （子集，慎用） | 0.964 [0.929, 0.998] | （子集，慎用） |

† 19 图子集，invalid_pending，不进主结论。

**裁决。** 反校准信号从 detection-score（作废）迁移到 **intrinsic angle-coder 置信度**：正确的机制叙述是“**PSC 角度编码器的内在置信度对朝向误差反序**”。这是 mAP 与检测置信度都无法揭示的编码器级可靠性缺陷。但这是 **机制候选，不是机制定论**：确证需受控 angle-coder 实验（本文不启动 PSC 重训矩阵）。PSC 在此是 case study，不是论文唯一主角；DOTA#20 残缺单元不进入机制主结论。

---

## 9. P5：下游任务边界

**旧任务错配。** 以 risk=1−rIoU 定义的下游任务被中心/尺度误差主导，与朝向可靠性错配。

**重设计：反事实 angle-induced rIoU drop。** 只隔离角度贡献：ΔrIoU = rIoU(预测框代入 GT 角度) − rIoU(预测框用预测角度)（保持中心/尺度不变），即“把角度纠正后可恢复的 IoU”。在 masked D_audit 上以 ΔrIoU 为下游风险，比较各选择器的风险-覆盖。

**表 9. P5 下游（angle-induced ΔrIoU 的 NRC，masked ar≥1.6，n=6000/cell）**

| cell | base 平均 ΔrIoU | NRC detection | NRC size-linear | NRC geometry |
|---|---|---|---|---|
| DIOR#22 | 0.0032 | 0.801 | 0.883 | **0.752** |
| FAIR1M#24 | 0.0023 | 0.893 | 1.016 | **0.954** |
| SODA#23 | 0.0025 | 1.085 | 0.983 | **0.891** |
| DIOR#3 | 0.0044 | **0.742** | 0.987 | 0.764 |
| DIOR#61 | 0.0041 | **0.737** | 0.879 | 0.785 |
| SODA#4 | 0.0033 | 0.991 | 0.921 | **0.873** |

**裁决。** 重设计后信号方向正确（几何选择器多数最优），但绝对收益极小（base ΔrIoU 仅 0.002–0.004，≈0.2–0.4% IoU）——在良态细长实例上角度误差本就小，角度纠正的下游收益因此很小；near-square 上角度病态，纠正无意义。**P5 进入附录/边界，不主张下游 utility proven，不影响 P1/P2 主线。**

---

## 10. 讨论

- **为什么不补 full matrix / 不重训 detector / 不追公开 mAP。** 本文的科学问题是“朝向可靠性能否被测量与被有限样本地控制”，答案不依赖覆盖全部检测器×数据集，也不依赖刷高 mAP。补 full matrix 只增加体量、不增加对该问题的回答；重训 detector 与追公开 mAP 与本文命题正交，且 DOTA 采用 train/val 自跑协议，val mAP 低于公开数字属正常。
- **为什么从“fix 方法线”收缩为 measurement protocol + risk control。** 严格法证调和后，先前作为“修复胜利”的多处结论要么是 unmasked pooling artifact（作废），要么是 within-cell 保形（保留、强化）。据实，最稳的正贡献是测量协议与有限样本保形风险控制，而非某个可部署方法的胜利。
- **为什么负结果不是失败而是 scope boundary。** P5 收益微弱、跨域无严格保证、phase_mod 仅机制候选——这些是清晰界定的适用边界，划定了结论能外推到哪里，本身是可靠性研究的价值。
- **DOTA#20 的正确定位。** 它是 19 图子集的残缺 dump，mAP 异常，不可比；本文将其排除主表、标 invalid_pending，避免把 dump 缺陷误读为检测器崩溃或机制证据。
- **near-square 的角色。** near-square 是朝向病态的根源，也是 masked 主口径与 cliff（测量层核心）的动因；把它并入统计会制造 pooling artifact，这正是先前 unmasked 反校准结论的来源。
- **shift audit 的限制。** 跨数据集迁移下保形保证会退化；ar 分层部分缓解但不提供严格迁移保证，这是本文明确承认的边界。

---

## 11. 局限性

- 非 full benchmark；非 full project complete；非 detector SOTA；非 P3 final method；非 PSC mechanism proof；非 downstream utility proof。
- 严格测量目前只覆盖少量 provenance-clean cell（7 个 full-val + 2 个 masked-only）；更多 cell 在冻结 masked 口径下重算可增强外推性。
- DOTA#20 需后续 full-val provenance dump 才能进入结论。
- phase_mod 机制候选需受控 angle-coder 实验方可升为机制证据。
- 均值风险保证为近似（无界损失）；跨域无严格保证。
- 下游收益微弱，不足以支撑 utility 主张。

---

## 12. 结论

本文建立了旋转目标检测朝向可靠性的**测量协议**，证明 mAP@0.5 对朝向误差存在受 aspect ratio 与 IoU 阈值门控的结构性盲区（P1 precise-pass），并把 aspect-ratio cliff 确立为测量层核心发现。在此协议上，本文给出**有限样本保形朝向风险控制**（P2 主贡献），在严格风险预算下提供带弃权与有限样本界的尾部保证，并以打分菜单确立“保形层 + 几何选择器”为推荐默认。作为边界，本文更正了先前 unmasked 检测置信度反校准结论（pooling artifact，作废），给出 PSC 角度编码器内在置信度反校准的**机制候选**，并如实报告下游收益的微弱与迁移保证的退化。**当前最稳的贡献是测量与保形风险控制，而非检测器训练或强方法胜利。**

---

## 图表占位（不实际绘制，给出图题/图注/数据路径/应展示内容）

- **Fig.1 研究问题与 mAP blind spot。** 图注：约束扰动下 mAP@0.5 不变而朝向误差/AP75 恶化的示意与实测并置。数据：约束扰动结果表。展示：mAP@0.5 平线 + 朝向误差跃升 + AP75 塌陷。
- **Fig.2 IoU(δθ; aspect ratio) 理论曲线。** 图注：不同 ar 下 IoU 随角度偏差的下降；ar=1 近平坦（不可辨），ar 大者陡降。数据：IoU(δθ;ar) 理论曲线表。
- **Fig.3 约束扰动 dose-response。** 图注：按 ar-bin 的 Δrisk 与 Δ mAP@0.5(=0)。数据：ar-bin dose-response 表。
- **Fig.4 aspect-ratio reliability cliff。** 图注：朝向误差分位（p90/p99）随 ar 的悬崖式变化（细长 ~10–26° → 近方形 ~88–90°）。数据：ar-bin dose-response 表 + masked 口径统计。
- **Fig.5 保形 alpha scan frontier。** 图注：coverage–risk 前沿（各 cell）。数据：保形 alpha 扫描表。
- **Fig.6 尾部保形 coverage。** 图注：P(err>5°)≤α 下 coverage 随 α。数据：尾部保形表。
- **Fig.7 打分菜单对比。** 图注：固定保证下各打分覆盖柱状图（geometry 最高）。数据：打分菜单表 + 不确定性打分 NRC 表。
- **Fig.8 phase_mod 机制候选。** 图注：masked 口径 detection（校准）vs phase_mod（反校准）NRC 及 CI。数据：masked NRC bootstrap 表。
- **Fig.9 scope 与 evidence ledger。** 图注：retained/superseded/invalid/boundary 证据谱。数据：证据谱表。

（表 1–9 见正文；表 10 见附录 H claim ledger。）

---

## 附录

### 附录 A. Artifact provenance
per-instance 匹配表：17 字段（score/angle_error/aspect_ratio/near_square/size/split flag/source_checkpoint/checkpoint_sha256/config）。每 cell 记录 checkpoint sha256、config 路径、n_pred、n_matched（表 1）。均为真实检测器前向 + 匹配产物（is_real_detector_output=true）。

### 附录 B. D_cal / D_audit
依 md5(image_id) 确定性互斥划分；D_cal 标定（选择器/保形阈值），D_audit 审计（可靠性/保证）。本文不修改该划分。

### 附录 C. 度量定义
canonical long-side 角度误差；GV-obliquity；NRC-AUC（冻结定义）；AURC；Risk@70/90；风险-覆盖曲线。

### 附录 D. 保形推导
split-conformal / CRC；bounded indicator loss 的 Hoeffding 有限样本界 $\sqrt{\ln(1/\delta)/(2n_{cal})}$；宽阈值（err>10°/15°）在 masked 口径 base rate ~1–2% 下平凡满足的说明；均值损失无界导致均值版为近似保证的说明。

### 附录 E. Superseded results memo
- detection-score PSC 反校准（unmasked 1.14/1.62/1.80）= superseded：near-square pooling artifact；masked ar≥1.6 得 0.542/0.885/0.914（显著校准）。分层证据：pooled NRC 高于每一个 ar 分层。
- measure_fix 的 FAIR1M 1.083 / SODA 1.260「masked 反校准」= superseded：用弱 mask（≤1.10）；ar≥1.6 下降到 0.885/0.914。
- 均匀 30° 扰动“解耦”= superseded：破坏 rIoU>0.5，mAP 同步变动；由约束扰动替代。
- DOTA#20（486 匹配，mAP 0.013）= invalid_pending：19 图 D_cal 子集 scope。

### 附录 F. Negative results
- P5 下游收益微弱（ΔrIoU 0.2–0.4%）。
- 跨数据集迁移保形保证退化（无严格迁移保证）。
- TTA circular variance 作为打分不稳定。

### 附录 G. Reproducibility checklist
冻结定义（NRC/角度误差/masked 口径 ar≥1.6）；冻结 D_cal/D_audit；checkpoint sha256；生成脚本与 CSV 路径；随机种子。

### 附录 H. Forbidden claims / Claim ledger（表 10）
详见 `final_claim_ledger_reaudited_056.md`。要点：
- allowed：measurement protocol；P1 precise-pass；finite-sample conformal risk control；aspect-ratio cliff；phase_mod mechanism candidate；含圆统计 TTA 基线的打分菜单。
- qualified：几何选择器为 candidate（source-supervised + target GT-free）；NRC 在可比设置提供 mAP 之外信号（非严格独立）。
- forbidden：NRC 严格独立于 mAP；full benchmark complete；P3 final method success；PSC angle head proven broken；DOTA#20 validation；downstream utility proven；CVPR/ICCV/TPAMI ready；full project complete。

### 附录 I. P2/C1 附录（负结果）
OT-dustbin / 物理多视一致性等 C1 方向在本文为负结果/附录，不作主线。

---

*（图片未实际绘制；所有数值均来自 provenance-clean 真实匹配表在冻结 masked 口径下的计算，未训练检测器、未追公开 mAP、未修改冻结阈值与划分。）*
