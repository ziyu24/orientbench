# OrientBench — 项目总进展报告（合作者版）

> 面向合作者的进展汇报。可直接阅读。所有数字来自 `final_matrix_summary` / metrics 报告，非凭记忆。
> git tag `orientbench-current-scope-final` · thresholds.yaml sha256 `b7c4e649…` 未变。

---

## 1. 项目当前结论

- **current approved scope 完成 = 是（current_approved_scope_complete=true）。**
- **full project 完成 = 否（full_project_complete=false）。**
- 一句话：当前已批准范围（DOTA formal scope + cross-dataset exploratory matrix）已**成功冻结交付**；完整项目（全 9-detector × all-dataset 矩阵 + genuine 多视角 C1 + 跨 host A4 因果）仍为 **partial**，剩余项为有证据的 coverage blocker，**非失败实验**。

---

## 2. 执行范围

本次交付 = **OrientBench current approved scope**：
- ✅ DOTA formal scope（D2 + host orientation + C1 augmentation-view + A4 same-host，已冻结阈值 + D_audit formal_pass）。
- ✅ cross-dataset exploratory matrix（6 datasets × 多 detector，全 exploratory）。
- ❌ 不包括 genuine physical multi-view C1（单视图数据集，无多物理视角采集）。
- ❌ 不包括 cross-host A4 causal（仅 same-host 统计归因）。
- ❌ 不包括 full 9-detector × all-dataset 完整矩阵。

---

## 3. 核心 formal 成果（DOTA frozen scope）

| 项 | 结果 |
|---|---|
| DOTA D2 partial formal gate | **passed**（认证的是**协议/阈值冻结/split 互斥/metric 可计算**，**不是**要求每个 detector NRC≤1.0）。组成 detector：#1 orcnn / #20 psc / #32 rtmdet（D2-audit NRC 0.67 / 0.74 / 0.62，near-square masked）。**注：#32 rtmdet 是 gate 组成项但仅 dcal-subset 推理，未进入第 4/5 节 full-val summary table**。NRC↔mAP 独立性见构造效度分析（§见 scientific_validity_audit，非 DOTA n=3） |
| RHINO host (C1/B) 训练+锁定 | DOTA-v1.0，val **dota/mAP 0.7201** @epoch35；ckpt sha256 **55a90abb…** |
| O2-RTDETR host (A4) 训练+锁定 | DOTA-v1.5，val **dota/mAP 0.6497** @epoch70；ckpt sha256 **3e32fa11…** |
| C1 augmentation-view consistency gate | **formal_pass**（D_audit：view-consistency p90 3.489°≤5.04，DropRate 0.136≤0.184） |
| A4 same-host source-attribution gate | **formal_pass**（D_audit：非 GV source HSIC p≤0.05；score pc≈-0.17/entropy≈+0.16 显著） |
| 阈值冻结 | token 017，D_cal 标定；**thresholds.yaml sha256 b7c4e649…** |
| D_cal / D_audit | 确定性 md5 split，**互斥**；D_audit 仅 holdout，未参与设阈值 |

---

## 4. 数据集与 detector 覆盖（23 real cells / 6 datasets）

| dataset | #det | detectors | formal/exploratory | notes |
|---|---|---|---|---|
| DOTA-v1.0 | 6 | orcnn, psc, rtmdet, lsknet, strip, rhino(+h2rbox weak) | formal-compatible（阈值未改） | 9-archetype 子集；D2/C1 formal |
| DOTA-v1.5 | 4 | orcnn, rtmdet-s, rtmdet-m, o2-rtdetr(A4) | formal-compatible | A4 host formal |
| DIOR-R | 6 | orcnn, psc, rtmdet, lsknet, ars_detr, strip | exploratory | 覆盖最全；ARS-DETR/Strip 解锁 |
| FAIR1M-v1.0 | 3 | orcnn, psc, lsknet | exploratory | full-val |
| SODA-A | 3 | orcnn, psc, lsknet | exploratory | full-val；dataset present |
| HRSC2016 | 1 | lsknet | exploratory | angle resolved_with_evidence |

---

## 5. 关键 exploratory metrics（NRC-AUC / median orient error°，near-square masked）

| dataset | detector | NRC-AUC | med_err° | status |
|---|---|---|---|---|
| DIOR-R | oriented_rcnn | 0.5212 | 1.062 | done |
| DIOR-R | psc | 0.5494 | 0.725 | done |
| DIOR-R | rtmdet_s | 0.4274 | 1.116 | done |
| DIOR-R | lsknet | 0.5294 | 1.102 | done |
| DIOR-R | strip_rcnn | 0.5061 | 1.181 | done |
| DIOR-R | ars_detr | 0.9985 | 4.264 | done（ARS-DETR DIOR 弱模型 mAP 0.4158） |
| FAIR1M-v1.0 | oriented_rcnn | 0.8450 | 1.900 | done |
| FAIR1M-v1.0 | psc | 1.0825 | 1.724 | done（NRC>1：选择弱于 random） |
| FAIR1M-v1.0 | lsknet | 0.8256 | 1.800 | done |
| SODA-A | oriented_rcnn | 0.8323 | 1.731 | done |
| SODA-A | psc | 1.2596 | 1.441 | done（NRC>1） |
| SODA-A | lsknet | 0.7632 | 1.545 | done |
| HRSC2016 | lsknet | 0.8068 | 5.875 | done（angle resolved） |
| DOTA-v1.0 | oriented_rcnn #1 | 0.5699 | 0.878 | formal-compatible |
| DOTA-v1.0 | rhino host | 0.7710 | 1.520 | formal-compatible (locked) |
| DOTA-v1.0 | psc #20 | 1.0574 | 1.004 | formal-compatible（NRC>1） |
| DOTA-v1.0 | strip #35 | 0.7167 | 1.499 | formal-compatible |
| DOTA-v1.5 | o2-rtdetr (A4) | 0.5515 | 1.771 | formal-compatible (locked) |
| DOTA-v1.5 | orcnn #2 | 0.6943 | 1.803 | formal-compatible |

> 观察：PSC angle-coder 在 DOTA/FAIR1M/SODA 多处 **NRC>1.0**（selection score 对朝向风险排序弱于 random）——跨数据集一致模式，值得后续分析。

---

## 6. 重要工程修复

- **GT discovery 修正**：021 误判 DIOR/FAIR1M 无 OBB GT（搜错扩展名/路径）；022 递归重扫找到真实 OBB（DIOR robndbox XML、FAIR1M points XML、SODA dota_format）。
- **SODA-A present**：纠正为 present + parser ready（dota_format_tiled_ss）。
- **scratch storage policy**：大文件（pth/pkl/schema）全入 `/dev/shm`，project 仅 manifest/sha256/metrics；git 0 大文件。
- **ARS-DETR env 解锁**：隔离 conda env（torch1.9/mmcv-full1.5.0/mmrotate0.1.0/e2cnn）；DIOR cross-dataset 跑通；独立 archetype，**非 RHINO 替代**。
- **Strip DIOR evaluator 修复**：`test_evaluator._delete_+DumpDetResults` 绕开 DOTAMetric 空-GT crash → 解锁。
- **HRSC angle resolved**：hrsc.py mbox_ang 直接作 le90 + mAP 0.906 双证据。
- **schema 统一**：17 字段，is_synthetic/not_detector_output guard。
- **verifier 90-101**：每轮只读验证，全部 VERIFIED。
- **git release/tag**：tag `orientbench-current-scope-final`。

---

## 7. Blockers 与边界（均为 coverage blocker，非失败实验）

| blocker | status | evidence | impact | next action |
|---|---|---|---|---|
| point2rbox ted.pth | blocked_upstream_artifact_unavailable_final | modelscope 空 / github 9B / hf 401 / openmmlab 404 | point2rbox weak_nonformal 不可跑 | 待上游恢复 |
| ARS-DETR FAIR1M/SODA | blocked_class_mapping_final | KeyError 空格类名 / config CLASSES 不匹配 | 2 cell 缺 | class-name adapter |
| Strip FAIR1M/SODA | no_baseline | pth_data 无对应 ckpt | 不可跑 | — |
| Strip/ARS-DETR HRSC | pattern_available | HRSC native farm 未跑（budget） | HRSC 多 detector 少 | 复用 _hrsc_root farm |
| genuine physical multi-view C1 | out_of_scope | 数据集单视图，无多物理视角 | C1 仅 augmentation-view | 新数据采集 |
| cross-host A4 causal | out_of_scope | 需多 host 因果设计 | A4 仅 same-host | P2/P3 + 批准 |
| full 9-detector × all-dataset | incomplete | partial matrix | 矩阵未满 | 逐 cell 补 |

---

## 8. 可宣称结论（allowed）

- DOTA 范围内 **D2 / host orientation / C1 augmentation-view consistency / A4 same-host source-attribution** 已冻结阈值并通过 D_audit formal gate。
- **6 datasets × 多 detector** 的 exploratory orientation-reliability（NRC/Risk/median error）已真实测量（23 cells）。
- Host checkpoints 已锁定 + 哈希记录（RHINO 55a90abb / O2-RTDETR 3e32fa11）。
- ARS-DETR 为**独立 archetype**，已隔离环境跑通 DIOR cross-dataset。
- current approved scope 完成；full project partial。

## 9. 禁止宣称结论（forbidden）

- ❌ full project complete。
- ❌ all datasets covered。
- ❌ 9-detector matrix complete。
- ❌ C1 genuine physical multi-view solved。
- ❌ A4 cross-host causal proved。
- ❌ ARS-DETR substituted RHINO。
- ❌ 任何 non-DOTA cell 为 formal gate passed。

---

## 10. 产物与路径

- 主报告（本文）：`docs/orientbench_project_progress_report.md`
- release：`outputs/releases/orientbench_final_current_scope/`
- final reports：`outputs/bench_core/reports/final_orientbench_report.md`、`final_orientbench_summary.csv`
- coverage matrix：`outputs/bench_core/reports/final_coverage_matrix.{md,csv}`
- claim ledger：`outputs/bench_core/reports/final_claim_ledger.md`
- reproducibility guide：`outputs/bench_core/reports/final_reproducibility_guide.md`
- artifact manifest：`outputs/bench_core/reports/final_artifact_manifest.json`
- thresholds：`configs/thresholds.yaml`（sha256 `b7c4e649…` FROZEN）
- scratch predictions（raw+schema，**非持久**）：`/dev/shm/cqc/orientbench/predictions/`
- git head：`bfdac5f4…` · git tag：`orientbench-current-scope-final`

---

## 11. 验证状态

- pytest：**264 passed**。
- verifier **90-101 全部 VERIFIED**（101_verify_final_release_031 21/21）。
- thresholds.yaml **未变**（b7c4e649…）。
- git large files：**0**；project pred schema >1MB：**0**。
- ⚠️ scratch（/dev/shm）**非持久**：raw/schema 重启后丢失，复现需按 reproducibility guide 重跑 inference；project 仅留 manifest+sha256+metrics。

---

## 12. 建议下一步

**A. 若接受当前阶段（推荐）**：停止实验，进入论文 / 报告 / 合作者评审。current scope 已冻结、可交付、可复现入口完整。

**B. 若继续扩展（最小行动）**：
1. ARS-DETR FAIR1M/SODA：写 class-name adapter（config CLASSES ↔ GT 名对齐，underscore 映射）。
2. Strip/ARS-DETR HRSC：复用 HRSC native farm（pattern 已验证）。
3. point2rbox：待上游恢复 ted.pth（仍 weak_nonformal）。
4. genuine multi-view C1 / cross-host A4：需新数据 + P2/P3 机制 + 监督员批准。
