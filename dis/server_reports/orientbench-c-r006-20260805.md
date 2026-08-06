# r006 标准 split-FST 有效性与发展广度门

- scientific snapshot: `60142448ff1f461531ad1eb2cd0c17785e782350`; execution HEAD: `7d067f44240b8790f5bc3cb346d6f866d09ce97e`
- 结论：structure `PASS_SPLIT_FST_VALIDITY`；development `FAIL_NO_BROAD_TARGET_FREE_DEVELOPMENT`。所有结果为 `RETROSPECTIVE_DEVELOPMENT_ONLY`，不构成确认性或部署保证。

## 结果

576 条冻结历史 frontier 重建 parity 为 `PASS`；六单元 lineage 为 `PASS`；r005 46 输入、8 非自身输出和授权提交路径复核为 `PASS`。新表含 7488 个候选（576 family × 13 grid），12/12 固定 score-regressor fit/predict，detector fit/predict 为 0/0。

primary split-FST 的顺序仅由 D_fit 的 `(p_fit,-n_fit,-coverage,index)` 冻结；exact-integer Bernoulli scene-event HB 比对 7488 个候选，r005 scalar `ceil(n*float_mean)` 的浮点硬化差异为 6762，本轮直接累计整数 k 的路径为权威实现。108 个全局零假设情境各 50,000 次模拟，split-FST 全部 CP 上界通过=True；Holm 敏感性单列通过=True。

target-GT-free 主 endpoint 的合格 development rows 为 14，覆盖 units `['A', 'B', 'C']`、datasets `['DIOR-R']`；广度门要求 3/6 units 与 2/3 datasets。target-aware zero-event witness 仅为不可部署诊断，不进入该门。历史 r004/r005 结论和冻结协议均未改写。

## 统计解释与边界

固定 split 令 D_fit 与 D_cal 的 exchangeable scene/tile unit 不重叠；条件于 D_fit，阈值、顺序与 alpha 均固定，D_cal 只用于合法 HB p-value，fixed-sequence 在首个未拒绝安全 null 后关闭，因此 strong FWER 由已知 split-FST/LTT 论证控制在 delta=0.1。本轮模拟仅作实现 sanity，而不是新定理。A--F outcome 已暴露，任何正面结果都只能用于下一版 protocol development；不能转写为独立确认、prevalence 或 TGRS 就绪。

## 合规

未训练、未 detector 推理、未下载、未使用 GPU、未读取 RSAR 或其他个人项目；仅重现固定 HistGradientBoostingRegressor。模拟使用 39/48 线程预算；原始 JSONL 读取和固定序列循环有串行部分，未将预算误报为实际利用率。sanitizer 为有界检查，不是完整泄漏证明。
