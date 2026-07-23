# Orientation Reliability：面向旋转目标检测的朝向可靠性基准与风险控制

## 摘要

旋转目标检测（oriented object detection, OOD）广泛使用 mAP 评价检测框的位置、类别与排序质量，但 mAP 并不总能充分刻画旋转框的朝向可靠性。对于船舶、车辆、机场跑道等具有方向语义的目标，同样的检测精度可能对应不同的角度风险；同时，检测置信度也不必然等价于朝向置信度。本文研究的问题是：如何在真实 detector artifacts 上测量 OBB angle reliability，并在可验证条件下控制被选择朝向预测的风险。

本文提出一个收缩版 orientation reliability benchmark 与 conformal risk control 框架。我们使用真实 raw/schema/matched artifacts 重新评估 P1-P5：P1 通过角度扰动、反向扰动与同数据集配对挖掘检验 mAP 与朝向风险的关系；P2 将 conformal risk control 作为任意 selection score 外部的阈值与保证层，在 frozen D_cal / D_audit 上给出 within-cell 风险控制；P3-P5 分别检查 PSC phase_mod 机制线、强不确定性基线和一个下游 rIoU-drop 任务。

真实证据结论是克制的。P1 partial：角度扰动显著改变 angle risk，但 mAP@0.5 也有较强响应，因此不能声称 NRC 与 mAP 严格独立。P2 pass：在 052 full real matched tables 与 frozen D_cal / D_audit 下，七个关键 cell 的 within-cell conformal risk control 均满足 alpha=15 degrees 的 audit 风险目标，violation rate 为 0。P3/P4 partial：PSC phase_mod 机制测试仅部分支持，geometry-aware selector 未稳定打赢 TTA circular variance。P5 fail：angle-induced rIoU drop 任务未显示稳定下游收益。本文贡献因此定位为：建立朝向可靠性测量与治理协议，给出可复现的真实证据边界，并将 conformal orientation risk control 作为当前最稳的正贡献。

## 关键词

旋转目标检测；朝向可靠性；风险覆盖；保形风险控制；选择性预测；遥感目标检测。

## 1. 引言

旋转目标检测的标准评价长期围绕 mAP 展开。mAP 对类别置信度排序和 IoU 阈值下的检测正确性敏感，是目标检测不可替代的核心指标。然而，在 oriented bounding box（OBB）任务中，检测框还包含角度分量。角度错误有时会改变 rotated IoU，有时却被几何形状门控。例如 near-square 目标在旋转后仍可能保持较高 IoU，而 elongated 目标对角度变化更敏感。这意味着 mAP 可以反映一部分角度错误，但未必完整反映朝向预测是否可靠、检测分数是否能筛选低角度风险样本、以及在选择性预测场景下能否控制风险。

本文不声称 NRC 与 mAP 严格独立。053 的真实 artifact 复跑显示，角度风险与 mAP 确实存在耦合：30 度角度扰动使 mean |Delta angle risk| 达到 26.4883 degrees，同时 mean |Delta mAP@0.5| 也达到 0.1810。因此，本文的主张不是“mAP 看不见全部角度错误”，而是更克制地表述为：mAP 未充分刻画 orientation reliability，仍需要独立的 risk-coverage 指标与风险控制机制来补充。

本文也不是检测器排行榜类型工作。DOTA 采用 train/val 自跑协议，不追公开 trainval/test mAP，不引用公开 leaderboard 数字作为贡献。非 DOTA 数据集使用项目既定实验口径，non-DOTA 结果中存在 exploratory 成分。本文关注 benchmark + conformal risk control：测量真实 detector 输出中的朝向可靠性，明确哪些证据成立、哪些证据不足，并在 within-cell setting 下提供可复现的 conformal risk control。

本文的贡献如下：

1. 提出 orientation reliability benchmark 的收缩版协议，使用 angle error、risk-coverage、NRC-AUC、AURC、Risk@70/Risk@90 和 near-square / well-defined region 分析真实 OBB 输出。
2. 在 052 real artifacts 上复跑构造性解耦实验，得到 P1 partial 结论：orientation risk 的变化可测量，但不能写成强解耦。
3. 将 conformal risk control 作为朝向选择的阈值与保证层，而不是新的 selection score；在 frozen D_cal / D_audit within-cell 设置下得到 P2 pass。
4. 如实报告 P3/P4/P5 的 partial/fail 结果，将 PSC 机制、强不确定性比较和下游任务收益作为边界与未来工作，而非主贡献。
5. 提供 artifact-governed reproducibility：052 manifest、full matched 17-field tables、per-matched phase_mod、TTA circular variance、verifier 与 claim ledger。

## 2. 相关工作

旋转目标检测。遥感场景中的目标常具有任意方向，旋转检测器在水平框检测基础上引入 OBB 表示、旋转 anchor、角度回归或角度分类。本文不提出新的 detector，而是在已有 detector 输出上测量朝向可靠性。

OBB angle representation。角度表示存在周期性、边界不连续和宽高交换问题。CSL、DCL、PSC 等 angle coder 试图通过平滑标签、稠密编码或相位编码缓解角度学习困难。本文将这些工作视为朝向预测机制背景，不把 053 中的 PSC phase_mod 结果写成机制证明。

Square-like / near-square ambiguity。当目标接近正方形时，角度在几何上可能弱可辨；当目标 elongated 时，角度变化更容易影响 rIoU。本文在指标定义中区分 near-square、moderate 和 elongated，并在理论 IoU 曲线中展示 aspect ratio 对 angle sensitivity 的门控作用。

GWD/KLD 与 distribution-aware losses。高斯 Wasserstein 距离、Kullback-Leibler divergence 等损失把旋转框建模为分布或椭圆几何，以缓解角度边界与长宽交换问题。本文不比较训练损失本身，而是在已有真实 detector artifacts 上评估输出可靠性。

Detector calibration / D-ECE。目标检测校准研究关注分类置信度、定位质量和检测分数的一致性。D-ECE 等指标为检测置信度校准提供了背景。本文的问题更窄：检测分数能否排序低角度风险样本，以及能否通过 conformal layer 控制选中样本的朝向风险。

Selective prediction。选择性预测研究在 coverage 与 risk 之间权衡，用拒识或 abstention 控制错误。本文将朝向预测放入 risk-coverage 语法，报告 coverage、abstention rate、AURC 与 Risk@k。

Conformal risk control。Conformal prediction 与 conformal risk control 提供 finite-sample 语义的风险控制方法。本文使用 conformal 作为 threshold / guarantee layer，而不是普通 selection score；within-cell 有保证，shift 下仅做 audit。

Uncertainty estimation。MC dropout、deep ensemble、TTA variance 和 detector-native quality score 可用于估计不确定性。本文在 P4 中只使用 052 已验证的 TTA circular variance；MC dropout、checkpoint ensemble、native entropy/angle quality 与 GWD/KLD uncertainty 没有 verified 052 artifacts，因此只报告 unavailable。

说明：本文中文稿暂以 [R1]-[R10] 作为真实文献占位符，定稿 bib 应覆盖 rotated detection、CSL/DCL/PSC、GWD/KLD、D-ECE、selective prediction、conformal risk control 和 uncertainty estimation；不得填入未经核验的作者、年份或页码。

## 3. 问题定义与指标

Orientation reliability 指 detector 对目标朝向的可选择可靠性。给定预测旋转框 `b_i=(x_i,y_i,w_i,h_i,theta_i)`、类别 `c_i`、检测分数 `s_i` 和匹配 GT `g_i`，我们关注 angle error 是否能被 score 或其他 selector 排序，并能否在固定 coverage 下控制风险。

Angle error。角度为 pi 周期量。对预测角 `theta` 与 GT 角 `theta*`，角度误差定义为最小周期差：

`e(theta, theta*) = min_{k in Z} |theta - theta* + k*pi|`，

并换算为 degrees，范围约束到 `[0,90]`。未匹配预测不进入 per-matched angle error 统计，但会参与 raw prediction rematching 和 mAP 计算。

Near-square / well-defined region。令 aspect ratio `ar=max(w,h)/min(w,h)`。near-square 表示 `ar` 接近 1，角度在几何上弱可辨；well-defined region 通常排除 near-square，强调角度有实际几何含义的样本。本文报告 near-square、moderate、elongated 分层，但不把 near-square trivial gain 包装成方法贡献。

Risk-coverage。给定 selector `q_i`，按 selector 从可靠到不可靠排序，保留前 `coverage` 比例样本，计算平均 angle error 作为 risk。Coverage 越低，abstention rate 越高。本文报告 Risk@70 和 Risk@90，即 coverage 为 70% 和 90% 时的 angle risk。

NRC-AUC。NRC-AUC 是 normalized risk-coverage 行为的归一化指标。`NRC=1` 表示随机排序基线，`NRC<1` 表示优于随机，`NRC>1` 表示 reverse-calibrated 或差于随机。本文使用 NRC 作为排序可靠性指标，但不声称它与 mAP 严格独立。

AURC。AURC 是 risk-coverage curve 的面积，越低表示在不同 coverage 下的平均风险越低。它与 NRC 一起描述 selector 是否能在 abstention 后降低 angle risk。

D_cal / D_audit。D_cal 用于确定 conformal threshold，D_audit 用于独立审计 empirical risk、coverage 和 violation rate。053 使用 frozen D_cal / D_audit，不修改 split，不进行泄漏式调参。

Formal vs exploratory。DOTA train/val 口径和 frozen split 支撑 formal evidence；non-DOTA 和跨 detector/dataset 分析根据既有项目标签可能属于 exploratory 或 audit。本文不把 exploratory 结果改写为 formal。

Conformal risk control。Conformal 不是 selection score。给定任意 score 或 selector，conformal risk control 在 D_cal 上选择阈值，使选中集合在 exchangeability 假设下满足目标风险语义；在 D_audit 上报告 empirical risk 和 violation。Shift audit 不承诺严格保证。

## 4. 数据与实验协议

历史覆盖包含 23 real cells / 6 datasets，用于建立 OrientBench 的数据与 detector 覆盖背景。但 054 论文的主分析以 052 real artifacts 为准，避免使用 proxy/synthetic 结果作为 final evidence。

052 real artifacts 包括：

| cell | dataset | detector | predictions | matched | artifact status |
|---|---|---|---:|---:|---|
| DOTA-v1.0/20 | DOTA-v1.0 | rotated_retinanet_psc | 2428 | 486 | full real |
| DIOR-R/22 | DIOR-R | rotated_retinanet_psc | 212448 | 29994 | full real |
| FAIR1M-v1.0/24 | FAIR1M-v1.0 | rotated_retinanet_psc | 484332 | 54768 | full real |
| SODA-A/23 | SODA-A | rotated_retinanet_psc | 1449379 | 309218 | full real |
| DIOR-R/3 | DIOR-R | oriented_rcnn | 60881 | 32161 | full real |
| DIOR-R/61 | DIOR-R | rotated_rtmdet_s | 110036 | 32696 | full real |
| SODA-A/4 | SODA-A | oriented_rcnn | 676208 | 376756 | full real |

表1 数据集与 real artifact coverage。数据路径：`top_journal_v3/reports/full_matched_tables_052.csv`；persistent matched tables：`outputs/persistent_artifacts/orientbench_real_052/matched_tables/`。

DOTA 使用 train/val 自跑协议，不追公开 test mAP。非 DOTA 使用既定训练/验证或 trainval/test 协议，但本文不把这些结果写成 leaderboard 对齐。P1-P5 复跑只使用 052 real artifacts：raw/schema predictions、GT OBB、full matched 17-field tables、per-matched phase_mod 和 TTA circular variance。

不补 full matrix 的原因是：053 已经给出足以决定论文定位的证据边界。继续补更多 detector/dataset 会增加覆盖面，但不能把 P1 partial、P3/P4 partial 或 P5 fail 改写成通过。本文因此停止新增实验，转向真实证据版论文定稿。

Artifact 持久化。大文件不写入 git；持久化目录为 `outputs/persistent_artifacts/orientbench_real_052/`，manifest 为 `outputs/persistent_artifacts/manifest_052.json`。报告、verifier 和论文写作文件写入 `top_journal_v3/`。

## 5. P1：构造性解耦实验

P1 目的在于检验 mAP 与 angle risk 是否能在受控条件下分离。053 在 raw predictions 上注入角度扰动，而不是只修改 matched table；每次扰动后重新匹配，重新计算 mAP@0.5、AP75、NRC、AURC、Risk@70 和 Risk@90。

角度扰动实验显示，angle risk 对扰动非常敏感。例如 30 度扰动下，各 cell 的 Delta angle risk 大多约为 25-28 degrees。但 mAP@0.5 也同步下降，尤其在 DIOR-R/3、DIOR-R/61、SODA-A/4 等 cell 上下降明显。因此，P1 裁决为 partial，而非 pass。

表2 P1 perturbation summary。数据路径：`top_journal_v3/reports/p1_angle_perturb_dose_response.csv` 和 `top_journal_v3/reports/p1_reverse_perturb_decoupling.csv`。

| cell | baseline mAP@0.5 | baseline NRC | Delta mAP@0.5 at 30deg | Delta angle risk at 30deg |
|---|---:|---:|---:|---:|
| DOTA-v1.0/20 | 0.0132 | 1.0221 | -0.0109 | 28.3014 |
| DIOR-R/22 | 0.6964 | 1.1265 | -0.1860 | 26.6927 |
| FAIR1M-v1.0/24 | 0.3650 | 1.5061 | -0.0800 | 26.1873 |
| SODA-A/23 | 0.6119 | 1.6733 | -0.1793 | 25.7744 |
| DIOR-R/3 | 0.7999 | 1.1205 | -0.2623 | 26.5307 |
| DIOR-R/61 | 0.8866 | 1.0500 | -0.3045 | 26.4684 |
| SODA-A/4 | 0.7592 | 1.3807 | -0.2439 | 25.4629 |

Reverse perturbation 对 score、center、scale 进行扰动，并保持 angle prediction 不作为直接扰动对象。该实验显示非角度因素可显著改变 mAP，且对 angle risk 的影响不总是同步。例如 score_noise 改变 detection-score NRC，但不改变 angle error distribution；center_shift 会通过重新匹配改变样本构成。这说明不能把 score 扰动造成的 NRC 变化误写成 angle reliability 本身变化。

同数据集配对挖掘在 DIOR-R 内找到 mAP 与 NRC 差异不同步的 candidate pair，例如 DIOR-R/22 vs DIOR-R/61 的 delta_mAP50=0.1902、delta_NRC=0.0765。这是 existence-style evidence，但不足以作为强 headline。

图2 的理论 IoU 曲线展示共中心矩形在不同 aspect ratio 下旋转后的 IoU。共中心正方形旋转 45 degrees 时 IoU 仍约 0.707，高于 0.5，说明 mAP@0.5 对 near-square 角度错误存在结构性弱敏感区；但真实数据中 elongated 与 matching 机制会使 mAP 对角度也较敏感。因此，P1 的正式结论为：mAP 未充分刻画 orientation reliability，但构造性解耦证据仅部分成立。

## 6. P2：Conformal Orientation Risk Control

P2 是本文主贡献。它不提出新的 selection score，而是将 conformal risk control 作为阈值与保证层套在 orientation reliability score 外部。Within-cell 设置中，D_cal 和 D_audit 来自同一 cell 且 frozen split 互斥；D_cal 用于选择阈值，D_audit 用于报告 empirical risk、coverage、abstention rate 和 violation rate。

目标风险设为 alpha=15 degrees，confidence=0.90。七个关键 cell 的 audit violation rate 均为 0，coverage 约为 0.93-0.95。该结果支持 P2 pass：在 exchangeability / 同分布假设下，within-cell conformal orientation risk control 可以给出有限样本语义的风险控制。

表3 P2 conformal within-cell results。数据路径：`top_journal_v3/reports/conformal_within_cell_risk_control.csv`。

| cell | alpha | empirical risk | coverage | abstention | violation | audit n |
|---|---:|---:|---:|---:|---:|---:|
| DOTA-v1.0/20 | 15.0 | 1.3941 | 0.9321 | 0.0679 | 0.0000 | 280 |
| DIOR-R/22 | 15.0 | 4.6681 | 0.9437 | 0.0563 | 0.0000 | 15466 |
| FAIR1M-v1.0/24 | 15.0 | 4.6945 | 0.9496 | 0.0504 | 0.0000 | 26108 |
| SODA-A/23 | 15.0 | 5.0777 | 0.9475 | 0.0525 | 0.0000 | 157586 |
| DIOR-R/3 | 15.0 | 4.4872 | 0.9445 | 0.0555 | 0.0000 | 16743 |
| DIOR-R/61 | 15.0 | 4.1538 | 0.9412 | 0.0588 | 0.0000 | 17033 |
| SODA-A/4 | 15.0 | 5.0303 | 0.9493 | 0.0507 | 0.0000 | 192250 |

Shift audit 将 source cell 上的 threshold 迁移到 target cell，报告 coverage、empirical risk 和 violation degradation。该部分不承诺严格 conformal guarantee。表4 只作为审计表，而不是理论保证表。

表4 shift audit。数据路径：`top_journal_v3/reports/conformal_shift_violation_audit.csv`。表中字段包括 source_cell、target_cell、threshold、empirical_risk、coverage、violation_rate、strict_shift_guarantee_claimed=False。

P2 的科学意义在于：即使 benchmark 发现 detector score 不总能可靠排序角度风险，也可以在已定义的 calibration/audit 协议下给出风险可控的选择性朝向预测。这是本文在 053 真实证据中最稳的正贡献。

## 7. P3：PSC 机制测试

P3 检查 PSC 机制线是否值得进入重训干预。本轮只使用三项低成本测试，不启动 PSC / CSL / DCL / regression 多 seed 重训矩阵。

三项测试包括：DOTA #20 phase_mod negative control、phase_mod 高分位 angle-error aliasing histogram、class / size / aspect ratio / dataset confounding check。所有测试使用 052 per-matched phase_mod full table，包括 DOTA #20。

表5 P3 mechanism tests。数据路径：`top_journal_v3/reports/psc_dota20_phase_mod.csv`、`top_journal_v3/reports/psc_phase_mod_aliasing_hist.csv`、`top_journal_v3/reports/psc_phase_mod_confounding_check.csv`。

| test | evidence | decision |
|---|---|---|
| DOTA #20 phase_mod negative control | DOTA #20 high-minus-low error=0.7186, Spearman=-0.0127 | not supportive |
| Aliasing fingerprint | only one of three free tests supports mechanism line | partial |
| Confounding check | mechanism signal not sufficiently clean across strata | partial / boundary |

总体裁决：P3/P4 partial 中的 P3 为 partial，机制支持测试 1/3 通过。不足以申请 PSC 重训矩阵。PSC 只能写成 mechanism candidate / case study，不能写成机制已被证明，也不能写成 P3 方法成功。

## 8. P4：强不确定性基线

P4 的目标是检验 geometry-aware selector 是否只是打赢弱 baseline。本轮使用 052 TTA circular variance full table，角度方差按 pi 周期变量计算：先映射 `theta -> 2theta`，再计算 circular variance。禁止使用 naive linear standard deviation 作为正式 baseline。

可用 baseline 包括 score-only、geometry-aware selector 和 TTA circular variance。MC dropout、checkpoint ensemble、native entropy / angle quality、GWD/KLD distribution uncertainty 因无 verified 052 real artifacts，报告为 unavailable，不伪造。

表6 P4 uncertainty baselines。数据路径：`top_journal_v3/reports/uncertainty_baselines_nrc.csv`。

| baseline | available | circular statistics | mean NRC summary |
|---|---|---|---|
| score-only | yes | no | detector confidence baseline |
| geometry-aware selector | yes | no | mean NRC=0.9579 |
| TTA circular variance | yes | yes, theta -> 2theta | mean NRC=0.9478 |
| MC dropout | no | n/a | no verified 052 artifact |
| checkpoint ensemble | no | n/a | no verified 052 artifact |
| native entropy / angle quality | no | n/a | no verified 052 artifact |
| GWD/KLD uncertainty | no | n/a | no verified 052 artifact |

结果为 P4 partial。Geometry-aware selector 未稳定打赢 TTA circular variance，因此本文不能声称 selector 优于所有强不确定性 baseline。P4 作为边界结果保留，提醒后续工作必须使用圆统计处理角度方差。

## 9. P5：下游任务

P5 只做一个低成本下游任务：angle-induced rIoU drop 降低。任务使用 052 full real matched predictions，风险定义为 `1 - matched rIoU`，比较 score-only、size-linear 和 geometry selector 在 coverage=0.5/0.7/0.9 下的 downstream risk。

表7 P5 downstream task。数据路径：`top_journal_v3/reports/downstream_selective_orientation.csv`。

| comparison | result |
|---|---|
| geometry vs score-only | mean risk improvement=-0.0018 |
| geometry vs size-linear | mean risk improvement=-0.0016 |
| proxy status | uses_real_matched_predictions=True; is_proxy=False |
| decision | P5 fail |

该结果不能包装为 downstream utility proof。正确结论是：在当前 angle-induced rIoU drop 任务中，selector 未显示稳定下游收益。未来需要更贴近应用成本的任务，例如 heading-sensitive navigation、crop alignment 或 class-specific orientation filtering。

## 10. 讨论

为什么强主张收缩。053 真实证据并没有支持 broader strong claim：P1 partial，P3/P4 partial，P5 fail。将这些结果包装成成功会损害论文可信度。收缩后的论文强调 benchmark、风险定义、真实 artifact 复现和 P2 conformal risk control。

为什么 P2 是保留贡献。P2 的成立不依赖 PSC 机制解释，不依赖 selector 稳定优于 TTA，也不依赖下游任务成功。它只要求 frozen D_cal / D_audit、within-cell exchangeability 和明确风险定义。七个关键 cell 的 empirical risk 均低于 alpha=15 degrees，violation rate 为 0，构成当前最稳正证据。

为什么 P3/P4/P5 仍有价值。P3 partial 阻止过早启动昂贵重训；P4 partial 说明 TTA circular variance 是强 baseline；P5 fail 防止指标收益被直接外推到下游应用。这些负结果构成 claim boundary，是 benchmark 论文的重要组成部分。

DOTA #20 不是 validation。DOTA #20 的作用是 Track A phase_mod negative control 和真实 PSC cell 证据，不是公开 leaderboard 对齐，不是 DOTA test claim。

为什么不继续堆 full matrix。当前问题不是覆盖面不足，而是核心 claim 边界已经清楚。补更多 cell 可能改善统计外观，但不能把 partial/fail 变成 pass。继续扩实验会偏离收缩版论文定位。

为什么不追公开 mAP。公开 DOTA 数字多使用 trainval/test 协议，本文使用 train/val 自跑协议，目的不是刷新 detector performance，而是分析 orientation reliability。

未来如何继续。后续可在三个方向推进：一是设计更贴合应用的下游任务；二是研究 shift-aware conformal risk control；三是在监督批准下重新设计 PSC 机制干预，而不是从 partial 机制证据直接启动大矩阵。

## 11. 局限性

本文存在以下局限：

- P1 partial：构造性解耦只得到部分支持，不能写成强解耦。
- P3 partial：PSC phase_mod 免费测试不足以证明机制线，也不足以启动重训矩阵。
- P4 partial：geometry-aware selector 未稳定打赢 TTA circular variance。
- P5 fail：当前下游 rIoU-drop 任务没有显示稳定收益。
- Non-DOTA exploratory：部分非 DOTA 结果属于 exploratory / audit 口径，不能改写为 formal。
- 本文不是完整项目结案，不覆盖所有 detector/dataset 组合。
- 本文不是检测器最优性能论文，不追 DOTA public mAP。
- 本文没有证明 deployable final method。
- 本文没有证明 PSC mechanism。
- 本文没有证明 downstream utility。

## 12. 结论

本文建立了面向旋转目标检测的 orientation reliability 测量与风险控制框架。真实 artifact 复跑显示，mAP 未充分刻画朝向可靠性，但 P1 构造性解耦证据仅为 partial；PSC 机制、强不确定性比较和下游任务也分别停留在 partial 或 fail。最稳的正贡献是 within-cell conformal orientation risk control：在 frozen D_cal / D_audit 和 052 full real matched tables 上，conformal threshold layer 以明确 coverage 和 violation rate 控制选中朝向预测的风险。

因此，本文的适当定位不是强方法论文，而是 orientation reliability benchmark + conformal risk control。跨域保证、机制证明和下游实用性仍需后续研究。

## 图表占位

图1 研究问题示意。图注：展示 mAP、angle error、risk-coverage 和 conformal risk control 的关系；强调本文不声称 NRC 与 mAP 严格独立。数据路径：conceptual schematic，无新增实验数据。

图2 IoU(delta theta; aspect ratio) 理论曲线。图注：展示共中心矩形在不同 aspect ratio 下旋转后的 IoU；标出 square 45 degrees IoU approximately 0.707。数据路径：`top_journal_v3/figures/iou_delta_theta_aspect_ratio_curve.csv`。

图3 angle perturb dose-response。图注：展示 epsilon=0/5/15/30 degrees 下 mAP@0.5、AP75、NRC、AURC、Risk@70/Risk@90 和分层 risk 的变化；结论为 P1 partial。数据路径：`top_journal_v3/reports/p1_angle_perturb_dose_response.csv`。

图4 conformal risk control coverage/violation。图注：展示 seven cells 的 coverage、abstention rate、empirical risk 和 violation rate；结论为 P2 pass。数据路径：`top_journal_v3/reports/conformal_within_cell_risk_control.csv`。

图5 shift audit violation degradation。图注：展示 source threshold 迁移到 target cell 后的 empirical risk 和 coverage；图中必须标注 no strict shift guarantee。数据路径：`top_journal_v3/reports/conformal_shift_violation_audit.csv`。

图6 PSC mechanism tests summary。图注：展示 DOTA #20、DIOR #22、FAIR1M #24、SODA #23 的 phase_mod high/low error 与 confounding check；结论为 P3 partial。数据路径：`top_journal_v3/reports/psc_dota20_phase_mod.csv`、`top_journal_v3/reports/psc_phase_mod_aliasing_hist.csv`、`top_journal_v3/reports/psc_phase_mod_confounding_check.csv`。

图7 TTA circular uncertainty baseline。图注：展示 score-only、geometry-aware selector、TTA circular variance 的 NRC/AURC/Risk@k；标注 theta -> 2theta circular statistics。数据路径：`top_journal_v3/reports/uncertainty_baselines_nrc.csv`。

图8 downstream rIoU drop negative result。图注：展示 score-only、size-linear、geometry selector 在 coverage=0.5/0.7/0.9 下的 downstream risk；结论为 P5 fail。数据路径：`top_journal_v3/reports/downstream_selective_orientation.csv`。

## 正式表格清单

表1 数据集与 real artifact coverage：见第 4 节。

表2 P1 perturbation summary：见第 5 节。

表3 P2 conformal within-cell results：见第 6 节。

表4 shift audit：见第 6 节，完整数据在 `top_journal_v3/reports/conformal_shift_violation_audit.csv`。

表5 P3 mechanism tests：见第 7 节。

表6 P4 uncertainty baselines：见第 8 节。

表7 P5 downstream task：见第 9 节。

表8 final claim ledger。

| claim type | statement | status |
|---|---|---|
| allowed | within-cell conformal orientation risk control | supported |
| allowed | orientation reliability benchmark / analysis | supported with scope |
| qualified | P1 construct validity | partial |
| qualified | shift audit | degradation report only |
| forbidden | P3 as validated method | remove |
| forbidden | PSC as proven mechanism | remove |
| forbidden | downstream utility as proven | remove |
| forbidden | NRC and mAP as strictly independent | remove |
| forbidden | full project completion or detector leaderboard claim | remove |

## 附录 A：Artifact manifest

主 manifest：`outputs/persistent_artifacts/manifest_052.json`。关键目录：`outputs/persistent_artifacts/orientbench_real_052/`。论文数据表：`top_journal_v3/reports/`。052 verifier：`top_journal_v3/scripts/verify_real_dump_matched_tables_052.py`。053 verifier：`top_journal_v3/scripts/verify_real_evidence_p1_p5_rerun_053.py`。

## 附录 B：D_cal / D_audit

D_cal / D_audit 使用 frozen split，不修改、不重新采样。P2 within-cell 保证依赖 D_cal 与 D_audit 图像级互斥及同分布假设。任何跨 cell 迁移都只写 audit。

## 附录 C：Metric definitions

附录 C 收录 angle error、aspect ratio bins、near-square/well-defined region、risk-coverage、NRC-AUC、AURC、Risk@70/Risk@90、mAP@0.5、AP75 的数学定义。

## 附录 D：Conformal details

附录 D 说明 conformal threshold 的计算、calibration risk、finite-sample bound radius、coverage 和 violation rate。重点说明 conformal 是 guarantee layer，不是 score。

## 附录 E：Negative results

附录 E 汇总 P1 partial、P3 partial、P4 partial、P5 fail，并解释为何这些结果要求收缩 claim。

## 附录 F：Forbidden claims

附录 F 放置 forbidden claims 和 claim ledger。正文不重复治理术语，只保留 scientific scope 和 evidence boundary。

## 附录 G：Reproducibility checklist

附录 G 包含 artifact 路径、sha256、生成脚本、verifier、pytest、git 大文件检查、未修改 thresholds.yaml / D_cal / D_audit 的记录。054 不使用 GPU，不训练 detector，不新增实验。
