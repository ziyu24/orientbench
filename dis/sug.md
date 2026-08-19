---
schema_version: 2
plan_id: b-r044-jprs-measurement-manuscript-20260818
dispatch_id: orientbench-b-r044-jprs-measurement-manuscript-20260818
initiator: B
business_instruction: "044"
base_sha: 72dfdd8f0060112bec90cfe0302f39d6804fa960
supersedes: b-r038-final-manuscript-20260815
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-18：『给出顶刊的方案，让服务器去执行，开始。』；r043 完成后用户确认『服务器执行完毕。』，授权沿已定顶刊路线继续推进。"
scientific_snapshot:
  primary: 72dfdd8f0060112bec90cfe0302f39d6804fa960
  accepted_positive_core:
    - "六个 full-validation 单元的受控角度扰动：AP50 不变、AP75 显著下降、朝向误差显著增加。"
    - "基于共中心同尺度矩形的角度可辨识性分析、well-defined orientation domain 与 geometry-normalized risk。"
    - "NRC/AURC/risk-coverage 与以完整图像为可交换单位的 finite-sample Learn-Then-Test / Hoeffding-Bentkus 风险控制。"
    - "DIOR-R、FAIR1M、SODA-A、DOTA-v1.0 的跨数据集/检测器证据与 600 目标双人互盲角度标注。"
  mandatory_negative_boundaries:
    - "r034: 旧 geometry selector 的主要翻转由 AR-only 定义性成分解释，方法主张终止。"
    - "r036/r037: Q-SetOD 集合/覆盖迁移路线终止。"
    - "r042: OER/OER-D 八单元均无正 Delta_AUGRC，REJECT_OER_METHOD。"
    - "r043: SAUR Stage A 在 DIOR-R/SODA-A 均发生大幅 AP50/AP75 回退，REJECT_SAUR_METHOD；且执行 gate 实现偏离冻结公式，只能拒绝已执行配置，禁止外推为全类不可能。"
  current_venue_floor: "STRONG_JSTARS_OR_REMOTE_SENSING"
  target_venue: "ISPRS Journal of Photogrammetry and Remote Sensing (JPRS)"
  target_route: "measurement-validity + geometry-aware evaluation + image-level finite-sample orientation-risk control；不声称 deployable selector/fix"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r044-jprs-measurement-manuscript-20260818/SERVER_EXECUTION_REPORT.md
read_set:
  - "整个 Git 跟踪仓库只读；优先使用 docs/paper_A_zh_post_human_073、docs/paper_zh_post_k1k4_068、docs/074_orientation_reliability_AB_split_full_report.md、docs/m4_risk_event_definition.md。"
  - "正式数字仅可来自 Git 跟踪的冻结表、audit bundle、正式 server report 或能由这些对象确定性重算的结果；不得从旧稿文字反抄数字。"
write_set:
  - docs/paper_jprs_r044/**
  - outputs/persistent_artifacts/orientbench_jprs_manuscript_r044_20260818/**
  - audit_bundles/r044/**
  - dis/server_reports/orientbench-b-r044-jprs-measurement-manuscript-20260818/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 0, gpu_hours_max: 0, cpu_core_hours_max: 96}
  wall_time: {seconds_max: 43200}
  data:
    allowed_dataset_ids: ["repository-tracked-evidence", "existing-frozen-orientbench-evidence-readonly"]
    read_bytes_max: 549755813888
    write_bytes_max: 10737418240
  write:
    allowed_paths:
      - docs/paper_jprs_r044/
      - outputs/persistent_artifacts/orientbench_jprs_manuscript_r044_20260818/
      - audit_bundles/r044/
      - dis/server_reports/orientbench-b-r044-jprs-measurement-manuscript-20260818/
      - claude_code_and_supervisor.md
    bytes_max: 10737418240
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
      - https://api.crossref.org/
      - https://doi.org/
      - https://openaccess.thecvf.com/
      - https://ieeexplore.ieee.org/
      - https://www.sciencedirect.com/
conflict_keys:
  - server-execution-slot
  - dis/sug.md
gates:
  - gate_id: G1_EVIDENCE_CLOSURE
    rule: "每个进稿定量 claim 必须有固定 claim_id、正文位置、canonical source path、source row/key、变换、容差和校验结果；禁止 nearest-value matching，全部 PASS 才能完成。"
  - gate_id: G2_SCIENTIFIC_HONESTY
    rule: "正文不得把 r034/r036/r037/r042/r043 的失败路线写成方法贡献、deployable selector 或已解决的 fix；不得宣称 NRC 独立于 mAP、PSC angle head 普遍反校准、DOTA SOTA、全项目完成或 JPRS ready。"
  - gate_id: G3_MANUSCRIPT_COMPLETENESS
    rule: "英文主稿必须形成可送审的完整论文，而非提纲/扩展摘要：题名、摘要、关键词、引言、相关工作、问题与几何、协议与有限样本控制、实验、结果、人工双标、讨论、局限、结论、数据/代码可用性、真实参考文献、图表题注均齐全。"
  - gate_id: G4_INDEPENDENT_VENUE_RED_TEAM
    rule: "成稿后对 novelty、technical soundness、evidence breadth、presentation、JPRS fit 五项各 1-5 分并列出至少 3 条最强拒稿理由；仅当五项均>=4、无致命未闭合 claim 且不存在方法失败包装时，终态才可为 JPRS_SUBMISSION_CANDIDATE，否则必须为 NOT_JPRS_READY。"
early_stop_conditions:
  - "发现 headline 数字无 canonical 证据、来源间不可消解矛盾或 claim checker 不能精确闭合时，输出最小矛盾表并终止，不得用旧稿数字填补。"
  - "触碰任何原始数据集、清白 endpoint、GPU 训练/推理或修改冻结科学产物时立即 failure early stop。"
kill_conditions:
  - "编造作者、单位、基金、致谢、实验、数据、引用元数据或投稿状态。"
  - "将失败 selector/Q-SetOD/OER/SAUR 包装为正方法，或用未完成/未审计结果填正文。"
  - "访问 DOTA-v2.0 val、SODA-A official test 或任何本轮未授权数据。"
  - "写出 write_set、修改治理 owner 文件或覆盖既有冻结产物。"
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: "执行完毕"}
  gated_early_stop: {execution_status: complete, receipt_first_line: "执行完毕"}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  partial: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  protocol_drift: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
---

# r044：JPRS measurement–diagnostic 完整成稿与证据闭合门

## 1. 唯一目标

把 OrientBench 当前仍成立的正证据写成一篇完整英文 JPRS 候选稿，并用可执行 claim checker 与独立红队决定它是否真的达到 JPRS submission-candidate 水平。

本轮不再发明或训练新方法。论文的技术贡献必须来自：

1. **Measurement validity**：用受控角度扰动证明 AP50 在明确几何区域内可以保持不变，而 AP75 与真实朝向误差显著恶化；因此 detection accuracy 不能代替 orientation reliability。
2. **Geometry-aware estimand**：从矩形旋转几何定义角度可辨识性、well-defined domain 与 geometry-normalized severe risk，明确 near-square/symmetry 的适用边界。
3. **Selective orientation-risk protocol**：NRC、AURC 与 risk-coverage 评价任意 confidence score 对角度风险的排序能力，措辞只到“在可比设置内提供 accuracy 之外的 reliability signal”。
4. **Image-level finite-sample control**：以图像而非实例作为可交换单位，用 fixed-sequence Learn-Then-Test 与 Hoeffding-Bentkus 有界损失上界选择阈值，避免实例独立假设造成的过度乐观。
5. **Evidence and human anchor**：跨多个遥感 OBB 数据集/检测器验证，并用 600 个互盲双标目标量化人工方向标签噪声与 5°/10° 风险语义。

标题优先采用：

> **Orientation Reliability in Oriented Object Detection: Geometry-Aware Measurement and Image-Level Risk Control**

可在不改变科学身份的前提下润色标题，但标题不得含 selector、correction、deployable、fix 或 state-of-the-art。

## 2. T1：证据地图与冲突清洗（先于写稿）

生成：

- `docs/paper_jprs_r044/evidence_map.csv`
- `docs/paper_jprs_r044/claim_ledger.csv`
- `docs/paper_jprs_r044/stale_claims_removed.md`

要求：

- 逐项定位 headline 数据的 canonical source；旧稿只是导航，不是数字证据。
- 特别清除当前中文稿中已经过时的“nonlinear geometry selector fixed-size bins 胜出”“PSC intrinsic phase head 已稳定反校准”等表述。
- r043 的公式偏离必须在 evidence map 中记为解释边界；论文最多写“所评估的修复尝试未获得一致增益”，不得写成全类方法不可能。
- DOTA-v1.0 只按本项目 train/val 口径报告，不比较公开 trainval/test mAP。
- 把 formal、audited post-outcome、exploratory、human-study 各类证据身份分开标记。

## 3. T2：完整英文主稿

输出 `docs/paper_jprs_r044/orientation_reliability_jprs.md`。目标是投稿级信息密度，建议 7,500–10,000 英文词；若低于 7,000 词，必须在报告中解释为何仍完整，禁止用空话凑字数。

正文必含：

- Abstract 与 5–7 个 keywords；摘要给出问题、方法、主要定量证据、边界，不含治理术语。
- Introduction：先提出“高 AP 不回答何时角度可信”的遥感应用问题，再给严格贡献清单。
- Related Work：OBB angle representation/periodicity/square-like ambiguity，GWD/KLD/distribution-aware losses，detector calibration/D-ECE，selective prediction/risk-coverage，conformal/finite-sample risk control。不得凭记忆编造字段。
- Geometry and problem formulation：给出 le90/轴向周期误差、共中心矩形角度容忍函数、well-defined domain、GV-obliquity/geometry-normalized event（若 GV-obliquity 没有唯一可回链定义则删除该名称，只保留可证公式）。
- Measurement protocol：完整 matching、eligible population、score direction、NRC/AURC/Risk@coverage、标定/审计划分和 image-level bound。
- Experiments：数据集、检测器、split、AP 口径、perturbation/reverse-control、人类标注协议、bootstrap 单位与多重比较边界。
- Results：以受控扰动为开篇主结果；随后是几何适用域、风险排序、图像级 finite-sample control、跨数据集边界、人类双标。负方法不得成为结果高潮。
- Discussion：为何实例级置信可能虚乐观、如何安全使用 orientation reliability、与 AP/calibration 的关系、遥感解译意义。
- Limitations：没有存活的 deployable repair；near-square 对象角度不适定；部分 detector-level 推断；DOTA 不做公开 test/SOTA 比较；human disagreement 不等于 GT error。
- Conclusion、Data/Code Availability、Ethics/annotation note、作者/单位/基金/致谢显式占位。
- References：只保留能核实的真实文献；同时生成 `references.bib` 与 `reference_audit.csv`，每条含 title/year/venue/DOI-or-official-URL/verification_status。

正文禁止出现 round 编号、dispatch、witness token、contest、hash-chain 等治理词汇；复现治理放补充材料。

## 4. T3：表、图、补充材料与投稿附件

输出：

- `docs/paper_jprs_r044/supplement.md`
- `docs/paper_jprs_r044/figures/` 下至少 5 幅可编辑 SVG + 对应 PNG + 生成脚本 + `figure_manifest.csv`
- `docs/paper_jprs_r044/tables/` 下正文与补充表的机器可读 CSV
- `docs/paper_jprs_r044/highlights.md`
- `docs/paper_jprs_r044/cover_letter.md`
- `docs/paper_jprs_r044/reproducibility_checklist.md`

建议核心图：

1. 问题示意与 AP50/angle-reliability 分离（必须由真实数值和清晰几何绘制，不生成虚构遥感样例）。
2. 六单元受控扰动前后 AP50/AP75/angle-error 对照。
3. 矩形 AR–angle-tolerance 几何曲线与 well-defined 区域。
4. 代表性 risk-coverage 曲线与 NRC 图。
5. image-level vs instance-iid 风险上界对照。
6. 人工双标 disagreement 分布（若证据足够，可作为第六图）。

所有图中数字必须进入 claim checker。不得读取未跟踪原图/原始数据；没有合法实例图证据就画机制图和统计图。

## 5. T4：精确 claim checker

在 `audit_bundles/r044/` 写独立校验程序与结果：

- `claim_spec.csv`：固定 `{claim_id, manuscript_location, source_path, source_key, transform, expected, atol}`。
- `validate_claims.py`：只按精确 path/key 查找，禁止最近值、模糊匹配或从主稿反向生成 expected。
- `claim_check.json`：总数、通过数、失败清单、输入 SHA-256。
- 至少做三项真实 mutation：改变一个 AP75、改变一个人工分歧统计、删除一个 source row；pristine 必须 0，mutated 必须非零。
- `manifest.csv`：本轮所有证据、稿件、图表和脚本的 size/SHA-256/can_recompute。

T3 校验代码必须独立于稿件/图表生成代码，不能共享 expected 常数源。

## 6. T5：独立红队与终态

先冻结完成版主稿，再做只读红队，输出：

- `docs/paper_jprs_r044/reviewer_1_measurement.md`
- `docs/paper_jprs_r044/reviewer_2_remote_sensing.md`
- `docs/paper_jprs_r044/venue_readiness.md`
- `audit_bundles/r044/gate.json`

Reviewer 1 重点攻击 measurement novelty、estimand circularity、AR-only 定义性成分、统计单位与多重比较。Reviewer 2 重点攻击 JPRS relevance、数据/检测器广度、实际遥感价值、缺少 deployable repair 与相关工作遗漏。每位必须给 accept/weak accept/weak reject/reject 倾向和最强三条拒稿理由。

`gate.json` 终态只能为：

- `JPRS_SUBMISSION_CANDIDATE`：G1–G4 全过；表示“可以进入作者信息/排版/投稿前人工审读”，**不等于已录用或宣称 ready**。
- `NOT_JPRS_READY`：任一硬门不满足；必须指出最小剩余科学缺口，不能把纯语言润色列为科学补救。
- `FAILURE_EARLY_STOP_EVIDENCE`：证据冲突或无法闭合。

## 7. 服务器执行纪律

1. 先写 `STARTED.json` 并单独 commit/push，再打开研究证据。
2. 仅使用 0 GPU；本轮不访问原始数据集、不训练、不推理。
3. 任务为纯写作与证据校验，但 claim 检索、hash、绘图和 mutation 应尽可能并行使用 CPU；无需为了满足 CPU 比例而制造无意义负载。
4. 每个主要阶段写进度日志；所有最终产物持久化并 Git 跟踪。
5. 完成后严格写 server report（schema 2 全字段）、commit + HTTPS push；回执首行按 completion mapping。
6. 若服务器发现计划与当前 Git 事实矛盾，优先诚实停止，不得自行放宽 gate 或改科学口径。

## 8. 完成定义

本轮“执行完毕”只表示稿件包、claim checker、图表、引用审计、双红队与 gate 都已产出并通过治理完整性检查。科学上是否达到 JPRS，只由 `gate.json` 与后续 B/C 验收决定；服务器不得直接宣称项目达到顶刊水平。
