# OrientBench r002 B5 负结论证据链收口

- round: `orientbench-c-r002-20260805`
- scientific snapshot: `8466602330a942c9bb8beff284aa8fc5b952a3b0`
- execution HEAD: `012207f29a4d17dcb525929eae41ebf0b310dc02`
- evidence closure verdict: `FAIL_EVIDENCE_DRIFT`
- scientific candidate gate: `FAIL_CANDIDATE_GATE`
- B6/B7: `STOPPED_NOT_RUN`
- training/inference: `0/0`

## 1. 前置完整性与直接输入

r001 八个锁定文件逐字节核对：`PASS`。执行中登记直接输入 333 个。
`m4_delta_theta_075_frozen.json` 与 `g0_comparison_manifest.csv` 的 raw SHA-256 分别精确匹配
`80d86a5f72e70405fe4a49db87aad61e6aea20a26af0ad1c5745bfd646d1e5cb` 与 `e038aed06b3aff86818c8663657f074798e90de867ab48ac9d2821c61c191a86`。r002 执行源码和测试源码记录 canonical SHA-256 与 Git blob hash；
scientific snapshot、execution HEAD 和未来 result commit 严格分离。

工作树的 tracked/index 在执行前干净；仅有已知、前轮已披露且未参与计算的 `.orientbench_transfer_parts/`
迁移分片，以及本轮授权的新文件。未执行 reset/clean，也未改动该迁移目录。

## 2. B3 raw 到 cache lineage

九个 B3 cache 逐 key 从 raw JSONL/JSONL.GZ 按原算法重构：直接解析 `image/score/error/ar/size/class/feature/`
`boundary/tta/vector/pred_box/gt_box`，然后只应用 `GT aspect_ratio>=2.1`。对象数组逐项编码，数值数组按 dtype、
shape 和 little-endian content hash 比较；浮点比较为 `rtol=0, atol=0, NaN-equal`。

lineage 结论：`PASS 9/9`。cache 未持久化 pred_id/gt_id，因此报告 raw 的
`image_id,pred_id,gt_id` 行序 hash，并以全部 cache key 的逐元素有序一致性证明 cache 行序。

## 3. 275 文件持久化 inventory

- files: `275`
- total bytes: `14579861468`
- aggregate path+bytes+SHA-256: `144857890f8b5cce79bd19a719adc9a441f10da223d963d9f9369d1aa9e9152d`
- duplicate content groups: `10`
- unreadable or missing files within the frozen inventory: `0`
- symlinks / dangling symlinks: `0 / 0`

文件数仅为辅助条件；本轮对每个文件记录内容 SHA-256，并用有序 path+bytes+hash 生成 aggregate。

## 4. common finite mask 与统计漂移

所有 candidate、phase_mod、detection_score 和 endpoint 在点估计与每个 bootstrap replicate 前使用同一 finite mask。
B4 24 行和 B3 非 TTA 行均为全量 finite。B3 的 TTA 两个 detector-head-seed unit 并非全量 finite：

| dataset | raw rows | excluded | endpoints |
|---|---:|---:|---:|
| DIOR-R | 48282 | 298 | endpoint_continuous |
| DIOR-R | 48282 | 298 | endpoint_severe_event |
| SODA-A | 193045 | 2104 | endpoint_continuous |
| SODA-A | 193045 | 2104 | endpoint_severe_event |

因此 r001 对 TTA 的点估计曾删除 NaN，而 bootstrap 把 NaN score 排到末端，二者仍未使用同一 universe。
r002 封闭该入口后，4 个 TTA candidate×endpoint 行发生科学数值或 universe 漂移；逐列最大数值差为 `0.024593006944616247`。
按预注册早停规则，evidence closure 判为 `FAIL_EVIDENCE_DRIFT`，不得把此差异静默解释为 bitwise stable。

## 5. 测试与 gate

正式/随机测试通过 7/7。随机显式展开 seed=`20260805`、
100 cases；覆盖 weighted selected/oracle/random/NRC、stable ties、NaN common mask、37-replicate 输入、paired
resample、candidate duplication 与 machine-derived verdict。

B3 development 仅为 DIOR-R/SODA-A，FAIR1M 单列 confirmatory，DOTA/RotatedFCOS 单列 external。
没有补造多 candidate×endpoint×seed 的成功规则。完全重复比较数为 `0`。
外部结果仍为 `0/24`，所以科学候选门保持
`FAIL_CANDIDATE_GATE`，`STOP_B6` 不变。r002 的漂移只否定“r001 全证据 bitwise 收口”，不挽救候选。

## 6. 合规

训练次数 `0`，推理次数 `0`，旧个人项目结果读取 `否`。未下载 D7/PCP-OBB、pcbobb、pcbobb_beyond 或
pcbobb_score_study；未修改 A、B1--B5 冻结文件、r001 文件、split、checkpoint、配置或 `dis/B.md`。
