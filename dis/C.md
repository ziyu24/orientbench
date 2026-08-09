---
round_id: orientbench-c-r019-dispatch-20260809
snapshot:
  primary: f53bb670dea92dca9c0056e20c0cd338d0e52c14
  scientific_data_cutoff: 8ce84331a14c12a5ac41e46cb354ca712286626e
review_mode: post_cc_adjudication
evidence_cutoff: 2026-08-09
cc_recommendation: no
cc_status: completed
---

# OrientBench C：CC 验收与 r019 唯一顶刊判别实验

## 结论

CC 两阶段确实完成：阶段一 `ce6e894377fa881f897c9c2952076461fba2df34`，阶段二 `f53bb670dea92dca9c0056e20c0cd338d0e52c14`；两次提交都只追加 `dis/B.md`。`strict_blind_independence=false` 已诚实披露，因此把它作为有效对抗审查而非严格独立复现。

当前最强可辩护定位仍是 **strong-JSTARS potential、尚未 ready；TGRS/ISPRS JPRS conditional candidate；CVPR/ICCV 关闭**。最致命问题是：唯一正向方法信号仍是失去时间锁的探索性 6/6 unit、3/3 dataset，且实际 schema 缺 axial feature、single-candidate margin 与冻结语义不符、w/h+90 等价未验证。

用户已授权继续服务器实验。唯一值得执行的是 r019：把 Core-6 当 development，先修正并远端封存一个唯一 `EQS-RC-R019`，再在 DOTA-v1.0 一个数据集的 ORCNN/RTMDet-M 两个 family 单元上做 target-label-sealed 前瞻 endpoint evaluation。它不是 r012 HRSC 独立确认的替补，也不是两个独立数据集确认；PASS 只显著增强 TGRS/ISPRS JPRS/strong-journal 证据，不自动保证录用或重开顶会。

## 证据锁

- active manuscript：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`，blob `07c4f2c1b65488d5a6b780962ea8e1e15a5cd9a3`；r019 不改稿。
- G2_double_prime：`docs/m2_g2doubleprime_ar21_size_control.md` 的 frozen fixed-size-bin 结果为 PASS；它是 target-GT diagnostic upper bound，不等于 deployable。
- Core EQS：r015 unit 6/6、dataset 3/3 仅作 development/exploratory；r014 formal verdict 仍为 `FAIL_PROTOCOL_R014`。
- HRSC：`0.0602`，CI `[-0.0143,0.1438]`，已揭盲且跨零；r019 不重跑、不扩样、不进入 gate。
- DOTA units：`reports/069_dota_clean_artifact_manifest.csv` 固定 `DOTA-v1.0/orcnn` 与 `DOTA-v1.0/rtmdet`，共享 5,297 tiles、55,804 GT；checkpoint/config/SHA 已登记。历史只有 identity matched labels，没有 hflip/vflip raw。
- DOTA 历史 33,029/34,383 是旧的 matched/filter rows 且含额外 near-square 排除，不能当 r019 样本量或功效；r019 的交换单位是原始 mother scene。
- 服务器侧仍须先实证 `pth_data/readme.md`、两 checkpoint/config、DOTA image tree、Core A–F raw/labels 和全部 SHA；C 本机不能替代该 preflight。
- protected B：blob `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`，C 与服务器绝不触碰。

## Claim 审计

| Claim | Evidence | 最强混杂因素 | 反证条件 | 置信度 |
|---|---|---|---|---:|
| G2 排除简单 size prior | M2 fixed-size-bin 11/15 支持 | target-GT 拟合，非部署证据 | 原表/split/bootstrap 被复核推翻 | 高 |
| r015 EQS 有正向 development signal | r015 6/6、3/3 同步 bootstrap | 时间锁失效、schema 偏差 | 原始 score/label 或重算不一致 | 高但仅探索性 |
| 当前稿仍有独立科学价值 | 测量协议、负迁移 0/6、遥感双标、统计单位纪律 | 被视为 calibration/selective-prediction 重包装 | 最近工作覆盖全部四支柱且无实质差异 | 中高 |
| corrected EQS 可迁移到 DOTA | 尚无 exact DOTA identity/h/v EQS endpoint | 一个数据集、既见 family、项目已接触 DOTA | r019 未达预注册 2/2 + aggregate gate | 未知 |
| r019 PASS 即顶刊 ready | 无 | venue 还要求完整实验、显著贡献和投稿稿质量 | 即使 PASS 仍可能因贡献/范围被拒 | 低，拒绝 |

官方 scope 也支持这一克制边界：[TGRS](https://www.grss-ieee.org/publications/transactions-on-geoscience-remote-sensing/) 要求 novel methodological advancement 与完整实验条件；[ISPRS JPRS](https://www.sciencedirect.com/journal/isprs-journal-of-photogrammetry-and-remote-sensing) 强调 significant contribution、理论背景与应用。r019 只解决当前最缺的前瞻方法证据，不替代贡献与写作审查。

## 可证伪创新候选

```text
candidate:
  problem: 不使用 DOTA target angle labels 的 prediction-only TTA selector 能否稳定改善两个 DOTA detector 的方向风险排序
  nearest_primary_work: 当前 r015 exploratory EQS、detection calibration 与 selective prediction
  material_delta: 长轴表示等价、完整轴向特征和公开 prelabel seal 下的遥感 OBB target-label-free 前瞻 endpoint
  mechanism: identity/hflip/vflip 的方向、重叠、中心、尺度和分数等变性异常预测 orientation risk
  minimum_decisive_test: DOTA mother-scene 同步 10,000 bootstrap，ORCNN/RTMDet-M 2/2 与等权 aggregate 同时过固定门
  kill_condition: production/timelock 硬门失败，或 DOTA 完整执行后未满足 PASS；之后不换 selector/gate/dataset 续命
  expected_paper_value: PASS 显著增强 TGRS/ISPRS JPRS；FAIL/INCONCLUSIVE 立即转 measurement/diagnostic 稿
```

## B/CC 继承

| B 项 | C 裁决 | 处理 |
|---|---|---|
| P1 探索性 EQS 在正文易被误读 | revise | 采纳资格风险；CI 可保留，但“支持”须在 r019 后改为探索性筛查或由新确认取代 |
| P2 §6.5 消费失效 UCB 残句 | adopt | r019 后删除/降格，不为旧 UCB 另开实验 |
| P3 axial 缺失 | adopt | r019 唯一 primary 实现独立 axial dispersion；不追溯修复 r015 |
| P4 w/h+90 unknown | experiment | 作为 prelabel production-path 硬门，不能过则技术早停 |
| P5 margin | revise/adopt stage 2 | r018 expected=0 是假失败；production 单候选返回 top1 IoU 仍偏离冻结常量 1，r019 修正并微测 |
| P6.1 leave-detector 分母 | reject B 具体归因 | 4/5 中失败的是 FAIR1M/PSC；RTMDet 是额外不可识别折，后续稿件按此说明 |
| P6.2 HRSC 约四倍实例 | revise | 独立单位是 image cluster；不做事后扩样或救场 |
| DOTA PASS 自动重开顶会 | reject as sufficient | 只作为一个数据集、两个既见 family 的前瞻支持证据 |
| DOTA 前瞻实验 | experiment/adopt | 用户已授权，按 r019 一次性执行 |

## 对抗性综合

本轮三个视角为统计/gate、实现/provenance、稿件/venue。最强反驳是 DOTA 已被项目广泛使用且两个单元共享母景，因此不是真正 pristine external dataset；应只称“未观察过 exact EQS endpoint 的前瞻复现”。集体盲区是 DOTA mother-map、服务器 runtime raw 与 checkpoint 仍需现场实证。任何缺失都必须早停，不能改用 tile bootstrap 或 HRSC 替补。

r019 选择修正后的单一 primary，而不是确认已知有实现债务的 r014 selector。代价是 r019 不得声称追溯确认 r015；收益是若 PASS，论文拥有一个在标签揭盲前整体冻结、实现语义完整的可辩护方法结果。旧 r014 实现至多作预声明 secondary descriptive，绝不能在 primary 失败后换主角。

## 唯一下一步

服务器拉取包含本轮 `dis/sug.md` 的 HTTPS `main`，执行 r019。必须先 push prelabel seal commit，再读取任何 DOTA GT/旧 matched JSONL；之后无科学早停，FAIL/INCONCLUSIVE 也要完整算完并如实 push。`cc_recommendation: no`，新证据前不再调用 CC。

## 决策台账

| 项目 | 决策 | 下一项证据生产动作 |
|---|---|---|
| CC 两阶段 | adopt FULL_COMPLETION，盲审独立性为 false | 不再调用 CC |
| r015 6/6 + 3/3 | keep as development/exploratory | 不升格、不重验收 |
| actual r014 selector | reject as top-journal primary | 仅 secondary descriptive |
| EQS-RC-R019 | experiment | prelabel public seal 后一次 DOTA target endpoint |
| HRSC | keep historical inconclusive | 不重跑、不扩样、不救场 |
| venue | TGRS/ISPRS JPRS conditional | PASS 后改稿与完整投稿审查；非 PASS 立即转写 |
| further server rounds | reject | r019 后禁止 r020 换 gate 续命 |
