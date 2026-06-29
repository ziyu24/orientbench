# OrientBench：面向旋转目标检测的朝向可靠性诊断基准

> 合作者审稿稿（v3，中文）。无新增训练/GPU 实验。DOTA 采用 train 训练 / val 验证自跑协议（非 trainval/test，不追公开 mAP）。thresholds 冻结 sha256 b7c4e649，D_cal/D_audit split 未变。
> 所有 exploratory 结论已标注；formal 仅限 DOTA frozen scope。核心结论凡 pending 均标 pending。

## 摘要

旋转目标检测（OBB）的主流评测以 mAP 为核心，难以刻画**朝向可靠性**——即检测器输出的朝向何时可信、何时灾难性失配。本文提出 **OrientBench**，一个面向朝向可靠性的诊断基准与协议：定义 GV-obliquity、归一化风险覆盖曲线下面积（NRC-AUC）、Risk@70/Risk@90、near-square 掩码与 aspect-ratio 退化曲线，并将 selection score 分为 intrinsic / detection-score proxy / post-hoc upper-bound 三轨以避免横向不可比。我们在 **6 个数据集 × 多个检测器、共 23 个真实评测单元（cells）**上系统测量朝向可靠性。主要发现：（1）在该 23-cell 异质矩阵上**未检测到 NRC 与 mAP 的显著相关**（Spearman -0.05，95% CI [-0.49, 0.48]），NRC 提供了不同于 accuracy 的可靠性信号（受 n=23 限制，不主张严格独立）；（2）存在显著的 **aspect-ratio reliability cliff**——朝向误差 p99 随长宽比趋近 1（近方形）从约 8–10° 升至约 84–90°，源于近方形目标朝向的**不适定性**（非检测器灾难性失败）；（3）**PSC（相位角度编码）检测器在以 detection-score 为 selection 时出现反校准**（NRC>1），经 bootstrap 在 **FAIR1M [1.03,1.13]、SODA [1.24,1.28]** 上显著，而 DOTA 掩码后为 0.84（不显著）。DOTA 范围内的 formal 协议（D2 partial gate、RHINO/O2-RTDETR host、C1 augmentation-view、A4 same-host）已冻结并通过 holdout 审计。本工作为 benchmark + diagnostic 定位；full project 未完成，非 DOTA 结果均为 exploratory。

---

## 1. 引言

mAP 衡量"框是否检出且定位准"，但对**朝向**只给出聚合误差，无法回答两个可靠性问题：在何种几何条件下朝向不可信？检测器的置信能否用于挑出朝向可靠的预测（selective prediction）？这在遥感密集小目标、近方形目标上尤为关键。

本文不追 DOTA 公开 test mAP，采用 **train 训练 / val 验证**的自跑协议；val mAP 低于公开论文属正常，且与本文命题无关——本文关注 **orientation reliability diagnostic**，而非精度排名。

贡献：（i）一套 near-square / aspect-ratio aware 的朝向可靠性度量与协议；（ii）NRC 与 mAP 的构造效度分析；（iii）aspect-ratio reliability cliff 的实证；（iv）PSC selection 反校准的跨数据集候选发现与机制门控设计。

## 2. 相关工作

旋转目标检测与角度编码（DCL/CSL/PSC 等）[R1]；遥感 OBB 基准（DOTA/DIOR-R/FAIR1M/SODA-A/HRSC）[R2]；不确定性与可靠性评测、selective prediction、risk-coverage [R3]；校准与 reliability diagram [R4]。本文区别：聚焦旋转**朝向**的可靠性与退化几何，而非检测精度或一般分类校准。（引用为占位 [R*]，待补 bib。）

## 3. Benchmark 与协议

- **数据集**：DOTA-v1.0、DOTA-v1.5、DIOR-R、FAIR1M-v1.0、SODA-A、HRSC2016。
- **检测器**：oriented R-CNN、rotated RetinaNet+PSC、rotated RTMDet、LSKNet、Strip R-CNN、h2rbox-v2、RHINO（rotated DETR）、O2-RTDETR（hybrid encoder）、ARS-DETR（独立 archetype，**非 RHINO 替代**）。
- **DOTA 口径**：train 训练 / val 验证（非 trainval/test）。
- **prediction schema**：统一 17 字段（含 obb、score、angle_version=le90、is_synthetic=false、not_detector_output=false、source/converter version、sha256）。
- **数据划分**：确定性 md5(image_id) → D_cal / D_audit，二者**互斥**；D_audit 仅 holdout，不参与设阈值。
- **formal vs exploratory**：formal 仅限 DOTA frozen scope；非 DOTA 一律 exploratory。
- **度量**：朝向误差 = OBB π-周期最短距离 `|((Δθ+π/2) mod π) − π/2|`∈[0,90°]（含 canonical long-side 解决 (w,h,θ)↔(h,w,θ+90°) 对称）；NRC-AUC（selection score 对朝向风险的排序质量，=1 等价随机，>1 反校准）；Risk@70/Risk@90；near-square 掩码（max/min 边长比 ≤1.10）；aspect-ratio 退化曲线。
- **selection score 三轨**：Track A intrinsic（检测器原生角度不确定性）；Track B detection-score proxy（所有检测器可算，用于公平横比，本文主口径）；Track C post-hoc upper-bound（D_cal 学 selector，D_audit 验证，标 upper bound）。

## 4. 数据与覆盖

**表 1（dataset/detector coverage）**——23 real cells / 6 datasets：

| dataset | #detectors | detectors | formal/exploratory | notes |
|---|---|---|---|---|
| DOTA-v1.0 | 6 | orcnn, psc, rtmdet, lsknet, strip, rhino（+h2rbox weak） | formal-compatible（阈值未改） | D2/C1 formal |
| DOTA-v1.5 | 4 | orcnn, rtmdet-s, rtmdet-m, o2-rtdetr(A4) | formal-compatible | A4 host formal |
| DIOR-R | 6 | orcnn, psc, rtmdet, lsknet, ars_detr, strip | exploratory | 覆盖最全 |
| FAIR1M-v1.0 | 3 | orcnn, psc, lsknet | exploratory | full-val |
| SODA-A | 3 | orcnn, psc, lsknet | exploratory | small-object |
| HRSC2016 | 1 | lsknet | exploratory | angle resolved_with_evidence |

## 5. 科学有效性分析（NRC vs mAP）

**表 3（NRC construct validity，n=23）**：

| 量 | 值 | 95% CI (bootstrap) |
|---|---|---|
| Spearman(NRC, mAP) | -0.046 (p=0.84) | [-0.49, 0.48] |
| Pearson(NRC, mAP) | -0.260 (p=0.23) | — |
| partial(NRC,mAP \| dataset+family) | -0.005（df=7） | [-1, 1]（退化，under-powered） |
| Spearman(NRC, median err) | 0.40 | — |
| mean rank distance NRC vs mAP | 7.83/23 | — |

**措辞（最终）**：在当前 23-cell 异质矩阵上，**未检测到 NRC 与 mAP 的显著相关**；NRC 提供了**不同于 accuracy 的 reliability signal**。受 n=23 限制且控制 dataset+family 后自由度仅 7（偏相关估计 under-powered），**不主张 NRC 完全独立于 mAP**。NRC 与朝向中位误差中度相关（0.40），符合"部分反映朝向误差"。最强单点反例为 PSC（见 §7）。

## 6. 尾部风险与 reliability cliff

**表（masked/unmasked 角度误差，°）**：

| 分组 | p90 | p95 | p99 |
|---|---|---|---|
| masked（well-defined，去 near-square） | 4–6 | 5–8 | **10–16** |
| unmasked（含 near-square） | — | — | **88–90**（near-square 主导） |

**关键澄清（不得误读）**：unmasked p99≈90° **不能**直接写成 detector catastrophic failure。角度误差计算正确（π-周期，最大 90°，无 bug）；90° 尾部来自 **near-square / aspect-ratio 退化**——长宽比趋近 1 时"哪条是长边"不适定，少数歧义目标朝向翻转 90°（该区 median 仍小，约 1–2°）。near-square 既是退化/歧义区，也可能是**任务核心难点**；masked summary 仅代表 **well-defined orientation region**。主文以 aspect-ratio 曲线解释。well-defined region 的 masked p99（10–16°）是**真实非平凡尾部**。

## 7. PSC 反校准机制候选

**表 4（PSC preflight，masked well-defined region，bootstrap CI）**：

| dataset | PSC NRC | 95% CI | 显著>1 | 同数据集对照（orcnn / lsknet / rtmdet） |
|---|---|---|---|---|
| FAIR1M-v1.0 | 1.083 | [1.027, 1.134] | **是** | 0.845 / 0.826 / — |
| SODA-A | 1.260 | [1.238, 1.281] | **是** | 0.832 / 0.763 / — |
| DOTA-v1.0 | 0.840 | [0.787, 0.900] | 否 | 0.570 / 0.714 / — |
| DIOR-R | 0.549 | [0.529, 0.572] | 否 | 0.521 / 0.529 / 0.427 |

- **发现（克制）**：以 detection-score 作 selection 时，**PSC 在 FAIR1M、SODA 上反校准且 bootstrap 显著**（CI 下界>1），是同数据集唯一 NRC>1 的 family；DOTA 掩码后为 0.84（**不显著**，此前 unmasked 的 1.06 为 near-square 驱动）；DIOR 不反校准。
- **只能说**：detection-score 作 orientation selection 时在 PSC family（2/4 数据集显著）反校准（Track B）。**不能说** PSC angle head 本身反校准——需 Track A intrinsic 或 angle-head control。
- **机制门控**：若 Track A（PSC 原生角度不确定性）仍 NRC>1，机制线（angle-coder 反校准）成立；若 Track A 正常而仅 Track B 异常，则降级为 **score-proxy mismatch**（detection-score 不适合作 PSC 的 orientation selection）。

## 8. Formal 结果与 exploratory 结果

**Formal（仅 DOTA frozen scope）**：
- D2 partial formal gate（detector #1/#20/#32，D2-audit NRC 0.67/0.74/0.62；认证协议/阈值冻结/split 互斥/metric 可计算，**非**要求每 detector NRC≤1）。
- RHINO host（C1/B，DOTA-v1.0，val mAP 0.7201，sha256 55a90abb…）。
- O2-RTDETR host（A4，DOTA-v1.5，val mAP 0.6497，sha256 3e32fa11…）。
- C1 augmentation-view consistency：formal_pass（D_audit）。
- A4 same-host source-attribution：formal_pass（D_audit）。
- thresholds.yaml sha256 b7c4e649…；D_cal/D_audit 互斥。

**Exploratory（cross-dataset）**：
- DIOR-R/FAIR1M/SODA-A/HRSC：见 §4–§7。
- ARS-DETR：独立 archetype，DIOR cross-dataset 解锁（NRC 0.999），**非 RHINO**。
- Strip R-CNN：DIOR cross-dataset 解锁（NRC 0.506）。
- point2rbox：上游 ted.pth 不可用，blocked。

## 9. 局限性

- **非 full project complete**；非 full 9-detector × all-dataset 完整矩阵。
- 非 DOTA 结果**均为 exploratory**，未冻结阈值。
- C1 **非** genuine physical multi-view（仅 augmentation-view，单视图数据集）。
- A4 **非** cross-host causal（仅 same-host 统计归因）。
- point2rbox 上游 artifact 不可用；ARS-DETR FAIR1M/SODA 因类名映射 blocked。
- P2/C1 不独立成文，作为 P3 组件/消融/负结果保留。
- P3（reliability-aware 方法线）需等待 cliff 与 PSC 机制门控实验。
- NRC 严格独立性受 n=23 限制；PSC 机制归因 pending control experiment。

## 10. 后续工作（最小行动）

- **PSC Track A vs Track B control**：提取 PSC 原生角度不确定性（Track A），与 detection-score proxy（Track B）对照；若 Track A 仍反校准，进入 reliability-aware orientation 方法线（P3）；若不支持，则 P1 作为 benchmark/diagnostic 收口，PSC 降级为 score-proxy mismatch。
- P3 是否推进取决于 reliability cliff 与 PSC control 结果。

## 11. 结论

OrientBench 的贡献在于**揭示 accuracy 之外的朝向可靠性问题**：NRC 提供了与 mAP 未检出显著相关的可靠性信号；朝向可靠性随 aspect-ratio 退化呈现断崖；detection-score 作 selection 在 PSC family（FAIR1M/SODA 显著）反校准。当前证据支持本工作作为**基准与诊断**继续推进；机制性方法主张（PSC angle-head 反校准、reliability-aware 方法线）仍需后续门控实验确认。

---

## 附录

### A. 实验配置
- envs：mr_dev1x(mmrotate 1.x)/ai4rs_train/arsdetr(mmrotate 0.1.0)/mr(0.3.4)。GPU 4×A30，inference world_size=4，未改 batch/lr/schedule。详见 final_reproducibility_guide.md。

### B. 数据覆盖表
- 见 §4 表 1 与 outputs/bench_core/reports/final_coverage_matrix.csv。

### C. 关键 cell manifest
- outputs/bench_core/reports/persistent_prediction_manifest_v2.json（8 key cells：DOTA #20/rhino、DIOR 3/22/47/16、FAIR1M 24、SODA 23；sha256+生成命令+can_recompute）。

### D. claim ledger
- outputs/bench_core/reports/p1_claim_ledger_final.md（allowed / pending / forbidden）。

### E. reproducibility
- outputs/bench_core/reports/license_reproducibility_notes.md。⚠️ raw/schema 在 /dev/shm（非持久），key cells 已持久化 outputs/persistent_artifacts/orientbench_v2/（gitignored），可复算。

### F. forbidden claims（以下均为**禁止宣称**，详见 p1_claim_ledger_final.md）
- ❌ 90° p99 = detector catastrophic failure（实为 near-square ill-posedness）。
- ❌ NRC 完全独立于 mAP（n=23 under-powered，不主张）。
- ❌ PSC angle head 已证明反校准（仅 Track B / score-level）。
- ❌ full project complete / all datasets covered / 9-detector matrix complete。
- ❌ C1 genuine physical multi-view solved。
- ❌ A4 cross-host causal proved。
- ❌ ARS-DETR = RHINO；❌ DOTA SOTA。

---

## 图表占位（不画图，给数据/图注）

**图 1 — aspect-ratio reliability cliff**
- 图目的：展示朝向可靠性随 aspect-ratio 退化的断崖。
- 数据：outputs/bench_core/reports/fig1_reliability_cliff_data.csv（per detector × ar-bin：NRC/median/p90/p99）。
- 主要读数：p99 随 ar 1.0→3.0+ 从 ~84-90° 降到 ~5-7°；NRC 在近方形区 ~0.93-0.97、well-defined 区 ~0.47-0.49。
- 支持结论：reliability cliff 真实，need aspect-ratio aware。
- 不支持：detector catastrophic failure。

**图 2 — masked/unmasked 角度误差 CDF**
- 图目的：对比 well-defined 与含 near-square 的误差分布尾部。
- 数据：outputs/bench_core/reports/fig2_angle_error_cdf_data.csv（masked/unmasked 的 p75/p90/p95/p99；完整 CDF 可由 persistent matched arrays 重算）。
- 主要读数：masked p99 10-16°；unmasked p99 88-90°。
- 支持结论：90° 尾部由 near-square 主导。
- 不支持：well-defined region catastrophic failure。

**图 3 — PSC family NRC bar + bootstrap CI**
- 图目的：展示 PSC 反校准（NRC>1）与显著性。
- 数据：outputs/bench_core/reports/fig3_psc_nrc_ci_data.csv（NRC + 95% CI + gt1_significant）。
- 主要读数：FAIR1M PSC 1.08 CI[1.03,1.13]、SODA PSC 1.26 CI[1.24,1.28] 显著>1；DOTA PSC 0.84 不显著；对照 family 均<1。
- 支持结论：PSC detection-score selection 在 FAIR1M/SODA 反校准（Track B）。
- 不支持：PSC angle head 已证明反校准；DOTA PSC 反校准。

**表 1–5**：表 1 coverage（§4）；表 2 formal vs exploratory scope（§8）；表 3 NRC construct validity（§5）；表 4 PSC preflight（§7）；表 5 blockers & claims（p1_claim_ledger_final.md + remaining_blockers）。
