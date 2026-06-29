# P1 硬债修订建议（measure_fix_v2）

> 仅在 measure_fix_v2 内提出修订建议，**不改旧 frozen 事实 / claim ledger 历史 / thresholds / split / formal 标签 / P1 frozen tag**。供 v2 论文正文采用。

## 1. NRC 构造效度 → within-dataset / comparable-setting（不再把跨数据集 Spearman 当 headline）
- **问题**：P1 把 23-cell 跨数据集 Spearman(NRC,mAP)=-0.05 当 headline；跨数据集异质 + n=23 + partial 偏相关 df=7 under-powered，不能支撑强独立性。
- **修订**：headline 改为 **within-dataset / comparable-setting** 分析——同 dataset 内不同 detector 的 NRC 排序 vs mAP 排序，逐 dataset 报告；跨数据集仅作 secondary。措辞固定为"未检测到显著相关；NRC 提供不同于 accuracy 的信号"。

## 2. PSC 推断单位 → detector/dataset-level（非 sample-level 外推）
- **问题**：PSC 反校准结论应限定在 detector×dataset 单元，不可外推为"PSC 在所有条件反校准"。
- **修订**：明确写 **PSC reverse-calibration 是 detector(PSC)×dataset(FAIR1M/SODA) 级现象**（bootstrap-significant 2/4 datasets；DOTA masked 0.84 不显著）；DIOR 不反校准。单位 = cell-level。

## 3. 正文补 GV-obliquity 定义
- gv_ratio = OBB area / HBB(axis-aligned bounding) area ∈(0,1]；gv_obb_needed = 1 − gv_ratio = "需要 OBB 的程度"（越大越斜，HBB 越浪费）。near-square+axis-aligned → gv_obb_needed→0。正文须给此定义 + 公式 + 与 aspect-ratio 的区别（GV 含朝向，ar 不含）。

## 4. related work 补全
- **D-ECE**（detection expected calibration error）：定位/分类校准 vs 本文朝向可靠性的区别。
- **selective prediction / risk-coverage**：NRC-AUC 的方法学根。
- **square-like / boundary problem**：近方形朝向 ill-posedness、角度周期边界。
- **GWD / KLD** 旋转回归损失：与朝向误差度量的关系。
- **angle uncertainty / angle coder**（CSL/DCL/PSC）：Track A 机制背景。

## 5. raw/matched predictions 持久化检查
- **问题**：/dev/shm 非持久，不能是唯一产物。
- **现状**：P1 已持久化 8 key cells 到 outputs/persistent_artifacts/orientbench_v2/（gitignored）+ manifest(sha256/生成命令/can_recompute)。
- **修订建议**：v2 阶段新增的 matched feature tables 持久化到 measure_fix_v2/artifacts/（manifest+sha256，大文件不进 git）；正文附录写明复算入口；/dev/shm 风险显式声明。

## 6. 治理内容下沉附录
- sha256、claim ledger、verifier、frozen tag 等治理内容**放附录**，不抢正文科学结果（measure→diagnose→fix 主叙事）。正文只引用关键 frozen 事实（thresholds sha256、split 互斥）。

## 边界
- 以上均为**修订建议**，未改任何旧 frozen 文件 / 历史事实 / claim ledger。v2 主线以 CLAUDE.md(v2) + 项目执行文件_v2 为准。
