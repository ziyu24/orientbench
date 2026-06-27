# Bench-Core v0.0 Sanity Report

> 生成时间: 2026-06-25 16:03 CST
> 范围: 指令 003 — Bench-Core-0 基元 skeleton + sanity。
> 状态: skeleton / sanity 完成；阈值未冻结，未启动任何正式实验、detector 推理或训练。

---

## 1. Inventory 摘要

来源: `/home/rspip/cqc/pro/study/pth_data/readme.md`（只读解析，指令 002）。

| 项 | 值 |
|---|---|
| baseline 总数 | 73 |
| valid | 67 |
| invalid | 6（id = 21,54,55,56,57,58，与 readme 一致）|
| inference_ready | 67（= 全部 valid）|
| pth/log/config 磁盘存在 | 73/73 全部存在 |
| 字段缺失 | 仅 `mmrotate_stack`/`env` 各 21 条 = `unknown`（family 不在 readme 兼容性表）|

产物: `outputs/bench_core/baseline_inventory.{json,csv}`、`baseline_valid_only.csv`。

---

## 2. RHINO 缺失风险（留痕）

- **RHINO-style rotated DETR 在 `pth_data/readme.md` 中未找到。** 现有 DETR-like 仅 ARS-DETR（id 14–19,44,72）。
- 这是 **C1/B baseline 冻结风险（R6）**，不是 Bench-Core-0 阻塞项。
- 处置（监督员 003 裁定）：C1/B 路线待合作者裁示——下载 / 训练 / 补充 / 另行批准替代；**裁示前不启动 B-MVE-0/1**；**不得把 ARS-DETR 伪装成 RHINO**；本轮不下载、不训练、不更换 baseline。
- 已同步记录于 `claude_code_and_supervisor.md` 与 `configs/thresholds.yaml`（B_C1 段保持 pending）。

---

## 3. 已实现 Bench-Core-0 基元

| 模块 | 文件 | 内容 |
|---|---|---|
| OBB geometry | `orientbench/core/geometry.py` | angle error（π 周期, [0,π/2]）、OBB area、HBB 外接框尺寸/面积、OBB→HBB、数值容错（非有限/非正边长→NaN）|
| angle metrics | `orientbench/metrics/angle.py` | 标量 + 批量 angle error、NaN 屏蔽均值 |
| GV-obliquity | `orientbench/metrics/gv.py` | gv_ratio / gv_hbb_safe / gv_obb_needed（定义冻结，未改）|
| constants | `orientbench/core/constants.py` | π 常数、Core-1 测量常数（β=1.5, n_min=3, τ_bg=0.5）、placeholder 阈值（带 `PENDING_THRESHOLD_FREEZE`）|
| stress buckets | `orientbench/buckets/stress_buckets.py` | basic valid flag、near-square bucket（placeholder 阈值）、padding-only metadata placeholder |
| risk-coverage | `orientbench/metrics/risk_coverage.py` | selective risk 曲线（score 降序）、AURC、Risk@70、Risk@90 |
| NRC-AUC | `orientbench/metrics/nrc_auc.py` | AURC_oracle（risk 升序）/ AURC_random（mean risk）/ NRC-AUC，退化保护 |

### 定义核对（与项目执行文件一致）
- `delta = abs(((θ_pred - θ_gt + π/2) % π) - π/2)` ∈ [0, π/2] ✓
- `W = w|cosθ| + h|sinθ|`, `H = w|sinθ| + h|cosθ|` ✓
- `gv_ratio = area(OBB)/area(HBB)`；`gv_hbb_safe = gv_ratio`；`gv_obb_needed = 1 - gv_ratio` ✓（未更改）
- `NRC-AUC = (AURC_model - AURC_oracle)/(AURC_random - AURC_oracle)`，0=oracle、1=random、越低越好 ✓

### Sanity demo（确定性）
GV-obliquity:

| case | gv_ratio | gv_obb_needed |
|---|---|---|
| upright 2:1 (θ=0) | 1.0000 | 0.0000 |
| square @45° | 0.5000 | 0.5000 |
| elongated 20:1 @45° | 0.0907 | 0.9093 |
| elongated 20:1 upright | 1.0000 | 0.0000 |

NRC-AUC（seeded toy, n=200, score≈-risk+noise）：AURC_model=0.2760, oracle=0.2541, random=0.5004 → **NRC-AUC=0.0891**, Risk@70=0.3692, Risk@90=0.4572。边界: oracle 排序→NRC-AUC=0；worst 排序→NRC-AUC≥1；全等 risk→degenerate=NaN。

---

## 4. 测试结果

命令: `python -m pytest tests/ -q` → **24 passed**（0.14s）。

- `tests/test_baseline_readme.py` — 7（表解析 / valid bool / 链接路径 / 数值转换 / metadata join / 缺字段容错）
- `tests/test_bench_core0.py` — 17（angle 周期与范围 / HBB 轴对齐与 45° / GV near-square vs elongated + 冻结恒等式 / risk-coverage 排序 / NRC-AUC oracle=0、worst≥1、degenerate=NaN / near-square placeholder）

未启动 detector 推理、训练、第三方下载；未修改 `pth_data`。

---

## 5. thresholds.yaml 冻结状态

文件: `configs/thresholds.yaml`（已建初版）。

- `freeze_status: pending`，`freeze_time: null`，`responsible_role: 全 null`。
- B_C1 / A_A4 / D2 三段阈值均 `status: pending`，gate 数值 `null`。
- 仅预填项目执行文件已明文给出的 **D2 `spearman_mAP_NRC_max: 0.95`**（§12.2 停止条件上界）与 bucket placeholder（near_square 1.15 / min_box_side 2.0），均标 pending，**无任何已批准阈值伪造**。
- 含 `change_log`，记录本次骨架创建。
- **结论：阈值未冻结 → 不开正式实验**（R8）。

---

## 6. 下一步建议

1. **C1/B**：等待合作者对 RHINO host 的裁示（下载/训练/补充/批准替代）；裁示前 B-MVE-0/1 冻结。
2. **Bench-Core-0 收尾**：把 GV-obliquity / angle error 接到真实 GT（`scripts/02_prepare_gt_index.py` + `orientbench/data/`），先在 1 个 DOTA/DIOR GT 上跑 GV 分布，产出 `gv_obliquity_baseline.csv`。
3. **Bench-Core-1**：实现 layout/background source measurement 与 class-conditional 桶；阈值经 R8 冻结后再开。
4. **inventory 补全**：如需要，由监督员提供 21 个 unknown family→(mmrotate_stack,env) 映射，或从各 baseline config 推断。
5. **阈值冻结**：由各责任角色提交 B/C1、A/A4、D2 具体阈值与统计检验，填入 `configs/thresholds.yaml` 并设 `freeze_time`。
