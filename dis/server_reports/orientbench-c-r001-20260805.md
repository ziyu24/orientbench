# OrientBench B3/B4 统计重审与 B5 可执行重门控

- round: `orientbench-c-r001-20260805`
- scientific snapshot: `9d9cdae1847f9c82e841f6f8b2692389cf9d9d79`
- execution HEAD: `41f56e6ce5f314730af0f3ccaf75e96ec60987b0`
- implementation SHA-256: `d40a9de1cab22e4300c8abbad45374e619b9926dbbea6c79b22c5d6bd4cb0266`
- final verdict: `FAIL_CANDIDATE_GATE`
- training/inference: `false/false`

## 1. 前置完整性

完整性检查通过 38/38 项。
`thresholds.yaml`、10 个 split、275 个持久化资产计数、B3 frozen dumps、
B4 三份 checkpoint/dump/evaluator manifest 及冻结 B1/B4 协议均已核对。
当前 HEAD 包含 9d9cdae scientific snapshot；其后提交仅为清理记录、迁移报告和本轮协作资产。
预先存在的 `.orientbench_transfer_parts/` 是未跟踪迁移分片，不参与输入或输出。

## 2. 旧实现与修正实现

旧 B3/B4 bootstrap 先在 image/mother-scene 内分别平均 candidate score、baseline score 和 risk，
再对 cluster means 计算 NRC。旧点估计则在全部 matched instances 上计算 NRC，因此二者不是同一 estimand。

修正实现保留原始实例顺序、score stable tie order 和实例级 NRC。每个 replicate 抽取 cluster 后，
把 cluster 被抽中的 multiplicity 作为该 cluster 内每个原始实例的整数权重。加权前缀风险和 oracle
均与逐行显式复制完全等价；candidate、phase_mod 与 detection_score 共用同一 resample ID。

等价性/复现测试通过 14/14 项。
G0 weighted implementation 也通过逐行显式 multiplicity 等价测试。

## 3. 独立复现旧异常

- B3：旧有区间的 58 行中，实例点差落在旧区间外 39 行（要求复现 39 行）。
- B4：24 行中对应异常 4 行（要求复现 4 行）。
- 修正后：B3 点差落在新同-estimand区间外 0/58；B4 为 0/24。

上述旧异常不是用区间必须机械包含点估计来单独定罪，而是与源码中 cluster-mean NRC 的明确
estimand 变化共同构成证据。修正表同时保留旧点差、旧区间和逐行异常标志。

## 4. 候选比较

B3 修正表共有 58 行，其中同时优于 phase_mod 与 detection_score 的单元行数为 27。
B4 修正表共有 24 行，对应行数为 0。
支持要求使用 paired delta NRC 的 97.5% 分位数严格小于 0；Endpoint C/E 分开判断。
外部 DOTA RotatedFCOS 三 seed 中，没有一个冻结候选在同一 endpoint 上三 seed 均同时优于
phase_mod 与 detection_score。因此 development-derived 候选未获得独立确认。

## 5. 身份与机制边界

ranking-only 候选的 prediction identity、boxes、classes、NMS 与 AP 审计保持通过。径向、切向、
频率和 boundary 干预会改变角度框，部分历史 full-evaluator 单元还改变 NMS/AP；它们只支持
mechanism-only，不构成 ranking-only/AP-invariant 修复。H1/H3 的有界机制证据可保留，但不能
继承为候选有效性。

## 6. 可执行 gate

B5 gate 由完整性、等价测试、模型健康、身份审计、外部机制重复和修正 bootstrap 条件逐行计算，
没有在生成代码中写死 H1--H4 状态或 final verdict。最终机器裁决为：

`FAIL_CANDIDATE_GATE`

影响：`STOP_B6`。原 `PASS_MECHANISM_BOUNDED` 只能保留为有界机制描述；
它不再构成执行 B6 的放行门。不得增加事后 score、seed、阈值或 endpoint 挽救候选。

## 7. 证据文件

- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_candidate_cluster_bootstrap_reaudit_r001.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b4_candidate_external_bootstrap_reaudit_r001.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b5_gate_reaudit_r001.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_b4_estimand_equivalence_tests_r001.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_b4_reaudit_manifest_r001.json`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/reaudit_b3_b4_r001.py`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/test_b3_b4_reaudit_r001.py`

复算命令：

```bash
/home/rspip/anaconda3/envs/mr_dev1x/bin/python top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/test_b3_b4_reaudit_r001.py
/home/rspip/anaconda3/envs/mr_dev1x/bin/python top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/reaudit_b3_b4_r001.py
```

本轮未修改冻结 B1--B5 输出、协议、数据、split、checkpoint、A 主稿或 `dis/B.md`。
