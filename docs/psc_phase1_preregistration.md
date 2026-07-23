# PSC Phase 1 预注册（机制与修复拆篇门控）

> 本文件在 Phase 1 首次实际启动时冻结。冻结后不得新增有利假说、不得改动 k 网格、阈值序列、比较基线或 PASS 条件。

## 0 时间冻结

- start_timestamp（服务器时间）：**2026-07-12 20:14:39 -0700**
- hard_deadline = start + 42 天：**2026-08-23 20:14:39 -0700**
- 终止规则：预注册任务全部完成 **或** 到达 hard_deadline，以先发生者为准；禁止延期；禁止开放式无限假说搜索。

## 1 第一个强制实验：PSC 相位向量径向缩放

对已充分收敛的 PSC 检测器（复用 K2 final PSC 检查点，DIOR-R 与 SODA-A、seed0..2），在 instrumented 前向中对角度分支解码前的相位向量施加径向缩放 z' = k·z。

**k 网格（运行前冻结，不得事后新增）**：
`k ∈ {0.25, 0.50, 0.75, 0.90, 1.00, 1.10, 1.25, 1.50, 2.00, 4.00}`

三个层级分别记录，互不混淆：
1. 编码向量级：decoded angle、phase_mod、径向梯度、切向梯度。
2. 检测 head 输出级：pred box、class、objectness、NMS 后集合。
3. full evaluator 级：AP50、AP75、angle error。

**分岔判据（冻结）**：
- 分支 A（解码径向不变 + 损失对模长弱约束）：主假说改为 "phase magnitude lacks identifiable uncertainty semantics"。判据：所有 k 的 decoded angle 与 k=1 的角度差 < 0.5° 中位、且 < 1.0° 的 p95；且 loss 对 k 的相对变化 < 1e-3。
- 分支 B（解码非完全径向不变 或 损失明确赋予模长语义）：继续检验 boundary/wrapping-conditioned reverse ranking。

## 2 预注册后续剖析（仅限以下 12 项，不得扩展）

1. phase_mod × angle error 条件分布
2. phase_mod × phase angle
3. phase_mod × objectness
4. phase_mod × feature norm
5. phase_mod × size
6. phase_mod × class
7. phase_mod × boundary angle / wrapping condition
8. 高 phase_mod × 大角度错误实例板清单
9. 多频解码角 circular disagreement
10. unwrap candidate energy gap
11. phase-direction margin
12. TTA phase-direction circular variance

## 3 强制比较基线（冻结）

phase_mod / negative phase_mod / detection score / TTA circular variance / DCL native / CSL native / 剖析产出的新分数（如有）。

统一口径：ar≥2.1；geometry-normalized severe event（δθ_0.75(ar)）；NRC / AURC / Risk@70 / Risk@90；image-level cluster bootstrap CI；至少 DIOR-R 与 SODA-A。不重训 detector、不改 box/class/AP，只改可靠性排序。

## 4 新分数非平凡性审计（冻结）

新分数须证明：非 phase_mod 简单取负；非单调温度变换；非 phase_mod 任意简单单调映射；非 detection score 近似复制；不依赖 GT；推理端可得；不依赖目标域 GT 标定。
报告：Spearman、Kendall、与 negative phase_mod 的 rank disagreement、isotonic predictability、top-k overlap、feature ablation、score 计算公式。

## 5 拆篇 PASS 条件（四项同时满足）

1. 找到可干预验证的结构性原因（非相关故事）。
2. 新分数非 phase_mod 简单单调变换/取负。
3. 新分数在 DIOR-R 与 SODA-A 稳定优于 negative phase_mod，且 image-level bootstrap CI 支持。
4. 不重训 detector、不改 box/class/AP，只改可靠性排序。

- PASS → 拆 A/B 两篇：A 保留一段 PSC 动机观察；B 承担机制/干预/修复；两篇不重复完整机制实验与主表。
- FAIL 或到 deadline → 不拆篇；有效机制结果并回 A 的机制小节；B 停止阻塞 A；不继续开放式搜索。
