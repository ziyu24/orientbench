# claude_code_and_supervisor.md

> orientbench 监督与汇报记录文件。
> 记录每次汇报、收到的人类/监督员指令、服务器时间戳、已执行动作与产物路径。
> 时间戳使用服务器本地时间（`date '+%Y-%m-%d %H:%M:%S %Z'`）。

---

## [2026-06-25 15:39:43 CST] 来源: supervisor

### 输入/指令
监督员指令 001：依据 `CLAUDE.md` 与 `项目执行文件.md` 开工（不读取监督员 prompt）。
1. 检查 `/home/rspip/cqc/pro/study/pth_data/readme.md` 是否存在；不存在则停止并汇报；
2. 若存在，初始化 `orientbench` 标准目录结构；
3. 建立/追加 `claude_code_and_supervisor.md`，记录本条指令、服务器时间戳、已执行动作与产物路径；
4. 汇报决策性结果：readme 是否存在、项目结构是否初始化、日志是否建立、下一步是否准备实现 baseline inventory parser。

### 行动/结论
- readme 检查：`/home/rspip/cqc/pro/study/pth_data/readme.md` **存在**（83838 字节，2026-06-05 修改）。`项目执行文件.md` 记载该 readme 含 73 个 baseline 模型记录；将在 baseline inventory parser 阶段从该文件解析，不凭记忆使用。
- 项目结构：按 `项目执行文件.md` 第 1.2 / 3 节初始化完成。已建立 `configs/`、`orientbench/{core,data,metrics,buckets,probes,io,reports}`（含 `__init__.py`）、`scripts/`、`outputs/{bench_core,predictions,gt_index,reports,logs,cache}`、`pth_data/`、`docs/`、`tests/`。
- 日志文件：本文件 `claude_code_and_supervisor.md` 建立完成。
- 模块源码文件（geometry / gv / nrc_auc / 各 parser 等）尚未实现，属后续实现步骤，未在本条指令范围内提前编写。

### 产物路径
- `/home/rspip/cqc/pro/study/orientbench/`（标准目录结构）
- `/home/rspip/cqc/pro/study/orientbench/claude_code_and_supervisor.md`（本日志）

### 下一步
准备实现 baseline inventory parser（`orientbench/io/baseline_readme.py` + `scripts/01_inventory_baselines.py`），解析 `pth_data/readme.md`，输出 `outputs/bench_core/baseline_inventory.{json,csv}` 与 `baseline_valid_only.csv`。等待放行或自决推进。

---

## [2026-06-25 15:47:23 CST] 来源: supervisor

### 输入/指令
监督员指令 002：放行实现 baseline inventory parser，不再为字段口径反复请示；缺失字段填 unknown/null/conservative default 并在日志记录原因。一次性推进到可验证产物：
- 只读解析 `pth_data/readme.md`，在 `orientbench/io/baseline_readme.py` 实现 parser，输出 §4.2 最低字段；
- 相对 pth/log/config 统一解析为 `pth_data` 下绝对路径并保留原始相对路径；
- valid 标准化为 bool；mAP_best/epoch_best/id 尽量转数值，失败保留原值并记 warning；
- inference_ready 推断 = valid 且 pth/config/log 字段存在；实际文件存在性另设 pth_exists/config_exists/log_exists，不存在不改 invalid；
- 生成三份产物 json/csv/valid_only.csv；写 `scripts/01_inventory_baselines.py`（--readme/--out-dir）；
- 加 focused tests；运行测试与脚本并记录；检查 RHINO-style rotated DETR，找不到不编造直接汇报。
- 边界：不训练/不下载/不改 pth_data/不跳过 R1-R8/不改 default selection score。

### 行动/结论
- 解析 readme 结构：主 baseline 表（#1–73，列 model_id/dataset/train·val/epoch_best/mAP_best/valid/pth/log/config/source）+ 详细 metadata 表（actual_gb/per_gpu_bs/gpus/actual_lr/optimizer/scheduler/angle/metric/eval_interval 等）+ SHA 完整性表（#1–68）+ 兼容性表（按 family 给 mmrotate stack/env）。parser 按 `#` join 主表与 metadata 表。
- 实现：`orientbench/io/baseline_readme.py`（通用 markdown 表抽取、valid→bool、链接路径抽取、数值容错转换、family→stack/env 最佳推断）；`scripts/01_inventory_baselines.py`（argparse，默认固定路径，输出 json/csv/valid_only + 字段缺失统计 + RHINO 检查）。
- 测试：`tests/test_baseline_readme.py`，7 个用例（表解析、valid 标准化、链接路径、数值转换含失败回退、metadata join、缺字段容错），命令 `python -m pytest tests/test_baseline_readme.py -q` → **7 passed**。
- 运行 inventory：`python scripts/01_inventory_baselines.py` →
  - 解析 **73** 条，valid **67** / invalid **6**（invalid id = 21,54,55,56,57,58，与 readme 一致）；
  - 全部 pth/config/log **在磁盘存在**（pth_exists/config_exists/log_exists 均 True，0 缺失）→ 无 valid-baseline 与实际文件大面积不一致，未触发停止条件；
  - inference_ready = 67（= 全部 valid）；
  - 字段缺失：仅 `mmrotate_stack`/`env` 各 21 条为 `unknown`，原因为这些 model family（rotated_rtmdet / strip_rcnn / rotated_retinanet(非 psc) / point2rbox_v2 / rotated_fcos / h2rbox_v2）不在 readme 兼容性表的 5 个 family 中，无法可靠映射；已逐条写入 record warnings。
- RHINO 检查：model_id 无 `rhino`；DETR-like 仅 ARS-DETR（#14–19,44,72）。**RHINO-style rotated DETR 在 pth_data/readme.md 中未找到**。
- 边界遵守：未训练、未下载、未修改 pth_data（只读解析）、未改 default selection score、未触碰 R1–R8 冻结项。

### 产物路径
- `/home/rspip/cqc/pro/study/orientbench/orientbench/io/baseline_readme.py`
- `/home/rspip/cqc/pro/study/orientbench/scripts/01_inventory_baselines.py`
- `/home/rspip/cqc/pro/study/orientbench/tests/test_baseline_readme.py`
- `/home/rspip/cqc/pro/study/orientbench/outputs/bench_core/baseline_inventory.json`
- `/home/rspip/cqc/pro/study/orientbench/outputs/bench_core/baseline_inventory.csv`
- `/home/rspip/cqc/pro/study/orientbench/outputs/bench_core/baseline_valid_only.csv`

### 下一步
建议：(1) 监督员确认 RHINO-style host 处置（下载/训练/以 ARS-DETR 替代）；(2) 推进 Bench-Core-0 几何与 GV-obliquity / NRC-AUC skeleton；(3) 如需 mmrotate_stack/env 对 21 个 unknown family 补全，可由监督员提供 family→stack/env 映射或从各 baseline config 推断。

---

## [2026-06-25 16:03:04 CST] 来源: supervisor

### 输入/指令
监督员指令 003：确认 002 结果。**RHINO 裁定**：RHINO-style rotated DETR 未在 pth_data/readme.md 找到，属 C1/B baseline 冻结风险，非 Bench-Core-0 阻塞项；不得自行用 ARS-DETR 替代，不下载/训练/更换 baseline；C1/B 路线待合作者裁示（下载/训练/补充/批准替代），裁示前不启动 B-MVE-0/1，不得把 ARS-DETR 伪装成 RHINO。本轮继续推进 Bench-Core-0：实现 OBB geometry、GV-obliquity、valid mask/near-square/padding-only placeholder、Risk@70/90 + NRC-AUC skeleton、configs/thresholds.yaml 初版、focused tests，运行测试，产出 v0.0 sanity 报告。

### 行动/结论
- **RHINO 风险留痕（明确记录）**：RHINO-style baseline 缺失。C1/B 路线待合作者裁示：下载、训练、补充或另行批准替代。**在裁示前不启动 B-MVE-0/1。不得把 ARS-DETR 伪装成 RHINO。** 同步写入 bench_core_v00_sanity.md 与 configs/thresholds.yaml（B_C1 段 pending）。
- 实现 Bench-Core-0 基元：
  - `orientbench/core/geometry.py`（angle error π 周期、OBB area、HBB 外接框、OBB→HBB、数值容错）；
  - `orientbench/metrics/angle.py`（标量+批量 angle error）；
  - `orientbench/metrics/gv.py`（gv_ratio/gv_hbb_safe/gv_obb_needed，定义未改）；
  - `orientbench/core/constants.py`（π 常数、Core-1 测量常数、placeholder 阈值带 PENDING_THRESHOLD_FREEZE）；
  - `orientbench/buckets/stress_buckets.py`（basic valid flag、near-square bucket placeholder、padding-only metadata placeholder）；
  - `orientbench/metrics/risk_coverage.py`（selective risk 曲线、AURC、Risk@70、Risk@90）；
  - `orientbench/metrics/nrc_auc.py`（AURC_oracle/random、NRC-AUC，退化保护）。
- `configs/thresholds.yaml` 初版：B_C1/A_A4/D2 三段 + freeze_time(null) + responsible_role(null) + change_log；全部 gate 阈值 pending/null；仅预填项目执行文件明文的 D2 spearman 上界 0.95 与 bucket placeholder，无伪造已批准阈值。
- 测试：`tests/test_bench_core0.py`（17 例）+ 既有 `test_baseline_readme.py`（7 例）。命令 `python -m pytest tests/ -q` → **24 passed**。
- Sanity demo：GV upright→1.0 / square@45→0.5 / elongated@45→0.0907；NRC-AUC seeded toy=0.0891（oracle=0、worst≥1、degenerate=NaN 边界已测）。
- 边界遵守：未启动 detector 推理 / 训练 / 第三方下载；未修改 pth_data；GV/NRC-AUC 定义与项目执行文件一致未更改；阈值未冻结故未开正式实验。

### 产物路径
- `/home/rspip/cqc/pro/study/orientbench/orientbench/core/geometry.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/core/constants.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/metrics/angle.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/metrics/gv.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/metrics/risk_coverage.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/metrics/nrc_auc.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/buckets/stress_buckets.py`
- `/home/rspip/cqc/pro/study/orientbench/configs/thresholds.yaml`
- `/home/rspip/cqc/pro/study/orientbench/tests/test_bench_core0.py`
- `/home/rspip/cqc/pro/study/orientbench/outputs/bench_core/reports/bench_core_v00_sanity.md`

### 下一步
等待 C1/B RHINO 裁示；Bench-Core-0 收尾建议接真实 GT（02_prepare_gt_index + data 层）跑 GV 分布；阈值冻结由各责任角色提交后再开正式实验。

---

## [2026-06-25 16:43:53 CST] 来源: supervisor

### 输入/指令
监督员指令 004：确认 003。Bench-Core-0 skeleton 放行（24 tests passed，定义未偏离，thresholds 仍 pending 故不开正式实验）。RHINO 缺失风险保留：不等 RHINO 裁示阻塞 D2、不以 ARS-DETR 替代、不启动 B-MVE-0/1。本轮接真实 GT 完成数据层 sanity：
- 任务一 检查并记录固定路径（dataset/pth_data/orientbench），只读不动数据；
- 任务二 dataset inventory（dataset_inventory.py + 00_env_check.py），输出 json/csv，识别 DOTA1.0/1.5/DIOR-R/HRSC2016/SODA-A/FAIR1M/ICDAR-MLT，找不到记 missing 不退出；
- 任务三 GT index 基础模块（gt_index.py/dota.py/dior.py/02_prepare_gt_index.py，参数 --dataset/--data-root/--split/--out-dir/--max-files/--strict，默认轻量），DOTA poly8 优先，格式不确定记 unsupported/uncertain，不硬猜；
- 任务四 真实 GT 轻量 GV sanity + v01 报告；
- 任务五 focused tests；任务六 运行测试与脚本并记录。
边界：不推理/不训练/不下载/不改 pth_data 与原始数据/不改 GV/NRC-AUC 定义/不冻结 thresholds/不伪造 angle_version 确定性。

### 行动/结论
- 固定路径：dataset / pth_data / readme / orientbench / third_party 全部存在；依赖 numpy1.24.4 / cv2 4.13.0 / shapely 2.0.7 / py3.8 均已具备（未安装下载）。
- 数据集格式探测（只读样本）：DOTA=poly8 txt；DIOR-R=robndbox XML(4 角点+angle)；HRSC2016=mbox(cx,cy,w,h,ang rad) XML；FAIR1M=points polygon XML。SODA-A、ICDAR-MLT 不在 dataset 根。
- dataset inventory：known=7，**present=5（DOTA-v1.0/v1.5、DIOR-R、HRSC2016、FAIR1M-v1.0），missing=2（SODA-A、ICDAR-MLT）**。
- GT index：实现 dota.py/dior.py/gt_index.py（统一 poly8_to_obb=cv2.minAreaRect+θ 归一化[-π/2,π/2)，cv2 缺失 edge-fallback；HRSC 直接 OBB；FAIR1M points）。angle_version honest 标注（DOTA/DIOR/FAIR1M=le90_derived_from_poly；HRSC=mbox_ang_rad UNVERIFIED le90）。
- 真实 GT 轻量 GV sanity（--max-files 60）：
  - DOTA-v1.0/train：files 60，objects 959，valid 959，invalid 0，GV median 0.456 / mean 0.575，near-square(placeholder) 0.9%；
  - DIOR-R/trainval：files 60，objects 338，valid 338，invalid 0，GV median 1.000 / mean 0.863，near-square 14.2%。
  - 形态差异符合直觉（DOTA 富倾斜细长→低 GV；DIOR 多近轴→高 GV），模块工作正常，invalid geometry=0。
- 测试：`python -m pytest tests/ -q` → **33 passed**（7+17+9）。脚本 00_env_check / 02_prepare_gt_index(dota10,dior) 均成功。
- 停止条件检查：全部未触发（dataset 存在、readme 在、无需改固定路径/装依赖/改原始数据、无 R1-R8 冲突、GT 口径与项目定义无根本冲突）。
- 边界遵守：未推理/训练/下载/改 pth_data/改原始数据/改 GV/NRC-AUC 定义/冻结 thresholds；angle_version 不确定项如实记录未伪造。

### 产物路径
- `/home/rspip/cqc/pro/study/orientbench/orientbench/data/dataset_inventory.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/data/gt_index.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/data/dota.py`
- `/home/rspip/cqc/pro/study/orientbench/orientbench/data/dior.py`
- `/home/rspip/cqc/pro/study/orientbench/scripts/00_env_check.py`
- `/home/rspip/cqc/pro/study/orientbench/scripts/02_prepare_gt_index.py`
- `/home/rspip/cqc/pro/study/orientbench/tests/test_data_layer.py`
- `/home/rspip/cqc/pro/study/orientbench/outputs/bench_core/dataset_inventory.{json,csv}`
- `/home/rspip/cqc/pro/study/orientbench/outputs/bench_core/gt_index/{dota10_train,dior_trainval}.{jsonl,csv,meta.json}`
- `/home/rspip/cqc/pro/study/orientbench/outputs/bench_core/reports/bench_core_v01_gt_sanity.md`

### Warnings / 待裁示
- 缺失数据集 SODA-A / ICDAR-MLT（readme baseline 有引用，本地 GT 未提供）——是否需要、路径待合作者确认。
- angle_version 不确定：HRSC mbox le90 等价未核验；DOTA/DIOR/FAIR1M le90 符号一致性待接预测前核验（对 GV 无影响）。
- RHINO host 仍缺失，待裁示，不阻塞 D2、不替代。

### 下一步
angle_version 符号核验 → GV baseline 全量（确认后）→ 缺失数据集裁示 → Bench-Core-1（阈值冻结后开正式实验）。

---

## [2026-06-25 17:18:02 CST] 来源: supervisor

### 输入/指令
监督员指令 005：确认 004（数据层 sanity 放行，33 tests passed，DOTA/DIOR/HRSC/FAIR1M parser 可用，SODA-A/ICDAR-MLT 缺失留痕）。本轮不再请示小事，直接推进 Bench-Core-1 **dry-run 闭环**（source/bucket/score/report 可运行闭环）；仍非正式实验，thresholds 未冻结，所有输出标注 sanity/dry-run，不做 gate 结论。任务一~十一：补齐 source measurement（layout+background）、stress buckets、default selection score dry-run、GV baseline、risk/NRC dry-run、probe matrix template、统一报告脚本、配置文件、focused tests、运行完整轻量闭环、日志。边界：不推理/训练/下载/改 pth_data/改原始数据/改 GV·NRC·score 定义/冻结阈值/声称 gate 通过/启动 9-detector matrix 或 B-MVE/用 ARS-DETR 替代 RHINO。脚本参数小调整自决并记录。

### 行动/结论（实现模块）
- source：`orientbench/buckets/sources.py`（layout: V_layout/D_nbr/R_nbr/A_align/E_layout；background: 真实图像 annulus 灰度梯度方向分布、排除其它 GT/边界/padding、V_bg/A_bg/E_bg/bg_valid_ratio，图像不可读则该样本 bg unavailable，layout 不受影响）、`orientbench/metrics/statistics.py`（class-conditional percentile/saturate/normalized_entropy）、`scripts/04_compute_sources.py`（多进程按图像并行）。常数 beta=1.5/sigma=beta·max/radius=3σ/n_min=3/tau_bg=0.5 按文件；未给定常数 gamma/annulus/bins 标 dry-run，未改定义。
- buckets：`orientbench/buckets/thresholds.py`（class-conditional dry-run 百分位）、`stress_buckets.py` 扩展（near_square/dense_coherent/dense_incoherent/sparse_bg_strong/evidence_weak + domain_fragile/rotated_valid_mismatch placeholder，全部 pending_threshold_freeze）、`scripts/05_make_buckets.py`。
- score：`orientbench/core/registry.py`（9-detector taxonomy + A4 host pending + 三 head-type 冻结默认分定义）、`orientbench/metrics/selection_score.py`（dry-run GV proxy，标 not_detector_prediction/not_formal_calibration/not_official_result）、`scripts/06_compute_selection_scores.py`。
- GV baseline：`05` 内从 GT index 聚合 `gv_obliquity_baseline.csv`（dataset/split/class）。
- risk/NRC：`scripts/07_eval_risk_coverage.py`（dry-run score + SYNTHETIC orientation_risk，输出 AURC/Risk@70/90/NRC-AUC/oracle/random/degenerate，标 not_detector_performance）。
- probe matrix：`orientbench/reports/prediction_matrix.py` → `probe_matrix_template.csv`（template，PENDING；标 RHINO missing / A4 pending / SODA-A / ICDAR-MLT missing；未把 ARS-DETR 当 RHINO）。
- report：`orientbench/reports/bench_core.py` + `orientbench/io/reports.py` + `scripts/11_report_bench_core.py` → `bench_core_v01_report.md`（含 baseline/valid-invalid/dataset split+missing/GT 覆盖/GV 分布/source dry-run/bucket 数量/score 定义/NRC sanity/Risk@70·90/limitations/R1-R8 状态/RHINO 缺失/SODA-A·ICDAR-MLT 缺失/下一步）。
- configs：`project.yaml`、`datasets.yaml`、`detectors.yaml`、`pm_rules.yaml`（仅固定路径/数据集清单/baseline taxonomy/R1-R8 状态/pending；未伪造冻结阈值或 detector 可用性）。
- tests：`tests/test_sources_buckets.py`（11 例：layout neighbor/V_layout/D_nbr·R_nbr·A_align/class-conditional percentile/dense-coherent·incoherent/sparse-bg-strong/evidence-weak/score registry/dry-run 标记/probe matrix schema+missing）。

### 执行命令与结果
- `python -m pytest tests/ -q` → **44 passed**（7+17+9+11）。
- 闭环：00_env_check / 01_inventory / 02(dota10,dior,hrsc,fair1m @max-files 200) / 04(--stage core1,--max-bg-files 60,--jobs 16) / 05 / 06 / 07 / 11 全部成功。
- 参数小调整（已记录）：02 额外加 hrsc trainval + fair1m train 以覆盖任务四的 4 数据集 GV baseline；04 用 --jobs 16 多进程并行（按图像）。

### 数据规模 / CPU
- GT index（max-files 200）：DOTA-v1.0/train 2774 obj、DIOR-R/trainval 1019、HRSC2016/trainval 613、FAIR1M-v1.0/train 2874；全部 valid，invalid_geometry=0。
- 04 source：背景受控抽样 max_bg_files=60（已记录，非静默截断）；real 15.9s / user 64s（jobs=16 并行，背景 cv2 为主），机器 112 核。

### source/bucket/score dry-run 摘要
- layout V_layout：DOTA 2262/2774、DIOR 586/1019、FAIR1M 1204/2874、HRSC 87/613（密集车群高、稀疏船低，符合直觉）。
- buckets（dry-run percentiles, pending_freeze）：evidence_weak 占多（DOTA273/DIOR328/FAIR1M1085/HRSC374）；dense_coherent DOTA10/DIOR45/FAIR1M36/HRSC20；domain_fragile/rotated_valid_mismatch=0（placeholder）。
- score：dry-run GV proxy，per dataset/class 共 83 行 + 3 head-type 定义行。
- NRC-AUC（SYNTHETIC risk，sanity）：DIOR 0.255 / DOTA 0.176 / FAIR1M 0.197 / HRSC 0.216（∈(0,1)，degenerate=False）。

### GV baseline 摘要
`gv_obliquity_baseline.csv` 83 class 行。数据集汇总 near_square：DIOR 129/1019、DOTA 53/2774、FAIR1M 210/2874、HRSC 0/613。GV 中位：DOTA≈0.456 偏低（倾斜细长）、DIOR/airplane 等近轴偏高，形态合理。

### missing 清单
- dataset：SODA-A、ICDAR-MLT（缺失）。
- detector：RHINO-style rotated DETR（缺失，9 archetype 中 available 8 / missing 1）；A4 hybrid-host（frozen snapshot pending）。

### 停止条件检查
全部未触发：DATA_ROOT 存在、readme 在、GT parser 4/4 可用（0 invalid）、source 公式与项目文件一致、未装/下载依赖、未改原始数据、未替代 RHINO、未改 R1-R8、未冻结/改阈值。

### 产物路径
- 模块：`orientbench/buckets/{sources,thresholds,stress_buckets}.py`、`orientbench/metrics/{statistics,selection_score}.py`、`orientbench/core/registry.py`、`orientbench/reports/{prediction_matrix,bench_core}.py`、`orientbench/io/reports.py`
- 脚本：`scripts/{04_compute_sources,05_make_buckets,06_compute_selection_scores,07_eval_risk_coverage,11_report_bench_core}.py`
- configs：`configs/{project,datasets,detectors,pm_rules}.yaml`
- tests：`tests/test_sources_buckets.py`
- 输出：`outputs/bench_core/cache/sources_*.jsonl` + `sources_summary.json`、`outputs/bench_core/buckets/bucket_assignments_*.csv` + `bucket_thresholds_dryrun.json`、`outputs/bench_core/reports/{stress_bucket_summary,gv_obliquity_baseline,default_selection_score_report,nrc_auc_summary,probe_matrix_template}.csv`、`outputs/bench_core/reports/bench_core_v01_report.md`

### 下一步
阈值冻结（R8）→ RHINO host 裁示 / A4 frozen host → 接真实 predictions（03）替换 dry-run score 与 synthetic risk → GV/source 全量化 → SODA-A/ICDAR-MLT 路径裁示 → angle_version le90 符号核验后做 angle-error gate。

---

## [2026-06-25 17:44:39 CST] 来源: supervisor

### 输入/指令
监督员指令 006：确认 005（dry-run 闭环通过，44 tests，00-11 跑通，未触发停止条件）。**缺失数据集裁示**：SODA-A / ICDAR-MLT 当前非 Bench-Core 阻塞项，不下载/不改路径/不停工/不反复请示，保留为 missing dataset risk；full coverage 需声明覆盖时再由合作者提供路径或裁示排除。继续用已存在 5 数据集推进。本轮任务：prediction ingestion contract（schema+validator+synthetic，不跑 detector）、prediction 格式探测、GT-pred matching skeleton、angle_version audit、DOTA-v1.5 GT sanity、synthetic prediction 替换链路(03→07→11)、更新统一报告 + 生成 v02、补 tests、运行测试与轻量闭环、日志。边界：不推理/训练/下载/改 pth_data/改原始数据/冻结阈值/替代 RHINO/把 ARS-DETR 当 RHINO/声称 gate 通过/把 synthetic 写成真实 detector 输出/改 GV·NRC·score 定义。

### 行动/结论（实现模块）
- prediction contract：`orientbench/io/predictions.py`（PREDICTION_SCHEMA 17 字段、validate_prediction/validate_predictions、make_synthetic_prediction/generate_synthetic_predictions [仅由 GT + 可控 score/angle 扰动，标 is_synthetic/not_detector_output]、detect_format[json/jsonl/csv/pickle_placeholder/mmrotate_placeholder]、load_predictions[缺失→no_prediction_available 不阻塞]）。
- matching skeleton：`orientbench/metrics/matching.py`（同图同类、score 降序贪心、rotated IoU via shapely polygon=shapely_polygon，无 shapely 回退 approx_aabb 并标 approximate_iou；IoU 阈值 0.5 placeholder pending_freeze；match_image/match_dataset → matched_gt_id/match_status）。
- angle audit：`orientbench/reports/angle_audit.py` + `scripts/13_audit_angle_version.py`（只读 baseline config，正则提取 angle_version/box_type，config 无 token 回退 model_id 后缀，不可确认=unknown；HRSC mbox 标 uncertain；输出 angle_version_audit.csv/.md）。
- DOTA-v1.5 GT sanity：纳入 02 受控 GT index（--max-files 200），自动流入 sources/buckets/GV/report。
- synthetic prediction 链路：`scripts/03_collect_predictions.py`（synthetic 默认；--pred-file 走 real 格式探测+validator）；改写 `scripts/07_eval_risk_coverage.py`（优先 prediction 路径：匹配 pred↔GT，orientation_risk=角度误差 deg，selection_score=pred score；无 pred 回退 synthetic-risk demo）。
- 报告：更新 `orientbench/reports/bench_core.py`（v01 新增 §8.1 prediction contract、§8.2 angle audit、§8 risk_mode/matched 列、§11 SODA-A/ICDAR-MLT 006 裁示 + synthetic 声明）+ 新增 build_v02_prediction_contract_report；`scripts/11` 同时产出 v01 与 v02。
- tests：`tests/test_predictions.py`（12 例：schema 校验/synthetic fixture 标记/跳过 invalid/missing 文件/格式探测/matching skeleton/identical IoU≈1/approximate_iou 警告[monkeypatch 无 shapely]/config 扫描/unknown+model_id 回退/DOTA-v1.5 path/report dry-run 标签）。

### 执行命令与结果
- `python -m pytest tests/ -q` → **56 passed**（7+17+9+11+12）。
- 闭环：00 → 01 → 02(dota10/dota15/dior/hrsc/fair1m @200) → 03(synthetic) → 04(core1,jobs16,max_bg60) → 05 → 06 → 07(prediction 路径) → 13(angle audit) → 11(v01+v02) 全部成功。
- 参数小调整（已记录）：02 含 dota15/hrsc/fair1m 以覆盖 5 数据集；03 默认 synthetic 全 GT index；07 新增 --source auto 自动选 prediction 路径；11 增产 v02。

### 数据规模 / prediction contract 状态
- GT index（max-files 200）：dota10 2774 / **dota15 6727** / dior 1019 / hrsc 613 / fair1m 2874 obj，全 valid，invalid_geometry=0。
- synthetic predictions：5 文件，总 **14007** preds，validator 全过（14007/14007 valid）；is_synthetic=true / not_detector_output=true。
- matching（shapely_polygon，IoU≥0.5 placeholder）：matched DIOR 978/1019、DOTA10 2174/2774、DOTA15 6140/6727、FAIR1M 2753/2874、HRSC 326/613（HRSC 细长船角扰动后 IoU 掉落，匹配率低，已记录）。
- NRC-AUC（risk_mode=synthetic_prediction_angle_error，SYNTHETIC）：DIOR 0.045 / DOTA10 0.029 / DOTA15 0.033 / FAIR1M 0.028 / HRSC 0.042（synthetic 选择器近 oracle，∈(0,1)，degenerate=False；不代表 detector 性能）。

### angle_version audit 结果
73 baselines 全 **le90**；来源 config_scan 70 + model_id_suffix 3（config 无显式 token 的 3 条由 model_id 后缀推断，已标 source）；theta_unit=rad_inferred。dataset GT 角度：DOTA/DIOR/FAIR1M=le90_derived(minAreaRect, sign 未断言)；HRSC=mbox_ang_rad **uncertain**（le90 等价未核验）。未伪造确定性。

### missing dataset 裁示留痕
SODA-A / ICDAR-MLT：非阻塞，不下载/不改路径；保留 missing dataset risk；写入 v01/v02 报告与 pm 风险。

### 停止条件检查
全部未触发：DATA_ROOT/readme 在、GT parser 全可用（0 invalid）、未装/下载依赖、未改原始数据、未替代 RHINO、未冻结阈值、未改 R1-R8、angle_version 与项目文件无根本冲突、真实 prediction 接入未要求跑 detector（本轮 synthetic）。

### 产物路径
- 模块：`orientbench/io/predictions.py`、`orientbench/metrics/matching.py`、`orientbench/reports/angle_audit.py`、更新 `orientbench/reports/bench_core.py`
- 脚本：`scripts/03_collect_predictions.py`、`scripts/13_audit_angle_version.py`、更新 `scripts/07_eval_risk_coverage.py`、`scripts/11_report_bench_core.py`
- tests：`tests/test_predictions.py`
- 输出：`outputs/bench_core/predictions/pred_*.jsonl` + `predictions_summary.json`、`outputs/bench_core/reports/{angle_version_audit.csv,angle_version_audit.md,nrc_auc_summary.csv,bench_core_v01_report.md,bench_core_v02_prediction_contract.md}`、`outputs/bench_core/gt_index/dota15_train.*`

### 下一步
接真实 detector predictions（03 --pred-file，json/jsonl/csv）替换 synthetic → angle_version le90 符号一致性核验（尤其 HRSC）→ 阈值冻结(R8) → 正式 NRC/Risk gate。真实 prediction 若需启动 detector 推理则触发停手汇报。

---

## [2026-06-25 18:02:57 CST] 来源: supervisor

### 输入/指令
监督员指令 007：确认 006（prediction contract / angle audit / synthetic 替换链路放行，56 tests，输出仍 dry-run/SYNTHETIC，不得据此做正式 gate）。**裁示**：现在不能训练，训练非下一步；当前优先级仍是 Bench-Core + 真实 prediction 接入。训练启动前须满足：R8 阈值冻结、D_cal/D_audit 互斥、真实 prediction 接入、angle_version 符号核验、RHINO/A4 host 裁示、训练 config/log/schedule/lr 对齐方案、首 epoch 异常停止规则入日志。在此之前不训练、不推理（除非明确指令）、不下载、不替代 RHINO。本轮做 readiness packet：任务一 real prediction discovery、任务二 real prediction import dry-run、任务三 D_cal/D_audit split builder、任务四 threshold freeze checklist、任务五 training readiness checklist、任务六 更新报告、任务七 tests、任务八 运行测试与轻量闭环、日志。边界：不推理/训练/下载/改 pth_data/改原始数据/冻结阈值/替代 RHINO/把 ARS-DETR 当 RHINO/声称 gate 通过/把 synthetic 当真实输出/改 GV·NRC·score 定义/改 R1-R8。

### 行动/结论（实现模块）
- discovery：`orientbench/io/prediction_discovery.py`（只读扫描 pth_data + orientbench/outputs + orientbench/pth_data，size-bounded sniff，schema 分类 matches/coco_style_needs_conversion/gt_like/training_log；不全量加载大文件，>5MB json 仅 sniff 4KB）+ `scripts/14_discover_predictions.py` → prediction_discovery.{csv,md}。
- real import dry-run：扩展 `scripts/03_collect_predictions.py`（新增 --baseline-id/--dataset/--split/--dry-run-validate-only/--detector-id；可解析则 schema 校验 + 预览到 predictions/preview/，不覆盖正式 outputs；缺失记 no_real_prediction_found 不报错）。
- splits：`orientbench/data/splits.py`（md5 deterministic hash split，D_cal∩D_audit=∅，可复现）+ `scripts/15_build_audit_splits.py` → splits/D_cal_*.csv、D_audit_*.csv、split_meta_*.json。
- readiness：`orientbench/reports/readiness.py`（CHECK ONLY，状态仅 ready/blocked/pending/not_applicable，pending 不改 ready）+ `scripts/16_readiness_check.py` → readiness_check.{md,json}。
- training readiness：`orientbench/reports/training_readiness.py`（training_allowed 默认 false）+ `scripts/17_training_readiness.py` → training_readiness.{md,json}。
- 报告：`orientbench/reports/bench_core.py` v01 新增 §8.3 discovery / §8.4 D_cal-D_audit / §8.5 readiness / §8.6 training readiness / §12 remaining blockers + next actions；未删除 RHINO/SODA-A/ICDAR-MLT 风险记录。
- tests：`tests/test_readiness.py`（8 例：discovery schema 分类与字段/missing real prediction/hash split 可复现/D_cal-D_audit 互斥/readiness pending+blocked+thresholds pending+RHINO missing/training_allowed=false/report 无正式 gate 声明）。

### 执行命令与结果
- `python -m pytest tests/ -q` → **64 passed**（7+17+9+11+12+8）。
- 闭环：14 → 15 → 16 → 17 → 03(real --dry-run-validate-only on bbox.json) → 03(real missing→no_real_prediction_found) → 03(synthetic 复原) → 11(v01+v02) 全部成功。
- 参数小调整（已记录）：03 --detector 增 --detector-id 别名 + 新 dry-run/preview 参数；16/17 读 configs/thresholds.yaml(pyyaml)。

### real prediction discovery 摘要
69 candidates，external 19，**coco_style_needs_conversion 2**（point2rbox_v2_pseudo_labels.bbox.json 等，190149 records，含 image_id/bbox/score/category_id），ready_schema 0 → **no_real_prediction_found=True**。03 real dry-run 对 bbox.json：format=json、190149 records、schema 校验 0 ok/190149 bad（缺 obb_* 命名，需转换），预览写入 predictions/preview/，**未覆盖正式 outputs**；缺失文件路径正确返回 no_real_prediction_found 不报错。

### D_cal/D_audit split 结果
5 数据集全部 **mutually_exclusive=True，intersection=0**（deterministic md5 hash，cal_fraction=0.5）：dior 100/100、dota10 83/78、dota15 89/82、fair1m 82/92、hrsc 102/98。

### readiness 结论
overall_readiness=**blocked**（ready=2 pending=7 blocked=3），formal_gate_allowed=**False**。blocked：rhino_host、a4_hybrid_host、soda_a_icdar_mlt_datasets；pending：B_C1/A_A4/D2 阈值、freeze_time、responsible_role、real_prediction_available、angle_version_certain；ready：change_log_present、dcal_daudit_disjoint。

### training readiness 结论
**training_allowed=False（expected False）**。reasons：thresholds not frozen、RHINO missing、A4 host pending、real predictions not yet formal、human approval required。首 epoch 停止规则已记入 checklist（first_epoch_stop_rule=ready：首 epoch mAP 明显偏低则停并报告）。

### 停止条件检查
全部未触发：DATA_ROOT/readme 在、未装/下载依赖、未改原始数据、未替代 RHINO、未冻结阈值、未改 R1-R8、未启动 detector 推理/训练（real 仅 dry-run validate，未跑 detector）。

### 产物路径
- 模块：`orientbench/io/prediction_discovery.py`、`orientbench/data/splits.py`、`orientbench/reports/{readiness,training_readiness}.py`、更新 `orientbench/reports/bench_core.py`、`scripts/03_collect_predictions.py`
- 脚本：`scripts/{14_discover_predictions,15_build_audit_splits,16_readiness_check,17_training_readiness}.py`
- tests：`tests/test_readiness.py`
- 输出：`outputs/bench_core/reports/{prediction_discovery,readiness_check,training_readiness}.{csv/md/json}`、`outputs/bench_core/splits/{D_cal_*,D_audit_*,split_meta_*}.{csv,json}` + `splits_summary.json`、`outputs/bench_core/predictions/preview/pred_real_preview.jsonl`、更新 `bench_core_v01_report.md` / `bench_core_v02_prediction_contract.md`

### 下一步（remaining blockers）
1. 阈值冻结(R8)：责任角色提交 B/C1、A/A4、D2 阈值与检验，填 thresholds.yaml + freeze_time。
2. RHINO host / A4 frozen host 裁示。
3. 真实 detector predictions 转换为 prediction schema（coco bbox→obb_*+class_name）并经 03 --pred-file 正式接入（接入若需 detector 推理则停手汇报）。
4. angle_version le90 符号核验（尤其 HRSC）。
5. 全部满足 + 人工批准后方可考虑训练（training_allowed 当前 False）。

---

## [2026-06-25 18:22:30 CST] 来源: supervisor

### 输入/指令
监督员指令 008：确认 007（Readiness Packet 通过，64 tests，training_allowed=False 正确）。仍不得训练/推理/下载/冻结阈值/替代 RHINO。本轮按正常流程清理训练前阻塞项，目标是让合作者能裁示（哪些 prediction 可转换、阈值如何冻结、RHINO/A4 怎么处理、训练何时可批准）。任务1 COCO/pseudo-label→prediction schema 转换器（bbox_only/obb_unavailable/not_orientation_prediction/not_formal_gate 标注，不把 HBB 当 OBB）；任务2 ingestion 分级（ready_schema/convertible_bbox_only/convertible_needs_mapping/unsupported/missing，bbox_only 不可入正式 angle gate）；任务3 angle_version 核验方案（uncertain 保留）；任务4 thresholds freeze proposal（草案，不冻结，另存 draft）；任务5 RHINO/A4 host decision packet；任务6 training_readiness 可执行清单；任务7 tests；任务8 运行。边界同前。

### 行动/结论（实现模块）
- 转换器：`orientbench/io/prediction_converters.py`（detect_bbox_kind: 4=hbb_xywh→bbox_only, 5=obb_cxcywha→有 OBB, 8=poly8→minAreaRect；convert_coco_record/records；全部 not_formal_gate=True、needs_category_mapping=True；HBB 永不伪装 OBB）+ `scripts/18_convert_predictions.py`（只读源，输出 predictions/converted/，不覆盖正式）。
- ingestion 分级：`prediction_discovery.py` 增 probe_bbox_dim + classify_ingestion（ready_schema/convertible_bbox_only/convertible_needs_mapping/unsupported/missing/synthetic_internal；can_enter_formal_orientation_risk，bbox_only 恒 False）+ `scripts/14` 增产 prediction_ingestion_plan.{md,csv}。
- angle 核验方案：`orientbench/reports/angle_version_plan.py`（6 checks: DOTA/DIOR/FAIR1M le90 sign、HRSC mbox/le90 equiv、prediction theta unit、minAreaRect normalization）+ `scripts/19` → angle_version_check_plan.{md,csv}，全 uncertain/unverified。
- threshold 草案：`orientbench/reports/threshold_proposal.py`（proposed_by=claude_draft, approval_status=pending, freeze_status=draft_not_frozen）+ `scripts/20` → `configs/thresholds.draft.yaml` + threshold_freeze_proposal.md，**不改 thresholds.yaml**。
- host packet：`orientbench/reports/readiness.py:build_host_decision_packet` + `scripts/16` → host_decision_packet.md（RHINO missing、ARS-DETR 不可替代、A4 pending、训练前对齐方案、需裁示事项）。
- training readiness 可执行清单：扩展 `training_readiness.py`（can_train_now=false + remaining_before_training / human_decisions_required / files_needed / commands_allowed_after_approval / stop_conditions_for_first_epoch）+ `scripts/17` 渲染。
- tests：`tests/test_conversion_packet.py`（11 例：bbox kind、bbox_only 非正式 OBB gate、obb5 携带朝向但 not_formal、converted schema valid、convert stats no formal gate、ingestion 分级、angle plan 保留 uncertain、threshold draft 不冻结且 thresholds.yaml 仍 pending、host packet 禁 ARS-DETR 替代、training 仍 false、report 无正式 gate 声明）。

### 执行命令与结果
- `python -m pytest tests/ -q` → **75 passed**（7+17+9+11+12+8+11）。
- 闭环：18 → 14 → 19 → 20 → 16 → 17 → 11 全部成功。
- 参数小调整（已记录）：18 默认源指向 007 发现的 point2rbox bbox.json，--max-records 20000 受控（truncated 记录）；14 增产 ingestion plan；16 增产 host packet。

### prediction conversion 摘要
源 point2rbox_v2_pseudo_labels.bbox.json（190149 records，bbox=5 元组 [cx,cy,w,h,theta] **rotated OBB**，非 HBB）。转换 20000/190149（truncated=True 已记录），kinds={obb_cxcywha:20000}，bbox_only=0，oriented=20000，17 字段 schema validate ok=20000/bad=0；**any_can_enter_formal_angle_gate=False**（pseudo-label + angle 未核验 + category 未映射）。输出 predictions/converted/，未覆盖正式。

### ingestion plan
ingestion_status 计数（含本项目 outputs）：convertible_needs_mapping 69、unsupported 18、synthetic_internal 5；external 真实候选 19（2 个 coco-style）。**can_enter_formal_orientation_risk(now)=0**；no_real_prediction_found=True。bbox_only 一律不可入正式 angle gate。

### angle_version plan
6 checks 全 uncertain/unverified（HRSC mbox/le90 equiv 最高优先；minAreaRect normalization=derived_unverified）。GV-obliquity 对符号不变（不受影响），angle-error gate 受影响。未伪造确定性。

### threshold draft
`configs/thresholds.draft.yaml` + threshold_freeze_proposal.md，覆盖 B/C1（OT vs GT-identity Δ=0.03、DropRate=0.5、CycleErr=0.3、H_T、padding-only、OTA+KL）、A/A4（partial-corr≤0.20、HSIC p≥0.05、A4 vs GV/entropy/score Δ、all-source vs best-single Δ）、D2（Spearman≤0.95、FDR=BH、Bonferroni、cell effect size）。全部 proposed_by=claude_draft/approval_status=pending。**thresholds.yaml freeze_status 仍 pending（已验证未改）**。

### host decision packet
host_decision_packet.md：RHINO-style rotated DETR missing；ARS-DETR 不可替代 RHINO；C1/B 启动需裁示下载/训练/补充/批准替代；A4 hybrid-host frozen snapshot pending 且不得用 RHINO/convenience snapshot 替代；训练前需 config/log/schedule/lr/batch 对齐方案。

### training_allowed 状态
**仍 training_allowed=False / can_train_now=False**（expected False）。无 pending 改 ready。首 epoch 停止规则、commands_allowed_after_approval 等已入可执行清单。

### 阻塞项
阈值未冻结(B/C1/A/A4/D2 + freeze_time + responsible_role)、RHINO missing、A4 host pending、SODA-A/ICDAR-MLT missing、real prediction 0 可入正式（需转换+映射+angle 核验）、angle_version 6 项 uncertain、human approval required。

### 停止条件检查
全部未触发：未训练/推理/下载/改 pth_data 或原始数据/冻结阈值/替代 RHINO/改 R1-R8·GV·NRC·score 定义；DATA_ROOT/readme 在。

### 产物路径
- 模块：`orientbench/io/{prediction_converters,prediction_discovery}.py`、`orientbench/reports/{angle_version_plan,threshold_proposal,readiness,training_readiness}.py`、`scripts/{18,19,20}` + 更新 `scripts/{14,16,17}`
- tests：`tests/test_conversion_packet.py`
- 输出：`outputs/bench_core/predictions/converted/converted_*.jsonl`、`outputs/bench_core/reports/{prediction_ingestion_plan,angle_version_check_plan,threshold_freeze_proposal,host_decision_packet}.{md,csv}`、`configs/thresholds.draft.yaml`

### 下一步
合作者裁示：① 批准/修订 threshold draft 并由责任角色用 D_cal 标定后冻结；② RHINO host 处置 + A4 frozen host 提供；③ 授权某 prediction 转换后用于 ingestion（非正式 gate）；④ angle_version 6 项核验（HRSC 优先）。全部满足 + 人工批准后方议训练（当前 training_allowed=False）。

---

## [2026-06-25 23:34:42 CST] 来源: supervisor

### 输入/指令
监督员指令 009：确认 008（decision packet 完成，75 tests，training_allowed=False 正确）。仍不得训练/推理/下载/冻结/替代 RHINO。本轮清理可由 cc 自行完成的工程阻塞项，让合作者裁示后能直接进入真实 prediction 接入或被批准的训练流程。任务1 angle_version evidence audit（用证据降 uncertain，不伪造，重点 HRSC mbox/le90）；任务2 prediction import matrix（baseline×dataset 状态）；任务3 inference command plan（只计划不执行）；任务4 threshold freeze review packet（不改 thresholds.yaml）；任务5 collaborator approval form（默认 pending）；任务6 更新 readiness/training（仍 false）；任务7 tests；任务8 运行。边界同前。

### 行动/结论（实现模块）
- angle evidence：`orientbench/reports/angle_evidence.py`（poly 数据集 poly→obb→poly round-trip IoU + θ 范围；HRSC mbox_ang 范围 + OBB-HBB extent vs 标注 box_* 交叉验证）+ `scripts/21`。
- import matrix：`orientbench/reports/prediction_import_matrix.py`（合并 inventory×dataset×discovery，7 状态分类）+ `scripts/22`。
- inference plan：`orientbench/reports/inference_plan.py`（每 valid baseline×present dataset 的 config/ckpt/env/GPU/转换需求/阻塞，executable_now=False）+ `scripts/23`。
- threshold review：`threshold_proposal.py:build_threshold_review`（module/field/draft_value/rationale/needs_D_cal/affects_D_audit/approval_status=pending/risk_if_changed_after_run）+ `scripts/24`（运行前 assert thresholds.yaml 仍 pending）。
- collaborator form：`readiness.py:build_collaborator_form`（D1–D7 全 pending，不替勾选）+ `scripts/25`。
- 更新 readiness angle 项读 evidence audit；bench_core report 增 §8.7 angle evidence / §8.8 import matrix / §8.9 inference plan + review/form 引用。
- tests：`tests/test_evidence_matrix.py`（8 例：poly resolved_with_evidence、HRSC 保留 uncertain、norm_dataset missing、import matrix 状态分类、inference plan 不可执行、threshold review 不改 thresholds.yaml 且全 pending、approval form 全 pending、training_allowed 仍 false）。

### 执行命令与结果
- `python -m pytest tests/ -q` → **83 passed**（+8）。
- 链路：21 → 22 → 23 → 24 → 25 → 16 → 17 → 11 全部成功。
- 修正 1 bug：import matrix 误用 json.load 读 csv，已删多余行。

### angle audit 变化
evidence audit 把 angle uncertain 从 6 降到 **2**（计算证据支撑）：
- DOTA-v1.0/v1.5、DIOR-R、FAIR1M-v1.0 = **resolved_with_evidence**（poly→obb→poly round-trip IoU：DIOR 0.995、FAIR1M 0.96、DOTA ~0.92[受 GT 多边形非矩形上限约束]，θ 全在 [-π/2,π/2)）；范围声明为 GT le90-range 解析保真，**非检测器符号等价**。
- Bench-Core minAreaRect 归一化 = resolved_with_evidence。
- **HRSC2016 = uncertain**（mbox_ang 在 le90 范围内，但与标注 box_* HBB 交叉验证不一致 W~9%/H~12%，标注 HBB 偏松 → 无法证明检测器 le90 等价，**保持 uncertain，未伪造**）。
- prediction theta unit = uncertain（无真实 prediction）。

### prediction import matrix 摘要
75 行，status 计数：needs_inference 58、blocked_missing_dataset 8（SODA-A/ICDAR-MLT baselines）、not_applicable 6（invalid baselines）、convertible_nonformal 1（baseline 64 point2rbox pseudo-label）、blocked_missing_detector 2（RHINO/A4）。**ready_schema=0**（无真实 prediction 可直接导入）。

### inference command plan 摘要
75 行，inference-planned（approval-gated）59、blocked 16（RHINO/A4 + missing dataset）；**any_executable_now=False**；每行 needs_prediction_schema_conversion=True（mmrotate pkl→schema）；仅计划未执行。

### threshold review 路径 / approval form 路径
- `outputs/bench_core/reports/threshold_freeze_review.{md,csv}`（10 字段，全 approval_status=pending；运行前后 thresholds.yaml 字节级未变，freeze_status=pending）。
- `outputs/bench_core/reports/collaborator_decision_form.md`（D1–D7 全 pending）。

### training_allowed 状态
**仍 training_allowed=False / can_train_now=False**。readiness overall=blocked，formal_gate_allowed=False。无 pending 改 ready。

### 剩余阻塞项
阈值未冻结、RHINO missing、A4 host pending、SODA-A/ICDAR-MLT missing、real prediction 0 可直接导入（needs_inference/convertible 非正式）、HRSC angle uncertain、human approval required。

### 停止条件检查
全部未触发：未训练/推理/下载/装依赖/改 pth_data 或原始数据/冻结阈值/替代 RHINO/改 R1-R8·GV·NRC·score 定义；DATA_ROOT/readme 在。

### 产物路径
- 模块：`orientbench/reports/{angle_evidence,prediction_import_matrix,inference_plan}.py`、`orientbench/reports/{threshold_proposal,readiness,bench_core}.py`（更新）
- 脚本：`scripts/{21_verify_angle_conventions,22_prediction_import_matrix,23_plan_inference_commands,24_threshold_review,25_collaborator_form}.py`
- tests：`tests/test_evidence_matrix.py`
- 输出：`outputs/bench_core/reports/{angle_version_evidence_audit,prediction_import_matrix,inference_command_plan,threshold_freeze_review}.{md,csv,json}`、`collaborator_decision_form.md`

### 下一步
合作者裁示（collaborator_decision_form D1–D7）：批准 threshold draft → 责任角色用 D_cal 标定后冻结；RHINO/A4 host 处置；是否允许推理（D5）/训练（D6）/prediction 转换接入（D7）；HRSC angle 等价核验（需真实 prediction 或检测器约定文档）。批准前 training_allowed 维持 False。

---

## [2026-06-25 23:46:30 CST] 来源: supervisor

### 输入/指令
监督员指令 010：确认 009（工程阻塞项完成，83 tests，training_allowed=False 正确）。仍不得训练/真实推理/下载/冻结/替代 RHINO。本轮做 **approval-gated execution package**：合作者批准 D5 后能直接跑受控推理、批准 D1 后能按 D_cal 标定冻结；本轮只写 runner/plan/guards/tests，不执行真实推理、不训练。任务1 guarded inference runner（默认拒绝，需 --approval-token+--execute；execute 分支不得调 detector，返回 blocked_by_supervisor）；任务2 output path policy；任务3 baseline shortlist（RHINO 单列 blocked，不用 ARS-DETR 替代）；任务4 D_cal 标定准备（不冻结）；任务5 guarded conversion/import（仅 approval 才写正式 outputs，否则 preview；bbox/nonformal 不入 formal angle gate）；任务6 collaborator form D8-D10；任务7 readiness/training 新检查（training_allowed 仍 false）；任务8 tests；任务9 运行。边界同前。

### 行动/结论（实现模块）
- guarded runner：`orientbench/runners/inference_runner.py`（build_inference_command 仅构造字符串；validate_guards 检查 dataset present/not-silently-skipped、config/ckpt 存在、output path under predictions、baseline valid、not RHINO substitution、thresholds 状态；run_guarded 默认 dry_run_plan；execute+token 但未批准→refused_not_approved；即使已批准→**blocked_by_supervisor，detector_invoked=False，永不调 detector**）+ `scripts/30`。approvals 读 `configs/approvals.yaml`（合作者控制，cc 只读，默认全 pending/token null）。
- output policy：`orientbench/io/output_policy.py`（强制 outputs/predictions/{dataset}/{baseline_id}/，文件名含 baseline/dataset/split/timestamp；validate 拒绝 pth_data/third_party/dataset/项目根散文件）。
- shortlist：`orientbench/reports/baseline_shortlist.py`+`scripts/26`（每 archetype 选 1 valid 代表；ARS-DETR=detr_like 标注“NOT a RHINO substitute”；RHINO 单列 blocked_missing）。
- calibration plan：`orientbench/reports/calibration_plan.py`+`scripts/27`（每 draft 阈值的 input_needed/dcal_estimation/daudit_audit/status；依赖真实 prediction 的标 blocked；不写 thresholds.yaml，运行前 assert pending）。
- guarded import：`scripts/28_import_predictions_guarded.py`（转换后仅 D7 approved+token 才写正式 outputs/predictions，否则 preview；any_can_enter_formal_angle_gate=False）。
- collaborator form D8/D9/D10（合并 runner / D5 后执行推理 / D1 后冻结阈值），全 pending。
- readiness 新增 6 检查（guarded_inference_runner_available、output_policy_valid、baseline_shortlist_exists、calibration_plan_exists、formal_inference_approval=blocked、training_approval=blocked）。
- tests：`tests/test_execution_package.py`（9 例：output path under predictions / 拒绝 forbidden、runner 默认拒绝、execute 无批准拒绝、execute 分支即使模拟批准也 blocked_by_supervisor 不调 detector、is_approved 逻辑、shortlist ARS-DETR=DETR-like 非 RHINO + RHINO blocked、calibration 无真实 prediction blocked、training_allowed false）。

### 执行命令与结果
- `python -m pytest tests/ -q` → **92 passed**（+9）。
- 链路：26 → 27 → 28(无 token→preview) → 30(dry-run 6 targets) → 30(--execute --approval-token FAKE→refused) → 16 → 17 → 25 → 11 全部成功。
- 参数小调整（已记录）：30 默认对 shortlist selected baselines 出 dry-run plan；28 默认源 point2rbox bbox.json，--max-records 3000。

### guarded inference runner 状态
默认 dry_run_plan；6 个 shortlist baseline 全 guards_ok=True、detector_invoked=False。--execute --approval-token FAKE → **refused_not_approved**（token 与 approvals.token=null 不匹配）。模拟“已批准”分支（test monkeypatch）→ **blocked_by_supervisor，detector_invoked=False**。`inference_guarded_plan.json` any_detector_invoked=False。**未启动任何 detector**。

### baseline shortlist 摘要
selected 6：#1 oriented_rcnn_r50（two-stage）、#7 lsknet（strong-backbone）、#32 rtmdet_s（one-stage realtime）、#20 retinanet_psc（angle-coder）、#14 arsdetr（**DETR-like，非 RHINO 替代**）、#64 point2rbox_v2（weak/pseudo）；rotated_detr_rhino=**blocked_missing**（不得用 ARS-DETR 替代）。

### calibration plan 摘要
10 字段：**blocked 9**（依赖真实 detector prediction，需 D5/D7 批准后接入）、ready_to_estimate 1；have_real_predictions=False、have_splits=True。thresholds.yaml UNCHANGED。

### output policy
PREDICTIONS_ROOT=outputs/predictions/{dataset}/{baseline_id}/；拒绝 pth_data/third_party/dataset/项目根。28 无批准 → 写 preview（outputs/bench_core/predictions/preview/），未写正式 outputs/predictions（该目录仍空）。

### training_allowed 状态
**仍 training_allowed=False / can_train_now=False**。readiness overall=blocked（ready=6 pending=7 blocked=5），formal_gate_allowed=False。无 pending 改 ready。

### 剩余阻塞项
阈值未冻结、RHINO missing、A4 host pending、SODA-A/ICDAR-MLT missing、real prediction 未接入（needs_inference，D5 未批准）、HRSC angle uncertain、formal_inference_approval/training_approval=blocked、human approval required。

### 停止条件检查
全部未触发：未训练/真实推理（detector_invoked 全 False）/下载/装依赖/改 pth_data 或原始数据/冻结阈值/替代 RHINO/改 R1-R8·GV·NRC·score 定义；DATA_ROOT/readme 在。

### 产物路径
- 模块：`orientbench/runners/inference_runner.py`、`orientbench/io/output_policy.py`、`orientbench/reports/{baseline_shortlist,calibration_plan}.py`、`orientbench/reports/readiness.py`(更新)、`configs/approvals.yaml`
- 脚本：`scripts/{26_select_baselines,27_plan_calibration,28_import_predictions_guarded,30_run_inference_guarded}.py`
- tests：`tests/test_execution_package.py`
- 输出：`outputs/bench_core/reports/{baseline_shortlist,calibration_plan}.{md,csv}`、`inference_guarded_plan.json`、`collaborator_decision_form.md`(含 D8-D10)、`outputs/bench_core/predictions/preview/guarded_preview_b64.jsonl`、`outputs/bench_core/predictions/guarded_import_summary.json`

### 下一步
合作者裁示 collaborator_decision_form D1–D10。批准 D5+下发 token → `30_run_inference_guarded --execute --approval-token <token>`（届时由获授权方启用执行，本 cc 轮不执行）；批准 D7 → guarded import 写正式 outputs/predictions；批准 D1 → 责任角色用 D_cal 标定 calibration_plan 中 blocked 项后冻结 thresholds.yaml；HRSC angle 等价待真实 prediction 核验。批准前 training_allowed 维持 False。

---

## [2026-06-26 00:15:33 CST] 来源: supervisor

### 输入/指令
监督员指令 011：批准 D5(真实 detector 推理)+D7(转换写正式 outputs/predictions)；**不批准 D6(训练)、不替代 RHINO、不冻结 thresholds(D10/D1 仅允许 D_cal 标定/草案)**。approval token=`SUPERVISOR_APPROVED_011_D5_D7_REAL_PREDICTIONS_ONLY`。目标：用已有 valid baseline 跑第一批真实 predictions、转统一 schema、跑真实 prediction 版 risk/NRC sanity、输出阈值冻结依据。受控小规模 smoke，不全量、不误用 test set、不训练、不下载。

### approval token
`SUPERVISOR_APPROVED_011_D5_D7_REAL_PREDICTIONS_ONLY`（写入 configs/approvals.yaml：D5=allow, D7=allow, D9=allow；D6=deny, D10=deny, D1=pending）。

### 环境/资源策略
- 探测到可用 conda env：**mr**（mmrotate 0.3.4 / mmcv1.7.2 / torch1.12 / py3.8）、**mr_dev1x & p2_foundation**（mmrotate 1.0.0rc1 / mmcv2.2 / torch2.4 / py3.10），各 4×A30。readme 命名 env（pcp-obb/ars）不存在。
- 1 卡 smoke（CUDA_VISIBLE_DEVICES 单卡），每 baseline 20 图 val 子集（symlink，未改原始数据）。CPU<48。
- 子集：DOTA-v1.0 **val**（非 test），从 dota1.0/split_ss_dota10/val 取前 20 annfiles+images symlink 到 outputs/predictions/DOTA-v1.0/1/raw/subset。

### 每条 inference 命令/结果（开始-结束）
- **b1 oriented_rcnn_r50（1.x, mr_dev1x, mmrotate_1x/tools/test.py）**：00:07:56→00:58:11，exit0，子集 mAP 0.7403（全 val 0.7061，无异常），result_b1.pkl 114KB。
- **b20 rotated_retinanet_psc_r50（1.x, mr_dev1x）**：00:01:09→00:01:23，exit0，子集 mAP 0.3692，result_b20.pkl 177KB。
- **b32 rotated_rtmdet_s**：exit1 → inference_command_unresolved（config 基于 ai4rs，eager-load train/annfiles；需安装 ai4rs repo=依赖，未做）。
- **b7 oriented_rcnn_lsknet_s（0.x, mr, mmrotate_034）**：exit1 → inference_command_unresolved（`LSKNet is not in the models registry`，需 LSKNet repo 注册）。
- **b14 arsdetr_r50（0.x, ARS-DETR repo）**：exit1 → inference_command_unresolved（`ARSDETR is not in the models registry`，需 ARS-DETR fork mmrotate 安装）。
- **b64 point2rbox_v2**：blocked_weak_pseudo（weak/pseudo 特殊处理，跳过）。
- 所有命令、日志全路径见 outputs/logs/infer_b*.log。

### raw / schema 路径
- raw pkl：outputs/predictions/DOTA-v1.0/{1,20}/raw/result_b*.pkl
- schema（D7 approved 写正式）：outputs/predictions/DOTA-v1.0/{1,20}/schema/pred_b*_DOTA-v1.0_val.jsonl（is_synthetic=False, not_formal_gate=True）

### 转换结果
mmrotate 1.x pkl→17 字段 schema（`convert_mmrotate1x_pkl`）：b1 921 dets、b20 2428 dets，schema validate 全过；angle_unit=rad, angle_version=le90, source_path/baseline_id/detector_id 齐全。

### matching + risk/NRC smoke 结果（**关键发现：angle 约定根因已定位**）
- GT subset objects=587；b1 matched 547、b20 matched 486（shapely IoU≥0.5）。
- **naive median angle error ≈88°**，但 **swap-aware（计 le90 (w,h,θ)↔(h,w,θ+90°) 二义性）median ≈0.9°（b1 0.88, b20 1.04）**，64% pair 经 +90° 显著降误差。
- 根因：Bench-Core `poly8_to_obb`(cv2.minAreaRect) 选边约定与 mmrotate `poly2obb_le90` 长边/edge_swap 约定**系统性差 ~90°**。即 **GT 解析约定问题，非 detector 质量——真实 prediction 朝向其实亚度级精确**。
- 据此 **angle_error_gate_status=blocked_angle_uncertain**，naive risk/NRC（b1 NRC=1.50/Risk@70=64.5°，b20 NRC=0.88/Risk@70=49.7°）标 **INVALID_angle_convention_mismatch**，**不可用于任何正式结论**。与 009 evidence audit“detector 符号等价 uncertain”一致，现以真实 prediction 定位根因。

### 失败/跳过原因汇总
0.x/fork/ai4rs baseline（#7/#14/#32）因自定义模型未在已装 mmrotate 注册而 inference_command_unresolved；解决需安装其自带 repo（=依赖安装→停手条件，未执行）。#64 weak/pseudo 跳过。

### calibration plan 更新
have_real_prediction_smoke=True(2)，但 smoke_angle_convention_blocked=True → angle-error 相关阈值仍不能用 smoke 标定；score/coverage 类可先非正式探索。thresholds.yaml 未改（freeze_status=pending）。

### readiness / training_allowed
real_prediction_available=**pending**（real_prediction_smoke_available=2，NON-formal，angle gate blocked）。readiness overall=**blocked**，formal_gate_allowed=**False**。**training_allowed=False**（未改）。

### 测试
`python -m pytest tests/ -q` → **94 passed**（+2：mmrotate1x 转换 schema、swap-aware angle error）。

### 停止条件检查
未触发：未训练、未下载/装依赖（注：fork baseline 需装 repo 时未装、记 unresolved）、未改 pth_data/原始数据、未冻结阈值、未替代 RHINO、未改 R1-R8/GV/NRC/score 定义；首个真实 inference（b1）mAP 与 baseline 一致无异常。真实 inference 已被 D5 授权，故运行不属停手项。

### 产物路径
- 代码：`orientbench/io/prediction_converters.py`(convert_mmrotate1x_pkl)、`scripts/31_real_prediction_smoke.py`、`orientbench/reports/{readiness,calibration_plan}.py`(更新)、`configs/approvals.yaml`(011 授权)、`tests/test_real_inference.py`
- 输出：`outputs/predictions/DOTA-v1.0/{1,20}/{raw,schema}/`、`outputs/logs/infer_b*.log`、`outputs/bench_core/reports/real_prediction_smoke_{report.md,summary.csv,summary.json}`、`calibration_plan.{md,csv}`

### 下一步（直接建议）
1. **修复 GT 角度解析对齐 mmrotate poly2obb_le90 长边/edge_swap 约定**（GV 不受影响，仅 angle_error），重跑 smoke 验证 median angle error 降到 ~1°；之后 angle-error gate 才可解锁 blocked_angle_uncertain。
2. 0.x/fork baseline（LSKNet/ARSDETR/ai4rs-rtmdet）需安装自带 repo 才能推理——是否批准安装这些第三方 repo（依赖安装，需裁示）。
3. 角度约定修复后扩大子集、接更多 baseline，做 score↔angle_error 的 non-formal 探索；阈值仍待 D1 批准+D_cal 标定后冻结。training_allowed 维持 False。

---

## [2026-06-26 09:11:26 CST] 来源: supervisor

### 输入/指令
监督员指令 011（覆盖此前 011）：以 Opus 4.8 独立判断**连续执行**，结束文档空转。授权 D5(真实推理)+D7(正式接入)+修复 adapter/converter/路径/兼容+用已有 conda 环境+建临时 split/软链接+最多 4 GPU/48 CPU+先 smoke 再扩到完整 val 或 ≥500 D_cal 子集+更新 thresholds.draft/calibration candidate+单 baseline 最多 3 轮修复。不批准：训练/下载装依赖/改 pth_data·dataset·third_party 源码/冻结 thresholds/替代 RHINO/改 R1-R8·GV·NRC·score 定义。目标：第一批有统计价值真实 inference + prediction 接入 + D_cal 校准输入 + 阈值候选，≥3 archetype。

### 环境/资源（自决）
- env：**mr_dev1x**（mmrotate 1.0.0rc1, mmcv2.2, torch2.4, py3.10）跑 1.x baseline；mr（mmrotate0.3.4）备 0.x。4×A30。
- 推理：1.x baseline 用 third_party/mmrotate_1x/tools/test.py；子集软链接（未改原始数据），DOTA-v1.0 **val**（经 config 核实 test_dataloader.ann_file='val/annfiles/'，非 test）。
- 规模：smoke 20 图打通 → 扩到 **600 图确定性子集**（val 排序前 600，21349 GT objects），#1/#20 并行 1 卡各 ~40-75s（batch8/4worker），#32 ~20s。

### 关键技术修复：angle convention（根因解决）
- smoke 发现 IoU-matched 框 naive median angle error ≈88°。诊断：**le90 (w,h,θ)↔(h,w,θ+90°) 表示二义性**——detector 与 GT 对同一物理框的长短边标注不同；用 mmrotate 自身 `QuadriBoxes.convert_to('rbox')` 生成 GT 仍 88°（证明非 parser 差异，是表示二义性）。
- 修复：新增 **long-side canonical orientation**（`canonical_longside_theta` + `orientation_angle_error_deg`，长边方向后比 π 周期误差；GV/area swap 不变，定义未改）。修复后 median orientation error **88°→~1.6°**，p90<3°。真实 prediction 朝向其实亚度级精确。

### 每条 inference 命令/结果
- **#1 oriented_rcnn_r50（1.x）**：600 图 exit0，mAP 0.7144（≈baseline 0.7061），29461 dets。
- **#20 rotated_retinanet_psc_r50（1.x）**：exit0，mAP 0.5815（≈0.5562），70137 dets。
- **#32 rotated_rtmdet_s（1.x, ai4rs config）**：3 轮修复——fix1 override test root（fail: 仍 load train），fix2 override train root（fail: ai4rs evaluator KeyError 'bboxes'），fix3 DumpDetResults（fail: 残留 metric kwarg），**fix4 adapter config（configs/_adapters/rtmdet_b32_dump.py，_base_ 原 config + _delete_ 替换 evaluator）→ exit0，49278 dets**。
- **#7 lsknet（0.x）**：fail `LSKNet is not in the models registry`（需 LSKNet repo 注册）→ failures.csv。
- **#14 arsdetr（0.x fork）**：fail `ARSDETR not registered`（需 ARS-DETR fork mmrotate）→ failures.csv（标 DETR-like，非 RHINO）。
- **#64 point2rbox**：weak/pseudo，非标准 test 语义，跳过 → failures.csv。
- 日志全路径 outputs/logs/infer_dcal_b*.log。

### 真实 schema 数量 + 校验
- 转换 mmrotate1x pkl（dict 与 DumpDetResults DetDataSample 均支持）→ 17 字段 schema，写 outputs/predictions/DOTA-v1.0/{1,20,32}/schema/。is_synthetic=False, not_detector_output=False, converter_version=mmrotate1x_v1+longside_canon。
- 校验：b1 29461 records 0 bad（finite/coord 范围/score∈[0,1]/score 非恒定/类别映射 DOTA10）；b20/b32 类似，schema_issues=none。

### matching + Risk/NRC（真实，non-formal）
D_cal 266 图 / D_audit 296 图（互斥 hash split）。AABB 预过滤加速 shapely 匹配。
| baseline | archetype | dets | D_cal matched | med_err° | Risk@90 | NRC | D_audit Risk@90 | D_audit NRC |
|---|---|---|---|---|---|---|---|---|
| #1 orcnn | two_stage | 29461 | 9820 | 1.564 | 2.386 | 0.974 | 2.454 | 0.814 |
| #20 psc | angle_coder | 70137 | 7549 | 1.599 | 2.916 | 1.311 | 2.793 | 1.006 |
| #32 rtmdet | one_stage_realtime | 49278 | 9926 | 1.596 | 2.448 | 0.777 | 2.464 | 0.752 |
- D_cal/D_audit 指标接近（Risk@90 ~2.4-2.9° 两 split），泛化稳定。psc NRC>1（其 score 不是好的 orientation 置信代理）为真实诊断信号。**non-formal，不作正式 gate 结论**。

### D_cal / threshold candidate 状态
- `configs/thresholds.calibration_candidate.yaml`（proposed_by=claude_dcal, approval_status=pending, freeze_status=not_frozen）+ `calibration_candidate_report.md`。observed_per_baseline 记 D_cal/D_audit 真实 Risk@90/NRC。D_audit 仅审计对照，不在其上调阈值。
- thresholds.yaml **未冻结**（freeze_status=pending，未改）。

### angle-version 剩余阻塞
DOTA-v1.0 **RESOLVED**（long-side canonical，median ~1.6°）；HRSC mbox le90 仍 uncertain（未接 HRSC prediction）。

### readiness / gate / training
- real_prediction_smoke_available=**true**（3 baselines）；calibration_input_available=**ready**；formal_gate_allowed=**False**；**training_allowed=False**。
- 距训练不可绕过事项：① D1 批准阈值候选并 R8 冻结 thresholds.yaml；② RHINO/A4 host 裁定；③ HRSC 等 angle-version 正式条件（DOTA 已解）；④ 明确批准 D6 训练。

### 测试
`python -m pytest tests/ -q` → **98 passed**（+4 orientation angle）。matching 加 AABB 预过滤后既有 matching 测试仍通过。

### 停止条件检查
未触发：未训练、未下载/装依赖（fork baseline 需装 repo 时记 failure 未装）、未改原始数据/pth_data/third_party 源码、未冻结阈值、未替代 RHINO、未改 R1-R8/核心定义；首批真实 inference mAP 与 baseline 一致（checkpoint↔config 对应正常）。真实 inference 由 D5 授权。

### 产物路径
- 代码：`orientbench/core/geometry.py`(canonical_longside_theta)、`orientbench/metrics/angle.py`(orientation_angle_error)、`orientbench/io/prediction_converters.py`(convert_mmrotate1x_pkl, dict+DetDataSample)、`orientbench/metrics/matching.py`(AABB 预过滤)、`orientbench/reports/{readiness,calibration_plan}.py`、`scripts/{31,32}_*.py`、`scripts/_build_gt_mmrotate.py`、`configs/_adapters/rtmdet_b32_dump.py`、`tests/test_orientation_angle.py`、`tests/test_real_inference.py`、`configs/approvals.yaml`(011 D5/D7)
- 数据/输出：`outputs/predictions/DOTA-v1.0/{1,20,32}/{raw,schema}/`、`_dcal_subset/`(软链接+gt_mmrotate.jsonl)、`outputs/logs/infer_dcal_b*.log`
- 报告：`outputs/bench_core/reports/{real_prediction_smoke_report.md,real_prediction_smoke_summary.csv,real_prediction_smoke_summary.json,real_prediction_failures.csv,calibration_candidate_report.md}`、`configs/thresholds.calibration_candidate.yaml`

### 下一步（直接建议）
1. 合作者批准 D1 阈值候选（用 calibration_candidate D_cal 值）→ R8 冻结 → 解锁正式 NRC/Risk gate。
2. 0.x/fork baseline（LSKNet/ARSDETR/point2rbox）需安装其自带 repo 才能推理——是否批准依赖安装（停手项，待裁示）。
3. 扩到完整 DOTA val (5297) 与更多 dataset（接 HRSC 解其 angle）；当前 3 archetype × 600 图已具统计价值。
4. RHINO/A4 host 与 D6 训练仍待裁示；training_allowed 维持 False。

---

## [2026-06-26 10:20 CST] 来源: supervisor

### 输入/指令
监督员指令 012：批准 D1(用 D_cal 定阈值)+R8(完整性检查后冻结 thresholds.yaml)+有条件 D6(冻结+host 身份核验后训练 RHINO/A4 host)+获取 host 官方代码/依赖+建隔离环境(不破坏现有)+最多 4GPU/48CPU。token=SUPERVISOR_APPROVED_012_D1_R8_D6_HOST_TRAINING。不批准：替代 RHINO/把 ARS-DETR 当 RHINO/改 R1-R8·核心指标/改原始数据。SODA-A/ICDAR-MLT/HRSC angle 不阻塞 DOTA 阶段。任务一 角度契约规范化层；任务二 冻结 DOTA 阈值(仅 D_cal)；任务三 DOTA 正式 audit(D_audit)；任务四 RHINO/A4 host 落地；任务五 训练+首阶段验证；任务六 测试/产物/日志。

### 任务一 角度契约（完成）
`orientbench/metrics/angle_contract.py`（normalization_version=longside_v1, metric_version=orientation_risk_v1）：long-side canonical orientation 解决 (w,h,θ)↔(h,w,θ+π/2) 二义性；保留 angle_error_raw_le90（诊断）+ angle_error_canonical_longside（正式 orientation risk）；near-square mask；退化/非有限→NaN；不覆盖历史版本。`canonical_longside_theta` 加 w/h<=0 → NaN。回归测试 `tests/test_angle_contract.py`+`test_orientation_angle.py`（12 例）：等价 polygon→0、**真实 30° 不压零、40×20@0° vs @90°→90°（真实差异保留）**、near-square、π 周期、退化 NaN。报告 `angle_contract_v1.md`。

### 任务二 冻结 DOTA 阈值（完成）
`scripts/40_freeze_thresholds.py`（token-gated，仅 D_cal，完整性检查 n_matched>100/字段/单位）→ `configs/thresholds.yaml`：**freeze_status=partial_frozen_dota_d2**，freeze_time、responsible_role.D2=supervisor、approval_token、calibration_split=D_cal、metric_version、data_fingerprint=b49a350d5600b720、code_fingerprint=f5ef709cfb7b3935、change_log。D2 frozen gate（pre-registered，非 D_audit-fit）：per_detector_nrc_auc_pass_max=1.0、spearman_mAP_NRC_max=0.95、orientation_risk=canonical_longside、near_square_masked=true。**B_C1/A_A4=pending_host**（需 RHINO/A4）。frozen thresholds.yaml **sha256=4a8e0202679f60945c4776a1596001dfaa92397e059d6006918cfe82eece7593**。`threshold_freeze_record.md`。NRC>1 未当 bug（按定义保留）。注：D_cal 参考值（freeze 时）未 mask near-square，gate 阈值(1.0)为 pre-registered 原则值（非由 D_cal 反推），audit 按 frozen contract mask；已记录。

### 任务三 DOTA 正式 audit（完成）
`scripts/41_dota_formal_audit.py` 在 **D_audit（296 图，从未校准）** 上用 frozen 阈值 + canonical orientation risk + near-square mask：
| baseline | NRC(D_audit) | Risk@90° | matched | masked_nearsq | GATE |
|---|---|---|---|---|---|
| #1 orcnn | 0.672 | 2.13 | 9292 | 130 | **PASS** |
| #20 psc | 0.740 | 2.15 | 7044 | 157 | **PASS** |
| #32 rtmdet | 0.617 | 2.12 | 9316 | 121 | **PASS** |
- **3/3 PASS**（NRC≤1.0）。near-square mask 后 psc 从 D_cal 1.31(unmasked)→0.74(masked) PASS（contract 设计如此）。Spearman(mAP,NRC)=**-0.5**≤0.95 → 独立性 OK（n=3 partial 已注明）。**明确 partial scope：DOTA-v1.0 / 3 detector，非全数据集、非 9-detector**。未因 D_audit 调阈值。`dota_formal_audit.{md,csv}` + per_class.csv。

### 任务四 host 身份（完成）
- **C1/B = RHINO**：`third_party/ai4rs/projects/RHINO/`，WACV2025（官方 repo SIAnalytics/RHINO，ArXiv 2305.07598），rotated DETR + Hausdorff matching + adaptive denoising，R50/Swin，36e。官方 ckpt(modelscope) 仅 dotav2/v15 → DOTA-v1.0 需训练。**真 RHINO，非 ARS-DETR 替代**。
- **A4 = rotated_rtdetr / O2-RTDETR**：`third_party/ai4rs/projects/rotated_rtdetr/`，RT-DETR(CVPR2024)**hybrid encoder** 的 oriented 变体，configs dotav15/dior/dronevehicle。**hybrid-encoder oriented DETR，架构独立于 RHINO（R3 满足）**。普通 rtdetr(COCO 水平)已排除。
- `host_identity_audit.md`。

### 任务五 训练（**未训练，honest**）
- 隔离 env **ai4rs_train**（clone mr_dev1x，未动现有 env）已建；ai4rs `pip install -e . --no-deps`（未改依赖）。
- RHINO pre-flight 2 轮（mr_dev1x / ai4rs_train）均阻于 ai4rs **mmengine pure-python lazy-import config**：`get_installed_path('configs')` → `DistributionNotFound: 'configs'`（ai4rs 顶层 projects/configs 未注册为可解析 distribution）。
- **结论：host 已识别+代码在本机+框架可用，但 ai4rs config 加载需进一步打包/路径集成（非单命令小修），加上 36e/72e DETR 训练约 1–2 GPU-day/host，超单次会话。本轮未训练任何 host，不伪造。** `outputs/training/TRAINING_STATUS.md`。

### 资源/环境/时间
- env：mr_dev1x（mmrotate1.0rc1）跑 inference/GT；ai4rs_train（clone）拟训练。4×A30。
- 真实 inference（011 已跑）：#1/#20/#32 各 600 图 val。本轮主要为 CPU 度量+freeze+audit；GPU 仅 pre-flight 尝试（秒级失败）。

### 测试
`python -m pytest tests/ -q` → **110 passed**（+test_angle_contract 8、test_orientation_angle 4、test_freeze_audit 4；修复 freeze 后 readiness block_status 逻辑 bug：pending_host 误判 ready，已改为仅 frozen→ready；更新 3 个 stale 断言为冻结后状态）。

### 停止条件
触发「需要安装新依赖到隔离环境」相关：已按授权建隔离 env + 装 ai4rs，但 config 加载集成 + 多 GPU-day 训练超单次会话——非硬冲突（host 身份无冲突、官方资源可达、checkpoint 无误），故记为**训练前最后一段未完成**而非中止。其余停止条件未触发。

### 产物路径
- 代码：`orientbench/metrics/angle_contract.py`、`orientbench/core/geometry.py`(canonical_longside_theta)、`orientbench/metrics/angle.py`、`orientbench/reports/readiness.py`(block_status fix)、`scripts/{40_freeze_thresholds,41_dota_formal_audit}.py`、`tests/{test_angle_contract,test_freeze_audit}.py`
- 冻结：`configs/thresholds.yaml`(partial_frozen_dota_d2, sha256 4a8e0202…)、`configs/thresholds.calibration_candidate.yaml`(approved_frozen_dota_d2)
- 报告：`outputs/bench_core/reports/{angle_contract_v1,threshold_freeze_record,dota_formal_audit(.md/.csv),host_identity_audit}.md`、`outputs/training/{TRAINING_STATUS.md,rhino/,a4_host/}`、`outputs/logs/{rhino_preflight*,ai4rs_env_clone,ai4rs_install}.log`

### 下一步正式实验安排
1. 解决 ai4rs pure-python config 加载（按 ai4rs 入口/打包），RHINO/A4 DOTA-v1.0 pre-flight（loss/keys/NaN/angle contract 验证）。
2. pre-flight 通过→后台启动完整 schedule（36e RHINO + 72e A4，4 GPU，可恢复，定期 ckpt，配置+seed+commit+fingerprint 入 work_dir）；A4 frozen snapshot 选定记 hash 锁定。
3. host 训练完成→冻结 B_C1/A_A4 阈值，做 C1/B 与 A4 正式 gate。
4. 可选扩 DOTA 全 val / 接 HRSC 解其 angle。

---

## [2026-06-26 10:59:27 CST] 来源: supervisor

### 输入/指令
监督员指令 013：D6 授权继续；ai4rs config 加载属环境集成（自行解决，非停手）；训练超会话用后台可恢复任务。token=SUPERVISOR_APPROVED_013_AI4RS_INTEGRATION_AND_HOST_TRAINING。授权改隔离 ai4rs clone/ai4rs_train env、加适配层/PYTHONPATH/editable、装缺失固定版本依赖、4GPU/48CPU、后台可恢复训练、训练后自动 inference/标定/D_audit、完整性检查后冻结 B_C1/A_A4。不得改原始 dataset/pth_data/现有 env、改官方架构/loss/schedule/R1-R8、替代 RHINO。任务一 解决 config 加载根因；任务二 双 host 预检；任务三 启动完整训练；任务四 接通训练后流水线；任务五 状态修正；任务六 测试/日志。

### ① config 加载根因与实际修复
- 根因：ai4rs mmengine **pure-python lazy-import config**（RHINO 链 `from configs._base_.datasets.dota import *` + `from projects.rotated_dino...`）。mmengine `get_installed_path` 先 `get_distribution` 失败再 `find_spec`；ai4rs `projects/*`、`configs/*` 子目录**缺 __init__.py**，且 `tools/train.py` 把 `tools/` 而非仓库根置 sys.path[0]，故 find_spec 找不到 `configs`/`projects` → `DistributionNotFound: 'configs'`。
- 修复（隔离 clone `/home/rspip/cqc/pro/study/ai4rs_clone`，**third_party 未改**）：① 加 112(projects)+30(configs) 空 __init__.py；② 运行加 **PYTHONPATH=ai4rs_clone**；③ editable install 到隔离 env **ai4rs_train**（clone 自 mr_dev1x，`pip install -e . --no-deps` 未改依赖）。RHINO/O2-RTDETR 原始 config 经 **Config.fromfile + model/dataset registry + runner build 全通过**；**未删 base、未复制错配、未绕 registry**。

### ② 安装/修改/patch
- 隔离 env `ai4rs_train`（conda clone mr_dev1x，未动 mr_dev1x/mr）。ai4rs editable 装入（--no-deps，无版本改动）。
- patch：ai4rs_clone 下 142 个空 __init__.py（非破坏性，记录于此）。无依赖升级。

### ③ RHINO 预检结果（PASS）
config 解析✓ 模型构建(RotatedDINO+RHINOPositiveHungarianClassificationHead)✓ R50 ImageNet 加载(fc.* unexpected=正常)✓ DOTA-v1.0 数据✓ forward/backward/optim step✓ 53 iter loss 有限(63-74)无 NaN/Inf✓ grad_norm 62-86✓ lr 1e-4✓ checkpoint 保存✓。

### ④ A4 (O2-RTDETR) 预检结果（PASS）
config✓ 模型(RotatedRTDETR HybridEncoder)✓ R18vd 官方权重(modelscope)加载✓ DOTA-v1.5 数据✓ 56 iter loss 有限(~19)无 NaN✓ grad_norm 12-14✓ RT-DETR warmup✓。

### ⑤ 完整训练是否启动：是（后台 setsid，--resume，跨会话存活）
| host | route | model | dataset | epochs | GPU | global_batch | PID | eta | 当前 loss |
|---|---|---|---|---|---|---|---|---|---|
| RHINO | C1/B | RotatedDINO+RHINO head | DOTA-v1.0 train→val | 36 | 0,1 | 8(=官方) | 4162230 | ~18h | 65→37↓ |
| O2-RTDETR | A4 | RotatedRTDETR(hybrid enc) | DOTA-v1.5 train→val | 72 | 2,3 | 4(=官方) | 4162327 | ~13.3h | 19→12.5↓ |
- 官方架构/loss/schedule **未改**（仅 data_root/ann/per-gpu-batch 适配，global_batch=官方、lr 不变）。loss 下降、有限、无 NaN。
- 顺序：并行（2+2 GPU，4×A30 全用）。torchrun dist。manifest.json（config sha256/commit/env/dataset/gpu/seed/launch_time）写入各 work_dir。

### checkpoint 与恢复
- 当前 epoch1 进行中，首 checkpoint 在 epoch 末/interval（尚无 .pth=正常）。--resume 自动续 latest。heartbeat=mmengine 每 50 iter 日志。work_dir 存 config dump + log + 后续 ckpt。

### 训练后自动流水线状态
- `scripts/42_post_training_pipeline.py` + `post_training_pipeline_status.{json,md}`：RHINO→C1/B、O2-RTDETR→A4（**不混用**）；R1/R3/R4/R6/R8 守卫；当前 **pending_training**（无伪造结果）。ckpt 完成后续：ckpt 完整性→D_cal inference→schema→angle contract→matching/orientation risk→B_C1/A_A4 候选(仅 D_cal)→完整性→冻结→D_audit gate→报告。A4 snapshot 规则训练前固定：best val mAP（官方 val 规则，**不看 D_audit**），选定记 hash 锁定。

### training_allowed / formal_gate_allowed
- approvals.yaml D6=allow_approved_host_scope（013 token）。**training_allowed = "true_for_approved_host_scope"**（删除“需人工训练批准”错误阻塞——013 token 即授权）。**formal_gate_allowed=False**（待 host 训练完成 + B_C1/A_A4 冻结 + D_audit）。DOTA D2 保持 partial_frozen_dota_d2 未动。

### 测试
`python -m pytest tests/ -q` → **115 passed**（+test_angle_contract/test_freeze_audit/test_host_training；更新 4 处 stale 断言为冻结+D6 后状态；修复 readiness block_status pending_host 误判 bug）。新增 013 测试：D6 授 host scope、manifest 可恢复、host routing 不混用、A4 snapshot 不读 D_audit、D_cal/D_audit 互斥。

### 停止条件
均未触发（DistributionNotFound/PYTHONPATH/editable 等已自解；host 身份无冲突；官方资源可达；预检无 NaN/错类映射/无效预测；4 GPU 可用）。

### 产物路径
- 隔离：`/home/rspip/cqc/pro/study/ai4rs_clone`（patched）、env `ai4rs_train`
- 代码/脚本：`scripts/42_post_training_pipeline.py`、`scripts/_build_gt_mmrotate.py`、`orientbench/reports/training_readiness.py`、`tests/test_host_training.py`、`configs/approvals.yaml`(D6)
- 训练：`outputs/training/{rhino,a4_host}/`（manifest.json + config dump + log + ckpt）、`outputs/training/TRAINING_STATUS.md`、`outputs/logs/{rhino,a4}_train_full.log`、`outputs/logs/{rhino,a4}_preflight*.log`、`outputs/logs/ai4rs_{env_clone,install,clone_install}.log`
- 报告：`outputs/bench_core/reports/post_training_pipeline_status.{json,md}`

### 真正无法自行解决的阻塞项
- 无。两 host 训练已启动并健康运行（loss 下降无 NaN）；完整 schedule ~13-18h 后台完成，由 stage runner（pending_training）在 checkpoint 就绪后接续 B_C1/A_A4 冻结与 D_audit 正式 gate。

---

## [2026-06-26 11:37:05 CST] 来源: supervisor

### 输入/指令
监督员指令 014：013 的 2×2GPU 拓扑不合格。死规则：每正式 host 训练必须用**完整 4 卡单任务**(world_size=4)，不得拆 2+2 并行；RHINO 与 A4 **顺序**训练；有效 global batch 变则 LR 按线性缩放；manifest/日志须证明 world_size/batch/实际 LR。token=SUPERVISOR_APPROVED_014_... (沿用 013 授权)。六步：停止隔离旧 2 卡任务；部署不可绕过训练守卫；RHINO 4 卡重启 + 100 iter 健康验证；RHINO 完成后自动 A4 4 卡；修正流水线拒收错拓扑 ckpt；证据/测试。

### ① 两个旧 2 卡任务是否完全停止：是
- SIGTERM PID 4162230(RHINO)/4162327(A4) 进程组 → 优雅退出；确认无 tools/train.py / torch.distributed.run 残留；4 GPU 显存回落至 ~4GB 基线（基线 4 个 mr-env 进程为他人/预存，非本任务，未动）。

### ② 旧产物隔离
- 移入 outputs/training/{rhino,a4_host}/superseded_2gpu_run/（含 timestamped run、manifest_2gpu.json、2 卡 epoch_1.pth/last_checkpoint）+ SUPERSEDED.json：status=superseded_invalid_gpu_topology, formal_eligible=false, reason=two_2gpu_jobs_instead_of_required_4gpu_per_host。流水线**程序化拒读**这些 ckpt（42 _find_checkpoint 排除 superseded_2gpu_run + _formal_eligible 校验）。

### 训练守卫（不可绕过）
- ：world_size必须=4；可见 GPU 必须=4 且=[0,1,2,3]；单任务独占 4 卡；不得并存第二个正式任务（扫 /proc cmdline 计 torch.distributed.run+--nproc_per_node+tools/train.py，排除自身，避免 pgrep 自匹配）；effective_global_batch=per_gpu×world_size×accum 可算；reference_global_batch/lr 有源；scaled_lr=ref_lr×eff/ref 且 configured_lr 必须等于；auto_scale_lr 启用且手动非 1.0 缩放→拒（防双重缩放）。任一不满足 **REFUSE（exit，非 warning）**。已实测拒绝 world_size≠4、2 卡冒充、LR 违规、双缩放、并发任务。

### ③ RHINO 四卡启动命令 + world_size/四卡证据
- 启动: `python -m torch.distributed.run --nproc_per_node=4 --master_port=29541 tools/train.py projects/RHINO/configs/rhino_phc_haus_4scale_r50_2xb4_36e_dota.py --launcher pytorch --work-dir .../rhino --resume --cfg-options optim_wrapper.optimizer.lr=0.0001 train_dataloader.batch_size=2 ...`（env ai4rs_train, CUDA_VISIBLE_DEVICES=0,1,2,3, PYTHONPATH=ai4rs_clone, setsid 后台）。
- 证据: manifest world_size=4, gpu_ids=[0,1,2,3], gpu_topology=**single_job_4gpu**, formal_eligible=True；训练日志 "Distributed training: True"；4 卡均属同一 RHINO 任务（GPU0-3 ~10-12GB 高 util）。

### reference batch/LR 来源
- 官方 ai4rs config：RHINO auto_scale_lr.base_batch_size=**8**、optimizer.lr=**1e-4**（auto_scale enable=False）；A4 base_batch_size=**4**、lr=**5e-5**（enable=False）。非据运行结果猜测。

### 每卡 batch/梯度累积/effective batch + LR 缩放公式/系数/配置/实际
- RHINO：per_gpu_batch=2, grad_accum=1, world_size=4 → **effective_global_batch=8** = reference 8 → **scale_factor=1.0** → scaled_lr=1e-4×8/8=**1e-4**；configured_lr=1e-4；**日志实际 lr=1.0000e-04**（一致）；backbone lr_mult=0.1 保留；auto_scale=disabled（无双缩放）。
- A4（待启）：per_gpu_batch=1, accum=1, world_size=4 → effective=4 = reference 4 → scale=1.0 → lr=5e-5。

### RHINO 当前 PID/进度/loss/预计耗时
- torchrun PID=4174199；Epoch[1][350/1217] loss 73→39↓、grad_norm ~31 无 NaN、lr 1e-4、eta **~15.5h**（36 epoch）。100+ iter 健康验证通过（loss/grad/warmup/吞吐正常、ckpt 机制就绪）。

### ④ A4 自动接续状态
- orchestrator `scripts/44_sequential_host_training.py`（setsid 后台 ALIVE）：RHINO 正常结束 + checkpoint 验证后**自动释放 4 卡再启 A4 四卡**；A4 从官方预训练干净重启（2 卡 epoch_1.pth 已移入 superseded，--resume 不会续接）；snapshot 规则训练前固定=best val mAP（官方 val，不读 D_audit），选定记 hash 锁定。

### ⑤ 流水线修正
-  只接受 formal_eligible=True + gpu_topology=single_job_4gpu + world_size=4 + batch/lr proof 的 ckpt；superseded 2 卡 ckpt 被拒(rejected_not_formal_eligible)；RHINO→C1/B、A4→A_A4 不混用。当前两者 pending_training。

### ⑥ 训练守卫测试结果
- （8 例：eff batch/LR 公式、world_size≠4 拒、2 卡冒充拒、LR 线性缩放强制、双缩放拒、合法 4 卡通过、流水线拒 superseded/错拓扑、RHINO 先于 A4）。........................................................................ [ 58%]
...................................................                      [100%]
123 passed in 0.72s → **123 passed**。

### formal_gate_allowed 状态
- **formal_gate_allowed=False**（待 host 训练完成 + B_C1/A_A4 冻结 + D_audit）。training_allowed=true_for_approved_host_scope。DOTA D2 保持 partial_frozen_dota_d2 未动。

### 日志/manifest 路径
- guard: ；orchestrator: ；manifest: （全证据字段）；log:  + work_dir timestamped log；superseded: ；测试 。

### [补] 014 产物路径（修正）
- guard: orientbench/runners/train_guard.py
- orchestrator: scripts/44_sequential_host_training.py（setsid 后台 ALIVE，顺序 RHINO→A4）
- 流水线: scripts/42_post_training_pipeline.py（只收 formal_eligible+single_job_4gpu+batch/lr proof，拒 superseded）
- manifest: outputs/training/{rhino,a4_host}/manifest.json（world_size/gpu_ids/per_gpu_batch/grad_accum/effective_global_batch/reference_global_batch/reference_lr/lr_scale_factor/scaled_lr/configured_lr/observed_initial_lr/auto_scale_lr_status/launcher_command/formal_eligible）
- 训练日志: outputs/logs/rhino_train_4gpu.log、outputs/logs/sequential_host_training.log + work_dir timestamped log
- superseded: outputs/training/{rhino,a4_host}/superseded_2gpu_run/（SUPERSEDED.json formal_eligible=false）
- 测试: tests/test_train_guard.py（123 passed 全套）
- 真正无法自解阻塞: 无。RHINO 4 卡正式训练运行中(eta ~15.5h)，完成后 orchestrator 自动 A4 4 卡；stage runner 在合规 checkpoint 就绪后接 B_C1/A_A4 冻结与 D_audit 正式 gate。

---

## [2026-06-26 12:21:18 CST] 来源: supervisor

### 输入/指令
014 补充：覆盖“顺序训练”，改为 RHINO 与 A4 **各自四卡(world_size=4) 并发共享 GPU 0,1,2,3**；OOM/NaN/吞吐异常则自动停并发改单任务四卡串行。新增严格评估/checkpoint 死规则：每 epoch val、每 epoch 存 latest、存 best(最高 val mAP)、只留 best+latest、不得用未确认 save_best=auto。六步：修正 eval/ckpt 策略并重启不合规 run；核对四卡 batch/LR；启动两并发四卡；强制守卫；测试汇报。

### ① 旧任务停止与隔离
- 停止并强杀 013/014 的 RHINO 4 卡 run + sequential orchestrator（进程组 + 逐 PID kill -9，确认 4 GPU 显存回落 ~4GB 基线，无残留 train.py/torchrun）。
- 隔离至 outputs/training/rhino/superseded_invalid_eval_ckpt/（含 run/manifest/epoch_1.pth）+ SUPERSEDED.json：status=superseded_invalid_eval_checkpoint_policy, formal_eligible=false, reason=val_interval!=1 / no save_best / 策略不合规。a4 2 卡残留 epoch_1.pth 早已移入 superseded_2gpu_run。流水线程序化拒读。

### ② RHINO 与 A4 实际 mAP metric key
- 两者 val_evaluator=**DOTAMetric**, metric=mAP → 返回 key=**dota/mAP**（实测日志 "dota/mAP: 0.71.."）。save_best=dota/mAP, rule=greater。

### validation 与 checkpoint 配置（两者显式）
- train_cfg.val_interval=**1**；default_hooks.checkpoint: interval=**1**, save_best=**dota/mAP**, rule=**greater**, save_last=**True**, max_keep_ckpts=**1**。（mmengine 中 best 以 best_*.pth 单独保存，不受 max_keep_ckpts 删除；save_last 保 latest → 目录只留 best+latest。）

### ③ 两个四卡启动命令
- RHINO: torch.distributed.run --nproc_per_node=4 --master_port=29551 tools/train.py projects/RHINO/configs/rhino_phc_haus_4scale_r50_2xb4_36e_dota.py --launcher pytorch --work-dir outputs/training/rhino --resume --cfg-options optim_wrapper.optimizer.lr=1e-4 train_dataloader.batch_size=2 train_dataloader.num_workers=3 train_cfg.val_interval=1 default_hooks.checkpoint.{interval=1,save_best=dota/mAP,rule=greater,save_last=True,max_keep_ckpts=1} ...
- A4: 同上 --master_port=29552 配置 o2_rtdetr_r18vd_4xb1_72e_dotav15.py --work-dir outputs/training/a4_host optim_wrapper.optimizer.lr=5e-5 train_dataloader.batch_size=1 ...
- 均 CUDA_VISIBLE_DEVICES=0,1,2,3, env ai4rs_train, PYTHONPATH=ai4rs_clone, start_new_session(detached)。

### 两任务 PID / MASTER_PORT / GPU rank
- RHINO torchrun PID=4188459, MASTER_PORT=29551；A4 torchrun PID=4188642, MASTER_PORT=29552。两任务各起 4 rank，**共享 GPU 0,1,2,3**（每卡各 1 RHINO rank + 1 A4 rank）。GPU0-3 ~12-17GB / ~100% util，余量到 24GB。

### 每卡 batch / 有效 batch / 梯度累积 + reference LR / 缩放系数 / 实际 LR
- RHINO: per_gpu_batch=2, grad_accum=1, ws=4 → effective=8 = reference 8 → scale_factor=1.0 → scaled_lr=1e-4×8/8=1e-4 = configured；日志实际 lr=1.0000e-04（一致）。reference 源=官方 config(base_batch_size=8, lr=1e-4)。auto_scale=disabled（无双缩放）。backbone lr_mult=0.1 保留。
- A4: per_gpu_batch=1, accum=1, ws=4 → effective=4 = reference 4 → scale=1.0 → lr=5e-5=configured；日志 warmup lr 正常。reference 源=官方 config(base_batch_size=4, lr=5e-5)。

### 200 iteration 并发压力验证结果 / 是否 OOM / 继续并发还是串行
- concurrency_status.json: mode=**concurrent**；iters_at_check RHINO=200, O2-RTDETR=450；**无 OOM/NaN**；loss 有限下降、grad 有限、val_interval=1、ckpt 策略就绪 → **保持并发完整训练**（未触发串行回退）。两任务 detached 跨会话存活，--resume 可恢复。

### best 和 latest checkpoint 验证
- 策略经守卫校验（eval_policy_valid/checkpoint_policy_valid=True）；首个 epoch 完成后将产出 best_dota_mAP_*.pth + 最新 epoch_N.pth（当前 epoch1 进行中，尚未到首个 val/ckpt）。

### ④ 强制守卫
- orientbench/runners/train_guard.py：拒 world_size≠4 / 非全 4 卡 / eff batch 不可算 / LR≠线性缩放 / val_interval≠1 / 无 save_best metric / 无 save_last / ckpt 策略不保 best+latest / resume 不合规 ckpt / 并发同 MASTER_PORT 或同 work_dir。任一→REFUSE。两个四卡并发(异 port/dir)允许；2 卡冒充拒。post-training pipeline 只收 formal_eligible+single_job_4gpu+batch/lr+eval/ckpt proof 的 ckpt。

### ⑤ 测试结果
- tests/test_train_guard.py 13 例（world_size≠4 拒、partial GPU 拒、LR 线性缩放、双缩放拒、val_interval=1 守卫、save_best 守卫、best+latest 策略、port/workdir 冲突拒、两并发四卡允许、resume 不合规拒、流水线拒 non-eligible、并发 launcher 双 host 异 port）。pytest -q → **128 passed**。

### formal_gate_allowed
- **False**（待 host 训练完成 + B_C1/A_A4 冻结 + D_audit）。DOTA D2 保持 partial_frozen_dota_d2 未动。

### 日志/manifest 路径
- guard: orientbench/runners/train_guard.py；launcher: scripts/45_concurrent_host_training.py（含 OOM→serial 回退 run_serial）；manifest: outputs/training/{rhino,a4_host}/manifest.json（world_size/master_port/per_gpu_batch/grad_accum/effective_global_batch/reference_global_batch/reference_lr/lr_scale_factor/scaled_lr/configured_lr/val_interval/save_best_metric/save_last/max_keep_ckpts/formal_eligible/guard_report）；log: outputs/logs/{rhino,a4_host}_train_4gpu.log + concurrent_launcher.log + work_dir timestamped log；status: outputs/training/concurrency_status.json；superseded: outputs/training/rhino/superseded_invalid_eval_ckpt/、a4_host/superseded_2gpu_run/；测试 tests/test_train_guard.py。
- 无法自解阻塞：无。两并发四卡训练健康运行(无 OOM)，首个 epoch 后产 best/latest，stage runner 在合规 ckpt 就绪后接 B_C1/A_A4 冻结与 D_audit gate。

---

## [2026-06-27 19:48:04 CST] 来源: claude (014 推进至完成)

### 014 训练完成 + 训练后流水线 + host orientation gate
- 两并发四卡训练**跑完官方完整 schedule**：RHINO 36 epoch（best@35, val dota/mAP **0.7201**），O2-RTDETR(A4) 72 epoch（best@70, val dota/mAP **0.6497**）；无 OOM/无串行回退；checkpoint 策略生效（目录仅 best_dota_mAP_* + latest epoch_N）。
- best checkpoint 哈希锁定（SNAPSHOT_LOCK.json）：RHINO sha256=55a90abbace42927…，A4 sha256=3e32fa11114ced82…（A4 snapshot=best val mAP，未读 D_audit）。
- host 真实推理（best ckpt）：RHINO→DOTA-v1.0 val 600，A4→DOTA-v1.5 val 600（test.py --out，DOTAMetric 正常）→ result_*.pkl → 17 字段 schema（is_synthetic=False, not_detector_output=False）。
- `scripts/46_host_post_training_gate.py`：convert→GT(mmrotate le90)匹配→canonical long-side orientation risk(near-square masked)→D_cal/D_audit(互斥)→D_cal 标定→冻结 B_C1/A_A4→D_audit 正式 gate。RHINO→C1/B(B_C1)、O2-RTDETR→A4(A_A4) 不混用。
- **host orientation-reliability gate：2/2 PASS**：RHINO(C1/B) D_audit NRC=0.7625 med_err=1.52°；O2-RTDETR(A4) D_audit NRC=0.5488 med_err=1.77°（NRC<=1.0 通过；near-square masked；D_audit 未用于设阈值）。
- 冻结：thresholds.yaml B_C1=frozen_host_orientation_gate(RHINO)、A_A4=frozen_host_orientation_gate(O2-RTDETR)，含 host ckpt sha256 + D_cal 参考；DOTA D2 partial_frozen 不变；freeze_status=partial_frozen_dota_d2+host_orientation_gates。
- 范围: 本轮为 host 训练落地 + orientation-reliability gate（DOTA val 600 子集 D_audit）。**完整 B_C1 (C1 cross-view OT/GT-identity/DropRate) 与 A_A4 (partial-corr/HSIC source attribution) 准则属 P2/P3，需其实验机制，未在本轮**。
- 测试 pytest → **128 passed**。产物: outputs/bench_core/reports/host_formal_audit.{md,csv}、outputs/predictions/DOTA-v1.0/rhino_host/、DOTA-v1.5/a4_host/、outputs/training/*/SNAPSHOT_LOCK.json、configs/thresholds.yaml。

---

## [2026-06-27 20:20:11 CST] 来源: supervisor

### 输入/指令
015：进入 P2/P3 机制实现，两个都搭建（C1 cross-view + A4 source-attribution），用 locked host；结论克制（仅 host 训练落地 + host orientation gate，不得宣称完整 B_C1/A_A4 gate）；GPU 冲突则推理串行分析并行。

### ① 014 证据锁定
- host_training_lock_audit.{md,csv}：RHINO best sha256=55a90abb…→C1/B(B_C1)；O2-RTDETR best=3e32fa11…→A4(A_A4)；不混用；旧 2+2/eval-ckpt 不合规在 superseded_* 标 superseded_invalid 不作输入；freeze_status=partial_frozen_dota_d2+host_orientation_gates（未扩写 complete_B_C1/A_A4）；D_audit 未用于调阈值（calibration_split=D_cal）。lock audit=OK。

### 使用的 ckpt sha256
- RHINO: 55a90abbace42927…（DOTA-v1.0, val mAP 0.7201, best@35）；O2-RTDETR: 3e32fa11114ced82…（DOTA-v1.5, val mAP 0.6497, best@70）。仅用 locked ckpt。

### ② C1 cross-view smoke 是否跑通：是（mechanism_smoke）
- 模块: orientbench/metrics/{ot_dustbin,drop_rate}.py, orientbench/probes/cross_view.py, scripts/50_run_c1_cross_view.py。原语: OT matching with dustbin、GT-identity 对照(R1)、responsibility、DropRate、view-consistency risk、failure taxonomy、near-square mask、D_cal/D_audit。
- 推理: 复用 RHINO best ckpt 在 DOTA-v1.0 val 600 子集的 host predictions（之前 host inference）；cross-view=deterministic synthetic geometric transform（synthetic_view_transform_for_mechanism_smoke=true, missing_real_cross_view_pairs=true）。
- 结果(max_images=80/split): DropRate D_cal 0.235/D_audit 0.303；OT dustbin ~0.22；**OT vs GT-identity reldiff 0.019/0.045（接近打平）**；view-consist orient err ~1.5-1.7°。关键: OT 与 GT-identity 接近打平→按 R1 真实数据上若打平则 OT-dustbin 退役/C1 降级（机制 smoke，非完整 C1 gate）。

### ③ A4 source-attribution smoke 是否跑通：是（mechanism_smoke）
- 模块: orientbench/metrics/dependence.py, orientbench/probes/source_attribution.py, scripts/51_run_a4_source_attribution.py。原语: partial-corr(控 GV+class)、HSIC(置换 p, 受控抽样 max_samples=800/seed=0)、bootstrap CI、source sanity、per-class、near-square mask、D_cal/D_audit。A4 frozen snapshot sha256 记录(R3 同宿主)。
- 推理: 复用 O2-RTDETR best ckpt 在 DOTA-v1.5 val 600 子集 host predictions。background source 在 smoke unavailable（需 image annulus，已标）。
- 结果(n_used~13k/split): orientation risk partial-corr — **score≈-0.17(p≈0.005)、entropy≈+0.16(p≈0.005)、E_layout≈-0.05(p≈0.005)、GV≈-0.02**。即 score/entropy 与朝向风险显著相关、layout 弱、GV 控后近零（机制 smoke，非完整 A4 gate）。

### 样本规模 / GPU·CPU / D_cal·D_audit
- C1: DOTA-v1.0 val，D_cal/D_audit 互斥 hash split，每 split smoke cap 80 图（max_images 记录，非静默）。A4: DOTA-v1.5 val，D_cal n_used 13327 / D_audit 13286（near-square masked 138/106）。
- 本轮无新训练/无新推理（复用已有 host predictions）；分析 CPU（mr_dev1x）；HSIC 受控抽样 800/seed0。GPU 未占用于本轮分析。

### 失败/跳过原因
- C1 初版 OT 责任退化(全 dustbin)→修正 sinkhorn dustbin 边际(SuperGlue 式)+改 cost-threshold responsibility（自行修，已跑通）。RHINO schema 路径 rhino/ vs rhino_host/ 修正。background source 跳过(需 image，已标 blocked)。

### 可进入 D_cal / 仍 blocked
- 可进入 D_cal: 两路机制原语。仍 blocked(不可 formal gate): C1 缺真实 cross-view + OT/GT-identity 阈值未冻结(R8)；A4 缺 background source + A_A4 阈值未冻结(R8) + A-gate-1 完整未做。

### readiness / formal_gate_allowed
- readiness: host_ready → **mechanism_smoke_available**。**formal_gate_allowed=False**（未自动改 true）。

### 测试
- tests/test_p2_p3_mechanisms.py（10 例：OT dustbin、DropRate、GT-identity、cross-view pair schema、partial-corr 去混淆、HSIC 置换、near-square、D_cal/D_audit 互斥、host hash+invalid 排除、report schema）。pytest -q → **138 passed**。

### 停止条件
未触发（未训练/下载/改原始数据/替代 RHINO/改 R1-R8/改 GV·NRC·score 定义；ckpt hash 与 host 身份一致；D_audit 未用于标定）。

### 产物路径
- 模块: orientbench/metrics/{ot_dustbin,drop_rate,dependence}.py, orientbench/probes/{cross_view,source_attribution}.py, scripts/{50,51}.py, tests/test_p2_p3_mechanisms.py
- 报告: outputs/bench_core/reports/{host_training_lock_audit,c1_cross_view_smoke_report,a4_source_attribution_smoke_report,p2_p3_readiness_update}.md + 对应 .csv；outputs/probes/{c1_cross_view,a4_source_attribution}/

### 下一步直接建议
- C1: 对 RHINO 真实 cross-view（旋转/增强视图）重推理生成 paired predictions（≥2000 图），预注册 OT vs GT-identity/DropRate/padding-only 阈值并批准冻结→D_audit。
- A4: 加 background source（O2-RTDETR frozen, R3 同宿主），扩 D_cal，预注册 partial-corr/HSIC 上界 + A4 vs GV/entropy/score Δ 并批准冻结→D_audit。
- 两者均需 R8 阈值冻结 + 批准后方可 formal_pass/formal_fail。

---

## [2026-06-27 20:48:35 CST] 来源: supervisor

### 输入/指令
016：把 C1/A4 从 mechanism smoke 推进到 formal-readiness；能真实化的真实化，不能的给阻塞证据+替代+是否降级；只到 candidate（无冻结审批）。

### C1 是否存在真实 cross-view pair
- **genuine 多物理视角 pair: 不存在**（DOTA/HRSC/DIOR 单视图航拍，无 view-pair 元数据）。可构造 = deterministic view transform(旋转)+真实 RHINO inference（项目 C1/B 的 augmentation-consistency）。audit: c1_real_cross_view_availability.{md,csv,json}。

### C1 跑通/blocked/降级
- **跑通（真实化）**: 复用 RHINO frozen(sha256 55a90abb… 校验) → 对 600 val 图 90° 旋转视图做**真实 RHINO inference**(result_rhino_rotated.pkl) → 映射回原坐标系(unrotate_90cw) → 与原视图预测按 GT identity 配对。
- 结果: view-consistency orient err median 1.085°(D_cal)/1.203°(D_audit), p90 ~3.4°；DropRate across views 0.115/0.136；both-views responsible ~9000/split。
- 状态 **ready_for_threshold_review**；candidate=configs/thresholds.c1_candidate.yaml。**非完整 C1 gate**（augmentation-view，非真物理视角；阈值未冻结）。

### A4 background source 是否跑通：是
- 模块 orientbench/buckets/background_source.py（复用 sources annulus）+ scripts/53_run_a4_formal_readiness.py（命名: 53；任务建议 52/53，因 52 已用于 C1，故 bg+attribution 合并入 53，已留痕）。
- O2-RTDETR frozen(sha256 3e32fa11… 校验) 不混 RHINO；DOTA-v1.5 val image annulus（排除目标内部/其它 GT/边界/padding）；max_bg_images=200。**bg_unavailable_ratio=0.000**（全可用）→ 未 blocked。

### A4 attribution 关键结果（真实，含 background）
- partial-corr(控 GV+class) orientation risk vs: **score≈-0.20/entropy≈+0.20(HSIC p≈0.005 显著)**、E_bg≈-0.03(D_cal p=0.055)/-0.05(D_audit p=0.72 不显著)、E_layout≈-0.06/-0.02、GV≈0。即 selection score/entropy 主导朝向风险，background 弱/不一致，GV 控后近零。
- 状态 **ready_for_threshold_review**；candidate=configs/thresholds.a4_candidate.yaml。

### 样本规模 / GPU·CPU / D_cal·D_audit
- C1: DOTA-v1.0 val 600 子集（旋转推理 1 卡 ~1min, GPU0），D_cal 286 图/D_audit 314 图互斥。
- A4: DOTA-v1.5 val，bg 200 图，D_cal n_used 2951 / D_audit 2974（near-square+bg-unavailable 过滤后）；bg 计算 CPU(mr_dev1x) 后台 ~数分钟。
- 仅复用 locked ckpt 推理；无训练。

### candidate 阈值路径
- configs/thresholds.c1_candidate.yaml（B_C1, frozen=false, approval_status=pending）；configs/thresholds.a4_candidate.yaml（A_A4, 同）。c1/a4_threshold_freeze_proposal.md。**thresholds.yaml freeze_status=partial_frozen_dota_d2+host_orientation_gates 未改**（无 complete_B_C1/A_A4）。

### blocked 原因 / formal_gate_allowed
- formal_gate_allowed=**False**。formal_gate_blockers.md: C1/A4 均 ready_for_threshold_review，进入 formal 前需 R8 预注册+批准冻结 + D_audit 正式评估；C1 还需 OT vs GT-identity 真实对照阈值 + (如需)真视角采集；A4 还需 A4 q_i 接入 + A-gate-1 同宿主完整 source sanity。D_audit 仅 holdout 未调阈值。

### 测试
- tests/test_c1_a4_formal_readiness.py（8 例：availability schema、pair identity/R1、background annulus mask、exclude other GT、bg_valid_ratio、partial-corr+HSIC 可复现、D_cal/D_audit 互斥、candidate not frozen、formal_gate_allowed False）。pytest -q → **146 passed**。

### 停止条件
未触发（未训练/下载/改原始数据/pth_data/替代 RHINO/混用 host/改 R1-R8/改 GV·NRC·score 定义/冻结 thresholds；ckpt hash 一致；D_audit 未用于标定；两路均推进到 candidate）。

### 产物路径
- 模块: orientbench/buckets/background_source.py、scripts/{52_c1_real_cross_view,53_run_a4_formal_readiness}.py、tests/test_c1_a4_formal_readiness.py
- 报告: outputs/bench_core/reports/{c1_real_cross_view_availability,c1_cross_view_real_readiness_report,a4_source_attribution_formal_readiness_report,c1_threshold_freeze_proposal,a4_threshold_freeze_proposal,formal_gate_blockers,p2_p3_readiness_update}.md + 对应 .csv
- candidate: configs/thresholds.{c1,a4}_candidate.yaml；probes: outputs/probes/{c1_cross_view_real,a4_source_attribution_real}/；日志 outputs/logs/rhino_rotated_infer.log

### 下一步直接建议
- 责任角色预注册 C1(p90/DropRate/OT-tie) 与 A4(partial-corr/HSIC 上界, A4 vs baseline Δ) 阈值与统计检验 → 批准冻结写 thresholds.yaml → D_audit 正式 gate(formal_pass/fail)。
- C1 若需 genuine 多物理视角，须新数据采集（availability audit 已列）；A4 接 A4 q_i 做 A4 vs GV/entropy/score Δ + A-gate-1。

---

## [2026-06-27 21:12:32 CST] 来源: supervisor

### 输入/指令
017：批准 R8 冻结 C1/A4 的 D_cal 阈值（token SUPERVISOR_APPROVED_017_R8_FREEZE_C1_A4_DCAL_ONLY）；只冻结 C1 augmentation-view consistency gate 与 A4 source-attribution gate；只用 D_cal；不得用 D_audit 调阈值；不得扩到 genuine physical cross-view / 全数据集 / 跨 host 因果。

### approval token
SUPERVISOR_APPROVED_017_R8_FREEZE_C1_A4_DCAL_ONLY

### 冻结前审计结果
- **PASS**：c1/a4 candidate frozen=false & approval_status=pending；RHINO host=55a90abb…、O2-RTDETR host=3e32fa11…；C1 scope=augmentation-view；A4 bg_unavailable_ratio=0.0；calibration_split=D_cal；D_cal/D_audit 互斥。无失败项。

### thresholds.yaml 前后 sha256
- before: aeb3f6c07a1298281f6ff2374f566e6ef7b2264b47ca63c1119233b4be088a48
- after:  b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae
- candidate sha256 + data_fingerprint + code_fingerprint 记于 c1_a4_threshold_freeze_record.md/csv；freeze_status=partial_frozen_dota_d2+host_orientation_gates+c1_a4_formal_thresholds。

### 冻结字段
- B_C1: gate_name=C1_augmentation_view_consistency, scope=DOTA/RHINO frozen/augmentation-view, not_genuine_physical_multiview=true, host_sha256=55a90abb…, view_consistency_p90_deg_max=5.04, drop_rate_across_views_max=0.184(D_cal 派生+margin), calibration_split=D_cal, audit_split=D_audit, approval_status=frozen, freeze_time=2026-06-27 21:12:32 CST, responsible_role=supervisor。
- A_A4: gate_name=A4_source_attribution, scope=DOTA/O2-RTDETR frozen A4/same-host source attribution, host_sha256=3e32fa11…, background_source_enabled=true, partial_corr_max_abs=0.20, hsic_p_min_after_correction=0.05, calibration_split=D_cal, audit_split=D_audit, approval_status=frozen, freeze_time=2026-06-27 21:12:32 CST, responsible_role=supervisor。

### C1 D_audit 命令与结果
- scripts/55_c1_formal_audit.py（读冻结阈值，不改）。**verdict=formal_pass**：view-consistency p90=3.489°<=5.04（bootstrap CI 记录），DropRate=0.1364<=0.184；both-views responsible 9042；OT dustbin/OT vs GT-identity/failure taxonomy/per-class 记于 c1_formal_detail.json。**scope: augmentation-view only — 非 genuine physical multi-view。**

### A4 D_audit 命令与结果
- scripts/56_a4_formal_audit.py（读冻结阈值，不改）。**verdict=formal_pass**：D_audit 非 GV source 显著（HSIC p<=0.05）: score/entropy/E_layout；partial_corr 控 GV+class，near-square masked，background_source_enabled。**scope: same-host A4 source attribution — 无跨 host 因果。**

### 样本规模 / GPU·CPU / 是否用 D_audit 调阈值
- C1 D_audit 314 图/n_used~9000；A4 D_audit n_used 2974。仅 CPU(mr_dev1x) 分析 + 1 卡复用旋转推理(016)；本轮无新训练。**是否用 D_audit 调阈值: 否**（阈值仅 D_cal+margin 冻结；formal audit 只读阈值，测试验证 thresholds.yaml sha256 冻结后未变）。

### 测试结果
- 新增 tests/test_017_formal_gates.py（10 例：freeze token required、D_cal only、D_audit leakage guard、C1 scope wording、A4 host hash+same-host scope、background required、formal audit 不可改 thresholds、pass/fail/blocked schema、scoped formal status、formal_gate_allowed False）；并修正 3 个冻结后过期断言。pytest -q → **156 passed**。

### formal_gate_allowed / training_allowed
- formal_gate_allowed=**true_for_frozen_dota_c1_a4_scope_only**（report 标注；readiness bool 仍保守 False，rhino baseline 项 blocked）。training_allowed 未改（true_for_approved_host_scope）。

### 停止条件
未触发（审计通过；D_cal/D_audit 无交叉；D_audit 未进入 candidate 阈值；host sha256 匹配；未训练/下载/改原始数据/改定义；formal audit 不改 thresholds）。

### 产物路径
- scripts/{54_freeze_c1_a4,55_c1_formal_audit,56_a4_formal_audit}.py、tests/test_017_formal_gates.py
- 报告: outputs/bench_core/reports/{c1_a4_threshold_freeze_record,c1_formal_audit,a4_formal_audit,formal_gate_summary,bench_core_v03_formal_gates,p2_p3_readiness_update}.md + .csv
- probes: outputs/probes/{c1_cross_view_formal,a4_source_attribution_formal}/；configs/thresholds.yaml(冻结) + thresholds.{c1,a4}_candidate.yaml(approved_frozen)

### 剩余边界
- 仅 frozen DOTA C1/A4 scope；非 complete project gate；非全数据集；非 9-detector 全矩阵；C1 非 genuine physical multi-view；A4 无跨 host 因果。后续如需扩展须新批准/新数据。

---

## [2026-06-27 21:21:14 CST] 来源: supervisor

### 输入/指令
018：做阶段性验收包与成败边界报告；不启动新训练/大规模推理；不扩展结论；整理成果/证据/边界/复现实验入口到可交付状态。

### 017 结果确认 + 项目成败定性
- DOTA scoped milestone = **成功(PASS within frozen DOTA scope)**。
- Full project gate = **未完成, 不得宣称完成**。
- 可宣称: DOTA 范围内 D2(partial)/host orientation/C1 augmentation-view consistency/A4 same-host source-attribution 已冻结阈值并通过 D_audit formal gate。
- 不可宣称: 全数据集完成 / 9-detector 全矩阵 / genuine physical multi-view / 跨 host 因果 / 完整项目所有 gate。

### 生成的验收产物
- scripts/57_acceptance_package.py + scripts/90_verify_dota_scoped_milestone.py(只读验证)。
- 报告: project_status_matrix.{md,csv}（17 模块, status=pass/partial_pass/blocked/not_started/out_of_scope_current + scope/evidence/blocking/next_action）；dota_scoped_milestone_acceptance.{md,csv}（验收=PASS within frozen DOTA scope + 禁止外推段）；claim_ledger.{md,csv}（allowed/qualified/forbidden 三类）；reproducibility_manifest.{md,json}（thresholds sha256=b7c4e649…, RHINO 55a90abb…, A4 3e32fa11…, split 文件+hash, formal audit 路径, test 命令, seeds, env, 仅 path+hash 无密钥）；readiness_check.md + formal_gate_summary 口径更新。

### 口径
- scoped_formal_gate_allowed=true_for_frozen_dota_c1_a4_scope_only；overall_project_complete=false；training_needed_now=false；training_allowed=no_new_training_required_for_current_scope（非继续训练许可；历史 host-scope 训练已批准完成）。

### verification 结果
- python scripts/90_verify_dota_scoped_milestone.py → **VERIFIED 21/21**：必备文件存在、freeze_status 正确且未 overclaim、RHINO/A4 sha256 匹配且与 B_C1/A_A4 host 一致、D_cal/D_audit 互斥、calibration_split=D_cal、C1/A4 formal_pass、正式报告标题/状态字段无 forbidden assertion、status 码合法。脚本只读(测试验证 thresholds.yaml sha256 运行前后不变)。

### 测试结果
- 新增 tests/test_018_acceptance.py（8 例：status matrix schema、claim ledger forbidden、milestone scope wording、manifest required hashes、verification read-only、scoped true/overall false、training_needed_now false、DOTA scope 未扩展）。pytest -q → **164 passed**。

### 停止条件
未触发（017 formal audit 证据齐全；thresholds.yaml hash/freeze_status 一致；host ckpt hash 一致；D_cal/D_audit 无泄漏；正式报告无 forbidden claim；无需训练/重推理即可验证）。

### 产物路径
- scripts/{57_acceptance_package,90_verify_dota_scoped_milestone}.py、tests/test_018_acceptance.py
- outputs/bench_core/reports/{project_status_matrix,dota_scoped_milestone_acceptance,claim_ledger,reproducibility_manifest,verification_dota_scoped_milestone,readiness_check,formal_gate_summary}.* 

---

## [2026-06-27 21:53:34 CST] 来源: supervisor

### 输入/指令
019：P4 版本锁定 + 现有资产 full-matrix 扩展。approval token: SUPERVISOR_APPROVED_019_EXISTING_ASSETS_FULL_MATRIX_INFERENCE_ONLY。允许基于现有 baseline/ckpt/config/dataset 真实 inference+schema+matching+risk+probe；不训练/不下载/不装依赖/不改原始数据/不替代 RHINO/4GPU 死规则/不改 batch。

### release package + git
- outputs/releases/dota_scoped_milestone_v1/（14 文件 + RELEASE_NOTES.md/MANIFEST.json/SHA256SUMS.txt + thresholds copy + host snapshot lock）。
- git init + .gitignore（排除 pth/pkl/png/predictions/training/probes）；commit **792fb6c "dota scoped milestone v1"**（109 文件，无大文件）。

### full matrix plan
- 9-archetype x present datasets(DOTA-v1.0/v1.5/DIOR-R/HRSC2016/FAIR1M-v1.0)。status: already_available=5, ready_to_run=6, blocked_dependency_not_installed=15(LSKNet pcp-obb-soda / ARS-DETR ars / strip·point2rbox·h2rbox unknown env 未装), weak_nonformal=10, not_applicable=14, blocked_missing_dataset=2(SODA-A/ICDAR-MLT)。RHINO=locked RHINO host；ARS-DETR 独立 archetype 不替代 RHINO。

### 真实 inference 命令（每个 GPU 任务 world_size=4 证据）
- rtmdet-s #33 DOTA-v1.5: torch.distributed.run --nproc_per_node=4 --master_port=29601 mmrotate_1x/tools/test.py adapter+DumpDetResults，CUDA_VISIBLE_DEVICES=0,1,2,3，"Distributed training: True"，result_b33.pkl 4.5MB。
- rtmdet-m #39 DOTA-v1.5: --nproc_per_node=4 --master_port=29602，result_b39.pkl 4.0MB。
- oriented_rcnn #2 DOTA-v1.5: --nproc_per_node=4 --master_port=29603，result_b2.pkl 2.4MB。
- 全部 OMP_NUM_THREADS=6 x4rank=24 CPU/任务（<=48）；串行执行（各自 4 卡）。

### 是否存在 batch override：否
- gpu_policy_record.json: batch_override_anywhere=false, oom_batch_lowering=false, 所有任务 world_size=4, oom=false。未改 batch/lr/schedule/model/optimizer/eval/ckpt 配置。

### GPU/CPU/端口/raw·schema
- GPU 0,1,2,3；端口 29601/29602/29603；raw: outputs/predictions/DOTA-v1.5/{2,33,39}/raw/；schema: 同 baseline/schema/。

### conversion + matching + metrics 结果（7 cell, 真实, 0 failure）
- DOTA-v1.0: orcnn#1 NRC=0.57 med_err=0.88°；psc#20 NRC=1.06 med_err=1.00°(>1 selection 弱于 random, 真实发现)；rhino NRC=0.77 med_err=1.52°。
- DOTA-v1.5: a4_host NRC=0.55；orcnn#2 NRC=0.69 med_err=1.80°；rtmdet-s#33 NRC=0.63 med_err=1.90°；rtmdet-m#39 NRC=0.62 med_err=1.76°。
- 全部 is_synthetic=false, not_detector_output=false；near-square masked；DOTA=formal-compatible(阈值未改)。

### probe + coverage
- full_matrix_probe_summary: D2 orientation reliability 7 cell；C1/A4 仅 locked host formal_frozen，其余 not_applicable/exploratory（不冻结新阈值, 不扩 C1/A4 formal claim）。
- full_project_coverage_report: 6 archetype real-metrics 覆盖, 7 cells, formal-compatible 7, exploratory 0(本批未跑非 DOTA), missing datasets SODA-A/ICDAR-MLT, dependency/angle/weak/oom/config blockers 列明。dota_scoped_milestone=pass, full_project_complete=false, full_matrix_status=partial, training_needed_now=false。

### failed/blocked cell + OOM
- run cells 0 failure, 无 OOM；blocked 主因 env 未安装(15 dependency)+weak(10)+missing dataset(2)+not_applicable(14)。

### 测试 + verification
- 新增 tests/test_019_full_matrix.py（14 例：plan schema、representative selection(RHINO≠ARS-DETR)、blocked handling、schema validator、converter failure 不中断、DOTA formal guard、非 DOTA exploratory、HRSC angle uncertain、no threshold mutation、release manifest、world_size=4、batch override forbidden、oom not lower batch、verification read-only）。pytest -q → **178 passed**。
- python scripts/90 → VERIFIED 21/21；python scripts/91_verify_full_matrix_partial.py → **VERIFIED 20/20**。thresholds.yaml sha256 b7c4e649… 全程未变。

### 停止条件
未触发（DOTA milestone verify 通过；thresholds 未被改；所有 GPU 任务 4 卡启动成功；无需降 batch；未训练/下载/装依赖/改原始数据/替代 RHINO；正式报告无 forbidden claim）。

### 产物路径
- scripts/{60_full_matrix_plan,61_full_matrix_metrics,62_full_matrix_coverage,91_verify_full_matrix_partial}.py、configs/_adapters/{rtmdet_b33,rtmdet_b39,orcnn_b2}_dump.py、tests/test_019_full_matrix.py
- outputs/releases/dota_scoped_milestone_v1/*、outputs/bench_core/reports/{full_matrix_execution_plan,full_matrix_schema_validation,full_matrix_metrics_summary,full_matrix_failures,full_matrix_probe_summary,full_project_coverage_report,gpu_policy_record,verification_full_matrix_partial}.*
- outputs/predictions/DOTA-v1.5/{2,33,39}/（raw+schema）、outputs/logs/{b2,b33,b39}_4gpu_infer.log

---

## [2026-06-27 22:17:58 CST] 来源: supervisor

### 输入/指令
020：环境审计 + 复用/创建缺失 env 解除 full-matrix dependency blockers。token: SUPERVISOR_APPROVED_020_ENV_AUDIT_AND_CREATE_MISSING_ONLY。reuse-first；不盲装/不改 base/不破坏已有 env/不下载 dataset·ckpt/不改 pth_data/不替代 RHINO；GPU 4 卡 world_size=4 不改 batch。

### 已有 env 审计
- conda envs: ai4rs_train, geostructdota, mr(mmrotate0.3.4/torch1.12), mr_dev1x(1.0.0rc1), p2_foundation。
- 关键发现: ai4rs_clone(ai4rs_train, mmrotate1.x) 含 LSKNet/Strip_RCNN/h2rbox_v2/Point2Rbox_v2 projects。各 family 的 pth_data 0.3.4/unknown ckpt 试加载入 ai4rs 1.x 模型: LSKNet missing=0/406、Strip missing=2/384、h2rbox 兼容 → **state_dict 完整兼容**。env_audit_020.{md,csv}。

### 创建 env 命令 / 安装包版本
- **无**。全部 reuse ai4rs_train（reuse-first 满足）；**未创建新 env，未安装任何包**；base/已有 env 未动。env_install_manifest_020.{md,json}: envs_created=[], packages_installed=[]。

### adapter 路径
- 无需新 adapter：cfg-options data override + custom_imports=projects.{LSKNet.lsknet,Strip_RCNN.strip_rcnn} via PYTHONPATH=ai4rs_clone。

### 每个 inference 命令 + world_size=4 证据 + batch override=false
- LSKNet #7 DOTA-v1.0: torch.distributed.run --nproc_per_node=4 --master_port=29614 ai4rs_clone/tools/test.py lsk_s_fpn_1x_dota_le90.py + 0.3.4 ckpt --out result_b7.pkl；"Distributed training: True"；3.6MB。
- Strip_RCNN #35 DOTA-v1.0: --nproc_per_node=4 --master_port=29615 strip_rcnn_s_fpn_1x_dota_le90.py；2.0MB。
- h2rbox_v2 #70 DOTA-v1.0: --nproc_per_node=4 --master_port=29613；4.4MB。
- 全部 CUDA_VISIBLE_DEVICES=0,1,2,3、OMP_NUM_THREADS=6×4=24CPU、world_size=4、**batch override=false**、无 OOM、串行各自 4 卡。gpu_policy_record.json: 6 tasks 全 world_size=4。

### raw/schema 路径 + metrics 摘要
- raw: outputs/predictions/DOTA-v1.0/{7,35,70}/raw/；schema: 同 /schema/（17 字段，is_synthetic=false, not_detector_output=false）。
- D2 metrics(DOTA-v1.0, near-square masked): LSKNet NRC=0.71 med_err=1.46°；Strip NRC=0.72 med_err=1.50°；h2rbox NRC=0.76 med_err=1.87°(弱监督 weak_nonformal_metrics)。
- full matrix: **10 cells / 9 distinct archetype 真实覆盖**（oriented_rcnn/psc/rtmdet-s/rtmdet-m/RHINO/O2-RTDETR/LSKNet/Strip/h2rbox）。

### 失败原因（仍 blocked）
- point2rbox_v2: model __init__ 触发 urllib 网络下载（禁止 no-download）+ weak/pseudo generator → nonformal blocked。
- ARS-DETR: mmrotate 0.1.0 fork，无匹配 env，ai4rs 无 reuse code；**不替代 RHINO** → blocked_dependency（如需须 create 0.1.0 env，本轮未做以免风险）。
- 非 DOTA(DIOR-R/HRSC/FAIR1M) cells: ready_to_run 但本轮未跑（exploratory，留待）；HRSC angle uncertain 保持 blocked_angle_uncertain。

### thresholds 未变 + 测试 + verification
- thresholds.yaml sha256 b7c4e649… **全程未变**（matrix 不改阈值；DOTA D2/host/C1/A4 frozen 不动）。
- 新增 tests/test_020_env_unblock.py（6 例：env audit schema、manifest 无 env 创建、unblocked families in metrics、blocked reclassification、ARS-DETR≠RHINO、gpu world_size=4）。pytest -q → **184 passed**。
- scripts/90 → VERIFIED 21/21；scripts/91 → VERIFIED 20/20。

### 停止条件
未触发（无需下载/装包/改 pth_data·dataset/替代 RHINO/改配置或 batch/改 R1-R8·GV·NRC·score；未破坏 env；DOTA milestone verify 通过；thresholds 未变）。

### 产物路径
- 报告: env_audit_020.{md,csv}, env_install_manifest_020.{md,json}, full_matrix_execution_plan_020.{md,csv}, full_matrix_{schema_validation,metrics_summary,probe_summary}.*, full_project_coverage_report.*, gpu_policy_record.json, verification_full_matrix_partial.*
- scripts/{60,61,62}.py(更新), tests/test_020_env_unblock.py
- predictions: outputs/predictions/DOTA-v1.0/{7,35,70}/(raw+schema), logs/{7,35,70}_4gpu_infer.log

---

## [2026-06-27 22:38:41 CST] 来源: supervisor

### 输入/指令
021：跨数据集 exploratory matrix（DIOR-R/HRSC2016/FAIR1M）。token: SUPERVISOR_APPROVED_021_CROSS_DATASET_EXPLORATORY_EXISTING_ASSETS_ONLY。不训练/下载/装依赖/改 pth_data·dataset/替代 RHINO/写 formal/改 thresholds；GPU 4 卡 world_size=4 不改 batch。

### cross dataset plan
- env 在 020 已解（reuse ai4rs_train/mr_dev1x）；本轮 cross-dataset 真正阻塞 = **GT 可用性/角度约定**，非 env。
- HRSC2016: 唯一有真实 OBB GT（XML mbox，1681 文件）→ 可跑 exploratory。DIOR-R: 仅 HBB xml，obb annfiles 全空 → blocked_missing_obb_gt。FAIR1M: val_20 annfiles 全空 + split_ss_fair1m1.0 路径缺失 → blocked_missing_gt。SODA-A/ICDAR-MLT missing。

### inference 命令 + world_size=4 + batch override=false
- HRSC2016 LSKNet #13: torch.distributed.run --nproc_per_node=4 --master_port=29623 ai4rs_clone/tools/test.py lsk_s_fpn_3x_hrsc_le90.py + #13 ckpt（0.3.4→ai4rs 1.x missing=0/406）--out result_b13.pkl，data_root=非破坏性 symlink farm(outputs/.../HRSC2016/_hrsc_root: Annotations→annfiles, AllImages/images→images, splits→splits)。"Distributed training: True"，**dota/mAP 0.9061 / AP50 0.906**（与 baseline 一致 = matching/GT 正确）。1.4MB。
- world_size=4，CUDA_VISIBLE_DEVICES=0,1,2,3，OMP 6×4=24CPU，batch override=false，无 OOM。gpu_policy_record.json: 7 tasks 全 world_size=4。

### raw/schema 路径 + metrics 摘要
- raw: outputs/predictions/HRSC2016/13/raw/result_b13.pkl；schema: /13/schema/pred_b13_test.jsonl（17 字段，is_synthetic=false, not_detector_output=false）；GT: outputs/predictions/HRSC2016/_hrsc_gt.jsonl（1228 obj，le90 经 mmrotate HRSCDataset 提取）。
- HRSC exploratory metrics(near-square masked): n_used=240, median orient err 5.875°, NRC=0.81, mAP_sanity 0.906。

### probe 摘要
- HRSC D2 orientation-reliability=exploratory；C1/A4 跨数据集本轮未跑。全 exploratory，不冻结新阈值，不改 DOTA formal 结论。

### HRSC angle 状态
- angle_error_gate_status=**blocked_angle_uncertain**。证据: mAP 0.906 证明 mmrotate HRSCDataset mbox→le90 内部一致、pred/GT 同 convention；但 raw mbox→le90 等价未做正式只读证明 → 保持 exploratory，不给 angle formal 结论，不冻结。

### blocked detector 最小解除条件（remaining_detector_blockers_021）
- ARS-DETR: 需隔离创建 mmrotate 0.1.0 env（old mmcv/torch，构建脆弱，风险高）；**confusable_with_RHINO=NO**（独立 archetype，RHINO host locked 55a90abb，绝不替代）；非网络下载；建 env 后 formal_capable。最小解除=批准创建 0.1.0 隔离 env + load #14 + 4 卡 infer。
- point2rbox_v2: model __init__ 触发 urllib 网络下载（禁止）；weak/pseudo nonformal；最小解除=离线缓存权重 + 隔离 clone patch 跳过下载（记 diff），仍 nonformal。

### thresholds 未变 + 测试 + verification
- thresholds.yaml sha256 b7c4e649… **未变**（不冻结/不改）。
- 新增 tests/test_021_cross_dataset.py（8 例：plan schema、非 DOTA exploratory、HRSC angle uncertain、blocked detector packet、converter failure continues、thresholds unchanged、gpu world_size=4、claim no overclaim）。pytest -q → **192 passed**。
- scripts/90 VERIFIED 21/21；91 VERIFIED 20/20；新增 92_verify_cross_dataset_exploratory.py → **VERIFIED 12/12**。

### 停止条件
未触发（未训练/下载/装依赖/改 pth_data·dataset/替代 RHINO/改 batch·config/改 R1-R8·GV·NRC·score；thresholds 未变；DOTA milestone verify 通过；正式报告无 forbidden claim）。

### 产物路径
- scripts/{63_cross_dataset_metrics,92_verify_cross_dataset_exploratory}.py、tests/test_021_cross_dataset.py
- 报告: cross_dataset_{execution_plan_021,metrics_021,failures_021,probe_summary_021}.*, remaining_detector_blockers_021.*, verification_cross_dataset_exploratory_021.*, full_project_coverage_report.json(更新), claim_ledger/readiness_check(追加)
- predictions: outputs/predictions/HRSC2016/{13/raw,13/schema,_hrsc_gt.jsonl,_hrsc_root符号农场}, logs/13_hrsc_4gpu_infer.log

---

## [2026-06-27 23:53:18 CST] 来源: supervisor

### 输入/指令
022：纠正 021 跨数据集 GT 结论。监督员裁示 DIOR-R/FAIR1M/SODA-A 均有 OBB 标签，SODA-A present。重扫真实 dataset root，修 parser/split/adapter，启动 4-GPU inference。token: SUPERVISOR_APPROVED_022_FIX_GT_DISCOVERY_AND_RUN_CROSS_DATASET_4GPU。

### DIOR/FAIR1M/SODA-A 重新扫描结果（dataset_gt_rediscovery_022）
- **DIOR-R OBB GT 找到**: /home/rspip/cqc/data/dataset/DIOR/annfiles/obb/*.xml（robndbox 8-corner），23463 非空；val split=splits/val.txt，images/trainval。
- **FAIR1M-v1.0 OBB GT 找到**: fair1m1.0/split/val_20/annfiles/*.xml（points/quad），4362 非空。
- **SODA-A present 并可解析**: /home/rspip/cqc/data/dataset/SODA-A（dota_format_tiled_ss/val_tiled DOTA-poly8 txt 12832 非空 + Annotations/*.json 源）；不再 missing_dataset。
- HRSC2016: annfiles mbox XML（保留，angle uncertain）。

### 旧 021 判断为何不充分
- DIOR obb 文件是 *.xml，021 只搜 *.txt → 误判 empty；FAIR1M find -size 优先级 bug + 假设 split_ss 路径；SODA-A 未递归发现 dota_format_tiled_ss。已全部纠正。

### GT index 规模（OBB nonzero）
- SODA-A 408 img / 15187 obj；DIOR-R 600 img / 4065 obj；FAIR1M-v1.0 521 img / 10408 obj（invalid=2）；HRSC 1228 obj。parser: parse_dior/parse_fair1m/parse_dota_txt（QuadriBoxes→le90，angle_version=uncertain）。

### inference 命令 + world_size=4 + batch override=false
- DIOR-R orcnn #3: torch.distributed.run --nproc_per_node=4 --master_port=29634 mmrotate_1x/tools/test.py adapter(xds_b3_dump.py, _base_=pth_data config, DumpDetResults) → result_b3.pkl 1.1MB。
- FAIR1M orcnn #5: --master_port=29635 → result_b5.pkl 1.8MB。
- SODA-A orcnn #4: --master_port=29636 → result_b4.pkl 1.5MB。
- 全部 CUDA_VISIBLE_DEVICES=0,1,2,3、world_size=4、OMP 6×4=24CPU、**batch override=false**、无 OOM。gpu_policy_record 10 tasks 全 world_size=4。数据用非破坏性 symlink farm（outputs/predictions/{ds}/_root），**未改原始 dataset**。

### raw/schema 路径 + metrics 摘要（全 exploratory）
- raw/schema: outputs/predictions/{DIOR-R,FAIR1M-v1.0,SODA-A}/{3,5,4}/；GT index: outputs/bench_core/gt_index/。
- D2 exploratory metrics（near-square masked，class 对齐）: DIOR-R #3 n_used=3281 med_err 1.13° **NRC 0.52**；FAIR1M #5 n_used=6770 med_err 1.89° **NRC 0.86**；SODA-A #4 n_used=11890 med_err 1.96° **NRC 0.84**；HRSC 240 **NRC 0.81**。4 cells 0 failed。

### HRSC angle 状态
- angle_error_gate_status=**blocked_angle_uncertain**（mbox↔le90 正式只读证明未完成；mAP 0.906 一致性 sanity 记录）；不影响其它 dataset 跑 inference。其余 dataset le90_via_quadriboxes 标 uncertain（exploratory，不冻结）。

### 失败/blocked
- 跑通 4/4（DIOR/FAIR1M/SODA/HRSC）。仍 blocked: point2rbox（网络下载 __init__）、ARS-DETR（mmrotate 0.1.0 无 env，不替代 RHINO）。

### thresholds 未变 + 测试 + verification
- thresholds.yaml sha256 b7c4e649… **未变**。
- 新增 tests/test_022_gt_discovery.py（10 例：DIOR/FAIR1M OBB discovery、SODA present、empty split≠missing、gt_index nonzero、recursive schema、exploratory guard、gpu world_size=4、thresholds unchanged、HRSC angle isolated）；修复 gt_index meta 'stats' schema（兼容 bench_core 报告）。pytest -q → **202 passed**。
- scripts/90 21/21、91 20/20、92 12/12、新增 93_verify_cross_dataset_gt_and_runs.py → **16/16**。

### 停止条件
未触发（未训练/下载/装依赖/改 pth_data·dataset/替代 RHINO/改 batch·config/改 R1-R8·GV·NRC·score；thresholds 未变；DOTA milestone verify 通过；正式报告无 forbidden claim）。

### 产物路径
- scripts/{64_cross_dataset_gt,65_cross_dataset_metrics_022,93_verify_cross_dataset_gt_and_runs}.py、configs/_adapters/xds_b{3,4,5}_dump.py、tests/test_022_gt_discovery.py
- 报告: dataset_gt_rediscovery_022.*, gt_index_cross_dataset_022.*, cross_dataset_metrics_022.*, cross_dataset_failures_022.csv, soda_a_status_022.*, verification_cross_dataset_022.*, full_project_coverage_report.json(更新)
- gt_index: outputs/bench_core/gt_index/{DIOR-R,FAIR1M-v1.0,SODA-A}_val.{jsonl,meta.json}；predictions: outputs/predictions/{DIOR-R,FAIR1M-v1.0,SODA-A}/

---

## [2026-06-28 00:14:42 CST] 来源: supervisor

### 输入/指令
023：跨数据集 multi-detector 扩展。token: SUPERVISOR_APPROVED_023_CROSS_DATASET_MULTI_DETECTOR_4GPU_EXISTING_ASSETS。
- **032 ignored_due_to_wrong_thread_or_stage**：明确不执行 032 / 不切 C-5/source-teacher；当前仍是 OrientBench full-matrix 扩展。

### 执行计划（cross_dataset_multidetector_plan_023）
- datasets: DIOR-R/FAIR1M-v1.0/SODA-A/HRSC2016。mr_dev1x(orcnn/psc/rtmdet via pth_data config+adapter)=可跑；lsknet/strip cross-dataset=blocked_config_mismatch（ai4rs 无 matching-class config）；ARS-DETR=blocked_dependency（0.1.0，不替代 RHINO）；point2rbox=weak_nonformal（网络下载）。

### inference 命令 + world_size=4 + batch override=false
- DIOR-R psc#22(port 29641)→1.7MB；DIOR-R rtmdet-s#61(29642)→1.3MB；FAIR1M psc#24(29643)→3.4MB；SODA-A psc#23(29644)→2.5MB。
- 全部 torch.distributed.run --nproc_per_node=4 mmrotate_1x/tools/test.py + adapter(DumpDetResults)，CUDA_VISIBLE_DEVICES=0,1,2,3，world_size=4，OMP 6×4=24CPU，**batch override=false**，无 OOM。symlink farm（未改原始 dataset）。gpu_policy_record 14 tasks 全 world_size=4。

### raw/schema 路径 + metrics 摘要（全 exploratory）
- raw/schema: outputs/predictions/{DIOR-R,FAIR1M-v1.0,SODA-A}/{22,61,24,23}/。
- D2 exploratory metrics(near-square masked): DIOR-R orcnn#3 NRC 0.52 / psc#22 NRC 0.59 / rtmdet#61 NRC 0.44；FAIR1M orcnn#5 NRC 0.86 / psc#24 **NRC 1.03**；SODA-A orcnn#4 NRC 0.84 / psc#23 **NRC 1.17**；HRSC lsknet#13 NRC 0.81。**8 cells 0 failed**。
- 观察(exploratory): PSC angle-coder 在 FAIR1M/SODA NRC>1.0（选择弱于 random），与 DOTA psc#20(NRC 1.06) 一致 — 跨数据集模式。

### 各数据集 detector 覆盖率
- DIOR-R: 3 detector（orcnn/psc/rtmdet）；FAIR1M-v1.0: 2（orcnn/psc）；SODA-A: 2（orcnn/psc）；HRSC2016: 1（lsknet）。

### full val 是否完成
- 否（受控 subset：DIOR 600 / FAIR1M 521 / SODA 408 img；HRSC test split）。**非静默截断**，cross_dataset_fullval_status_023 明确记录原因（exploratory 吞吐 + 多 detector 优先）；如需 full val 同 4-GPU 去 SUBSET cap 重跑。

### HRSC angle 状态
- blocked_angle_uncertain（mbox↔le90 正式只读证明未完成；不阻塞其它 dataset）。

### 失败/blocked
- 跑通 4/4 ready cells。blocked: lsknet/strip cross-dataset(config_mismatch)、ARS-DETR(0.1.0 env)、point2rbox(网络)。

### thresholds 未变 + 测试 + verification
- thresholds.yaml sha256 b7c4e649… **未变**。
- 新增 tests/test_023_multidetector.py（10 例：plan schema、ready executed、gpu world_size=4、batch forbidden、schema、exploratory guard、thresholds unchanged、HRSC angle、fullval no silent trunc、no 032/C5 artifacts）。pytest -q → **212 passed**。
- scripts/90 21/21、91 20/20、92 12/12、93 16/16、新增 94_verify_cross_dataset_multidetector.py → **15/15**。

### 停止条件
未触发（未训练/下载/装依赖/改 pth_data·dataset/替代 RHINO/执行 032/改 batch·config/改 R1-R8·GV·NRC·score；thresholds 未变；DOTA milestone verify 通过；正式报告无 forbidden claim）。

### 产物路径
- scripts/{65(更新),94_verify_cross_dataset_multidetector}.py、configs/_adapters/xds_b{22,61,24,23}_dump.py、tests/test_023_multidetector.py
- 报告: cross_dataset_multidetector_plan_023.*, cross_dataset_schema_validation_023.*, cross_dataset_metrics_023.*, cross_dataset_fullval_status_023.*, verification_cross_dataset_multidetector_023.*, full_project_coverage_report.json(更新)
- predictions: outputs/predictions/{DIOR-R,FAIR1M-v1.0,SODA-A}/{22,61,24,23}/

---

## [2026-06-28 11:01:37 CST] 来源: supervisor

### 输入/指令
024：full-val + env/network unlock + matrix 扩展，严格 scratch 存储。token: SUPERVISOR_APPROVED_024_FULLVAL_ENV_NETWORK_SCRATCH_MATRIX_EXPANSION。SCRATCH=/dev/shm/cqc/orientbench；大文件(pth/pkl/raw/schema>1MB)→SCRATCH，项目仅留 manifest/sha256/metrics。

### 网络权限使用
- 已用网络（点对点下载尝试）。**未创建新 env**（full-val 复用 mr_dev1x 足够）。**未安装新依赖**。base/已有 env 未动。

### 资源
- /dev/shm 170GB free；4×A30 idle；网络 openmmlab+github 通；0 遗留进程。resource_startup_024.{md,json}。

### 下载文件
- point2rbox ted.pth: URL=https://www.modelscope.cn/models/wokaikaixinxin/mmrotate/resolve/master/Point2Rbox_v2/ted.pth → raw curl 返回 JSON metadata（需 modelscope SDK/auth 取二进制），**下载未完成**；记于 env_network_unlock_024。

### 每个 inference 命令 + world_size=4 + batch override=false
- DIOR-R orcnn#3 full-val: torch.distributed.run --nproc_per_node=4 --master_port=29691 mmrotate_1x/tools/test.py adapter(scratch farm, DumpDetResults) → /dev/shm/.../DIOR-R/3/raw/result_b3.pkl(10.3MB)，5863 img。
- FAIR1M orcnn#5 full-val: --master_port=29692 → result_b5.pkl(13MB)，3896 img。
- SODA-A orcnn#4 full-val: --master_port=29693 → result_b4.pkl(45MB)，12832 img。
- 全部 CUDA_VISIBLE_DEVICES=0,1,2,3、world_size=4、OMP 6×4=24CPU、**batch override=false**、无 OOM、无降 batch。

### raw/schema scratch 路径 + 项目 manifest
- raw: /dev/shm/cqc/orientbench/predictions/{ds}/{bid}/raw/；schema: 同 /schema/（DIOR 37MB/FAIR1M 118MB/SODA 421MB，全在 SCRATCH）。
- 项目: outputs/predictions/{ds}/{bid}/manifest.json（raw/schema scratch 路径 + sha256 + count + schema fields + validation summary + sample）+ schema_validation.csv + metrics_summary.csv。**项目无大文件**（git 不追踪 pkl/大 jsonl）。

### metrics 摘要（full-val, exploratory, near-square masked）
- DIOR-R #3: n_pred=60881 n_used=28437 **NRC 0.52** med_err 1.06°（与 subset 0.52 一致）。
- FAIR1M #5: n_pred=188153 n_used=48969 **NRC 0.84** med_err 1.9°（subset 0.86）。
- SODA-A #4: n_pred=676208 n_used=323616 **NRC 0.83** med_err 1.73°（subset 0.84）。

### ARS-DETR / point2rbox 解锁状态
- ARS-DETR: **needs_env**（隔离 mmrotate 0.1.0 + old mmcv-full/torch，构建风险高，本轮未建以免破坏 env，路径记录）；independent_archetype=true，**not_RHINO_replacement=true**。
- point2rbox: **needs_download**（modelscope SDK/auth）；**weak_nonformal**，不影响 formal gate。
- lsknet/strip cross-dataset: needs_adapter（ckpt head 已匹配数据集 num_classes，需 class-map adapter，不假改 head；本轮未跑）。

### full-val 完成情况 + 失败/blocked
- DIOR-R/FAIR1M/SODA-A orcnn **full-val 完成**（非 subset，非静默截断）。HRSC test split 已（022）。
- blocked: ARS-DETR(needs_env)/point2rbox(needs_download)/lsknet·strip cross-dataset(needs_adapter)，failures_024.csv。

### thresholds 未变 + verification + pytest + git
- thresholds.yaml sha256 b7c4e649… **未变**。
- 新增 scripts/{70_fullval_gt,71_fullval_metrics,95_verify_fullval_matrix_024,_cross_dataset_parsers}.py。
- verification: 90 21/21、91 20/20、92 12/12、93 16/16、94 15/15、95_verify_fullval_matrix_024 **23/23**（scratch 存储/manifest→scratch/sha256/git 无大文件/thresholds/world_size4/ARS≠RHINO/point2rbox weak）。
- 新增 tests/test_024_fullval.py（12 例：scratch policy、no large in project、manifest→scratch、env unlock、ARS≠RHINO、point2rbox weak、adapter 不假改 head、world_size4、fullval no silent subset、thresholds、exploratory、converter failure）。pytest -q → **224 passed**。
- git: 29bfbf1 024 full-val cross-dataset: DIOR/FAIR1M/SODA orcnn full-val (scratch storage)；large files tracked: 0。

### 停止条件
未触发（未训练/改原始 dataset·pth_data/替代 RHINO/改 batch·config 语义/改 R1-R8·GV·NRC·score；thresholds 未变；DOTA milestone verify 通过；正式报告无 forbidden claim；下载目标=named baseline 辅助权重）。

### 产物路径
- scripts/{70,71,95,_cross_dataset_parsers}.py、configs/_adapters/fv_b*.py、tests/test_024_fullval.py
- 报告: resource_startup_024.*, fullval_matrix_plan_024.*, env_network_unlock_024.*, adapter_manifest_024.*, schema_validation_024.*, metrics_024.*, failures_024.csv, probe_summary_024.*, verification_fullval_matrix_024.*, fullval_gt_index_024.csv, full_project_coverage_report.json(更新)
- 项目 manifest: outputs/predictions/{DIOR-R,FAIR1M-v1.0,SODA-A}/{3,5,4}/manifest.json
- SCRATCH: /dev/shm/cqc/orientbench/predictions/（raw+schema 大文件）、downloads/、gt_index meta outputs/bench_core/gt_index/*_fullval.meta.json

---

## [2026-06-28 12:06:45 CST] 来源: supervisor

### 输入/指令
025：大胆执行解锁剩余 detectors + full-val。token: SUPERVISOR_APPROVED_025_UNLOCK_REMAINING_DETECTORS_AND_FULLVAL_RUNS。能下载/建 env/写 adapter/跑 full-val 就做，失败记录继续。

### 网络下载记录
- point2rbox ted.pth: modelscope（SDK + raw resolve）→ 服务器返回「文件内容为空」(Code 10990101007)/404 → **upstream 文件不可用**，blocked_download_source_empty。weak_nonformal。
- pip 安装: torch 1.9.0+cu111, torchvision 0.10.0, mmcv-full 1.5.0, mmdet 2.25.1, e2cnn, modelscope（隔离 env）。

### env 创建记录
- **arsdetr**（隔离 conda env, python3.8, torch1.9.0+cu111, mmcv-full1.5.0, mmdet2.25.1, mmrotate0.1.0 fork, e2cnn）。base/已有 env 未动。arsdetr_env_025.{md,json}。

### adapter 记录
- configs/_adapters/{fv_b*(scratch farm), arsdetr_b14(0.1.0 data.test override)}.py；LSKNet cross-dataset 用 cfg-options num_classes+img_suffix（**不假改 head**，ckpt head 已匹配）。

### 每个 inference 命令 + world_size=4 + batch override=false
- psc/rtmdet full-val: DIOR#22(29701)/#61(29702), FAIR1M#24(29703), SODA#23(29704)（mr_dev1x, mmrotate_1x/tools/test.py）。
- LSKNet cross-dataset full-val: DIOR#10(29712)/FAIR1M#12(29721)/SODA#11(29722)（ai4rs_train, cfg-options num_classes+img_suffix）。
- ARS-DETR: DOTA-v1.0 #14(29731)（arsdetr env, torch.distributed.launch --nproc_per_node=4, ARS-DETR/tools/test.py）。
- 全部 CUDA_VISIBLE_DEVICES=0,1,2,3, world_size=4, **batch override=false**, 无 OOM。gpu_policy_record 25 tasks 全 world_size=4。

### scratch 路径 + project manifest
- raw+schema 全在 /dev/shm/cqc/orientbench/predictions/；project 仅 manifest/sha256/metrics（outputs/predictions/{ds}/{bid}/manifest.json）。项目无大 schema（git 0 大文件）。

### 失败原因
- point2rbox: modelscope upstream 文件空（blocked_download_source_empty）；weak_nonformal。strip cross-dataset 本轮未跑（LSKNet 优先）。

### metrics 摘要（全 exploratory, near-square masked）
- psc: DIOR#22 NRC 0.55 / FAIR1M#24 NRC 1.08 / SODA#23 NRC 1.26；rtmdet: DIOR#61 NRC 0.43。
- LSKNet cross-dataset: DIOR#10 NRC 0.53 / FAIR1M#12 NRC 0.83 / SODA#11 NRC 0.76。
- ARS-DETR DOTA-v1.0 #14: NRC 1.20 med_err 1.73°（exploratory；independent_archetype, NOT RHINO）。

### thresholds 未变 + verification + pytest + git
- thresholds.yaml sha256 b7c4e649… **未变**。
- verification: 90 21/21, 91 20/20, 92 12/12, 93 16/16, 94 15/15, 95 23/23, 新增 96_verify_unlock_remaining_detectors_025 **18/18**。
- 新增 scripts/{72_fullval_metrics_all,96_verify...}.py、tests/test_025_unlock.py（10 例）。pytest -q → **235 passed**。
- git: 06736a0 025 unlock ARS-DETR(env)+LSKNet(cross-dataset)+psc/rtmdet full-val; point2rbox blocked；large tracked 0。

### 停止条件
未触发（未训练/改原始 dataset·pth_data/替代 RHINO/改 batch·config 语义/改 R1-R8·GV·NRC·score；thresholds 未变；DOTA milestone verify 通过；arsdetr env 隔离未破坏已有 env；下载目标=named baseline 辅助权重）。

### 产物路径
- scripts/{72,96}.py、configs/_adapters/{fv_b*,arsdetr_b14}.py、tests/test_025_unlock.py
- 报告: unlock_remaining_detectors_025.*, arsdetr_env_025.*, point2rbox_download_025.md, fullval_remaining_cells_025.csv, metrics_025.*, verification_unlock_remaining_025.*, full_project_coverage_report.json(更新)
- project manifest: outputs/predictions/{DIOR-R,FAIR1M-v1.0,SODA-A,DOTA-v1.0}/{22,61,10,24,12,23,11,14}/manifest.json
- SCRATCH: /dev/shm/cqc/orientbench/predictions/（raw+schema）, env /home/rspip/anaconda3/envs/arsdetr

---

## [2026-06-28 12:59:57 CST] 来源: supervisor

### 输入/指令
026：不让 GPU 空闲；需训练则先训再并行推进。token: SUPERVISOR_APPROVED_026_TRAIN_IF_NEEDED_AND_CONTINUE_FULL_MATRIX。

### 是否有训练任务 / 训练是否启动
- **no_training_needed**：扫描 remaining cells（Strip/ARS-DETR cross-dataset, HRSC detectors）在 pth_data 均有 valid matching checkpoint → 按规则不训练，直接 inference。training_need_scan_026.* + 026_training_manifest.json(training_needed=false)。GPU 由 inference 占用不空闲。

### 并行 GPU 使用情况
- 演示并行：ARS-DETR(arsdetr env) + Strip(ai4rs env) 并发共享 4 卡（异 port）。出现 torchelastic worker 重启/不稳 → **按规则改串行 4-GPU**。串行后 cross-dataset ARS-DETR/Strip 仍 worker crash/stall。

### 新增成功 cells / 失败 blocked
- 成功(本轮新): 无新完成 inference cell（cross-dataset ARS-DETR/Strip blocked_runtime）。本轮交付为 scans/proofs/unlock-load-proofs。
- ARS-DETR cross-dataset(DIOR/FAIR1M/SODA/HRSC): ckpt load OK(missing=0)，inference **blocked_runtime**（cross-dataset farm 4-GPU worker crash-loop, torchelastic 8 attempts）。ARS-DETR DOTA-v1.0(025) 成功。
- Strip cross-dataset(DIOR #47): ckpt load OK(missing=2/384，**不假改 head**)，inference **blocked_runtime**（worker stall）。
- 修了 .jpg→.png symlink(ARS-DETR DOTADataset 硬编码 .png) 与 work_dirs/Task1 清理，仍 worker 级不稳。

### ARS-DETR cross-dataset 状态 / Strip 状态
- 均 ckpt-load 已证 + DOTA scope 成功；cross-dataset inference blocked_runtime（记录原因继续，未训练/未改协议）。

### point2rbox 状态
- **blocked_upstream_artifact_unavailable**：ted.pth modelscope「文件内容为空」/github 9B(asset 不存在)/huggingface 401。weak_nonformal，不进 formal gate。

### HRSC angle 状态
- **resolved_with_evidence**：hrsc.py:175-181 将 mbox_ang 直接作为 le90 rbox theta（无变换）+ LSKNet HRSC mAP 0.906 双证据。hrsc_angle_proof_026.md。

### 关键 metrics
- 本轮无新完成 cell；既有 cross-dataset full-val(025): DIOR/FAIR1M/SODA orcnn/psc/rtmdet/LSKNet + ARS-DETR DOTA 不变。

### 存储 / GPU policy / thresholds
- 存储合规（大文件 scratch，project manifest，git 0 大文件）。GPU policy: 所有 job world_size=4, batch override=false。thresholds.yaml sha256 b7c4e649… **未变**。

### env 创建记录
- 本轮未建新 env（复用 025 的 arsdetr env）。

### verification / pytest / git
- 新增 scripts/97_verify_train_and_continue_026.py → **VERIFIED 13/13**；90-96 全过（21/20/12/16/15/23/18）。
- 新增 tests/test_026_train_continue.py（7 例）。pytest -q → **242 passed**。
- git: 01327f4 026 no-training-needed; HRSC angle resolved; point2rbox blocked_upstream; ARS-DETR/Strip cross-dataset blocked_runtime；large tracked 0。

### 停止条件
未触发（no_training_needed 故未训练；未改原始 dataset/pth_data/替代 RHINO/改 batch·config 语义/改 R1-R8·GV·NRC·score；thresholds 未变；DOTA milestone verify 通过；arsdetr env 隔离；无系统级 GPU 故障——worker crash 为 cross-dataset run 局部失败，已记录继续）。

### 下一步最小行动
- ARS-DETR/Strip cross-dataset blocked_runtime 根因排查（单卡 smoke 定位 worker crash，或换 ann-listing/数据 pipeline）；point2rbox 等上游恢复 ted.pth；Strip cross-dataset 改 DumpDetResults 评估器避开 DOTAMetric。

### 产物路径
- scripts/97_verify_train_and_continue_026.py、tests/test_026_train_continue.py
- 报告: training_need_scan_026.*, cells_status_026.*, hrsc_angle_proof_026.md, point2rbox_download_025.md(更新), verification_train_and_continue_026.*, full_project_coverage_report.json(更新)
- outputs/training/026_training_manifest.json

---

## [2026-06-28 13:33:05 CST] 来源: supervisor

### 输入/指令
027：GPU 不许空转；无必训 cell 则启动 replicate/fallback training，并行推进 inference/debug/HRSC/point2rbox/metrics。token: SUPERVISOR_APPROVED_027_KEEP_GPU_BUSY_TRAIN_REPLICATE_AND_RUN_QUEUE。

### 10 分钟内是否启动 GPU job：是
- 先试 ready inference（Strip DIOR clean）→ 仍 init stall；改启 **replicate training**（oriented_rcnn DOTA-v1.0 官方 #1 config），4-GPU 跑起来（util 45-100%，eta ~1.6h）。GPU 持续占用。

### 启动了哪些训练
- replicate training: oriented_rcnn_r50_fpn_1x_le90 DOTA-v1.0（官方 config，data_root 路径修正到 dota1.0/split_ss_dota10，**不调参/不改 batch/lr/schedule/model**）。
- 标注: trained_by_027_replicate=true, not_original_readme_checkpoint=true, not_formal_gate=true, exploratory_or_fallback=true。每 epoch eval, best+latest, workdir=scratch。**status=running**（）。027_replicate_training_manifest.json。

### 启动了哪些 inference/debug + 关键运行期发现
- 调试 cross-dataset Strip/ARS-DETR worker stall：发现 **bare run_in_background torchrun 命令 GPU 正常启动；nohup-bash-wrapper 启动 stall（worker 不上 GPU, util 0%）**。
- **根因**: 026/027 早期 Strip/ARS-DETR cross-dataset blocked_runtime 主因 = 启动方式（nohup wrapper），非模型/数据。replicate training 用 bare 命令即跑通（util 高），佐证此结论。下一轮用 bare 命令重试 cross-dataset Strip/ARS-DETR 应可跑通。

### 并行策略 + world_size=4 + batch override=false + OOM/NCCL/worker crash 记录
- 训练占满 4 卡（util 高）；cross-dataset inference 并发会争显存，留待训练后/bare-command 重试。所有 GPU job world_size=4, batch override=false。无 OOM；早期 worker stall=launch-method（已定位非系统级 GPU 故障，bare 命令正常）。

### 新增成功 cells / 正在训练 jobs + ETA
- 新增完成 inference cell: 无（cross-dataset 重试留待）；**replicate training 运行中**（ETA ~1.6h，scratch）。

### point2rbox 状态
- blocked_upstream_artifact_unavailable（不变；ted.pth 所有上游不可用）。weak_nonformal，未阻塞 GPU。

### ARS-DETR/Strip 状态 / HRSC 多 detector 状态
- ARS-DETR/Strip cross-dataset: blocked_runtime 根因=launch-method（待 bare 重试）；ckpt-load 已证；DOTA scope 成功。
- HRSC angle resolved_with_evidence（026）；HRSC 多 detector inference 留待训练后 GPU 空闲 bare-command 跑。

### 关键 metrics
- 本轮无新完成 cell；既有 cross-dataset full-val(025) 不变。

### 存储 / thresholds / verification / pytest / git
- 存储合规（大文件 scratch；project manifest；git 0 大文件）。thresholds.yaml sha256 b7c4e649… **未变**。
- 新增 scripts/98_verify_gpu_busy_training_queue_027.py → **VERIFIED 10/10**；90-97 全过。
- 新增 tests/test_027_gpu_busy.py（7 例）。pytest -q → **249 passed**。
- git: b848ee0 027 keep GPU busy: replicate training running 4-GPU; launch-method root cause for cross-dataset stalls；large tracked 0。

### 停止条件
未触发（replicate training 用官方 config 不调参；未改原始 dataset/pth_data/替代 RHINO/改 R1-R8·GV·NRC·score；thresholds 未变；DOTA milestone verify 通过；非系统级 GPU 故障——bare 命令 GPU 正常）。

### 下一步最小行动
- 训练完成后取 best/latest + sha256 写 manifest（trained_by_027_replicate）；用 **bare run_in_background 命令**重试 cross-dataset Strip/ARS-DETR + HRSC 多 detector（根因已定位）；point2rbox 等上游恢复。

### 产物路径
- scripts/98_verify_gpu_busy_training_queue_027.py、tests/test_027_gpu_busy.py
- 报告: gpu_busy_training_027.md, verification_gpu_busy_training_027.*, full_project_coverage_report.json
- outputs/training/027_replicate_training_manifest.json；training workdir=/dev/shm/cqc/orientbench/training/replicate_orcnn_dota10_027

---
## [2026-06-28 15:31:29 CST] 来源: claude (027 训练完成回填)
- replicate training (oriented_rcnn DOTA-v1.0, trained_by_027_replicate) **完成 12 epoch**：best dota/mAP **0.7015** @epoch12（原 baseline #1=0.7061，delta 0.0046，忠实复现）。best/latest + sha256 写入 027_replicate_training_manifest.json（status=completed, NOT formal/NOT readme substitute, in scratch）。GPU 现空闲（其余为他用户 baseline）。
- 下一步: 用 bare run_in_background 命令重试 cross-dataset Strip/ARS-DETR + HRSC 多 detector（根因=launch-method 已定位）。

---

## [2026-06-28 17:26:24 CST] 来源: supervisor

### 输入/指令
028：立即把 GPU job 跑起来；用 bare launcher 重跑 blocked_runtime 队列；自主修 runtime，不请示；同 cell 连续失败 3 次才标 blocked。token: SUPERVISOR_APPROVED_028_RUN_NOW_FIX_RUNTIME_AUTONOMOUSLY。

### 10 分钟内启动的 GPU job
- ARS-DETR cross-dataset DIOR-R #16（bare run_in_background torchrun, 4-GPU, arsdetr env, port 29871）→ util 74-76% 跑通，**full-val 完成 68MB/40668 preds**。launch_status_028.md。

### 每个命令 + 失败重试 + 修复动作（自主）
- ARS-DETR DIOR 先 wrong-ckpt-path(我猜错) → 改正确 ckpt（best_mAP_4158_epoch_35.pth）。
- 再 ZeroDivisionError（**真根因=空 annfile，ARS-DETR 0.1.0 DOTADataset 加载 0 images**）→ 用真实 GT(DOTA poly8, obb→corners) 填充 DIOR/FAIR1M/SODA farm annfiles → DIOR 跑通。
- ARS-DETR FAIR1M #18: KeyError 'Engineering-Ship'（**FAIR1M 类名含空格，与空格分隔 DOTA-txt + ARS-DETR 固定 CLASSES 不兼容**）→ blocked_runtime_with_evidence。
- Strip DIOR: 填充 annfile 破坏 mmrotate-1.x（KeyError 'vehicle'，DIOR 类不在 DOTA metainfo）→ 复原空 annfile → 推理 OK([700/733]) 但 DOTAMetric 空 GT IndexError → **改 evaluator=DumpDetResults** → running/near-complete (inference [700/733] OK, evaluator fixed)。

### GPU 使用 + world_size=4 + batch override=false
- 全程 bare-command 4-GPU world_size=4，util 50-76%，batch override=false，无降 batch。GPU 持续占用。bare run_in_background 启动正常（区别于早期 nohup-wrapper）。

### 已完成 cells / 失败 cells + 证据
- 完成: ARS-DETR DIOR-R #16 full-val（exploratory NRC 0.999 n_used=33；ARS-DETR DIOR 弱模型 mAP 0.4158）。Strip DIOR #47 running/near-complete (inference [700/733] OK, evaluator fixed)。
- blocked_runtime_with_evidence: ARS-DETR FAIR1M #18（类名空格格式）。ARS-DETR SODA #17 deferred（同风险）。

### point2rbox / HRSC angle
- point2rbox: blocked_upstream_artifact_unavailable（不变；未占主线）。HRSC angle: resolved_with_evidence（026 不变）。

### 新增 metrics
- ARS-DETR DIOR-R #16: NRC_AUC 0.999, med_err 4.26°（exploratory；arsdetr_xds_metrics_028.csv）。independent_archetype, NOT RHINO。

### 存储 / thresholds / 测试
- 存储合规（raw+schema scratch；project manifest+sha256；git 0 大文件）。thresholds.yaml b7c4e649… **未变**。
- pytest -q → **249 passed**（90-98 verification 全过）。git commit 0e026cb。

### 下一步还在跑什么
- Strip DIOR #47 running/near-complete (inference [700/733] OK, evaluator fixed)（完成后 convert+metrics）。
- 下一步: ARS-DETR FAIR1M/SODA 需类名匹配 ARS-DETR config CLASSES 的 annfile（underscore/无空格映射）；SODA ARS-DETR（类名无空格，可填充重试）；Strip FAIR1M/SODA（empty annfile + DumpDetResults 模板已验证）。

### 产物路径
- scripts/73_arsdetr_xds_metrics.py、launch_status_028.md, heartbeat_028.json, cells_status_028.md, arsdetr_xds_metrics_028.csv
- outputs/predictions/DIOR-R/16/manifest.json；raw/schema 在 /dev/shm/cqc/orientbench/predictions/

---

## [2026-06-28 18:00:47 CST] 来源: supervisor

### 输入/指令
029：full-matrix 收尾，自主执行，能跑就跑能修就修，单 cell 留痕后继续。token: SUPERVISOR_APPROVED_029_FULL_MATRIX_FINISH_AUTONOMOUS。

### 029 阶段性完成
- 收尾 + 报告收口。final_matrix_summary：**22 real cells / 6 datasets**。

### 新增成功 cells / 最终 detector×dataset 覆盖率
- 最终矩阵覆盖: DIOR-R **5 detectors**(orcnn/psc/rtmdet/lsknet/arsdetr), DOTA-v1.0 6, DOTA-v1.5 4, FAIR1M-v1.0 3(orcnn/psc/lsknet), SODA-A 3(orcnn/psc/lsknet), HRSC2016 1(lsknet)。
- 本轮新增 inference 完成: 无（Strip DIOR 多次重试 evaluator/DDP 收尾不稳）；本轮主要为收口 + 自主修复尝试 + 报告整合。

### 仍 blocked cells + 证据
- Strip cross-dataset(DIOR #47): **blocked_runtime_with_evidence**（4+ 次：inference [700/733] OK，DumpDetResults/DDP 收尾反复 crash；LSKNet 同路径成功，Strip 特定不稳）。
- ARS-DETR FAIR1M: blocked_class_mapping_with_evidence（空格类名 'Engineering-Ship' 与空格分隔 DOTA-txt 不兼容）。
- point2rbox: blocked_upstream_artifact_unavailable（ted.pth 全上游空/404/401）。
- remaining_blockers.{md,csv} 全记录。

### point2rbox / ARS-DETR / Strip / HRSC 多 detector 状态
- point2rbox: blocked_upstream（weak_nonformal，未占主线）。
- ARS-DETR: cross-dataset DIOR 解锁完成；FAIR1M class-map blocked；SODA/HRSC pattern 可用未跑。independent_archetype, NOT RHINO。
- Strip: cross-dataset blocked_runtime（DOTA scope 020 成功）。
- HRSC 多 detector: lsknet 完成；angle resolved_with_evidence；其它 detector pattern 可用。

### full-val 状态 / 关键 metrics
- full-val 完成: DIOR/FAIR1M/SODA orcnn(024) + psc/rtmdet/lsknet(025) + ARS-DETR DIOR(028)。HRSC test split。
- 关键 metrics(exploratory): DIOR orcnn 0.52/psc 0.55/rtmdet 0.43/lsknet 0.53/arsdetr 0.999; FAIR1M 0.84-0.86/psc 1.08/lsknet 0.83; SODA 0.83/psc 1.26/lsknet 0.76; HRSC lsknet 0.81。

### GPU 使用是否持续 / 存储是否合规 / thresholds
- GPU: 本轮间歇（cross-dataset Strip 反复 stall/crash，killed 后空闲短时；replicate training(027) 已完成）。bare-command 启动正常。
- 存储合规: 17 个 project 大 schema 移至 scratch(_archive)，**project 0 大文件**；raw/schema 全 scratch。thresholds.yaml b7c4e649… **未变**。

### verification/test/git
- pytest -q → **257 passed**。verifier 90-99 全过（含新增 99_verify_full_matrix_finish_029 13/13）。git: 3220d2f 029 full-matrix finish: 22 cells/6 datasets consolidated; remaining blockers + evidence; large tracked 0。

### 报告收口（task 10）
- final_matrix_summary.{md,csv}, remaining_blockers.{md,csv}, full_project_coverage_report.json(final_matrix), project_status_matrix/claim_ledger/readiness_check/formal_gate_summary(更新), heartbeat_029.json, launch_status_028.md。

### 停止条件
未触发（未改原始 dataset/pth_data/替代 RHINO/改核心指标定义；thresholds 未破坏；非系统级 GPU 故障——bare command 正常；scratch 155G free）。

### 下一步是否需要人工裁决
- 不强需。剩余 cross-dataset cells（Strip FAIR1M/SODA/HRSC, ARS-DETR SODA/HRSC/FAIR1M-classmap）pattern 已验证，可后续自主补；但 Strip evaluator/DDP 不稳与 FAIR1M class-map 需更多 runtime 调试预算。genuine multi-view C1 / cross-host A4 需新数据+批准（out_of_scope）。

### 产物路径
- scripts/{74_final_matrix_summary,99_verify_full_matrix_finish_029}.py、tests/test_029_finish.py
- 报告: final_matrix_summary.*, remaining_blockers.*, heartbeat_029.json, verification_full_matrix_finish_029.*
- scratch: /dev/shm/cqc/orientbench/predictions/（raw+schema+_archive）

---
## [2026-06-28 18:26:59 CST] 来源: supervisor
### 030 final push（简报已写入 docs/cc_latest_report.md，本处仅审计）
- token SUPERVISOR_APPROVED_030_FINAL_PUSH_AND_FILE_ONLY_REPORTING。汇报规则改为只写 docs/cc_latest_report.md（clear+rewrite），终端仅 REPORT_WRITTEN。
- 新增成功 cell: Strip cross-dataset DIOR #47（NRC 0.506；关键修复 test_evaluator._delete_+DumpDetResults 绕开 DOTAMetric 空-GT crash）。final matrix 23 cells/6 datasets，DIOR-R 6 detectors。
- blocked final w/ evidence: ARS-DETR FAIR1M(class-space)、ARS-DETR SODA(class-mapping KeyError, 3 retry)、point2rbox(upstream dead: modelscope空/github 9B/hf 401/openmmlab 404)、Strip/ARS-DETR HRSC(pattern available budget-bound)。
- 存储: 移大 pred schema(a4_host/rhino)至 scratch _archive，project 0 大 pred schema。thresholds b7c4e649 未变。
- verification 100_verify_final_push_030 + 90-99 全过；pytest passed；git lightweight。建议进入 031 final freeze/report。

---
## [2026-06-28 22:16:10 CST] 来源: supervisor
### 031 final freeze/report（简报写入 docs/cc_latest_report.md，本处审计）
- token SUPERVISOR_APPROVED_031_FINAL_FREEZE_AND_REPORT。无新实验/无 GPU job（cells 已有 metrics；backfill 11 个 per-cell manifest 自 aggregate metrics，非重跑）。
- 生成最终报告: final_orientbench_report/summary/claim_ledger/limitations/artifact_manifest/reproducibility_guide/release_notes/coverage_matrix/blocker_evidence。release 包 outputs/releases/orientbench_final_current_scope（manifest+sha256，无大文件）。
- 冻结确认: thresholds b7c4e649 未变；git 0 大文件；project 0 大 pred schema；23 cells 全有 manifest。current_approved_scope_complete=true, full_project_complete=false。
- verification 101_verify_final_release_031 21/21；90-100 全过；pytest 264 passed。

---
## 2026-06-28 23:53:21 CST 来源: supervisor
### 032 合作者进展报告（简报 docs/cc_latest_report.md；审计）
- token SUPERVISOR_APPROVED_032。无实验/GPU/thresholds 变更。生成 docs/orientbench_project_progress_report.md + summary.json + release copy；verification 102 VERIFIED 10/10；thresholds b7c4e649 未变；git 0 大文件。

---
## 2026-06-29 10:59:19 CST 来源: supervisor
### 033 P1 科学有效性审计 v2（简报 docs/cc_latest_report.md；审计）
- token 033。无训练/GPU。修 3 矛盾(PSC NRC≤1 误述/rtmdet#32 缺表/NRC-mAP n=3)。construct validity: Spearman(NRC,mAP)=-0.046, partial(ctrl both)=-0.005 → NRC⟂mAP。tail risk: unmasked p99≈89°(near-square), masked p99 10-16° → cliff 真实。PSC 反校准(DOTA/FAIR1M/SODA NRC>1)成立。selection score 三轨 + 持久化(2.6GB→persistent_artifacts gitignored)。verifier 102_v2 21/21。P1 值得继续。thresholds b7c4e649 未变。

---
## 2026-06-29 12:42:17 CST 来源: supervisor
### 034 合作者决策包（简报 docs/cc_latest_report.md 用 👇/👆 包住；审计）
- token 034。无训练/GPU/thresholds 变更。生成 collaborator_p1_scientific_validity_packet / decision_form(D1-D7) / one_page_summary。新汇报格式：cc_latest_report 用 👇👆 入口出口包住，终端只输出同样包住的文件路径。verifier 103_verify_collaborator_packet_034 8/8；pytest 264 passed；git 0 大文件。等待 D1-D7 裁决。

---
## 2026-06-29 13:24:57 CST 来源: supervisor
### 035 P1 深度核验+单文件报告（简报 cc_latest_report 👇👆 包住；审计）
- token 035。无训练/GPU/thresholds·split 变更。p99 核验: 代码正确, 90°=near-square ill-posed(非 catastrophic, 纠正 033), masked p99 10-16° 真实。cliff 成立(p99 vs ar). NRC 构造效度: Spearman -0.046 CI[-0.49,0.48], partial df=7 under-powered → 未检测显著相关, 不主张严格独立. PSC Track B 反校准稳定. 单文件 docs/orientbench_p1_scientific_report.md(034 分散→_superseded). 14 p99 figs + cliff fig(gitignored). verifier 104 19/19; pytest pass; git 0 大文件.

---
## 2026-06-29 15:34:06 CST 来源: supervisor
### 036 P1 中文论文标准审稿稿（简报 cc 👇👆；审计）
- token 036。无训练/GPU/thresholds·split 变更。单文档 docs/orientbench_p1_chinese_paper_draft.md(11 节+附录+图表占位, 无期刊名). bootstrap NRC CI(masked): FAIR1M PSC[1.027,1.134]/SODA PSC[1.238,1.281] 显著>1; DOTA PSC 0.840[0.787,0.900] 不显著(修正 unmasked 1.06=near-square). fig1/2/3 数据 csv. persistent 8 key cells(+DOTA #20/rhino). claim ledger + license 完成. verifier 105 19/19; pytest pass; git 0 大文件. 下一步等 PSC Track A/B control 批准.

---
## 2026-06-29 15:54:08 CST 来源: supervisor
### 037 P3 可行性门控（简报 cc 👇👆；审计）
- token 037。无训练/host 重训/full matrix/追 mAP；thresholds·frozen split 未改。Track A: PSC saved preds 无 angle logits(只 bboxes/scores/labels)→unavailable, 需 forward dump(encode_size=6 相位码). Track B/C(D_cal→D_audit, 互斥): post-hoc selector 显著改善 FAIR1M 1.153→0.627 / SODA 1.254→0.464 / DOTA 0.740→0.503, AURC 全降 → PSC=score-proxy mismatch 可修复. cliff: near-square delta~81.6°(trivial), well-defined p99~8.3°(modest). 门控: P3 有条件启动(post-hoc/unified-proxy 路线), 首步=PSC forward dump 提取 Track A. 单文件 docs/p3_feasibility_gate_report.md. verifier 106 14/14; pytest 264; git 0 大文件.

---
## 2026-06-29 16:50:24 CST 来源: supervisor
### 038 P3 G2′ feasibility（简报 cc 👇👆；审计）
- token 038。无 detector 训练/full matrix/Track A dump；thresholds·P1 split 未改。G2′ PASS: well-defined(ar>=1.6, near-square 排除) 上非线性 geometry-aware selector 显著优于 score+ar 线性(D_audit, 所有 cell+pooled DELTA CI>0; pooled P3 NRC 0.409 vs linear 0.626, delta 0.217[0.211,0.221]). ar>=1.3/2.0 sensitivity 一致. feature imp: box size+GV 主导, log_ar 极小→非 ar/非 near-square trivial. 诚实: P3=upper-bound post-hoc(用 GT 标签训练), 非 deployable; 未声称 P3 已成立. 下一步 pass 分支: G1/G3/G4 + Track A dump. 单文件 docs/p3_g2prime_feasibility_report.md. verifier 107 14/14; pytest 264; git 0 大文件.
## 2026-07-02 18:44:34 CST

- 指令来源: SUPERVISOR_049_CODEX_TOP_JOURNAL_EVIDENCE_UPGRADE_V2
- 执行动作: 读取 AGENTS.md 和 项目执行文件_v2_measure_fix.md；创建 top_journal_v3；生成 P1-P5 partial evidence package、写作 patch、验证器输入产物。
- 关键产物路径: top_journal_v3/docs/, top_journal_v3/reports/, top_journal_v3/figures/, top_journal_v3/scripts/run_049_evidence.py
- pass/fail/partial: partial；P3 机制免费测试未达升级标准。
- 是否触发停止条件: 是，P3 per-instance mechanism artifacts 缺失导致不得进入 PSC 重训矩阵；P1 final construct validity 受 proxy/synthetic raw predictions 限制。
- 下一步建议: 定位非 synthetic detector raw predictions 和 per-instance PSC phase_mod dump 后复跑。

## 2026-07-02 18:46:20 CST

- 指令来源: SUPERVISOR_049_CODEX_TOP_JOURNAL_EVIDENCE_UPGRADE_V2
- 执行动作: 读取 AGENTS.md 和 项目执行文件_v2_measure_fix.md；创建 top_journal_v3；生成 P1-P5 partial evidence package、写作 patch、验证器输入产物。
- 关键产物路径: top_journal_v3/docs/, top_journal_v3/reports/, top_journal_v3/figures/, top_journal_v3/scripts/run_049_evidence.py
- pass/fail/partial: partial；P3 机制免费测试未达升级标准。
- 是否触发停止条件: 是，P3 per-instance mechanism artifacts 缺失导致不得进入 PSC 重训矩阵；P1 final construct validity 受 proxy/synthetic raw predictions 限制。
- 下一步建议: 定位非 synthetic detector raw predictions 和 per-instance PSC phase_mod dump 后复跑。

## 2026-07-02 18:46:44 CST

- 指令来源: SUPERVISOR_049_CODEX_TOP_JOURNAL_EVIDENCE_UPGRADE_V2
- 执行动作: 读取 AGENTS.md 和 项目执行文件_v2_measure_fix.md；创建 top_journal_v3；生成 P1-P5 partial evidence package、写作 patch、验证器输入产物。
- 关键产物路径: top_journal_v3/docs/, top_journal_v3/reports/, top_journal_v3/figures/, top_journal_v3/scripts/run_049_evidence.py
- pass/fail/partial: partial；P3 机制免费测试未达升级标准。
- 是否触发停止条件: 是，P3 per-instance mechanism artifacts 缺失导致不得进入 PSC 重训矩阵；P1 final construct validity 受 proxy/synthetic raw predictions 限制。
- 下一步建议: 定位非 synthetic detector raw predictions 和 per-instance PSC phase_mod dump 后复跑。

## 2026-07-02 18:47:16 CST

- 指令来源: SUPERVISOR_049_CODEX_TOP_JOURNAL_EVIDENCE_UPGRADE_V2
- 执行动作: 读取 AGENTS.md 和 项目执行文件_v2_measure_fix.md；创建 top_journal_v3；生成 P1-P5 partial evidence package、写作 patch、验证器输入产物。
- 关键产物路径: top_journal_v3/docs/, top_journal_v3/reports/, top_journal_v3/figures/, top_journal_v3/scripts/run_049_evidence.py
- pass/fail/partial: partial；P3 机制免费测试未达升级标准。
- 是否触发停止条件: 是，P3 per-instance mechanism artifacts 缺失导致不得进入 PSC 重训矩阵；P1 final construct validity 受 proxy/synthetic raw predictions 限制。
- 下一步建议: 定位非 synthetic detector raw predictions 和 per-instance PSC phase_mod dump 后复跑。

## 2026-07-02 20:09:29 CST

- 指令来源: SUPERVISOR_050_CODEX_REAL_ARTIFACT_RECOVERY_AND_EVIDENCE_COMPLETION
- 执行动作: real artifact audit；基于 verified non-synthetic artifacts 生成 partial real evidence；未启动训练/GPU inference。
- 关键产物路径: top_journal_v3/reports/real_artifact_inventory_050.csv; outputs/persistent_artifacts/manifest_050.json; top_journal_v3/docs/top_journal_evidence_decision_050.md
- pass/fail/partial: partial; P3 fail for escalation.
- 是否触发停止条件: 是，DOTA #20 phase_mod 与 exact per-matched phase_mod table 缺失，不能进入 PSC 重训矩阵。
- 下一步建议: 先补 DOTA #20 instrumented forward dump 和 exact per-pred match index persistence，再复跑 P3/P4。

## 2026-07-02 20:14:33 CST

- 指令来源: SUPERVISOR_050_CODEX_REAL_ARTIFACT_RECOVERY_AND_EVIDENCE_COMPLETION
- 执行动作: real artifact audit；基于 verified non-synthetic artifacts 生成 partial real evidence；未启动训练/GPU inference。
- 关键产物路径: top_journal_v3/reports/real_artifact_inventory_050.csv; outputs/persistent_artifacts/manifest_050.json; top_journal_v3/docs/top_journal_evidence_decision_050.md
- pass/fail/partial: partial; P3 fail for escalation.
- 是否触发停止条件: 是，DOTA #20 phase_mod 与 exact per-matched phase_mod table 缺失，不能进入 PSC 重训矩阵。
- 下一步建议: 先补 DOTA #20 instrumented forward dump 和 exact per-pred match index persistence，再复跑 P3/P4。

## 2026-07-02 21:03:02 CST

- 指令来源: SUPERVISOR_051_CODEX_HANDOFF_AND_REAL_EVIDENCE_RECOVERY
- 执行动作: 读取 AGENTS.md 和 项目执行文件_v2_measure_fix.md；生成 handoff map、artifact locator、cell status、gap plan；离线恢复 PSC/TTA/matched capped artifacts；未启动 GPU/inference/training。
- 关键产物路径: top_journal_v3/docs/codex_handoff_map_051.md; top_journal_v3/reports/real_cell_artifact_status_051.csv; outputs/persistent_artifacts/manifest_051.json
- pass/fail/partial: partial recovery; P3 final rerun still blocked by DOTA #20 phase_mod.
- 是否触发停止条件: 未触发科学早停；触发 artifact gap stop for final P3.
- 下一步建议: 052 先补 DOTA #20 Track A dump 与 full matched persistence，再复跑 P1-P5。

## 2026-07-02 22:12:26 CST

- 指令来源: SUPERVISOR_052_CODEX_FORCE_REAL_DUMP_AND_FULL_MATCHED_TABLES
- 执行动作: 用真实 DOTA #20 PSC checkpoint/config/shadow farm 运行 4GPU instrumented forward dump；持久化 DOTA #20 phase_mod pkl；重建 7 个 full matched 17-field tables；生成 4 个 PSC cell per-matched phase_mod full table；生成 7 个 TTA cells theta->2theta circular variance full table；新增并运行 052 verifier。
- 关键产物路径: outputs/persistent_artifacts/orientbench_real_052/; outputs/persistent_artifacts/manifest_052.json; top_journal_v3/reports/full_matched_tables_052.csv; top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv; top_journal_v3/reports/tta_circular_variance_full_052.csv
- pass/fail/partial: pass for artifact recovery/readiness; P1-P5 now have verified real-artifact inputs for rerun.
- 是否触发停止条件: 未触发；未修改 thresholds.yaml、D_cal/D_audit、原始 dataset、pth_data；未训练 host；未补 full matrix。
- 下一步建议: 053 复跑 P1/P2/P3/P4/P5 scientific analyses using only 052 verified real artifacts.
## 2026-07-02 23:59:09 CST

- 指令来源：SUPERVISOR_053_CODEX_REAL_EVIDENCE_P1_P5_RERUN。
- 执行动作：接手 052 real artifacts 后复跑 P1-P5 真实证据；P1 全量 raw/schema 扰动后重新匹配；P2 frozen split conformal；P3 PSC per-matched phase_mod 免费测试；P4 TTA circular variance 强基线；P5 angle-induced rIoU drop 下游任务；更新 053 verdict/report/verifier。
- 关键产物路径：`top_journal_v3/docs/top_journal_evidence_decision_053.md`；`top_journal_v3/docs/codex_latest_report.md`；`top_journal_v3/scripts/verify_real_evidence_p1_p5_rerun_053.py`。
- 是否触发停止条件：未触发受保护文件/训练/矩阵扩展停止条件；证据裁决要求 claim 收缩。
- 下一步建议：以 053 真实证据为准进入收缩版论文写作，不写 broader top-tier ready，不启动 PSC 重训矩阵。
## 2026-07-03 11:38:06 CST

- 指令来源：SUPERVISOR_054_CODEX_REDUCED_SCOPE_CHINESE_PAPER_FINALIZATION。
- 执行动作：根据 053 真实证据裁决完成收缩版中文论文定稿包；未新增实验、未训练、未触碰受保护 split/threshold；新增 reduced-scope verifier 并准备验证。
- 关键产物路径：`top_journal_v3/docs/orientation_reliability_reduced_scope_paper_zh.md`；`top_journal_v3/docs/final_reduced_scope_paper_plan_054.md`；`top_journal_v3/docs/negative_results_and_boundaries_054.md`；`top_journal_v3/docs/conformal_risk_control_main_claim_054.md`；`top_journal_v3/docs/final_claim_ledger_reduced_scope_054.md`；`top_journal_v3/docs/codex_latest_report.md`。
- 是否触发停止条件：未触发工程停止条件；触发科学 claim 收缩，P2 保留为主正贡献，P3/P4/P5 不再作为主贡献。
- 下一步建议：将中文稿交合作者审稿，后续只做文字和引用校正，不再扩实验。
- 验证结果：`verify_reduced_scope_paper_054.py` PASS；`pytest -q tests/test_bench_core0.py` 17 passed；protected diff clean；tracked git big-file check clean。
## 2026-07-03 12:36:14 CST

- 指令来源：用户要求为后续接手者记录当前工作交接。
- 执行动作：新增 `top_journal_v3/docs/codex_successor_handoff_054.md`，记录接手前状态、052 real artifacts、053 真实证据复跑、054 收缩版论文定稿、当前裁决、禁区、路径和后续建议。
- 关键产物路径：`top_journal_v3/docs/codex_successor_handoff_054.md`。
- 是否触发停止条件：否；只做文档交接，未新增实验、未训练、未触碰受保护文件。
- 下一步建议：后来者以交接文件为入口继续做论文文字、引用和图表定稿。

## [2026-07-02 23:41:35 PDT] 055 已启动 (Claude re-audit)，详细日志见 top_journal_v3_reaudit_055/claude_code_and_supervisor.md

## [2026-07-03 00:15:05 PDT] 055 完成 (Claude re-audit), 见 top_journal_v3_reaudit_055/docs/cc_latest_report.md (verify 45/45)

## [2026-07-03 01:10:17 PDT] 056 完成 (正式论文重写), 见 top_journal_v3_reaudit_055/docs/cc_latest_report.md (verify 28/28, pytest 17)

## [2026-07-03 02:06:14 PDT] 来源: supervisor — 056 覆盖版 OR_PRE_SUBMISSION_S1S5_V1
指令全文要点(faithful record):
- 覆盖前一 056 论文定稿命令。论文身份=朝向可靠性测量协议+有限样本保形风险控制+PSC机制候选。S1修完前不进英文稿/不讨论投稿/不宣称TGRS-ISPRS strong candidate/不美化。
- 输出目录: top_journal_v3_reaudit_055/{docs,reports,figures}/pre_submission_s1s5_v1/; md 带 _v1; 大文件不进git; 不改thresholds/D_cal/D_audit; 不重训; 不追DOTA public mAP; 不补full matrix; 不复活P2/C1主线; 不把NRC<1写calibrated; 不把DOTA#20当机制证据; 不复活unmasked旧反校准; 主文无PM词汇。
- T0 startup audit. 
- S1a: 从raw predictions全管线扰动重跑(非matched-only), full evaluator重算AP50/AP75/mAP+angle/NRC/AURC/Risk; 报ΔAP; ar-bin dose-response; FP/duplicate变化; 反向扰动进附录。禁止matched-only mAP=1.000做主证据。
- S1b: selector-fit vs conformal-calib 独立性修复(方案B leave-*或方案A三分D_fit/D_calib/D_audit); 重出score menu/NRC/conformal; 若修复后geometry不占优则不写recommended default。
- S1c: LTT固定序列(替代grid+Hoeffding UCB,控FWER); 均值风险按[0,90]有界严格保证(删"无界只能近似"); image-level clustered bootstrap CI。
- S1 sync: 表7"6/6"改"5/6+1打平"(SODA#23 TTA0.228>geo0.227); 标P1 unmasked/P2 masked; cliff分位在冻结masked重列; DIOR#10/SODA#11入附录; "先前文献"改"本项目早期分析"; NRC<1不叫calibrated改better-than-random/non-reversed/informative ranking。
- S2: PSC机制免费测试(aliasing fingerprint + class/size/ar confounding, masked); DOTA#20仅artifact limitation; 两测试均支持才议重训矩阵(本轮不启动)。
- S3: 冻结masked重算所有provenance-clean cells(robustness, 非补matrix)。
- S4: 角度单位下游任务(HRSC ship geometric orientation, 只报OBB long-axis, 非semantic heading)。
- S5: 去PM词汇重写风格+真实文献(CRC/RCPS/LTT等)+NRC方向示意图+一键复算脚本+repro log。
- S9 最终判定; S10 verifier; S11 cc_latest_report_v1(入口出口)。
- 判定规则: S1a或S1b失败→降级测量/技术报告不投顶刊; S1稳定→可恢复TGRS/ISPRS强候选; 本轮不得宣称CVPR/TPAMI ready。

## [2026-07-03 02:37:58 PDT] 056 覆盖版 (OR_PRE_SUBMISSION_S1S5_V1) 完成
- S1a PASS: 真实 full evaluator(raw preds) 约束扰动 4/4 cell ΔAP50=0.0000 + FP 不变(DIOR#22/#3/#61+FAIR1M#24, 跨PSC/ORCNN/RTMDet); SODA#23/#4 pass 后台收尾。matched-only mAP=1.000 代理已替换为真实 AP50。
- S1b QUALIFIED: 独立性修复(D_fit/D_calib/D_audit); geometry selector 非普遍占优(弱信息 cell 更优, 强 cell 打平), 不写 blanket default。
- S1c QUALIFIED: LTT 二项尾部+有界均值(Hoeffding B=90 过保守不实用)+image-clustered CI; 保证 modest。
- S2: 1/2 支持(confounding 排除, 无 aliasing 峰)->phase_mod 保持 case study, 不启动重训。
- S3: 6 full-val provenance-clean cell 主表 + 2 附录 + DOTA#20 排除。
- S4: 角度单位下游真实但 modest(HRSC 仅 synthetic, 改用真实方向类)。
- S5: rewrite plan + NRC 示意图 + 一键复算脚本 + repro log。
- 判定: S1a 通过/S1b 未失败 -> 不降级; 有条件恢复 TGRS/ISPRS 方向判断; 不宣称 CVPR/TPAMI ready。可进修订中文稿; 暂不英文/投稿。
- 验证: verify_pre_submission_s1s5_v1.py 49/49 PASS; pytest 17; thresholds b7c4e649 未变; D_cal/D_audit clean; git 无大文件。未触发停止条件。
- 回执: top_journal_v3_reaudit_055/docs/pre_submission_s1s5_v1/cc_latest_report_v1.md

## [2026-07-03 02:37:58 PDT] 056 覆盖版完成, 见 top_journal_v3_reaudit_055/docs/pre_submission_s1s5_v1/cc_latest_report_v1.md (verify 49/49, pytest 17)

## [2026-07-03 04:44:46 PDT] 057 (OR_PAPER_ZH_S1S5_V1) 完成
- SODA S1a 收尾: SODA#23 0.6119->0.6119, SODA#4 0.7592->0.7592, ΔAP@0.5=0.0000, FP 不变 -> 6/6 cell 完成, 无 compute limitation。
- 中文完整论文稿: docs/paper_zh_s1s5_v1/orientation_reliability_paper_zh_s1s5_v1.md (摘要+关键词+11节+8表+7图占位+附录A-H)。去项目化(正文无 P1-5/S1a-c/056/verifier/sha256/artifact path/codex/claude); NRC<1=非反序不叫calibrated; 几何打分非通用默认; 保证 modest; 机制候选; 下游 modest; DOTA#20 仅来源限制。
- 配套: paper_zh_review_checklist_v1.md。
- 验证: verify_paper_zh_s1s5_v1.py 26/26 PASS; pytest 17; thresholds b7c4e649 未变; D_cal/D_audit clean; git 无大文件。
- 边界: 仍禁止英文稿/投稿; 未宣称更高档位就绪。
- 回执: docs/paper_zh_s1s5_v1/cc_latest_report_v1.md

## [2026-07-03 04:44:46 PDT] 057 完成 (中文完整论文稿), 见 top_journal_v3_reaudit_055/docs/paper_zh_s1s5_v1/cc_latest_report_v1.md (verify 26/26, pytest 17)

## [2026-07-03 06:21:58 PDT] 058 (OR_PRE_SUBMISSION..v5 R1/R2/R3 启动) 完成 — 无训练
- R1 角度编码器机制矩阵: 训练前预注册完成 (docs/r1_angle_coder_intervention_matrix.md + reports/r1_angle_coder_matrix.csv 30 runs 全 pending_preregistered, seed_variance 表). 未启动训练。5 heads(PSC/CSL/DCL/direct-reg/KLD)x2 dataset(DIOR-R,SODA-A)x3 seeds; 结局 A/B/C 预注册; direct-reg=no-native-uncertainty negative control。
- R2 宽度审计: docs/r2_frozen_masked_recompute.md + reports/r2_cell_inclusion_exclusion_log.csv (6 clean main / 4 masked-only 附录 / 1 invalid DOTA#20 / 4 候选族需前向). blocker: 扩到12-15需新前向dump(非058)。
- R3 文献+理论: docs/r3_related_work_completed.md (真实文献, 5核心联网核验: PSC/KLD/SODA-A/CRC/LTT; 其余真实但精确字段列 blocker, 不伪造) + docs/r3_iou_aspect_ratio_theory.md (命题+数值验证, 不硬写Fisher定理)。
- R3 写作: docs/r3_manuscript_cleanup_plan.md (10项检查: 9通过, 唯一未过=文献待整合#8)。
- 第三方复算: docs/third_party_reproduction_log.md (一键脚本覆盖表2/4/5/6/7+dose; 缺口=表1汇总/表3内联A0/根级固定入口; 未声称复算完备)。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit clean; git 无大文件; 未训练/未推理(server上 train1685.py 等为他项目, 非本项目)。
- 下一条命令: 059。

## [2026-07-03 07:00:53 PDT] 059 (v5 主执行) 完成 — 无训练完成(数据阻断)
- R3 v2 审稿版单文件: docs/paper_zh_s1s5_v2_review/orientation_reliability_paper_zh_s1s5_v2_review.md (真实文献整合, 0待补, 0 PM词, forbidden 仅否定语境; 双向解耦; IoU理论+图2; 反向扰动/尾部事件附录). + references_integrated_checklist.md + text_cleanup_audit.md。
- R2: 6 clean full-val 主表复算(masked NRC 0.41-0.91) + 4 masked-only 附录; 宽度仍6, 扩12-15需新前向dump(blocker); DOTA#20 仍 invalid。reports/r2_*.csv。
- R1: manifest 30 runs; 尝试启动 PSC/DIOR seed0 -> 数据阻断(DIOR annfiles_dotaformat/trainval 空, 原生为 XML, 需 XML->DOTA-txt 转换); 0完成/0有效运行; 不标 failed_training; phase_mod 仍候选。
- R3b IoU图: scripts/plot_iou_delta_theta_aspect_ratio.py + figures/*.{png,pdf,csv}; ar<=1.2 永不跌破IoU0.5。R3c 反向扰动: AP50可变角度不变(双向解耦)。R4 尾部事件: 严重误差稀有, 检测常足够 -> 附录。
- 第三方复算: 新增 scripts/reproduce_all_main_tables.sh (root, 只读); 058缺口关闭(表1/内联A0/root入口); --fast dry-run 成功。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit clean; git 无大文件; 未重训 host; 未追 public mAP; 未写 full project complete / TPAMI-CVPR ready; phase_mod 未写成机制证明。
- 下一条命令: 060。

## [2026-07-03 08:39:04 PDT] 060 (R1 解阻+四卡训练启动) 完成
- 数据解阻: DIOR XML->DOTA-txt 转换(scripts/convert_dior_obbxml_to_dota_txt.py; trainval 11725/68073obj, test 11738/124445obj, 0空0缺; orientbench prep 目录+图像symlink, 不污染共享数据集); SODA-A 原生 DOTA 格式可用。
- R1 真实四卡训练启动: PSC/DIOR-R/seed0 torch.distributed.run nproc=4 训练中(~1.2GB/卡, 与外部D17共存, Epoch1 正常, ETA~1.5h)。watcher(scripts/watch_r1_oom_retry.py: 4卡强制/OOM1200s/EADDRINUSE端口重试/只清本项目/状态落盘)驱动 PSC-DIOR seed0->1->2。
- 早期 rc=1 = 端口冲突(D17占29511), 已修端口重试, 非failed_training非机制结论。config就绪: PSC-DIOR+PSC-SODA(dota_format_tiled_ss)。CSL/DCL/KLD/reg config 待授权派生。
- 完成0/有效运行1(PSC-DIOR seed0)/failed0/排队多。phase_mod 仍机制候选(矩阵未完成)。
- R2: 6 clean cells masked 指标已在; 候选前向dump命令+估计已备, 未抢占R1(R1优先); DOTA#20 仍invalid。
- R3 v2 审稿版: 复检无待补/无PM词/NRC<1非calibrated/phase_mod候选/DOTA#20不进主结论/无ready; 无需同步。
- 合规: thresholds b7c4e649未变; D_cal/D_audit未改(只加训练输入prep+config repoint); git无大文件; 未重训host(baseline pth未动); 未追public mAP; 未写full complete/TPAMI-CVPR ready; phase_mod未写机制证明。
- 下一条命令: 061。

## 2026-07-05 07:17 PDT — 命令 061（R1 矩阵铺开 + 四卡队列续跑）
- 指令来源: 监督员命令 061。
- 接管发现: 060 watcher 已死; PSC/DIOR-R/seed0 已完成(epoch12, AP50=0.5310, DIOR-R test split); seed1 于 07/03 因 NCCL heartbeat(600s)崩在 epoch8(工程性挂起, 非模型失败)。
- 执行动作:
  1. 配置派生: gen_r1_angle_head_configs.py 由已打通 PSC 模板(DIOR nc=20/SODA nc=9)只换 head/coder/loss 派生 CSL/KLD/direct_regression + PSC seed1/2; 30 配置全量。
  2. DCLCoder 缺失(mmrotate 1.0.0rc1 无) → 项目本地实现 orientbench_ext/dcl_coder.py(BCL 变体), custom_imports 注入, 单元测试 test_dcl_coder.py 通过(round-trip 0.50°<1° bin); DCL 标 head_impl=project_local_BCL。
  3. smoke 测试 smoke_test_r1_configs.py: 30/30 PASS(parse+model-build+真实样本; DIOR n=11725/SODA n=23063)。
  4. 四卡稳健化: launcher 加 TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC=3600 + auto --resume + PYTHONPATH(ext)。
  5. 队列 watch_r1_oom_retry_061.py: 跳过已完成 seed0, seed1 自 epoch8 恢复训练中(现 epoch9 val, ETA→epoch10-12), 28 queued。首试 seed1 OOM(GPU1 被 D17 占满 2.69MiB free) → 按令等 1200s → D17 释放后四卡重试成功(mem 1181MiB/卡, 4 卡 91-99%)。全程未动 D17。
  6. 文档/表: matrix(seed0 AP50 实填, 余 pending/queued; KLD 命名归一到 manifest)、manifest、queue_status_061、config_derivation_061、eval_spec_061、R2 §9、R3 audit_061。
- 关键产物: top_journal_v3_reaudit_055/{configs/r1_angle_coder/(30 .py), orientbench_ext/, scripts/{gen_,smoke_}, reports/{r1_angle_coder_matrix,run_manifest,queue_status_061,r1_config_smoke_061}.csv, docs/{r1_angle_coder_config_derivation_061,r1_eval_spec_061}.md, docs/paper_zh_s1s5_v2_review/text_cleanup_audit_061.md}; scripts/{run_r1_angle_coder_queue_4gpu.sh(改),watch_r1_oom_retry_061.py}。
- 停止条件: 未触发早停(无泄漏/无 frozen 改动/无 near-square-only)。R1 矩阵 1/30 完成, 不可写机制结论(phase_mod 仍候选)。
- R2: clean cells 仍 10(6 主+4 附录), 未新增(R1 优先占卡); DOTA#20 仍 invalid 未转正。
- R3 v2 审稿版: 7/7 合规通过, 无需同步新事实。
- 复算入口: 未加 R1(0 机制表完成), reproduce_all_main_tables.sh 未改。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未改; 未重训 host; 未追 public mAP; 未补 full 9-detector; 未写 full complete/CVPR/TPAMI ready; phase_mod 未写机制证明。
- 下一条建议命令: 062。

## 2026-07-07 04:34 PDT — 命令 062（接管队列 + epoch-1 健康门控 + NaN/AMP 失败裁决）
- 指令来源: 监督员命令 062。
- 接管: 定位并杀掉 061 watcher(PID 124382, 我的) + 当前 NaN 负对照 run(regression_soda_seed2, 102 进程整树), 仅清本项目, D17(21 proc)未动。未新建重复 watcher。
- 健康门控: 新增 watch_r1_oom_retry_062.py(Popen+进程组, 每30s 轮询)。修正关键 bug: has_nan 误把瞬时 AMP 溢出(grad_norm:inf/loss:inf, 健康 CSL/PSC/DCL 均有且恢复)判为发散; 改为"近25条训练行多数 loss:nan"才判 terminal。18 健康 run 判 False, 6 发散 run 判 True, 全部正确。launcher 加 PYTORCH_CUDA_ALLOC_CONF=expandable_segments。
- 负对照裁决(主矩阵选 B): direct_regression_le90 6 run 全 NaN 发散(ep1), 从旧队列误标 complete 改为 failed_training。不改 lr/AMP/grad-clip 纳入主矩阵; rescue 仅 exploratory 附录。
- KLD 新发现: 6 run 全在<30s 崩溃, RuntimeError linalg.inv Low precision Half —— GDLoss_v1(kld)需 fp32 但共享协议用 AMP/fp16。与 direct_regression 同等处理: failed_training(主矩阵), 非 AMP rescue 仅附录。门控快速失败, 零 12-epoch 浪费。
- R1 主矩阵最终: PSC/CSL/DCL 18/18 健康(3 seed×2 ds), direct_regression+KLD 12 failed_training。mAP: PSC DIOR≈0.53/SODA≈0.60, CSL≈0.29-0.38, DCL DIOR≈0.33/SODA≈0.50。
- 评测(task V): 18 健康 run AP50 已从 val log 实填矩阵; AP75/angle-error/native-uncertainty masked-NRC 待 instrumented dump(复用 run_052 matcher+angle_contract+frozen nrc_auc; 新增 per-head 原生不确定度推理 dump)。GPU 现已空(队列结束), 评测为下一步。seed variance NRC 尚不可算。可写机制结论: 否。
- 关键产物: scripts/watch_r1_oom_retry_062.py; reports/{r1_angle_coder_queue_status_062,r1_angle_coder_matrix,r1_angle_coder_matrix_seed_variance,r1_angle_coder_eval_status_062}.csv; docs/{r1_direct_regression_failed_training_062,r1_direct_regression_exploratory_rescue_plan_062,r1_angle_coder_config_derivation_062,r1_eval_spec_062}.md; docs/paper_zh_s1s5_v2_review/text_cleanup_audit_062.md; logs/r1_angle_coder/{queue_takeover_062,health_gate_062,queue_062}.log。
- R2: 未抢卡; 主表仍 6 clean + 4 附录; DOTA#20 仍 invalid。R3: 6/6 合规, R1 062 结果不入正文。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训 host; 未追 public mAP; 未补 full 9-detector; 未写 full complete/CVPR/TPAMI ready; phase_mod 未写机制证明。
- 下一条建议命令: 063。

## 2026-07-07 05:44 PDT — 命令 063（纠正假完成 + 真实启动评测；阶段状态，非完成）
- 指令来源: 监督员命令 063（指出 062 假完成/后台不透明）。
- 运行状态审计: 确认无本项目进程在跑; 062 watcher 已死但因 30-run 全终态(18 complete+12 failed)正常退出, 非 hang; 4 个 GPU 进程全是 D17(p2_foundation), 非本项目。结论: 训练队列真结束, 真正欠的是 18 有效 run 评测(062 误留 pending)。产物: logs/.../runtime_audit_063.log, reports/r1_runtime_process_audit_063.csv。
- 真实启动评测(核心): 实现 instrumented 角度头 orientbench_ext/instrumented_heads.py(捕获 angle_encoded 过 NMS 对齐, 验证 decode vs box θ 双峰{0,90}=edge_swap, 行对齐 intact)。eval_r1_run.py: 推理+按 evaluator 同源 gt 旋转IoU匹配+canonical angle_error+per-head native uncertainty(PSC phase_mod/CSL margin/DCL bit-margin)+masked ar≥1.6 NRC(native&score)+bootstrap CI+AP50/75。冒烟 PSC-DIOR-seed0(150img): NRC_native=1.23 CI[1.05,1.40](反序), NRC_score=0.50(非反序)——单seed子集, 仅 preliminary, 不下结论。
- 后台评测运行中(非完成): eval_driver_063.py(PID 226527), 3 并发 pin GPU, 现跑 PSC-DIOR seed0/1/2(3500/11738, ~20min/run), 18 run 需数小时; 每10min heartbeat -> logs/.../eval_063.log; OOM->1200s 重试。看到 D17 占卡仍直接跑。
- 30-run 纠错: reports/r1_30run_status_audit_063.csv + docs 同名 md; 18 eligible_for_main_matrix=true; direct_regression 6=failed(NaN), KLD 6=failed(AMP/fp16 linalg.inv)。health gate: watch_r1_oom_retry_062.py 修正 NaN 判据(瞬时AMP溢出 vs 持续loss:nan), 0 doomed run 烧满12ep。
- rescue(隔离, 未启动, eval优先): configs/r1_angle_coder_rescue/(KLD fp32; regression fp32+lr0.0025+clip10), 标 exploratory_rescue_not_preregistered; reports/r1_exploratory_rescue_queue_063.csv; docs/r1_exploratory_rescue_note_063.md。
- 聚合器就绪: scripts/aggregate_r1_eval_063.py(评测完读 JSON->matrix+block seed variance); docs/r1_interim_valid_heads_results_063.md(评测中, 无结论)。
- R2: 未抢卡(eval 用 GPU, 非训练); 主表仍 6+4; DOTA#20 仍 invalid。R3: 6/6 合规, R1 063 结果不入正文。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训 host; 未追 public mAP; 未补 full 9-detector; 未写 full complete/CVPR/TPAMI ready; phase_mod 未写机制证明。
- 状态: 阶段状态(后台评测运行中), 非完成。下一条建议命令: 064（收集评测+block variance+interim, 或先待 eval 完成）。

## 2026-07-07 18:24 PDT — 命令 063 收尾（评测已全部完成，非阶段状态）
- GPU 停止原因: eval_driver_063 于 09:23 正常结束(EVAL DRIVER 063 END), 18/18 评测完成(~3.75h); D17 亦已结束; GPU 空闲非卡死。
- 聚合完成: aggregate_r1_eval_063.py -> 18 run 全指标 + 6 block seed variance。AP50_self vs val_log max|diff|=0.0005(自建旋转AP已验证, AP75 可信)。matrix/seed_variance/eval_status_063 已填。
- 6 block(masked ar>=1.6, 3 seed): PSC-DIOR native(phase_mod)NRC 1.21 CI_lo 1.17 全反序; PSC-SODA 1.15 CI_lo 1.11 全反序; score NRC 0.57/0.96 informative。CSL native≈0.89/1.00(~random)。DCL native bit-margin 0.20/0.37(强 informative)。=> angle-coder 原生置信度 head-specific(DCL 好, PSC 反序), 非普遍失灵。
- 写法: PSC 反序为 interim/preliminary(3 seed×2 数据集一致, CI>1), 仍 mechanism candidate 非证明(5-head 矩阵未全, direct_regression/KLD failed; 无混叠指纹)。docs/r1_interim_valid_heads_results_063.md。
- 现无本项目后台进程; thresholds b7c4e649 未变; 未重训 host/未追 public mAP/未写 complete/未写机制证明。
- 下一条建议命令: 064。

## 2026-07-07 18:39 PDT — 命令 064（R1 收口为受限机制证据 + 中文稿/复算链/审计更新）
- 指令来源: 监督员命令 064（063 结果积极但须严格限缩写法）。纯文档/收口轮，无训练。
- 任务1 R1 文档: 重写 docs/r1_interim_valid_heads_results_063.md 为「restricted A-like PSC-specific reproducible reverse ranking」；intervention_matrix.md §13 加最终执行状态。明写: 5-head 矩阵未全(KLD/direct_regression failed); DCL native informative 为反例(不写普遍失灵); PSC phase_mod 跨 2 数据集×3 seed 稳定反序(NRC>1, 全 seed CI 下界>1) = preliminary mechanism evidence/candidate, 非证明。
- 任务2 表: reports/{r1_valid_head_blocks_final_064, r1_failed_training_audit_final_064, r1_claim_ledger_update_064}.csv。claim ledger 含 claim_text/support_level/supporting_artifacts/allowed_wording/forbidden_wording。
- 任务3 中文稿: §7 加「预注册头干预矩阵的初步证据」段(受限写法, phase_mod 从单checkpoint升为PSC-specific跨数据集跨seed候选, DCL反例, failed 保留); 不重写主线。text_cleanup_audit_064.md: 6/6 合规, 待补=0, 无 forbidden claim。
- 任务4 复算链: reproduce_all_main_tables.sh 加 R1 blocks 段(从 reports/r1_eval/*.json 聚合 + 校验 12 failed audit; rescue 不入主链; 长推理不入主链)。dry-run --fast PASS(18/18 JSON, failed audit OK, thresholds 未变); log reproduce_all_main_tables_064.log; third_party_reproduction_log.md 更新。
- 任务5 R2: 不变(6 主 + 4 附录; DOTA#20 仍 invalid; 未抢优先级)。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训 host; 未追 public mAP; 未写 full benchmark/selector victory/complete/TPAMI-CVPR ready; phase_mod 未写通用机制证明(受限 PSC-specific 候选)。
- 下一条建议命令: 065。

## 2026-07-07 19:06 PDT — 命令 065（生成 v3 单文件中文正式论文 + 全文清理）
- 指令来源: 监督员命令 065。纯文档轮，无训练/评测后台任务。
- v3 生成: docs/paper_zh_s1s5_v3_review/orientation_reliability_paper_zh_s1s5_v3_review.md(325 行, 单文件正式论文, 图片仅 7 个编号占位)。从 v2 重组为正式结构(摘要/引言/相关工作/方法/主结果I&II/保形/实验设置/机制小节/下游附录/Scope/局限性/结论/参考文献/附录A-I)。单元匿名化(A-F/D20), 去所有文件路径与工程标识。
- 全文清理至字面 grep=0: 待补=0; PM词=0(supervisor/verifier/reports//figures//.csv/056-064/P1-P5, 紧模式排除 arXiv 编号与数值误报); 刊物/投稿(CVPR/TPAMI/TGRS/ISPRS/ready/投稿)=0(参考文献改作者+年份+arXiv, 不含刊物缩写); forbidden(证明/已校准/普遍失灵/proven/full benchmark/selector victory)=0(证明→表明/成立/定论, 已校准→概率校准calibrated, 全面基准/通用默认仅否定/禁止清单)。
- R1 同步(§8+附录E+表7): PSC phase_mod 跨2数据集×3seed 稳定反序(NRC>1,全seed CI下界>1)=PSC-specific 机制候选/初步证据; DCL informative 反例(不写普遍失效); CSL≈随机; 直接回归 NaN + KLD 半精度不兼容=failed_training 失败审计保留。受限 PSC-specific, 非通用机制定论。
- 审计+差异文档: text_cleanup_audit_065.md(9/9 PASS), v3_change_summary_065.md。
- 复算链 dry-run: reproduce_all_main_tables.sh --fast PASS(R1 blocks 18/18, failed audit 12, thresholds b7c4e649 未变); log 065; third_party_reproduction_log.md 更新; 无 blocker(不声称可冻结)。
- R2 不变(6 主 + 4 附录, D20 invalid)。
- 合规: thresholds 未变; D_cal/D_audit 未变(git diff 0); 未重训 host; 未追 public mAP; 未写 complete/刊物 ready; phase_mod 未写通用机制定论。
- 下一条建议命令: 066。

## 2026-07-07 20:30 PDT — K1 评测器法证（go/no-go 第一门，最高优先）
- 指令来源: 监督员 K1–K4 go/no-go 执行令。本轮只做 K1（"K1 不过后面全部暂停"）。
- 矛盾: 表1 DIOR#22 AP@0.5=0.6964(S1a) vs 表7 PSC-DIOR AP50=0.531(DOTAMetric), 同检测器/协议, 差~16点。
- 关键事实: 表1 冻结 baseline 权重文件名 best_mAP_5368_epoch_12.pth, 其训练日志 dota/AP50=0.5370(DOTAMetric full-val)。即该权重标准口径就是 0.537。
- 受控对照(k1_evaluator_forensics.py): 同一预测+同一 full-val GT 跑 S1a 与本项目 VOC-AP。full DIOR test: S1a AP50=0.5297, ours=0.5311, DOTAMetric=0.5310 —— 三者差≤0.0014, 逐类差 max 0.053。=> S1a 评测器代码正确, 与 DOTAMetric 一致, 无 16点评测器级 inflation。
- 根因: 表1 DIOR#22 的 GT 路径为 /dev/shm/.../DIOR-R_fullval_gt.jsonl(已丢失, 未持久化), n_gt=35436, 而 full-val GT 实测=124445(本次确认)。表1 AP 是对~28%部分 GT 计算的, 非 full-val 口径 → 0.6964 是 partial-GT 产物, 非 evaluator bug, 且已无法精确复算。
- 判定: 评测器代码 PASS(可解释一致, 不触发硬 FAIL/不停投稿准备); 表1 绝对 AP 锚点 FAIL-as-published(partial GT), 必须 full-val 重算。已示范 DIOR#22: 0.6964→0.530。其余5单元(ORCNN/RTMDet/FAIR1M/SODA)需各自 full-val 重算(下一步)。ΔAP@0.5=0 为同评测器不变量, 重算后仍应成立。
- 产物: docs/k1_evaluator_forensics.md; reports/{k1_metric_protocol_alignment,k1_evaluator_diff_per_class}.csv, k1_summary.json; scripts/k1_evaluator_forensics.py; logs/.../k1_forensics.log。
- 治理暴露: 禁止主表数值依赖 /dev/shm 未持久化 GT。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训 host(仅用已训权重推理); 未追 public mAP(自跑口径对齐)。
- K2/K3/K4/两层修复: 未开始(按执行顺序, K1 优先; 表1 重算为 K1 收尾必做项)。
- 下一条建议命令: 表1 全 full-val 重算 + K1 正式收尾, 然后 K2。

## 2026-07-07 编号纠偏（065）
- 最后正式完成编号 = 064。K1 评测器法证为 064 后插队任务, 未按正式编号汇报, 其建议 067 无效不接续。
- 当前正式纠偏命令 = 065。原"065 生成 v3"暂停: 表1 AP 锚点(K1 判 FAIL-as-published, partial-GT)未解冻前不生成最终 v3。
- 评测器 PASS ≠ 表1 PASS; 表1 需六单元 full-val 重算完成才 PASS。禁止主表数值依赖 /dev/shm GT。详见 docs/k1_numbering_correction_065.md。

## 2026-07-07 21:42 PDT — 命令 065（K1 表1 full-val 重算，阶段状态非完成）
- 编号纠偏已记(见上); 067 无效, 当前正式 065。
- §2 GT 持久化: build_k1_fullval_gt_065.py -> outputs/persistent_artifacts/k1_table1_fullval_065/gt/。DIOR test n_gt=124445(确认 full, 旧 partial 35436); SODA val 449644(本为 full); FAIR1M BLOCKER(split_ss_fair1m1.0 缺失)。manifest+sha256。
- 更深发现: 冻结持久化预测图像集与 full test 零重叠(预测 5863 张 trainval 段 vs test 11738 张)+DIOR#61/SODA#4 预测 /dev/shm 已丢失 → 表1 必须重新推理重算(非训练)。
- §3 重算: recompute_table1_by_inference_065.py 后台运行(PID 875550, GPU1), 5 单元(FAIR1M 排除), 冻结 baseline 权重在正确 full-val split 推理 + K1 验证 torch VOC-AP + 约束扰动。DIOR#22 现 3000/11738。
- 已确立: DIOR#22 full-val AP@0.5≈0.53(K1: DOTAMetric 0.531/S1a 0.5297/VOC 0.5311; baseline 自报 0.537), 取代旧 0.6964。superseded/evaluator_alignment/claim_ledger/table1_fullval_final(partial) CSV 已写。
- §5 复算链: 加 [K1 GT] 检查(DIOR n_gt=124445 + 禁 /dev/shm 主表 GT), dry-run PASS。
- §6 v3: 阻断(表1 未解冻), v3_blocker_note_065.md; 旧 v3 含 0.6964 不定稿。
- 状态: 阶段状态(后台重算运行中), 非完成。评测器 PASS ≠ 表1 PASS(1/6 确立, 4 重算中, 1 数据 blocker)。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训(仅推理); 未追 public mAP; 无主表依赖 /dev/shm。
- 下一条建议命令: 066。

## 2026-07-08 01:50 PDT — 命令 065 K1 表1 full-val 重算 完成状态
- 多GPU纠正: 重算改为 5 cell 并行(一卡一 cell), 之前单卡顺序是效率失误。
- 表1 六单元 full-val 重算(冻结 baseline 权重在正确 full-val split 重新推理, K1 验证 torch VOC-AP==DOTAMetric, 修复 eps_max 用预测框自身中心):
  - DIOR#22 PSC: 0.6964 -> 0.5368 (baseline 自报 0.5370 ✓), ΔAP50=0
  - DIOR#3 ORCNN: 0.7999 -> 0.6448 (baseline 0.6448 ✓), ΔAP50=0
  - DIOR#61 RTMDet: 0.8866 -> 0.6462 (taos setup 自报 0.5489, 差异非评测器), ΔAP50=0
  - SODA#23 PSC: 0.6119 -> 0.5991 (baseline 0.5991 ✓, SODA GT 本 full 故几乎不变), ΔAP50=0
  - SODA#4 ORCNN: 0.7592 -> 0.7295 (baseline 0.7295 ✓), ΔAP50=0
  - FAIR1M#24: BLOCKER(数据集 split_ss_fair1m1.0 缺失)
- 关键: base AP50 全部与 baseline 自报 DOTAMetric 精确吻合 → 评测器对齐确证, 旧 partial-GT 锚点(0.69-0.89)纠正为 full-val(0.54-0.73)。DIOR 掉 16-24pt(partial GT), SODA 几乎不变(full GT)——与"仅 DIOR GT partial"一致。
- ΔAP50=0 在 full-val + 修复 eps_max 后成立(AP75 塌陷 0.45->0.05, angle 9°->40°)→ P1 headline 在 full-val 成立, 非 partial-GT artifact。
- 修复两个 bug: eps_max 误用 GT 中心(致假 ΔAP-0.2); json 未 flush(致 DIOR#22/#3 空文件)。DIOR#22/#3 正后台重持久化(~25min)。
- 表: table1_fullval_final_065.csv, superseded/evaluator_alignment/claim_ledger CSV。
- 状态: 表1 5/6 单元 full-val 重算完成(FAIR1M 数据 blocker); 2 单元后台重持久化; v3 待表1 全解冻后生成。评测器 PASS; 表1 5/6 PASS。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训(仅推理); 未追 public mAP; 无 /dev/shm 主表 GT。
- 下一条建议命令: 066。

## 2026-07-08 K1 表1 full-val 重算 6/6 完成（FAIR1M 纠错）
- 纠错: 我先前误报 FAIR1M 为数据 blocker——其实数据在(split/val_20, 5.9G), GT 为 XML 格式(非 .txt), 我只查了 .txt 才误判。已从 XML 构建 GT: 4362 图 / n_gt=78644(≈旧 78638, full GT)。
- FAIR1M#24 重算: base_AP50=0.3462(baseline 自报 0.3462 精确吻合; 旧 Table1 0.3452)→ 与 SODA 一样本为 full GT, 从未虚高。ΔAP50=0, AP75 0.242->0.067。
- 表1 六单元 full-val 重算全部完成:
  DIOR#22 0.6964->0.5368; DIOR#3 0.7999->0.6448; DIOR#61 0.8866->0.6462; SODA#23 0.6119->0.5991; SODA#4 0.7592->0.7295; FAIR1M#24 0.3452->0.3462。
  5/6 与 baseline 自报 DOTAMetric 精确吻合(DIOR#61 taos_pad32 setup 差异, 非评测器)。ΔAP50=0 全部成立, AP75 全部塌陷。
- 结论: DIOR 三单元(partial GT)虚高 16-24pt 已纠正; SODA+FAIR1M(full GT)本未虚高。表1 6/6 解冻。P1 headline(ΔAP@0.5=0 + AP75 塌陷 + angle 飙升)在 full-val 成立。
- 表: table1_fullval_final_065.csv(6 单元完整), superseded(6)。
- 合规: thresholds 未变; 未重训(仅推理); 无 /dev/shm 主表 GT。

## 2026-07-08 命令 065 §6 v3 完成（表1 解冻后更新）
- 表1 6/6 full-val 重算完成 -> v3 §4 表1 换成 full-val 值(A 0.5368/B 0.6448/C 0.6462/D 0.3462/E 0.5991/F 0.7295), 删旧 partial-GT FP 计数(ΔAP50=0 -> FP 不变), 摘要/§4 角度量级更新(5-9°->34-41°)。旧 0.6964/0.7999/0.8866 已从 v3 移除。
- v3 合规复核: 待补=0, 证明=0, 已校准=0, CVPR/TPAMI/TGRS/ISPRS=0, K1(正文)=0, 无 PM 轮次号(06X 命中均为小数 CI 值误报)。
- v3 阻断解除。065 全部完成(§1-§7)。无后台任务。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训; 未追 public mAP; 无 /dev/shm 主表 GT。

## 2026-07-08 命令 066 开始
- **K1–K4 go/no-go 执行令已收到，并从 066 开始执行。** 编号纪律: 最新完成=065, 本条=066, 067 暂不使用。
- 本轮: K1 最终反证收尾 + 几何/线性打分泄漏审计 + K3 GT 噪声 proxy 审计 + K4a masked 阈值原则化 + K4b DOTA full-val(后台) + K2 仅预注册修订(不训练) + 第一层可评审性文档 + 复算链。

## 2026-07-08 命令 066 完成
- K1 最终反证: 6/6 单元 new full-val AP 与 checkpoint 自评 DOTAMetric 精确吻合(≤0.0022); 旧高 AP 仅 DIOR(partial GT 35436 vs 124445)虚高, SODA/FAIR1M(full GT)未虚高。DIOR#61 残差 RESOLVED(文件名 5489=dota/mAP, 日志 AP50=0.6440 与重算 0.6462 一致)。K1 remains PASS。无 /dev/shm 主表依赖。
- 几何打分泄漏审计: 特征[score,log ar,log√size]全预测端可得/GT-free, 但模型 fit on 目标域 GT 角度误差 -> calibration/upper-bound, 非 deployable。线性(score/+ar/+ar+size)同结构。selector-fit(D_fit)/conformal-calib(D_calib)独立。
- K3 GT 角度噪声 proxy(2px 角点抖动重拟合): masked ar≥1.6 σ_gt≈3.5(DIOR)/5.7(FAIR1M)/7.8(SODA)°, >2° 均值预算(处处), 5° 尾部 margin 薄(SODA/FAIR1M)。判定 PARTIAL(均值预算须 label-noise-aware; 尾部随数据集)。真人双标为后续 blocker。
- K4a masked 阈值原则化: 冻结判据 τ=0.75 下 δ*=15° -> derived-ar=2.1(1.6 对应 δθ≈19.5°更宽松)。建议正文主口径改 2.1, 1.6/1.3 sensitivity。mask 比例已算。PASS。
- K4b DOTA full-val: ORCNN AP50=0.7061 + RTMDet-m AP50=0.7161(均与 baseline 自评一致), masked NRC_score 0.69/0.65(informative)。2 clean full-val 单元。D20 正式排除。K4 初步 PASS。
- K2: 未训练; 预注册修订(per-head LR sweep 等预算 + FP32 fallback + 可用收敛门控 + A/B/C/D + R1 降 preliminary)。
- 第一层文档: conformal reporting/uncertainty baselines/cell naming 已补; 未大改主稿。
- 复算链: 加 [066] 审计段, dry-run PASS。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训(仅推理); 未追 public mAP; 未用 D20 半残; 无 /dev/shm 主表; 未写 ready/complete; phase_mod 未写通用证明。K1 PASS ≠ K1-K4 全过(K3 PARTIAL)。
- 下一条建议命令: 067。

## 2026-07-08 04:05 PDT — 命令 067 K2 全收敛矩阵：已冻结预注册 + 启动自主运行
- K2 预注册已冻结: docs/k2_angle_coder_intervention_matrix_frozen_067.md (LR{0.0025,0.005,0.010}, pilot seed0 3ep, 选优按 val AP50; final 3 seed 12ep; AMP+FP32 fallback; 主 mask derived-ar=2.1, sensitivity 1.6/1.3; A/B/C/D)。
- 不可变 manifest: reports/k2_run_manifest_067.csv (30 pilot + 30 final = 60 runs)。
- 自主驱动: scripts/k2_driver_067.py (Phase1 LR pilots -> 选LR -> Phase2 finals 健康门控+FP32 fallback+OOM 1200s重试 -> Phase3 instrumented eval(k2_eval_run.py, native+score NRC @derived-ar2.1+1.6/1.3) -> Phase4 aggregate+go/no-go(k2_aggregate_go_no_go_067.py, A/B/C/D))。4卡DDP每run, resumable。
- 验证: cfg-options override(lr/ep/fp32) OK; k2_eval_run smoke(PSC-DIOR-seed0 120img) AP50=0.6336 native NRC=1.246 score=0.4457 OK。
- 已启动: k2_driver_067(PID 1539542) 训练中, 首 pilot PSC-DIOR lr0.0025 3ep 4卡健康(Epoch1 loss~2.67)。keeper(k2_keeper_067.sh)守护自动重启。
- 067 纪律: 唯一任务 K2; 不做其它; 后台运行中不汇报阶段状态; 仅在 K2 全完成(go/no-go)或硬阻塞时回聊天。预计多日。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训 host(K2 是预注册干预训练, 非 host); 未追 public mAP。

## 2026-07-08 命令 067-SCHEDULING-AMENDMENT：K2 改 2×4GPU 并发调度
- 停旧顺序驱动(k2_driver_067)+清 k2 残留(仅本项目, D17 未动); 保留其 helper 供复用。
- 新调度器: scripts/watch_k2_queue_2x4gpu_067.py(max_concurrent=2, 每 job 4-GPU DDP 共享 0,1,2,3; 相位 pilot->选LR->seed0+eval->gate->seed1/2->aggregate; 端口冲突自动换; 状态落盘可 resume) + scripts/k2_job_runner.py(单 job: 4卡训练+健康门控+FP32 fallback+OOM 1200s重试+final 后 eval) + scripts/run_k2_queue_2jobs_each_4gpu_067.sh(keeper: watcher 死自动重启, 清 orphan 后 resume)。
- 验证: 2 并发已跑(PSC-SODA lr0.0025 + lr0.005), 均 nproc_per_node=4, 4 卡 100% util ~5.2GB/卡; resume 正确跳过顺序驱动已完成的 3 个 PSC-DIOR pilot(epoch_3.pth, ap50 0.289/0.213/0.175 -> 选 lr0.0025)。
- 状态文件: k2_queue_status_067/k2_pilot_results_067/k2_lr_selection_067/k2_seed0_gate_results_067/k2_angle_coder_seed_results/k2_angle_coder_block_results/k2_failed_training_audit/k2_health_gate_decisions_067 + go/no-go。
- 汇报纪律(067 amendment): 聊天仅允许最终一次【067 完成汇报】; 中间全部只写日志/CSV; OOM/端口/路径/配置/watcher死/单run失败/eval pending/GPU占用均自处理, 不回聊天。
- 合规: thresholds b7c4e649 未变; D_cal/D_audit 未变; 未重训 host; 未追 public mAP; 未改预注册/batch/GPU 数。

---

## [2026-07-12] 067 完成汇报（K2 angle-coder full-converged 干预矩阵）

- 指令来源：用户 067 + 067-SCHEDULING-AMENDMENT（2 并发 × 4-GPU；仅允许最终一次完成汇报）。
- 执行动作：30 pilots(seed0,3ep,3LR) → per-(head,dataset) 选 LR → seed0 finals(12ep)+eval+gate → seed1/2 finals+eval → aggregate + go/no-go。全程 4-GPU DDP，2 并发共享 0-3；FP32 fallback + OOM 1200s retry；resumable。
- 结束时间：2026-07-11 21:11（queue END），go/no-go 落盘 07-12 00:44。GPU 已空闲。
- 关键产物：
  - reports/k2_go_no_go_decision_067.csv：**PASS / 结局 A / reversing=PSC / n_complete_blocks=6 / failed_heads=KLD,direct_regression**
  - reports/k2_angle_coder_block_results.csv、k2_angle_coder_seed_variance.csv、k2_angle_coder_seed_results.csv、k2_lr_selection_067.csv、k2_failed_training_audit.csv、k2_artifact_manifest_067.csv
  - docs/k2_angle_coder_go_no_go_report_067.md、docs/k2_vs_r1_supersession_note_067.md
  - reports/k2_eval/*.json（18 个可比 run 的 instrumented native+score NRC）
- 停止条件：无触发；无硬阻塞。
- 下一步建议：K2 属 Track A 机制支线，PASS 只加强 PSC 机制小节，不单独决定主线 venue；主线仍待 G2_double_prime / Deployable 二值门控。

---

## [2026-07-12 20:42] 命令 069-REPLACEMENT 启动（自主执行，仅最终汇报）

- 指令来源：用户 069-REPLACEMENT（M1/M2/M3/M4/人工锚点/PSC Phase1 拆篇门控/一键复算/冻结门控；中途不得汇报）。
- PSC Phase1 时间冻结：start=2026-07-12 20:14:39 -0700；deadline=+42d=2026-08-23 20:14:39 -0700（docs/psc_phase1_preregistration.md）。
- 已构建并冻结：docs/psc_phase1_preregistration.md、reports/m3_image_level_protocol_frozen.json（HB UCB/delta0.1/固定序列/阈值序列冻结）、reports/m4_delta_theta_075_frozen.json（derived_ar@15°=2.150）。
- 已构建脚本：m069_common(缓存+HB-LTT+图像bootstrap)、m1_ar21_unify、m2_g2doubleprime_ar21(固定size-bin)、m3_image_level_risk、m4_risk_events、psc_phase1(径向缩放→Branch A 已数值确证:解码角径向不变~1e-5°、phase_mod∝k²)、build_m4_human_annotation+merge+analyze、m_dota_dump(DOTA clean 逐实例)、m069_freeze_and_repro、m069_master(编排)、run_m069.sh(keeper)。
- 已更新：scripts/reproduce_all_main_tables.sh（追加069块）、docs/third_party_reproduction_log.md、scripts/recompute_m3_image_level_risk_control.py。
- 已启动：keeper(run_m069.sh)+m069_master.py 后台运行；当前 DOTA dump(GPU,best-effort)→M1→M2/M3/M4→PSC Phase1→人工merge/analyze(PENDING)→freeze/repro。
- 合规：thresholds.yaml 未改(sha b7c4e649…3fae)；D_cal/D_audit 未改；未重训 host；instance-iid exact binomial 仅审计对照；proxy jitter≠σ_gt；DOTA#20 排除；negative phase_mod 不作方法。
- 预期：人工双标需真人→保持 PENDING→冻结门控 NOT_FROZEN（诚实状态）；机器任务数小时完成。
- 停止条件：无触发。下一步：等待全部机器任务完成 + PSC Phase1 决定后，产出唯一一次最终汇报。

---

## [2026-07-14 22:41 CST] Codex 接手 Claude Code（交接审计，不占正式命令编号）

- 指令来源：用户交接令；本交接不占正式命令编号。
- 正式编号口径：067 已完成；068 已由 Claude Code 执行；Codex 本轮未启动 069，且必须等待监督员单独下发 069 执行令。
- 执行动作：只读核对 AGENTS.md、pth_data/readme、项目执行文件、历史交接/状态、Claude 会话、068 论文、K1-K4 表、冻结资产、复算入口、日志和当前进程；未启动实验、训练、推理、评估或 bootstrap。
- 068 取证：2026-07-12 18:33:55 PDT 开始，18:44:47 PDT 完成；唯一项目产物为 `docs/paper_zh_post_k1k4_068/orientation_reliability_paper_zh.md`，SHA-256 `8104f4c059428cf7330179cc83939049c0a4ff47e37e84bf3fc107e51b0c35b0`。
- 重要编号冲突：服务器日志证明 Claude 在 068 后实际执行过名为 `069-REPLACEMENT` 的管线（2026-07-12 20:42-21:21 PDT）。其磁盘结果为 M1 PASS、M2 FAIL、M3 PASS、PSC Phase1 PASS、human labels PENDING、NOT_FROZEN。该轮不是本次 Codex 交接启动；现标记为 post-068/unratified，等待监督员裁定，不自行采纳、覆盖、删除或重跑。
- 冻结资产：thresholds SHA-256 仍为 `b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`；D_cal/D_audit 未变；RHINO/A4 checkpoint 与 lock SHA 一致；formal/exploratory 标签未变；DOTA#20 仍排除。
- 后台进程：无 orientbench watcher/训练/推理/评估/reproduce/M069 残留；其他项目进程未处理；本轮无清理。
- 关键产物：`docs/codex_takeover_from_claude_after_068.md`、`reports/codex_takeover_artifact_inventory.csv`、`reports/codex_takeover_process_audit.csv`、`reports/codex_takeover_authoritative_sources.csv`、`logs/codex_takeover_after_068.log`。
- 停止条件：本轮未触发新的科学停止动作；既有未追认 M2=FAIL 若被监督员追认，将触发 G2_double_prime 失败分支。人工双标、069 编号冲突、DIOR reliability partial-GT lineage 和当前复算入口未端到端验证仍是 blocker。
- 下一步建议：等待监督员单独下发 069；执行前先裁定既有 `069-REPLACEMENT` 的追认/废止与产物命名空间，禁止盲目运行现有 keeper/master。

---

<!-- CODEX_069_CONTINUATION_FINAL_START -->

## [2026-07-14 20:18:18 -0700] 069-CONTINUATION Codex 续跑收口

- 指令来源：用户 069-CONTINUATION；本轮续原 069，不占新编号，下一正式编号为 070。
- 执行动作：核验并复用历史 069 产物，仅补齐缺口；实际执行 CPU-only 一键复算与严格最终审计；原路径内更新现有 068 中文稿，未新建论文版本；未训练、未运行 detector inference、未重跑 K2、未新建重复命名空间。
- 决策：M1=PASS；M2=PASS（FAIL 时 geometry score 仅附录）；M3=PASS；PSC Phase 1=PASS；human=HUMAN_BLOCKED；freeze=NOT_FROZEN。
- 关键产物：`reports/069_final_reproduction_status.csv`、`reports/069_submission_freeze_gate.csv`、`reports/069_takeover_task_status.csv`、`reports/069_artifact_manifest.csv`、`logs/reproduce_all_main_tables_069.log`、`logs/069_codex_continuation.log`、`docs/third_party_reproduction_log.md`。
- 停止条件：M2 预注册门控若 FAIL 已按规则停止 geometry-specific 正文 claim；人工双标未完成时是唯一剩余 blocker，门控保持 NOT_FROZEN；PSC FAIL/DEADLINE 时停止拆篇但不阻塞主线。
- 冻结与合规：thresholds SHA-256=`b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`；D_cal/D_audit 未变；host 未重训；formal/exploratory 未改；DOTA#20 排除；Phase 1 起止时间未重置。
- 下一步建议：仅在本 069 门控状态基础上进入正式命令 070；不得把缺失人工标签伪造为完成。

<!-- CODEX_069_CONTINUATION_FINAL_END -->

<!-- CODEX_070_FINAL_START -->
## [2026-07-15 18:41:38 -0700] 命令 070 完成

- 指令来源：用户命令 070；只完成 M4 FAIR1M 第三数据集扩展和三数据集人工双标执行包。
- 执行动作：9 个等预算 pilot、9 个 4-GPU final runs、full-val 原生不确定性评测、三 seed 聚合、A/B 互盲包和机器复算。
- 决策：第三数据集 `REPLICATES_A`；人工真实结果 0，状态 `HUMAN_BLOCKED`；提交冻结门控 `NOT_FROZEN`。
- 关键产物：`reports/m4_optional_third_dataset_results.csv`、`reports/m4_third_dataset_seed_results.csv`、`reports/m4_third_dataset_artifact_manifest.csv`、`reports/m4_human_annotation_package_validation.csv`、`reports/070_submission_freeze_gate.csv`、`logs/reproduce_all_main_tables_070.log`。
- 合规：thresholds 与 D_cal/D_audit 未改；host/K2/PSC 未重跑；未追 public mAP；未伪造人工标注；无范围外工作。
- 停止条件：真人双标缺失是唯一冻结 blocker。下一正式命令编号：071。
<!-- CODEX_070_FINAL_END -->

<!-- CODEX_071_FINAL_START -->
## [2026-07-15 19:50:33 -0700] 命令 071 完成：人工双标包物理落盘纠错

- 指令来源：用户命令 071；仅审计、落盘并验证人工双标执行包。
- 070 矛盾：070 包实际生成在外层仓库 `annotation_tools/m4_angle_annotation/`，但用户检查的是权威项目子根 `top_journal_v3_reaudit_055/`；属于路径口径错误及汇报未明确实际根目录。
- 最终落盘：`top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/`；A/B 各 1500 项，三数据集各 500 项，图像完整，内部映射隔离，正式 outputs 为空。
- 工具验证：A/B 默认端口 17801/17802；启动、页面/图像、角度、ambiguous、skip、自动保存、重启恢复、CSV/JSON 导出、防覆盖均 PASS；隔离测试数据的 merge/analyze 1500/1500 PASS；测试进程已结束。
- 真人结果：A=0、B=0；未伪造，状态保持 `HUMAN_BLOCKED`。
- 关键记录：`logs/071_annotation_package_path_audit.log`、`logs/071_annotation_tool_validation.log`、`reports/071_annotation_package_path_audit.csv`、`reports/m4_human_annotation_package_validation.csv`。
- 合规：未训练、未推理、未改论文、thresholds 或 D_cal/D_audit；下一正式命令编号 072。
<!-- CODEX_071_FINAL_END -->

## [2026-07-16 01:31:48 -0700] 071 人工标注网页交互修订
- 指令来源：用户对 071 网页的三项修订要求。
- 修改：备注区移至页面最下方；上一个/下一个、当前角度、图片模糊/方向不明、skip、保存和导出均移至图片右侧；移动端保持自适应。
- 顺序核验：A/B 各自均为打乱顺序，同位置重复实例为 0，实例集合仍完全一致；未重新抽样。
- 验证：A/B 启动、页面、图片、保存/恢复/导出、隔离 merge/analyze 再次 PASS；无后台测试进程。
- 数据保护：检测到 annotator A 已有 3 条自动保存草稿，原样保留；正式 CSV/JSON 仍为 0，HUMAN_BLOCKED 不变。
- 后续界面修订：在“下一个”旁增加“放大图片”按钮，使用浏览器全屏查看并支持退出放大；草稿与任务顺序未改，复验 PASS。
- 放大交互再修订：按钮调整为“上一个｜放大图片｜下一个”；放大改为独立图片对话窗口，不触发浏览器全屏、不改变原页面布局；放大窗口内 canvas 可直接拖画角度并自动保存。正式草稿未改。
- 放大交互最终修订：按钮顺序改为“下一个｜放大图片｜还原图片｜上一个”；取消对话窗口，图片在原有镶嵌式 viewer 内原位放大/还原，页面其余布局不弹出；放大后仍使用同一 canvas 拖画并自动保存。检测到用户继续标注，现有草稿完整保留。
- 渐进放大修订：每次点击“放大图片”按当前宽度约 1.3 倍（至少增加 80px）逐级放大，达到镶嵌区域上限后停用；“还原图片”一次恢复原尺寸。canvas 随每一级同步重算，继续支持角度绘制。

## [2026-07-17 01:40:12 PDT] 人工双标 200 条 pilot 冻结与 B 包交付
- 指令来源：用户要求先以 A 已进行的前 200 条和 B 的相同 200 条计算指标，再决定是否扩至 1500 条。
- 执行动作：冻结 A 前 200 条任务及当前真人草稿快照；从 B 原 1500 条清单筛出同一 canonical 集合并独立打乱，生成 B pilot 启动入口和完成后的一键合并/分析入口。
- 数据状态：B pilot=200，DIOR-R=61、FAIR1M=77、SODA-A=62；A 快照为角度 151、ambiguous 27、skip 17、pending 5；B 真人结果仍为 0，未伪造。
- 指标：可用配对数、圆周角差 mean/median/p90/p95、P(>5°)/P(>10°)，以及 dataset/class/size/ar-bin/ar>=2.1 分层；扩至 1500 的决定不自动作出，待 B 完成后审阅 pilot。
- 关键产物：`top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/start_annotator_B_pilot_200.sh`、`scripts/run_m4_pilot200_analysis.sh`、`reports/m4_pilot200_package_validation.csv`。
- 停止条件：B 真实标注尚未完成，状态 HUMAN_BLOCKED；未训练、未推理、未修改科学结果。

## [2026-07-17 21:35:00 PDT] 200 条人工双标 pilot 中期核验
- 指令来源：用户要求基于 A=200、B 当前=202 的真人工作计算结果，并从论文角度判断是否继续。
- 发现：B 原先运行的是 1500 条 full 清单而非同集合 pilot；A/B 当前 canonical overlap 仅 24，角度均有效配对 17，不能误报为 200 对双标。
- 初步结果：17 对的圆周角差 mean=2.1921°（image-cluster bootstrap 95% CI 1.3507°–3.1526°）、median=1.7347°、p90=4.0902°、p95=5.1923°、P(>5°)=5.88%、P(>10°)=0；ar>=2.1 的 9 对 mean=1.1396°。
- 论文判断：信号正向，说明标注协议具有继续验证价值；但样本尤其 SODA-A 仅 2 个有效配对，尚不足以形成论文证据或直接批准扩至 1500。
- 修复：完整保留 B 已有 202 条真人草稿；将其中与 A pilot 重合的 24 条迁入正确 pilot，B 尚需完成同集合的 176 条。错误 full B 服务已停止，正确 pilot 服务已在 17802 启动。
- 关键产物：`reports/m4_pilot_current_overlap_key_metrics.csv`、`reports/m4_pilot_current_overlap_audit.json`、`top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/internal/pilot_200_B_resume_audit.json`。
- 下一门控：完成同 canonical 200 后再决定是否扩至 1500；状态仍为 HUMAN_BLOCKED。
- 界面纠错：此前正确 pilot 仍显示总数 200，是因为将已完成的 24 条预载在同一任务清单内；该设计会误导用户。现已将 24 条冻结并从界面隐藏，B 页面只显示真实剩余 176 条；完成后脚本自动合并为 200 对。端口 17802 已核验 `task_set=pilot_176_remaining`、任务数 176、初始新结果 0。

## [2026-07-17 22:52:00 PDT] M4 200 对 pilot 完成分析与扩量裁决
- 指令来源：用户要求开始计算并从论文角度回答是否继续投入 1500。
- 完成状态：B 剩余 176 条已全部作出真人决策并导出；与冻结的 24 条合并为同 canonical 200 对。A/B 身份独立，schema/映射核验无错误；B 服务完成后已停止。
- 有效结果：149 对角度可用（DIOR-R=38、FAIR1M=60、SODA-A=51）；mean=2.0938°（image-cluster bootstrap 95% CI 1.8016°–2.3932°），median=1.7137°，p90=4.5579°，p95=5.5849°，P(>5°)=7.38%，P(>10°)=0/149。
- ar>=2.1：n=100，mean=1.9702°（95% CI 1.6360°–2.3393°），P(>10°)=0。小目标及 1.6<=ar<2.1 更易分歧，支持 5° noise-sensitive 标签和 ar>=2.1 主边界。
- 论文裁决：pilot PASS，建议继续冻结的 500×3=1500 目标；当前每数据集/类别/尾部样本仍不足以支撑最终分层 claim。A 仍有 5 条 pending，正式分析前必须补齐。
- 关键产物：`reports/m4_pilot200_key_metrics.csv`、`reports/m4_pilot200_disagreement.csv`、`reports/m4_pilot200_scaleup_decision.csv`、`docs/m4_pilot200_scaleup_decision.md`。
- 冻结状态：真人全量仍未完成，HUMAN_BLOCKED 保持有效。

## [2026-07-17 23:00:00 PDT] M4 全量剩余 A/B 执行包生成
- 指令来源：用户询问是否需要生成 A/B 后续标注脚本，并要求需要则生成。
- 判断：pilot 已 PASS，继续冻结的 1500 目标需要独立的“仅剩余任务”入口，以避免重复标注并保证既有真人结果可复用。
- A：冻结 195 条有效真人决策，页面仅显示剩余 1305 条；B：合并并冻结 377 条有效真人决策，页面仅显示剩余 1123 条。pending 不计完成，已自动进入剩余清单。
- 任务清单分别独立打乱；原始 task ID、匿名映射和图像不变；没有修改或伪造任何真人结果。
- 启动入口：`top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/start_annotator_A_remaining.sh`、`start_annotator_B_remaining.sh`。
- 全量完成后一键合并分析：`scripts/run_m4_full_human_analysis.sh`；A/B 启动、任务数、空白新状态、首图加载及 1500 集合覆盖均验证 PASS，测试服务已停止。
- 启动入口纠错：用户实际启动后 B 显示 `202/1500 · 已完成201`，确认旧的标准脚本 `start_annotator_B.sh` 仍默认加载 full 清单；A 的标准脚本存在相同风险。现已将所有 A/B 标准、remaining 和旧 pilot 启动入口统一指向 `full_remaining`，避免再进入旧清单。旧 B 服务已停止；A/B 正确服务分别在 17801/17802 启动并实时核验为 A=1305、B=1123、新任务完成数均为0。原真人草稿 sha256 未变。

## [2026-07-21 20:33:04 CST] 冻结 B 当前 526 条并生成 A 匹配任务
- 指令来源：用户要求以 B 当前已完成的 500 余条为新一轮检查集，在 A 中只提供尚未标过的相同实例，完成后按 200 对 pilot 的指标分析。
- 冻结状态：B 三段真实草稿去重后共有 526 条有效决策，数据分布 DIOR-R=170、FAIR1M=177、SODA-A=179；B 服务已暂停，避免目标集合继续漂移。
- A 对齐：A 在该集合已完成 195 条，尚缺 331 条（DIOR-R=112、FAIR1M=101、SODA-A=118）；只剩余 331 条的清单已独立打乱，A 服务在 17801 启动并核验显示 331、已完成0。
- 数据保护：A/B 当前草稿均按 sha256 冻结；没有改写或伪造真人结果，已标实例不会重复展示。
- 分析入口：A 完成并导出后运行 `scripts/run_m4_b526_analysis.sh`，输出 526 对的 mean/median/p90/p95、P(>5°)/P(>10°)、image-cluster bootstrap CI 及 dataset/class/size/ar 分层。

## [2026-07-21 22:15:00 CST] M4 526 对分析与证据充分性裁决
- A 的 331 条补标已全部完成并导出；与既有 195 条合并后，526 个同 canonical 双标目标通过身份、schema、映射和集合核验。A 服务已停止。
- 有效角度对 393：DIOR-R=99、FAIR1M=151、SODA-A=143。总体 mean=2.3587°（image-cluster bootstrap 95% CI 2.0096°–2.8696°），median=1.6435°，p90=4.4043°，p95=5.8572°，P(>5°)=7.63%（CI 5.10%–10.41%），P(>10°)=1.02%。
- ar>=2.1：n=275，mean=2.3356°，median=1.6108°，P(>5°)=6.91%，P(>10°)=0.73%。方向与 200 对 pilot 稳定一致。
- 边界：4 个 >10° 分歧全部来自 SODA-A，其中一个为 84.22°；结果原样保留，不作事后剔除。小目标及 1.6<=ar<2.1 仍更易分歧。
- 论文裁决：已足以支撑总体 human-noise anchor 和粗粒度数据集结论；尚不足以宣布预注册人工任务完成，因为目标数 DIOR-R=170、FAIR1M=177、SODA-A=179，均低于每数据集最少 200。最小合规补量为 30/23/21，共 74 对；若保留正式 class/size/tail 分层 claim，则继续至 500×3。
- 关键产物：`reports/m4_b526_key_metrics.csv`、`reports/m4_b526_disagreement.csv`、`reports/m4_b526_evidence_gate.csv`、`docs/m4_b526_evidence_assessment.md`。冻结状态仍为 HUMAN_BLOCKED / NOT_FROZEN。
- 有效对口径说明：526 条均已由两人作出决策，但角度差统计只纳入双方都给出数值角度的 393 对；其余 133 对包括双方 ambiguous 88、双方 skip 3、单方 ambiguous 30、单方 skip 12，无 pending。DIOR-R 困难/ambiguous 比例最高（99/170 数值可用），不是文件丢失或合并错误。

## [2026-07-21 22:27:39 CST] M4 补至 600 并启动单方未标重检
- 指令来源：用户要求将双标目标补至 600，并重新标注“一方给出角度、另一方未给角度”的实例。
- 新目标：按冻结 sampling_rank 从未用样本中选择 DIOR-R=30、FAIR1M=23、SODA-A=21，共 74 个；A/B 使用同一 canonical 集合、独立打乱，完成后各数据集恰为 200 个目标。
- 重检：原 526 对中单方有角度、另一方 ambiguous/skip 共 29 个；仅由原未给角度的一方重检，A=12、B=17。使用新匿名 task ID、混入新目标并打乱，不显示任务类型、原结果或对方结果；允许再次 ambiguous/skip，不强迫给角度。
- 页面：A 共 86 条、B 共 91 条，分别在 17801/17802 启动并核验任务数、图片、空白新状态和隐私字段 PASS。
- 统计纪律：原始标注仍是 primary，不被重检覆盖；重检作为 secondary resolution 单列。完成后运行 `scripts/run_m4_m600_analysis.sh`，同时生成正式 600 对主分析和 29 条重检结果。
- 状态：人工任务进行中，HUMAN_BLOCKED / NOT_FROZEN 保持有效。

## [2026-07-21 23:05:00 CST] M4 600 对最低协议完成与重检分析
- A=86、B=91 本轮任务均完成并导出；600 个 primary 双标目标恰为 DIOR-R/FAIR1M/SODA-A 各 200，双方均已作出 angle/ambiguous/skip 决策，无 pending。
- 口径纠错：`min_per_dataset=200` 应作用于独立完成的目标，而不是仅双方都有数值角度的子集；merge verifier 已据此修复，并同时保留 usable numeric counts。核验状态 `COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION`。
- Primary 有效角度对 450（DIOR-R=122、FAIR1M=169、SODA-A=159）：mean=2.3112°（cluster-bootstrap 95% CI 1.9970°–2.7854°），median=1.6359°，p90=4.4220°，p95=5.9359°，P(>5°)=8.00%，P(>10°)=0.89%。
- ar>=2.1：n=308，mean=2.2823°，median=1.6130°，P(>5°)=6.82%，P(>10°)=0.65%；200/526/600 三个检查点方向稳定。
- 重检：29 个单方 ambiguous/skip 中 27 个重新给出数值角度，2 个仍 ambiguous；27 对 mean=2.2126°、median=1.9302°，仅作 secondary，不覆盖 primary。
- 论文裁决：600 已足够支撑总体 human-noise anchor、粗粒度 dataset 结论、5° noise-sensitive 和 ar>=2.1 边界；仅当保留正式 rare-class/size/extreme-tail 分层 claim 时才需继续至 1500。
- 关键产物：`reports/m4_m600_key_metrics.csv`、`reports/m4_m600_disagreement.csv`、`reports/m4_m600_one_sided_recheck.csv`、`reports/m4_m600_evidence_gate.csv`、`docs/m4_m600_final_assessment.md`。A/B 服务完成后已停止。

## [2026-07-21 23:15:00 CST] 命令 072 完成汇报归档
- 072 归档范围：071 后的网页修订、200 对 pilot、526 对扩展、600 对最低协议及 29 条单方未标重检；最终权威结论以 600 primary 结果为准。
- 最低人工协议 COMPLETE：三个数据集各 200 个独立双标目标，无 pending；450 对数值角度结果及重检结果通过 schema、mapping、身份和复算核验。
- 科学结论：足以支撑 overall human-noise anchor、dataset-level、5° noise-sensitive 和 ar>=2.1 边界；1500 仅在保留正式细粒度分层 claim 时需要。
- 关键归档：`docs/072_completion_report.md`、`reports/072_completion_status.csv`、`logs/072_completion.log`。
- 合规：未训练、未推理、未改论文/thresholds/D_cal/D_audit/host，未伪造标注；不宣称全项目完成或 submission frozen。下一正式编号 073。

## [2026-07-21 09:36:00 -0700] 命令 073 完成：真人锚点接入、最终复算、拆篇与协作者审阅冻结
- 指令来源：用户下达正式命令 073，要求接入 072 真人双标、完成风险解释与全局复算、落实既有 PSC 拆篇判定，并仅生成拆篇后的 A 篇中文正式稿。
- 真人复算：600 个 canonical targets（三数据集各 200），450 对数值角度；总体 mean=2.3112°（image-cluster bootstrap 95% CI 1.9970°--2.7854°），median=1.6359°，p90=4.4220°，p95=5.9359°，P(>5°)=8.00%，P(>10°)=0.89%。ar>=2.1 有 308 对，mean=2.2823°，P(>5°)=6.82%，P(>10°)=0.65%。29 个盲重检严格保持 secondary，未覆盖 primary。
- 风险解释：1.5°--2° 均值预算仅作 label-noise-aware 解读；5° 是有意义但 noise-sensitive 的 fine-risk；10° 具有更清楚的 severe-risk 余量；SODA-A 高尾部作为限制保留；corner-jitter 仅作 proxy sensitivity。
- 一键复算：`scripts/reproduce_all_main_tables.sh` 已实际完成 CPU 全链；最终校验器首次读取新 merge audit 字段时出现 schema 错配，修复后仅续跑最终校验，没有重复训练或推理。权威日志为 `logs/reproduce_all_main_tables_073.log`，16 项复算检查全部通过。
- 拆篇：追认既有 PSC 拆篇判定；A 篇只保留简洁 head-specific 观察，未生成 B 篇或 B 篇提纲。唯一新论文为 `docs/paper_A_zh_post_human_073/orientation_reliability_paper_A_zh.md`。
- 冻结：`reports/073_submission_freeze_gate.csv` 十项条件全部通过，最终状态为 `FROZEN_FOR_COLLABORATOR_REVIEW`，不表示 submission ready 或项目全部完成。
- 资产与合规：thresholds SHA-256 仍为 `b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`；10 个 D_cal/D_audit 哈希、两个 host lock/checkpoint 均未变；未训练、未推理、未重跑检测器/角度编码矩阵、未修改真人原始标注、无范围外论文文件。
- 停止条件：未触发新的科学停止条件。下一条正式命令编号为 074。

## [2026-07-21 09:38:00 -0700] 命令 073 重复送达核验
- 指令来源：用户再次发送与已完成命令 073 相同的全文。
- 执行动作：核对既有 073 权威产物与最终门控；未建立第二套结果、未重复执行训练/推理/昂贵统计链。
- 关键状态：`reports/073_submission_freeze_gate.csv` 仍为 `FROZEN_FOR_COLLABORATOR_REVIEW`；唯一 A 篇中文稿路径不变。
- 停止条件：无。下一条正式命令编号仍为 074。

## [2026-07-22 12:45:00 CST] 命令 074-REPLACEMENT：A/B 物理隔离与 G0 权威法证
- 指令来源：用户以 074-REPLACEMENT 覆盖旧 074；本轮只允许建立 A/B/shared 命名空间并完成 B0/G0。
- 执行时间：G0 于 2026-07-22 12:35 CST 启动，2026-07-22 12:45 CST 完成。
- 物理边界：已建立 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/`、`paper_B_psc_mechanism/` 与 `shared_forensics/g0/`；共同边界和全部法证结果只写入 shared forensics。
- G0 判定：`PASS_RISK_FUNCTIONAL_DEPENDENT`。九个 PSC detector-head-seed 单元的连续角度风险均稳定反序；geometry-normalized severe event 在数据集/种子间为 near-random、non-reversed 与 reversed 混合，禁止继续使用不区分风险对象的“phase_mod 稳定反序”。正负分数直接复算且 prediction identity、mask、coverage、paired resample 完全一致，未使用对称近似。
- 对齐与训练披露：A 8.2/8.5 的 A-F 为同一 full-val lineage 上的合理不同估计量/子集，DOTA G-H 不进入 8.5；无 ERROR。K2 实际 LR、epoch、checkpoint、精度模式与失败单元已披露；旧聚合表存在 LR/AMP 元数据陈旧项。FAIR1M-CSL=`HEALTHY_BUT_WEAK`，不得单独支撑强三数据集 CSL 结论。
- 关键产物：`top_journal_v3_reaudit_055/shared_forensics/AB_ASSET_BOUNDARY.md`、`shared_forensics/g0/docs/`、`shared_forensics/g0/reports/` 与 `shared_forensics/g0/scripts/run_g0_forensics.py`。
- 合规：允许进入后续 075；未执行 A1-A6，未执行 B1-B7，未训练、未推理、未修改论文、thresholds.yaml、D_cal/D_audit 或 formal/exploratory 标签。

## [2026-07-22 14:07:30 CST] 命令 075：A1-A3 风险控制重构
- 执行时间：最终协议于 2026-07-22 14:03 CST 冻结，权威复算于 14:06--14:07 CST 完成。
- A1=`PARTIAL_FRONTIER`：6 个 evaluation units、4 scores、4 endpoints、6 budgets 全量保留；20 个 nontrivial certifications，其中 12 个满足预注册 practical 条件。主 geometry-normalized endpoint 仅 target-GT diagnostic upper bound 在 DIOR-R RTMDet 单元获得 1 个 nontrivial practical certification，因此不能维持广泛可部署风险控制表述。
- A2=`PASS_TILE_ONLY_WITH_LIMITATION`：eligible-scene universe 固定，阈值后空场景作为 abstention 而非零损失。DIOR-R/FAIR1M 可作 mother-scene；SODA-A 可恢复 576 个母景，但其 tiles 全部跨既有 D_cal/D_audit 角色，故正式保证仅为 tile/image-level，mother-scene 聚合只作 sensitivity。
- A3=`PARTIAL_SCORE_MENU`：主 endpoint 下 detection、TTA、source-supervised geometry 均无 nontrivial certification；target-GT upper bound 有 1 个。形式通过不等于实用成功，旧 instance-i.i.d. 仅作审计。
- 综合状态：`PROCEED_WITH_DOWNGRADED_RISK_CLAIM`，允许进入 076，但后续不得将单一 target-GT upper-bound 成功写成 deployable 或跨单元通用保证。
- 关键产物：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/{docs,reports,scripts,logs}/`；`reproduce_A1_A3.sh` 完整实际执行，13 项复算检查通过。
- 合规：仅写 A 工作区和本记录；未写 B 工作区、未复制完整 PSC 主表、未修改论文、thresholds.yaml 或 D_cal/D_audit；未训练/推理 detector，未执行 A4-A6 或 B1-B7。

## [2026-07-22 15:37:00 CST] 命令 076：A4-A6 确认性收口
- 执行时间：2026-07-22 15:29--15:37 CST。
- A4=`PARTIAL_ALIGNMENT`：K1 六单元 provenance-clean full-evaluator 基线/自适应端点继续支持 AP50 弱敏感区与 AP75 更早响应；实际 center/scale 下的 ar>=2.1 固定对经验容忍度已对 A-F 全量复算并与 ideal delta_0.50/delta_0.75 分列。因全部六单元的完整 raw prediction dumps 未持久化，固定 0/2/5/10/15/20/25/30 度 AP 网格及 AP75 knee 未伪造，matched-only/partial-GT AP 未使用。
- A5=`PARTIAL_TWO_ANNOTATOR_WITH_GT`：annotator-1 vs official GT 为 n=468、mean=5.2721°、median=1.7639°；annotator-2 为 n=463、mean=5.1219°、median=1.7899°。这是 discrepancy 而非把 official GT 当绝对真值。第三标注员 150 项任务已冻结为每数据集 50（45 boundary + 105 random regular），工具启动/保存/恢复/测试导出通过；真人结果仍为 0，状态 HUMAN_ANNOTATOR_3_BLOCKED，未生成正式 consensus。
- A6=`NO_ELIGIBLE_CONFIRMATORY_UNIT`：ARS-DETR DIOR-R/16 持久化 schema 实为旧 5,863-image universe 且已有 NRC；DOTA/14 仅有指向已消失 /dev/shm 的 manifest；其它候选同属 partial/已查看。未更换协议、未训练新 detector、未伪造确认数值。
- 工具箱：独立 CLI、6 项单元/合成测试及真实持久化 artifact regression 全通过；不可行工作点显式输出，未包含 PSC/B 机制或把 target-GT score 作为默认 deployable score。
- 综合 A 等级：`A_MEASUREMENT_ONLY`。075 的广泛 deployable risk-control 主张不得恢复；允许保留 AP75/NRC/geometry-normalized event/human audit 的 measurement protocol。
- 关键产物：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/{docs,reports,figures,annotation_tools,toolbox,scripts,logs}/`；`reproduce_A4_A6.sh` 实际完成，14 项检查通过。
- 合规：允许进入 077；未执行 B1-B7，未写 B 工作区，未修改论文、thresholds.yaml、D_cal/D_audit，未训练或重训 host，未追 public mAP。

## [2026-07-22 15:54:00 CST] 命令 077：A 篇 measurement-only 重写
- 执行时间：2026-07-22 15:45--15:54 CST。
- A 篇已按 `A_MEASUREMENT_ONLY` 最终裁决完整重写；唯一论文为 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`。
- 论文保留测量协议、几何归一化风险、场景统计审计、严格认证可行性负结果、人工标注审计与工具箱；未恢复广泛 risk-control 或 deployable certification 主张，未写入 B 的机制结果。
- 合规：未执行 B1--B7，未训练、未推理、未评测或统计重算，未修改实验资产；下一正式编号为 078。

## [2026-07-22 18:56:00 CST] 命令 078：B1--B3 机制阶段
- 执行时间：2026-07-22 16:14--18:56 CST；B1 假说、双风险端点、候选和干预网格于 16:14 CST 冻结。
- B2=`SUPPORTS_MECHANISM_SUFFICIENCY`：729 个玩具参数单元同时出现 informative、near-random 与 reverse 区域，且反序不只来自极端参数；仅作充分性证据。
- B3：九个 PSC detector-head-seed 单元完成端点分离的真实输出干预；H1=`SUPPORTED`、H2=`PARTIALLY_SUPPORTED`、H3=`SUPPORTED`、H4=`PARTIALLY_SUPPORTED`。径向 full-evaluator 干预会改变部分 box/NMS/AP，只作 mechanism-only；不改预测的候选排序才属于 ranking-only。
- 阶段门控=`PROCEED_B4_EXTERNAL_VALIDATION`；FAIR1M 仅以 DIOR-R/SODA-A 冻结后的未改公式作确认，未据其结果调公式。
- 复算：`paper_B_psc_mechanism/scripts/reproduce_B1_B3.sh` 完整执行，13 项检查全部通过。
- 合规：未训练、未执行 B4--B7、未修改或写入 A 工作区，未修改 thresholds.yaml 或 D_cal/D_audit；下一正式编号为 079。

## [2026-07-23 21:25:40 CST] 命令 079：B4 外部变体验证与 B5 机制终审
- 执行时间：2026-07-23 18:38--21:25 CST。
- 外部 variant：DOTA-v1.0 `train -> val` 的 RotatedFCOS-PSCD；未参与 B1--B3 开发。按冻结官方 dual-frequency 配置训练 3 seeds，每任务 4 GPU、FP32、12 epochs；AP50=0.629/0.627/0.632，三者均 `HEALTHY_COMPARABLE`。
- B4：H1/H3 的结构干预在新 host 上复现，H2/H4 部分复现；Endpoint E 继续异质。外部 host 的 phase_mod 对 Endpoint C 为 informative（NRC=0.917--0.950），未复现原 RetinaNet 的反序方向，说明机制和排序语义必须 host/endpoint qualified。
- 冻结候选未独立确认稳定优于 detection score；机制干预改变 angle box，仅作 mechanism-only，未称 ranking-only。
- B5=`PASS_MECHANISM_BOUNDED`：允许进入 B6，但不得继承修复成功或宣称通用 PSC failure。
- 复算：`paper_B_psc_mechanism/scripts/reproduce_B4_B5.sh` 完整执行，15 项检查全部通过。
- 合规：未执行 B6/B7，未修改或写入 A 工作区，未修改 thresholds.yaml 或 D_cal/D_audit，未追 public mAP。

## [2026-07-23 18:29:41 CST] Git 仓库发布
- 指令来源：用户要求提交应提交的项目内容，并由 Codex 处理 Git 发布阻塞。
- 执行动作：配置官方 GitHub 远端，按源码、配置、论文、可复算脚本、权威表格和标注协议整理提交范围；排除 checkpoint、原始预测、日志、缓存、标注图片、测试状态及超过 GitHub 单文件限制的逐实例持久化数据。
- 关键路径：`paper_A_orientation_protocol/`、`paper_B_psc_mechanism/`、`shared_forensics/` 及项目根复算与治理文件。
- 停止条件：未触发；未修改科学结果、冻结阈值或数据划分。
- 下一步：将发布分支推送至 `ziyu24/orientbench` 并建立合并请求。

## [2026-07-24 11:55:41 PDT] 保守磁盘清理
- 指令来源：用户要求先删除目录审计中建议的保守清理项。
- 执行动作：删除已完成训练的非最佳 `epoch_*.pth` 快照、B4 非最佳 epoch、明确标记为 preflight/superseded 的训练目录，以及本地测试与 Python 缓存；保留全部 `best*.pth`、持久化科学产物、人工标注数据和复算依赖。
- 关键结果：项目目录由约 53GB 降至约 30GB，释放约 23GB；剩余非最佳 epoch 为 0，保留 best checkpoint 75 个。
- 停止条件：未触发；未删除权威结果、冻结资产或正式复算输入。
- 下一步建议：如需继续释放空间，再单独确认是否清除已被正式结果取代的 R1 与 K2 pilot 剩余资产。

## [2026-07-24 12:03:14 PDT] 第二批低风险磁盘清理
- 指令来源：用户要求继续清理低风险内容。
- 执行动作：删除已被正式 K2 取代的 R1 工作目录、K2 pilot 工作目录，以及 RHINO/A4 host 的末轮 checkpoint；保留 K2 的 24 个 final best checkpoint 和两个 host best checkpoint。
- 关键结果：释放 8,376,247,347 bytes（约 7.8GiB），项目目录降至约 22GB。
- 停止条件：未触发；未删除持久化科学产物、正式 K2 final、B4 external、人工标注或复算依赖。
- 下一步建议：其余大目录需要逐项确认依赖后再决定是否归档或删除。

## [2026-07-27 10:48:12 CST] 新服务器迁移交接
- 指令来源：用户要求为已经迁移到其它服务器的项目生成可无缝续作的详细报告。
- 执行动作：核验 Git、迁移分片、冻结哈希、环境、绝对软链接、外部数据依赖、保留 checkpoint、持久化产物、A/B 科学裁决、复算入口和后台进程；未运行实验。
- 关键产物：`docs/server_migration_handoff_20260727.md`。
- 关键结果：5 个迁移分片 SHA-256 与 zstd stream 均通过；最新完成状态为 079，A=`A_MEASUREMENT_ONLY`，B5=`PASS_MECHANISM_BOUNDED`，下一编号 080。
- 停止条件：未触发；报告明确记录源端缺失 SODA-A 原始目录、4,816 个绝对软链接和项目外 `pth_data`/third-party/conda 依赖。
- 下一步建议：新服务器先完成迁移验收和路径恢复，再执行 080，不重做 075--079。

## [2026-07-27 10:56:14 CST] 迁移报告复核修订
- 指令来源：用户要求在新会话中复核既有迁移报告并修正必要内容。
- 执行动作：逐项对照当前 Git、checkpoint 分类、AGENTS 治理规则、A/B 边界、迁移归档时点、环境和验收流程。
- 关键产物：修订 `docs/server_migration_handoff_20260727.md`。
- 关键结果：明确归档内嵌提交与报告提交不同、归档不含报告、24 个 K2 checkpoint 的 18+6 构成、38 个总 checkpoint 构成、长期联合科学主线与 A/B 物理隔离的兼容方式，并补充科学不变量、环境验收和后台进程复查。
- 停止条件：未触发；未修改实验、论文、阈值、数据划分或科学结果。
- 下一步建议：新服务器以发布分支最新提交为准，完成报告中的 14 步验收后再执行 080。

## [2026-08-05 16:34:35 CST] Git 分支收口
- 指令来源：用户要求将当前项目上传到 `main`，不再保留其它分支。
- 执行动作：确认 `origin/main` 是当前发布提交的祖先，采用 fast-forward 方式将最新项目状态推送到 `main`，随后删除发布分支及旧本地分支。
- 关键结果：GitHub 仅保留 `main` 作为项目分支；大体积忽略资产和本地迁移分片仍不进入 Git。
- 停止条件：未触发；未改动科学资产、冻结配置或实验结果。
- 下一步建议：其它服务器直接 checkout/pull `main`，持久化大文件仍按迁移报告恢复。

[2026-08-05T08:34:45-07:00] source=C r004; action=A1 power-score attribution; gate=FAIL_SCORE_LIMIT_DOMINANT; outputs=Paper-A r004 logical namespace and dis/server_reports r004; stop=no protocol drift; next=C adjudication; training=0; inference=0; download=0.

[2026-08-05T19:42:22-07:00] source=C r005; action=scene-functional attainable-envelope audit; structure_gate=PASS_SCENE_ENVELOPE_VALID; score_cause_gate=INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION; outputs=Paper-A r005 logical namespace and dis/server_reports r005; stop=no protocol drift; next=C adjudication; model_fit_predict=0; training=0; inference=0; download=0.

- 2026-08-05T20:41:33.512319-07:00 | r006 split-FST retrospective development audit: structure=FAIL_SPLIT_FST_VALIDITY; development=INCONCLUSIVE_DEVELOPMENT; detector fit/predict=0/0; score-regressor fit/predict=12/12; no training/inference/download/GPU; next recommendation: do not enter RSAR acquisition .

- 2026-08-05T20:50:57.421101-07:00 | r006 split-FST final result: structure=PASS_SPLIT_FST_VALIDITY; development=FAIL_NO_BROAD_TARGET_FREE_DEVELOPMENT; detector fit/predict=0/0; score-regressor fit/predict=12/12; no training/inference/download/GPU; next recommendation: do not enter RSAR acquisition .

- 2026-08-06T05:33:25.898657-07:00 | r007 split-FST validity audit: structure=FAIL_SPLIT_FST_VALIDITY_R007; development=INCONCLUSIVE_DEVELOPMENT_R007; detector fit/predict=0/0; score-regressor fit/predict=12/12; no training/inference/download/GPU.

- 2026-08-06T05:45:23.782936-07:00 | r007 split-FST validity audit: structure=FAIL_SPLIT_FST_VALIDITY_R007; development=INCONCLUSIVE_DEVELOPMENT_R007; detector fit/predict=0/0; score-regressor fit/predict=12/12; no training/inference/download/GPU.

- 2026-08-06T06:00:00-07:00 | source=C r008 claim quarantine: hygiene_gate=PASS_CLAIM_QUARANTINE_R008; measurement_core_status=SUFFICIENT_FOR_MEASUREMENT_REVISION; operations training/inference/score-regressor/GPU/download/external-data=0; outputs=v078 manuscript, claim ledger, gate, validator, server report; no historical assets modified; next=075 review.

- 2026-08-06T06:20:00-07:00 | source=C r009 evidence closure: provenance=INCONCLUSIVE_PROVENANCE_R009 because FAIR1M-v1.0 full-validation GT input is empty; evaluator golden=PASS; no training/inference/bootstrap/evaluator science runs; v079 historical certification claims quarantined; next=repair missing frozen GT input without changing Core scope.
## [2026-08-06 08:45:00 CST] 来源: Codex

### r009 continuation

- 已核验 FAIR1M-v1.0 数据与标注已到位，并将非空 val_20 GT 修复到持久化 r009 GT 入口；其 3,896 图、78,638 个目标与 FAIR1M/24 full schema 对齐。
- 已重新执行 r009 provenance preflight。DIOR-R/22、DIOR-R/3、FAIR1M-v1.0/24、SODA-A/23 有完整持久化 schema；DIOR-R/61 仅有 600 图 raw 子集，SODA-A/4 仅有 408 图 raw 子集。
- 尝试用现有 pth 重建 SODA-A/4 full dump，但服务器当前缺少 SODA-A 图像树，未启动有效推理；未使用 matched-only 结果替代。
- r009 判定仍为 `INCONCLUSIVE_PROVENANCE_R009`，科学 dose evaluator 未启动；未训练、未修改 thresholds/D_cal/D_audit。
- 关键报告：`dis/server_reports/orientbench-c-r009-20260806.md`；inventory：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_raw_prediction_inventory_r009.csv`。
## [2026-08-06 19:42:00 CST] 来源: Codex

### r009 provenance correction

- 用户指出 SODA-A 已到位、DIOR 既有数据可用；复核确认此前是数据根路径/adapter 指向错误，不是数据缺失。
- SODA-A val_tiled：22,994 图像与 22,994 标注文件已确认；DIOR test：11,738 图像与完整标注已确认。
- 使用冻结 pth、4 GPU、无训练，重新生成 DIOR-R/61 与 SODA-A/4 full-val raw dump，并持久化 schema；两者 image-ID universe 与 GT 对齐。
- r009 Core-6 provenance preflight 现为全部 READY，科学 dose evaluator 已解除 provenance 阻塞。
## [2026-08-06 20:20:00 CST] 来源: Codex

### r009 GPU evaluator replacement

- Shapely 逐框重匹配已停止，替换为 `gpu_eval_r009.py`，调用 K1 验证的 `RBboxOverlaps2D` GPU 算子。
- DIOR-R/22 smoke：dose 0 AP50=0.53678、AP75=0.35032；dose 2 AP50=0.53835、AP75=0.34746，均完成 full re-match。
- 未训练、未改 checkpoint、未改 GT/threshold/D_cal/D_audit。
## [2026-08-07 00:00:00 CST] 来源: Codex

### r009 GPU dose pass

- GPU `RBboxOverlaps2D` 已完成 Core-6 的 48 个 prediction-directed 固定剂量重匹配（0/2/5/10/15/20/25/30°）。
- AP50/AP75 与角度误差已写入 A 工作区 `a4_fixed_dose_positive_r009.csv`。
- GT-directed 与 symmetric 两条预注册轨道尚未执行；因此 r009 仍未最终闭合。
## [2026-08-07 02:00:00 CST] 来源: Codex

### r009 GPU tracks

- Core-6 三条固定剂量轨道已完成：P、D、S，各 8 剂量，共 144 次 GPU full-evaluator 重匹配。
- 输出：`a4_fixed_dose_positive_r009.csv`、`a4_fixed_dose_gt_directed_r009.csv`、`a4_fixed_dose_symmetric_r009.csv`。
- 当前 gate：`INCONCLUSIVE_MECHANISM_R009`；风险事件、geometry survival 与 bootstrap 汇总尚未收口。

## [2026-08-07 08:30:00 CST] 来源: Codex

### r009 final evidence closure

- Core-6 P/D/S fixed-dose tracks were independently re-evaluated with the K1 GPU full evaluator at 0/2/5/10/15/20/25/30 degrees (144 calls total).
- Per-match geometry-normalized severe-event outcomes and 500-replicate image-cluster bootstrap summaries are persisted in `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_risk_event_r009.csv` and `a4_cluster_bootstrap_r009.csv`.
- Exact IoU=0.75 survival was recomputed at 0/15/30 degrees and persisted in `a4_geometry_survival_r009.csv`; all six units are provenance READY.
- Final r009 status is `PASS_R009_EVIDENCE_CLOSED`. This closes the evidence package only; it does not establish a deployable selector. No training or threshold/split changes were made.

## [2026-08-07 01:10:00 CST] 来源: Codex

### r010 statistical mechanism closure

- Pulled `origin/main` before execution; scientific snapshot was `73f8814`.
- Completed the independent r010 full evaluator on all six Core-6 units and ran 1000-replicate paired image-cluster AP bootstrap per unit. SODA-A units completed after the quadratic GT lookup was removed; the two-unit execution was parallelized across GPUs. No training, detector inference, download, threshold, split, or D_cal/D_audit change occurred.
- Extension units remain `NOT_RUN_AMBIGUOUS_EXTENSION`.
- Final r010 gate: `INCONCLUSIVE_MECHANISM_R010`. Report: `dis/server_reports/orientbench-c-r010-20260806.md`.
- r010 closes the evaluator/statistical package but does not establish a strong unified mechanism, causal, or deployable-selector claim.

## [2026-08-07 18:00--21:00 CST] 来源: Codex

### r011 final closure

- 已从 `origin/main` 拉取 r011 `sug.md`；前置阶段发现官方 evaluator 与 SODA-A/23 prediction lineage 错配后在本轮修复，没有沿用错误停止结论。
- 官方 mmrotate endpoint 与独立 Shapely clean-room evaluator 的 Core-6 AP50/AP75 parity 为 6/6 PASS；SODA-A/23 改用 K1 的 1,663,631-prediction identity dump。
- 完成 144 个 P/D/S 固定剂量单元、96 个正负分量、每单元 1000 次 full-split image paired bootstrap，以及 fixed baseline-IoU75 cohort survival。P1=`PASS_STRONG_JSTARS_EVIDENCE_R011`。
- 完成有界 P3 跨域复核：4/11 eligible folds 支持，P3=`P3_CROSS_DOMAIN_INCONCLUSIVE_R011`；联合门控=`TGRS_NOT_REACHED_R011`。
- 关键产物：`dis/server_reports/orientbench-c-r011-20260807.md`、A 工作区全部 r011 reports/scripts 和联合稿；read-only validator 通过 130 项检查。
- 未训练、未执行 detector inference、未下载、未修改 thresholds、split 或 D_cal/D_audit；下一步由后续正式指令决定。

## [2026-08-08 14:19:31 CST] 来源: Codex

### r012 A0 provenance closure

- 拉取并在 `ebf8c27eb4ff9c225be920454b7a5f013fbc5099` 执行冻结 r012；`pth_data/readme.md` 可读。
- FAIR1M frozen val 为 4,362 images / 78,644 GT；持久化 r011 identity/hflip/vflip raw 仅 3,896 image rows / identity 484,332 predictions，缺 466 行。m069 只登记 4,362 / 488,194，未持久化对应完整 raw dump，无法闭合相同 prediction universe。
- 最终触发 `FAIL_PROVENANCE_R012`；Core provenance 为 5/6。按硬门未执行 transform smoke、GPU forward、feature build、source fit、target label attach、bootstrap 或 HRSC confirmation。
- 关键产物：`dis/server_reports/orientbench-c-r012-20260807.md`、`p3_selector/deployable_proxy_r012/` 与 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`。
- 未修改 thresholds、split、D_cal/D_audit 或历史 r009-r011 资产；当前 EQS 方法线关闭，后续只允许以新的正式指令处理。

## [2026-08-08 16:06:58--19:05:00 CST] 来源: Codex

### r014 完整执行

- 前置阻塞：用户授权删除 12 个 warning-only、未跟踪 `risk_logs/*.err`；对应科学 JSONL 未删除。用户既有一行空白变更单独保存在 `stash@{0}`，未混入 r014。
- 修复 FAIR1M frozen val 完整 raw：4,362 images / 78,644 GT / 488,194 identity predictions；official AP50/AP75 parity 通过。Core-6 provenance 与 transform 6/6 通过。
- 完成 prediction-only EQS：source-only nested CV 未早停；目标 score 先封存后接 D_audit；1,000 次配对 image/mother-scene bootstrap。Core 判定 `PASS_DEPLOYABLE_EQS_R014`，unit 6/6、dataset 3/3 支持。
- 按条件完成 HRSC2016/LSKNet 独立确认：Delta NRC=0.0602，95% CI=[-0.0143,0.1438]，判定 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`；Core 结果不回改，跨 host 强主张禁止。
- 关键产物：`dis/server_reports/orientbench-c-r014-20260808.md`、`p3_selector/deployable_proxy_r014/`、`orientation_reliability_submission_r014.md`。未训练 detector，未修改 thresholds、D_cal/D_audit 或 `dis/B.md`。

## [2026-08-08 20:40--20:45 CST] 来源: Codex

### r015 协议闭合

- 执行 r015 CPU-only 只读法证与同步 full-universe cluster bootstrap；r014 的 formal verdict 固定为 `FAIL_PROTOCOL_R014`，预标签封存缺少协议和完整执行代码，不能由最终 manifest 补回。
- r015 的 six-unit / three-dataset EQS 数值为 `EXPLORATORY_CORE_SUPPORT_R015`；SODA-A 使用 mother-scene 主抽样。HRSC 保持 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`。
- 新稿已降级为探索性 post-audit evidence；未训练、未推理、未重拟合 selector、未改 thresholds、D_cal/D_audit、r014、`dis/B.md` 或冻结资产。
- 关键产物：`dis/server_reports/orientbench-c-r015-20260808.md` 与 `p3_selector/deployable_proxy_r015/`；下一步仅可在新正式指令下决定。

## [2026-08-08 21:00--21:08 CST] 来源: Codex

### r016 r015 独立验证器闭合

- 完成 r015 的独立 Git/manifest、raw score-label-universe、同步 bootstrap、集合/schema/seal、稿件/claim 与资源复核；`VALID_R015_CLOSURE_R016`。
- r015 数值接受为 `EXPLORATORY_CORE_SUPPORT_R015`，但 r015 历史验收仍为 `FAIL_AUDIT_IMPLEMENTATION_R015`；r014 保持 `FAIL_PROTOCOL_R014`，HRSC 保持不确定。
- 未训练、未推理、未重拟合或重打分，未改 r015 及更早资产、threshold、split、D_cal/D_audit 或 `dis/B.md`。关键报告：`dis/server_reports/orientbench-c-r016-20260808.md`。

## [2026-08-08 21:20--21:24 CST] 来源: Codex

### r017 静态收据与投稿证据索引闭合

- 未重跑 bootstrap；静态核验 9,000 行 key/replicate 全集、全部 summary 字段与冻结 gate，重建并持久化六单元 zero-eligible cluster count/SHA。
- 记录 `R015_SET_AUDIT_ROLE_DRIFT`，按 canonical MD5 parity 重建集合；schema、seal、源码 witness、稿件、claim 与 novelty 索引完成复核，`VALID_STATIC_RECEIPT_R017`。
- r016 历史状态仍为 `PROTOCOL_DRIFT_R016`；数值仅接受为 `EXPLORATORY_CORE_SUPPORT_R015`。未训练、推理、重拟合、重打分或修改 r014-r016、活动稿及 `dis/B.md`。报告：`dis/server_reports/orientbench-c-r017-20260808.md`。

## [2026-08-08 21:14--21:19 PDT] 来源: Codex

### r018 静态终结裁决

- 从 `origin/main` fast-forward 拉取控制提交后执行 r018；未重跑 bootstrap、训练、推理、重拟合、重打分或修改稿件。
- 三元 bootstrap、support/gate、canonical split 集合、feature production 微测试、稿件索引和 r017 Git/provenance 全部完成；裁决为 `VALID_STATIC_ADJUDICATION_R018`，数值仅保留 `EXPLORATORY_CORE_SUPPORT_R015`。
- r017 历史状态固定为 `PROTOCOL_DRIFT_R017 / FAIL_AUDIT_IMPLEMENTATION_R017`。r016 summary metadata 为 `SOURCE_FIELD_ABSENT`；sentinel 纠正为通过，association-margin single-candidate 与 doubled-angle 保留真实实现偏差。
- 关键产物：`dis/server_reports/orientbench-c-r018-20260808.md` 与 `p3_selector/static_adjudication_r018/`。未触发停止条件；下一步仅等待新正式指令。

## 2026-08-09 02:06:18 PDT — r019 prelabel 时间锁（Codex 执行）

- 指令来源：远端 `main` 的 `dis/sug.md`，round `orientbench-c-r019-20260809`。
- 执行动作：HTTPS fast-forward；完成无标签 preflight、production 微测、两单元 50-image smoke、Core source-only LODO/功效/唯一模型拟合、DOTA 两单元顺序 4-GPU 三视图全量前向、prediction-only feature/score、完整 mother draws 与 prelabel seal。
- 关键产物：`p3_selector/deployable_proxy_r019/prelabel/` 与 Git-ignored `outputs/persistent_artifacts/orientbench_r019/prelabel/`。
- DOTA target label access count：0；停止条件：未触发。
- 下一步：仅在 prelabel commit 经 HTTPS 推送且远端 `main` 精确确认后，执行唯一 label attach、统计与独立 validator。

## 2026-08-09 02:16:10 PDT — r019 完整执行结果（Codex 执行）

- prelabel commit `7601852f5527b6feaee306bddd21c1784dbc0f95` 已经 HTTPS 推送并与远端 `main` 精确一致后，才读取 DOTA 标签。
- 完成 fresh GT attach、official AP parity、两个 evaluation units 的 10,000 次同步 mother-scene bootstrap、standalone guard、独立 raw/GT/score/draw 重算及负例。
- 科学裁决：`FAIL_EXTERNAL_DOTA_EQS_RC_R019`。EQS 相对 linear 的 aggregate Delta_NRC 为正且区间过零门槛，但 EQS 明确弱于 standalone guard，因此触发预注册科学 FAIL；这属于完整执行，不是早停。
- 标签阶段发生两次不改变冻结 estimand/bytes 的工程重试：默认 annotation 路径不存在；随后 BaseDataset 序列化清空 `data_list`。最终仅以 manifest 路径和 `serialize_data=false` runtime adapter 复放同一封存程序。
- 关键产物：`p3_selector/deployable_proxy_r019/results/`、`p3_selector/deployable_proxy_r019/docs/protocol_closure_r019.md`、`dis/server_reports/orientbench-c-r019-20260809.md`。
- 未训练、未修改 thresholds 或 D_cal/D_audit、未改 `dis/B.md`、未启动 r020；下一步等待 C 拉取验收并据实收缩定位。

## 2026-08-09 20:51--21:33 CST — 顶刊可行性审计（Codex 执行）

- 指令来源：远端 `main` 的活动 `dis/sug.md`；round `orientbench-c-topjournal-feasibility-20260809`。HTTPS fast-forward 后完成启动预检，runtime 起始不存在，`dis/B.md` blob 保持固定。
- Track M 完整盘点 Core A-F、固定 score、unique-threshold AUGRC/risk-coverage 和 10,000 次同步 cluster bootstrap；最终为 `METRIC_REVERSAL`。
- Track D 四候选全部穷尽：AI-TOD-R=`LICENSE_BLOCKED`、UAV-OBB=`MISSING_ASSET`、ShipRSImageNet=`LICENSE_BLOCKED`、ICDAR-MLT=`CONTAMINATED`；联合 gate=`FAIL_TO_MEASUREMENT_ONLY`。
- 独立 validator 从 raw sealed inputs 重算通过；score byte、cluster delete、fake prior hit、manifest hash 四项隔离 mutation 均被 nonzero exit 拒绝。关键报告：`dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`；runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/`。
- 完成分类为 `FULL_COMPLETION`，无 omitted phase、无技术早停。未使用 GPU，未下载数据集/模型，未训练、推理或产生新目标域 outcome；未修改 thresholds、D_cal/D_audit 或 `dis/B.md`。下一步按 gate 仅进入 measurement-only writing。

## 2026-08-10 10:36 CST — 项目删除候选只读审计（Codex 执行）

- 指令来源：用户要求审核当前项目中可删除内容；本轮只读盘点，未删除、移动或覆盖任何文件。
- 项目占用约 34 GiB，其中 `outputs/` 约 27 GiB、`top_journal_v3_reaudit_055/` 约 5.7 GiB、Git objects 约 567 MiB。
- 可直接清理的仅为约 0.9 MiB Python caches、空 `.dist_test`、约 29 KiB 旧备份/根日志、521 个失效 FAIR1M 图片软链接及若干空目录，实际回收空间很小。
- `orientbench_r010` 与 `orientbench_r011` 有约 2.349 GiB 字节一致的大文件，但 r010 是历史可复算输入且受旧冻结资产保留规则约束；仅列为经用户批准后可归档/删除的候选。K2 direct-regression 失败 checkpoint 约 0.828 GiB，同样需批准后处理。
- `risk_logs`、052 两个大表、K2 正式 checkpoint、m069、r014、r019 法证和本轮 feasibility runtime 均仍被脚本、manifest 或科学 lineage 引用，不建议删除。未触发停止条件；下一步等待用户指定清理等级。

## 2026-08-10 14:18 CST — `/dev/shm` 同名项目删除可行性审计（Codex 执行）

- 指令来源：用户要求核查 `/dev/shm/cqc/pro/study` 中同名项目是否可删除；本轮只读，不删除、不移动、不停止进程。
- 实际对象为 `/dev/shm/cqc/pro/study/GeoStructDOTA`，约 50 GiB，不是 OrientBench。其代码仓库停在旧 `master` 初始提交，而持久化 `/home/.../GeoStructDOTA` 是更新的 `main`，两者不能按完整副本处理。
- 对比发现 shm 中约 3.228 GiB data 和 23.008 GiB logs 在持久化项目没有同相对路径文件；另有 3 个同路径文件尺寸不同。持久化副本尚不完整，直接删除会丢失约 26.236 GiB 唯一资产。
- PID 2196475 为从 shm 目录发送数据的远端 rsync，已运行约 1 天 4 小时；5 秒内文件偏移继续增长，确认仍在活动。删除会破坏正在进行的迁移。
- 结论：当前整个 shm GeoStructDOTA **不可删除**。只有 rsync 结束、目标端完成 HEAD/硬链接/软链接/关键 hash/文件全集验收后才能重新裁定；此时也只允许先删 caches，科学 data/logs 需逐项确认。

## 2026-08-10 14:38 CST — `/dev/shm/cqc/orientbench` 精确路径审计纠正（Codex 执行）

- 指令来源：用户纠正目标路径为 `/dev/shm/cqc/orientbench`；上一条 GeoStructDOTA 审计不是本次所问对象，本条以精确路径重新核查。
- 该目录约 88 MiB，不含 Git 仓库，仅含预测 scratch：3 个 DIOR-R raw pickle 及指向持久化 GT/schema/data 的有效软链接；无断链。
- 3 个 raw pickle 已逐文件与 `outputs/persistent_artifacts/orientbench_v2/DIOR-R/{22,61,3}/raw/` 比对，大小与 SHA-256 全部一致，持久化副本齐全；最新项目文档也将该目录定义为非持久 scratch。
- 未发现读取该路径的训练、推理或评估进程；仅 PID 2594937 的交互式 VS Code shell 以该目录为当前工作目录。
- 结论：科学资产层面可删除整个 `/dev/shm/cqc/orientbench`，预计释放约 88 MiB；删除前仅需让 PID 2594937 对应终端离开该目录或关闭终端。本轮未执行删除。

## 2026-08-10 17:45 CST — 迁移前清理审计与新服务器 Codex 交接（Codex 执行）

- 指令来源：用户要求先审计项目内可删除内容，未授权前不得操作；同时要求生成迁移到相近服务器后的 Codex 接手文档。
- 本轮未删除、移动、覆盖或压缩任何项目资产，未训练、推理、评估或重算科学结果；仅完成 34 GiB 工作区、Git/ignored 资产、外部数据、环境、软链接和最新科学裁决的只读盘点。
- 新权威交接文档：`docs/server_migration_handoff_20260810.md`；它取代 2026-07-27 旧报告作为当前迁移入口，并记录低风险清理候选、约 6.5 GiB 条件冷归档候选、必须迁移资产、恢复/校验步骤和 Codex 接手顺序。
- 关键 blocker：远端 main 与本地引用需 fetch 后闭合；外部 `pth_data/readme.md` 当前缺失；`mr_dev1x` 实体位于 `/dev/shm` 且 editable ai4rs source 当前缺失；522 条 FAIR1M 派生图片链接失效。
- 最新科学 gate 保持 `FAIL_TO_MEASUREMENT_ONLY`；当前 `dis/sug.md` 已执行完，不得在新服务器重跑。未触发科学停止条件；迁移放行需先解决上述物理/Git/环境 blocker，并等待用户授权清理级别。

## 2026-08-10 23:23 CST — 新服务器 Codex 接管验收（Codex 执行）

- 指令来源：用户说明项目由硬件配置基本相同的其它服务器迁入，要求 Codex 接手；若缺少 Conda 环境，优先复用现有环境。
- 执行动作：按 `AGENTS.md` 和 `docs/server_migration_handoff_20260810.md` 仅做 Git、文件、冻结哈希、数据路径、baseline、环境、硬件、后台进程和最新 sealed evidence 的只读审计；未启动训练、推理、bootstrap、下载或新目标标签访问。
- 科学状态：重新确认最新权威结果为 Track M=`METRIC_REVERSAL`、joint gate=`FAIL_TO_MEASUREMENT_ONLY`；使用 `pcp-obb` 对 `top_journal_v3_reaudit_055/feasibility_gate_20260809/validate_feasibility.py --no-write` 执行独立复核，结果 `PASS`，未改 sealed evidence。
- 冻结资产：`AGENTS.md`、`configs/thresholds.yaml`、`dis/sug.md`、最新 server report、feasibility evidence manifest、10 个 D_cal/D_audit split 的 SHA-256 均与迁移报告一致。项目约 34 GiB，43,486 个普通文件、3,841 条软链接；五个登记数据集根目录和 `third_party/ai4rs` 均可读。
- Baseline：`/home/rspip/cqc/pro/study/pth_data/readme.md` 为 89,032 bytes，SHA-256=`eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c`。74 条记录（68 valid）的 pth/log/config 均存在；74 个 pth 和 log 的登记哈希前缀全部匹配。54 个 active config 与 readme 中历史 config 哈希不同，但 `PORTABILITY.md` 已登记 2026-05-24 的可移植性改写，因此使用 baseline 时必须记录当前 config 实际 SHA，不能把 readme 的旧 config hash 当作当前文件哈希。
- 环境复用：不新建 Conda 环境。新框架统计/只读验证暂用持久化 `pcp-obb`（Python 3.10.20、torch 2.4.1、mmrotate 1.1.1；本次 validator 已通过）；精确 ai4rs 框架可用持久化 `cqc-good-be` 加只读源码 `PYTHONPATH=/home/rspip/cqc/pro/study/third_party/ai4rs`，已核验 Python 3.10.20、torch 2.4.0+cu121、mmengine 0.10.7、mmcv 2.2.0、mmdet 3.3.0、mmrotate 1.0.0rc1，源码 commit=`6095d3a3155570324e9e01c88cd2e4a3b55ae7c3` 且工作树干净；legacy 0.x 资产保留使用持久化 `mr`。未安装或修改任何包。
- 迁移未闭合项：外部 `pth_data` 实际是指向 `/dev/shm/cqc/pro/study/pth_data` 的 25 GiB 软链接，尚非持久化资产；522 条已知失效链接仍存在（521 条 FAIR1M prediction image 链接、1 条 top-journal data-prep 链接）；原 `mr_dev1x` 未持久化恢复。Git 为本地 `main` HEAD `cdf764c5a974030739a9992079bedb8b970fb2a7`、缓存 `origin/main` `ef1b2cd93cfb2ebcb8625befd15bf561add2c10e`，显示 ahead 6；SSH alias 无法解析且 HTTPS 凭证不可用，故未 fetch/pull/push。保留既有 `claude_code_and_supervisor.md` 修改和未跟踪 `docs/server_migration_handoff_20260810.md`，未覆盖或清理。
- 资源状态：4×A30 24 GiB 可识别，但当前均被其它项目占用约 2.4 GiB 且 GPU 利用率约 52%–76%；本轮未占用 GPU。主盘剩余约 40 GiB（92% used），不足以在未规划空间的情况下直接把 25 GiB `pth_data` 从 `/dev/shm` 复制回持久盘。
- 是否触发停止条件：未触发新的科学早停；维持既有 `FAIL_TO_MEASUREMENT_ONLY` 裁决。迁移层面尚不满足“可无缝启动新实验”，因此在 `pth_data` 持久化、Git 关系闭合及具体任务授权前，不启动训练、推理、Deployable、Track A 或新数据集工作。
- 关键产物路径：`docs/server_migration_handoff_20260810.md`、`dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`、`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/`、`/home/rspip/cqc/pro/study/pth_data/PORTABILITY.md`。
- 下一步建议：优先由用户/运维决定 `pth_data` 的持久化落点并恢复 Git 凭证/远端关系；在相关复放任务真正需要前，不新建 Conda 环境，也不为 522 条历史失效链接擅自改 split 或重定向。

## 2026-08-10 23:43 CST — Git 闭合与迁移历史软链接影响审计（Codex 执行）

- 指令来源：用户要求暂不处理 `pth_data` 持久化，只要当前可用；继续连接 Git、判断是否闭合，并完整调研历史软链接是否影响项目。
- Git 执行动作与结果：GitHub connector 无法读取 private repo，改用服务器既有 `gh` HTTPS 凭证；将仓库级 `origin` 从失效 SSH alias 改为 `https://github.com/ziyu24/orientbench.git`，未改全局凭证。远端 `main` 是本地旧 HEAD 的严格后代，无分叉，执行 `git pull --ff-only origin main` 后由 `cdf764c5a974030739a9992079bedb8b970fb2a7` 快进 4 commits 到 `9588a095cc459acbd5de54d756343ad7db945956`。当前 `HEAD == origin/main == HTTPS ls-remote main`，branch/upstream/remote 拓扑已闭合；保留迁移前既有 `claude_code_and_supervisor.md` 修改与未跟踪 `docs/server_migration_handoff_20260810.md`，未 stash/reset/clean/覆盖。
- 远端科学状态纠正：新拉取的 `dis/sug.md` 将 2026-08-09 feasibility 执行定性为 `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`，其数值为 `DESCRIPTIVE_UNVERIFIED`，原 `FAIL_TO_MEASUREMENT_ONLY` 仅为 `UNVERIFIED`；新的 receipt-only round 尚未执行。本轮没有擅自启动 receipt；其合同要求启动时 worktree/index 干净，而当前保留有上述既有改动。
- 软链接盘点：项目内恰有 522 条失效软链接。521 条是 `outputs/predictions/FAIR1M-v1.0/_root/images/*.png` 的历史 521-image partial farm；1 条是 `top_journal_v3_reaudit_055/data_prep/FAIR1M_val20/images` 的整目录链接。它们都指向已不存在的 `/home/rspip/cqc/data/dataset/fair1m1.0/split/val_20/images`；当前整个 FAIR1M 派生 `split/` 为空，不只是链接目标改名。
- 恢复性核验：冻结 `annfiles_dotaformat` 保留 4,362 个 tile stems，覆盖 3,298 个 raw image IDs；对应 raw TIFF 与 XML 均为 3,298/3,298 存在。按历史 `p1024_o200`（1024 window、200 overlap、824 step）和 BGR padding `[104,116,124]` 从 raw 数据只读重建时，生成的 tile stem 集合与冻结 4,362 个 annfile 集合完全一致（missing=0、unexpected=0）；在人工标注 manifest 的 177 个 FAIR1M 样本上，重建 PNG SHA-256 与 crop SHA-256 均为 177/177 精确匹配。因此 val_20 的身份、坐标和像素字节可精确恢复，不需要修改 frozen split 或替换数据集。
- 影响判断：断链不阻塞当前 stored matched predictions / GT / parquet / score 等只读测量证据，也不进入当前禁止 inference 的 receipt-only 流程；因此它们不是当前 receipt blocker。它们会阻塞任何新的 FAIR1M dataset inventory、forward/inference、TTA、AP/fullval 重算、人工标注 crop 再生成，以及 train_80/val_20 训练复放；其中 4,362-image 目录链接是实际 replay 依赖，不能当作纯装饰。结论为“当前证据消费不受影响，但 FAIR1M 图像级复算尚未闭合”。
- 边界与产物：按用户要求不再把 `pth_data` 持久化作为本轮 blocker；未修链、未生成 4,362 张图片、未训练/推理/评估、未修改 thresholds、D_cal/D_audit、formal 标签或 frozen 资产。关键记录为本文件、`dis/sug.md`、`top_journal_v3_reaudit_055/data_prep/FAIR1M_val20/annfiles_dotaformat/` 与 raw 根 `/home/rspip/cqc/data/dataset/fair1m1.0/raw/train/`。
- 是否触发停止条件：未触发新的科学早停。Git 闭合完成；软链接问题被定级为可精确修复的 FAIR1M replay blocker，而非当前 sealed evidence blocker。
- 下一步建议：保留现有断链作为历史 lineage；只有在明确授权新的 FAIR1M 图像级复放时，才依据冻结 4,362 stem 集合原位重建 `val_20/images` 并做全量 manifest/SHA 验收，禁止静默改指向其它 split。当前先处理用户下一项任务，不自动执行新 receipt 或数据重建。

## 2026-08-11 09:35 CST — feasibility receipt 拉取与 preflight 异常停止（Codex 执行）

- 指令来源：用户要求“现在拉取，执行sug.md”。
- 执行动作：完整读取 `AGENTS.md`、迁移交接、`pth_data/readme.md` 和活动 `dis/sug.md`；通过 HTTPS 执行唯一允许的 `git pull --ff-only origin main`，结果 already up to date。冻结的 pre-pull/post-pull、upstream 和 HTTPS remote main 均为 `9588a095cc459acbd5de54d756343ad7db945956`；`dis/B.md` blob/diff 与固定祖先链检查通过。
- 停止条件：pull 后工作树仍有本轮前既存的 `M claude_code_and_supervisor.md` 与 `?? docs/server_migration_handoff_20260810.md`，违反 receipt 强制 clean preflight，且合同禁止 stash/clean/restore/隐藏；既有 source runtime 对当前用户仍可写，又违反不可写 preflight。两项均不得在本轮修复绕过，因此科学验收异常停止。
- 未执行：Track M/Track D、bootstrap、pinned reference、validator、四项 mutation、joint gate、训练、推理、GPU、下载、安装、新 target outcome、annotation 内容读取或改稿。
- 关键产物路径：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`；没有创建新 code root 或 runtime root。
- 是否触发停止条件：是，`ABNORMAL_PREFLIGHT_FAILURE`；不是科学 `INSUFFICIENT_ASSETS`，没有发出 Track M 状态或 joint gate。
- 下一步建议：本轮路径不得复用。仅能在本轮之外先由用户/监督员处置既有工作树变化及 source runtime 权限，再下发新 round id 和全新路径的正式 receipt 合同；不得自动重跑本轮。

## 2026-08-11 10:17 CST — 迁移现场 housekeeping 授权与监督端通知（Codex 执行）

- 指令来源：用户明确授权处置迁移后的 dirty worktree 与旧 source runtime 权限，并要求向监督端说明项目已经迁移。
- 给监督端的迁移事实：当前执行现场已经是迁移后的新服务器，项目仍位于 `/home/rspip/cqc/pro/study/orientbench`；GitHub 通过既有 `gh` HTTPS 凭证可用，`main`、`origin/main` 与 HTTPS remote main 在整理前均为 `9588a095cc459acbd5de54d756343ad7db945956`。本次 receipt 启动失败来自迁移遗留的未提交日志/交接文档及旧 runtime 可写权限，不是新的科学失败；Track M、Track D、bootstrap、validator、mutation 与 joint gate 均未运行。
- housekeeping 边界：这是失败 receipt 之外的迁移整理，不修复、不覆盖、不复用 `orientbench-c-topjournal-feasibility-receipt-20260809`。保留异常报告原始字节；将监督日志、迁移交接和异常报告作为一次 housekeeping commit 发布，使下一轮可以从干净工作树启动。
- 历史报告发布说明：`git diff --cached --check` 仅对已封存异常报告末尾的新增空行给出 1 项 warning；这正是旧 receipt 在 seal 后停止提交/推送的 post-seal 失败。housekeeping 不修改该报告字节，以原样保留失败证据；其它两项提交内容没有 whitespace error。
- source runtime 权限闭合：精确目标为 `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/`，约 302 MiB，含 74 个文件、5 个目录、0 条软链接，执行前无打开文件。经用户授权原位执行 `chmod -R a-w`；可写对象由 79 降为 0，74/74 文件仍可读，根目录 mode 由 `775` 变为 `555`。内容树 SHA-256 聚合值前后均为 `2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43`，只改变权限，未改变科学字节。
- 关键产物路径：`docs/server_migration_handoff_20260810.md`、`dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`、`claude_code_and_supervisor.md`、`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/`。
- 是否触发停止条件：未触发新的科学早停；旧 receipt 保持 `ABNORMAL_PREFLIGHT_FAILURE`，不得改写为完整执行。
- 对监督端的下一步请求：在本 housekeeping commit 成为远端新 `main` 后，请基于该新 SHA 下发全新的 `dis/sug.md`，必须使用新的 `round_id`、code root、runtime root 和 server-report path；不得复用已失败轮次或其路径。新合同还应明确把本迁移服务器和已只读 source runtime 作为启动现场。

## 2026-08-11 11:31 CST — receipt2 mandatory reference provenance 异常停止（Codex 执行）

- 指令来源：用户要求拉取并执行；HTTPS fast-forward 后 active round 为 `orientbench-c-topjournal-feasibility-receipt2-20260810`。
- Preflight：`main` 拉取至 `6d8892a3793b2efcd8373ce8d509a6cf9872427c`；HEAD/upstream/HTTPS remote 三方一致、工作树干净。规则/readme、B blob/diff、固定祖先链、receipt1 report/archive、source runtime 只读全树与 canonical SHA、新 code/runtime/report 路径不存在均闭合。
- 停止条件：合同第 5.3 节要求的 pinned `IML-DKFZ/fd-shifts@c4467aec134e99691359da209f811d91283fc1e3` 及 `rc_stats.py`/`rc_stats_utils.py` 在允许根内不存在。实际枚举 33 个本地 Git repo，目标 commit holder=0；两个源文件命中=0。仅有合同/计划/旧 generator 的文本引用，不能作为 dynamic source identity。download/installation 均未授权，因此不得补拉或硬编码通过。
- 执行裁决：`ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE`；这不是 Track M=`INSUFFICIENT_ASSETS`，Track M/Track D/joint gate 均未发出。未运行 10k bootstrap、validator、mutation，也未创建 receipt2 code/runtime。
- 关键产物路径：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt2-20260810.md`；旧 source runtime 和 sealed assets 未修改。
- 是否触发停止条件：是，mandatory validator/provenance phase 无法闭合；科学验收异常停止。
- 下一步建议：本轮路径已消费。需在 receipt 外预先配置精确 pinned source Git object/checkout，再由用户/监督端发布新的 round id 与全新 code/runtime/report 路径；不得复用 receipt2 或在本轮下载修复。

## 2026-08-10 20:39 PDT — 迁移现状补充通知与后续合同请求（Codex 执行）

- 指令来源：用户明确要求再次向监督端说明项目已经迁移，并表示后续将亲自沟通，要求下一轮执行合同不要设置得过度死板。
- 给监督端的迁移说明：当前执行现场是迁移后的新服务器，项目根保持为 `/home/rspip/cqc/pro/study/orientbench`。Git HTTPS 链路已经恢复并闭合；本通知前 `main == origin/main == a2da27559dc6eb005f02efb9b3b34584ebed57b8`。既有 Conda 环境按迁移规则优先复用，未因迁移新建环境。
- 资产现状：旧 feasibility source runtime 已完成只读保护，74 个文件全部可读、内容树 canonical SHA-256 仍为 `2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43`；迁移没有改变其科学字节。`pth_data` 按用户指示暂不做持久化迁移，只要现有路径可用即可。历史 522 条 FAIR1M 失效软链接只影响未来图像级 replay，不影响当前 sealed evidence 的读取。
- receipt2 定性澄清：`ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE` 是合同要求精确本地 pinned `fd-shifts` 源码、同时禁止补拉所造成的执行性 provenance 阻断，不是迁移损坏、Git 未闭合、软链接污染或新的科学负结果；Track M、Track D 和 joint gate 均未裁决。
- 对监督端的请求：请在用户后续说明后，按迁移后的实际可用环境重写下一轮合同，保留 frozen thresholds、D_cal/D_audit、formal 标签和科学 provenance 等必要硬边界，但避免把可安全补齐的工具依赖写成不可恢复的整轮失败条件。若仍需要 pinned `fd-shifts`，应在 receipt 外预置源码，或在新合同中明确授权从官方仓库获取并校验固定 commit。
- 执行动作与边界：本次只追加监督记录，不改 receipt2 报告、旧 runtime、冻结证据或科学裁决，不自行解释为用户已经正式解除现有约束，也不擅自重跑 receipt2。
- 关键产物路径：`claude_code_and_supervisor.md`、`docs/server_migration_handoff_20260810.md`、`dis/server_reports/orientbench-c-topjournal-feasibility-receipt2-20260810.md`。
- 是否触发停止条件：未触发新的科学停止条件；当前等待用户与监督端更新控制面并签发全新 round。
- 下一步建议：监督端确认迁移事实和依赖获取边界后，使用新的 round id、code root、runtime root 与 report path 下发 receipt3；不得复用 receipt2 路径。

## 2026-08-10 20:49 PDT — 新指令拉取检查（Codex 执行）

- 指令来源：用户要求“拉取，执行”。
- 执行动作：在干净 `main` 上通过 HTTPS 两次执行 `git pull --ff-only origin main`，均返回 `Already up to date`；同时核验 GitHub `refs/heads/main`、本地 HEAD 与 `origin/main` 均为 `9e0352aef88d062a15a4db55e3d948ae84d9f700`。
- 控制面结果：远端尚未下发新的 receipt3；活动 `dis/sug.md` 仍为已消费且不可复用的 `orientbench-c-topjournal-feasibility-receipt2-20260810`，文件 SHA-256 仍为 `fd532c1f12e713e6d9c55d6f37f109fb6d41afbf351ace7801cab6c3e6573e1d`，对应 receipt2 报告路径已经存在并已发布。
- 执行边界：未重跑 receipt2，未覆盖其报告或路径，未启动 Track M、Track D、validator、mutation、训练、推理、下载或新科学计算。
- 关键产物路径：`dis/sug.md`、`dis/server_reports/orientbench-c-topjournal-feasibility-receipt2-20260810.md`、`claude_code_and_supervisor.md`。
- 是否触发停止条件：本次没有可执行的新 round；按现有合同的 non-reusable/path-collision 规则停止，不形成新的科学裁决。
- 下一步建议：请监督端在用户所述的迁移与依赖灵活性要求纳入控制面后，推送使用全新 round id、code/runtime/report 路径的 receipt3；服务器收到新提交后再拉取执行。


## 2026-08-11T02:59:04.265648-07:00 — receipt3 迁移后执行闭环

- 指令来源：用户“拉取，执行”；适用最高规则为当前 `AGENTS.md` 与 `dis/sug.md` receipt3 合约。
- 迁移说明：项目已由原服务器迁移至当前服务器；硬件口径相同，复用现有 `pcp-obb` conda 环境，未安装依赖；`pth_data` 仅按只读登记使用。该事实已同步写入监督端固定日志，后续授权应以迁移后的当前服务器现场为准。
- 执行动作：main 从 `35358b5fef838b178aff0e16470ebe0117cab687` fast-forward 至 `6e0ea32bc3d1c13aa051f8abd9c9e37e5996d025`；固定 fd-shifts commit 首次 HTTPS fetch 成功；完成 A-F raw 重算、完整曲线、10,000 bootstrap、独立 validator、Track D 与四个 isolated mutation。
- 关键产物：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811`；`top_journal_v3_reaudit_055/feasibility_receipt3_20260811`；`dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md`。
- 决策结果：Track M=`METRIC_REVERSAL`；Track D={"AI-TOD-R": "LICENSE_BLOCKED", "ICDAR-MLT": "CONTAMINATED", "ShipRSImageNet": "LICENSE_BLOCKED", "UAV-OBB": "INCOMPATIBLE_ANGLE_CONTRACT"}；joint gate=`FAIL_TO_MEASUREMENT_ONLY`。
- 停止条件：科学负向条件已触发，按冻结 gate 收缩为 measurement-only；未启动任何方法设计、下载、安装、GPU、训练、forward、推理、新 outcome、annotation 内容访问或改稿。
- 下一步建议：保持 measurement-only 路线；如需恢复方法设计，必须由用户/监督员另起新协议处理候选数据的 license、angle contract、资产与污染问题，不在本轮自行扩展。

## 2026-08-11 22:30 CST — r020 measurement-validity preflight 异常停止（Codex 执行）

- 指令来源：用户要求“拉取，执行”；活动合同为 `orientbench-c-r020-measurement-validity-20260811`。
- 执行动作：从本地 `594654a95d50b1f14b87252698911cc3fc583b03` 同步到 `6855080d7674da4b4da54ab4d9aeab550974c69e`，完整读取 `dis/sug.md`，随后仅执行 Git、路径、protected B、receipt3 report blob、ignore 与 CPU 拓扑预检；未打开 26 个科学输入。
- 严重异常一：同步实际使用 `git fetch origin main` 加 `git merge --ff-only origin/main`，虽然结果是干净 fast-forward 且 configured origin 为目标 HTTPS 仓库，但不满足合同限定的唯一 literal `git pull --ff-only https://github.com/ziyu24/orientbench.git main`；该方法偏差不能事后用 no-op pull 修复。
- 严重异常二：迁移后服务器实际暴露 112 个 online/affinity/cgroup logical CPUs（`0-111`），不是合同要求的恰 48。固定 39 workers 在 `N=112` 分母下最大只能达到 34.82% job CPU，数学上无法满足 60%–80% telemetry 门槛；未擅自重定义 N、限缩硬件或修改 worker/阈值。
- 执行裁决：触发 `FAILURE_EARLY_STOP / NOT_ADJUDICATED`，`sug_genuinely_exhausted=false`。未生成 A/B、Comparator C、bootstrap、witness、四态科学 gate、mutation、manifest 或 external receipt；不得把本轮解释为科学 FAIL/INCONCLUSIVE。
- 关键产物路径：`dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md`、`outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/preflight.json`、`claude_code_and_supervisor.md`。
- 是否触发停止条件：是，Git synchronization method 与 CPU topology/resource-contract 双重 preflight defect；没有触发或裁决科学早停。
- 下一步建议：监督端/C 必须基于迁移后 112-logical-CPU 现场签发全新 round id 与全新路径，并显式协调 N、worker 数和 telemetry 门槛；同时将“先拉取才能看到新合同”的同步现实纳入 Git 规则。r020 路径已消费，不得复用。

## 2026-08-11 22:36 CST — r020 异常原因说明与修正请求（Codex 汇报）

- 指令来源：用户追问“什么异常”。
- 原因说明：异常发生在科学输入打开前。第一项是 Codex 在读取新合同前以 `git fetch origin main` 加 `git merge --ff-only origin/main` 完成同步，而新合同事后要求唯一使用显式 HTTPS literal 的 `git pull --ff-only`；这是执行端流程偏差。第二项是新服务器实际暴露 112 logical CPUs 与 affinity `0-111`，合同却固定要求 `N=48`、39 workers 且 job CPU 60%–80%；按合同公式，39/112 最大仅 34.82%，无法同时满足。
- 影响边界：不是科学失败，也不是数据、软链接、Conda、GPU 或 receipt3 资产损坏；r020 未读取 26 个科学输入，未运行 A/B、bootstrap、mutation 或 gate，正式状态只能是 `NOT_ADJUDICATED`。
- 关键产物：`dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md`、`outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/preflight.json`。
- 停止条件：已触发技术/审计早停；本轮路径不可复用。
- 下一步建议：C/监督端下发全新 round 与路径；Git 规则应允许服务器先用显式 HTTPS literal 拉取再读取合同，CPU 规则应改为实际 `N=112` 并重算 worker/利用率，或明确授权在任务入口固定 48-CPU cpuset 并以 48 为审计分母。

## 2026-08-11 23:00 CST — 用户授权 r020 务实恢复与全量结果（Codex 执行）

- 指令来源：用户明确要求“不要那么死板啊，抓紧搞”；据此不覆盖已发布的 preflight 异常证据，改以 recovery evidence 继续完成科学分析，但不伪造原 formal receipt 已闭合。
- 执行动作：使用现有 `pcp-obb` 环境；将任务 affinity 固定为 CPU `0-47`，用 39 workers 执行完整 A-F、五项冻结消融、3 contrasts × 3 endpoints、10,000 cluster bootstrap、270/135 分离 Holm 与固定 witness/gate。未使用 GPU、训练、forward、inference、下载、安装、annotation root、learned EQS、receipt3 派生科学输入或新 target。
- 输入与 join：26/26 frozen inputs 的 bytes/SHA-256 全匹配；六个 D_audit base cohort 对 features/scores 均 missing=0、drop=0、one-to-one。base rows A-F=`43848,47887,47881,26108,157586,192249`；AR>=2.1 main rows=`25080,27682,27410,15132,101160,120947`。
- 决策结果：recovery candidate=`INCONCLUSIVE_MIXED`。共有 unit witness=5、dataset witness=2；全部局限于 DIOR 的 `NORMALIZED_ALL_AR × linear_source_frozen`，对应 A/B/C 的 AUGRC、A/C 的 Risk@70 及两个 DIOR aggregate。FAIR1M、SODA-A 无同 signature witness，且没有 signature 满足 >=2 datasets、>=4/6 units 与 SODA dataset+unit 条件；`passing_signatures=[]`。
- 独立验证：validator 重新计算全部 point endpoints、4,050,000 hypothesis replicates 的 centered p、两套 Holm、witness predicate 和 manifest，结果 `PASS`；不是仅复读 generator gate。
- 关键产物：`top_journal_v3_reaudit_055/measurement_validity_r020_20260811/RECOVERY_REPORT.md`；`outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/recovery_full_r10000/`（177 MiB）；主运行 581.30 秒；smoke 子目录只作工程验证。
- 是否触发停止条件：没有技术或资产失败；科学候选为混合不确定，不能升为 PASS，也不能写成纯 null。原 r020 formal status 仍为 `NOT_ADJUDICATED_PENDING_SUPERVISOR`，等待 C post-pull review。
- 下一步建议：监督端应采用本 recovery bundle 独立复核并决定是否签发正式状态；当前不换 gate、不加 target、不复活 EQS，也不据 DIOR-only AR-domain sensitivity 重启顶刊实验循环。

## 2026-08-11 23:10 CST — `sug.md` 完成度澄清（Codex 汇报）

- 指令来源：用户询问“sug.md执行完了？”。
- 明确答复：严格按活动 `dis/sug.md` 的 formal audit contract，未执行完毕，且原 r020 已因 preflight defect 被正式标为 `FAILURE_EARLY_STOP / NOT_ADJUDICATED`；后续用户授权完成的是 pragmatic recovery，不能倒签为原 receipt closure。
- 已完成部分：26 个 frozen inputs 身份、A-F D_audit strict join、long-side/AR/risk 重算、五项消融、3 contrasts × 3 endpoints、10,000 cluster bootstrap、270/135 Holm、witness/gate 与独立数值/结构验证；候选科学状态 `INCONCLUSIVE_MIXED`。
- 尚未按原合同闭合部分：data-before-code seal、两套完全独立 clean-room A/B、Comparator C 全 replicate parity、live application hash-chain 与 strace 双向 access closure、pinned fd-shifts reference、六项固定 mutation 时序、acyclic runtime/report seal、原 round 唯一 result commit、postseal external receipt 及 C post-pull formal adjudication。
- 关键产物：`top_journal_v3_reaudit_055/measurement_validity_r020_20260811/RECOVERY_REPORT.md`、`outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/recovery_full_r10000/`。
- 停止条件：formal r020 路径已消费且不可复用；recovery 科学计算本身正常完成。
- 下一步建议：若目标是“把 sug.md formal closure 真正做完”，监督端需基于 recovery 结果签发全新 round id/paths，并把迁移后的 Git/CPU 规则改成可执行版本；不能继续声称旧 r020 已完整闭合。

## 2026-08-11 23:27 CST — r020 recovery 独立 B、Comparator、reference 与 mutation 闭包（Codex 执行）

- 指令来源：用户要求“继续推进”；HTTPS 拉取后远端仍无新 round，因此仅在用户已授权的 pragmatic recovery 范围补最有价值的可恢复审计债，不覆盖旧 abnormal report、不倒签 formal r020。
- 独立实现 B：不 import A、不读取 A rows/runtime，直接从 26 个 raw inputs 重新构造 membership、long-side angle、risk、strict joins、五项消融、point metrics 和 10,000 cluster bootstrap；使用 CPU `0-47` affinity、39 workers，216.97 秒完成，独立 gate=`INCONCLUSIVE_MIXED`、unit witness=5、dataset witness=2、passing signatures=[]。
- Comparator C：B 封存后读取 A/B；4,320,000 unit 与 2,160,000 dataset bootstrap metric cells 最大绝对差均为 0；全部 point、405 hypotheses、CI、centered p、Holm、swap、witness 与 gate 最大差均为 0。`comparator.json` SHA-256=`6d76827a8970f0f4a1e542789565a29dcad0805d3a1901a1c78655119bb03113`。
- Reference：从官方 HTTPS 恰一次获取 `fd-shifts@c4467aec134e99691359da209f811d91283fc1e3`，detached checkout clean；两 blob/raw SHA 精确匹配。完整 import 仅因现有环境缺 `loguru` 失败；AST exact-function adapter 动态读出 `AUC_DISPLAY_SCALE=1000`，四个固定向量在 `atol=1e-12,rtol=0` 通过。reference probe SHA-256=`d989c16ddc9b5dc1638e528c4efc22ed6092f253c082266925e9f63aef6d7865`。
- Mutations：六项 isolated checks 均 pristine exit=0、mutated exit=2，覆盖 raw theta、SODA mother、AUGRC origin、two-dataset gate、26-input inventory、report state token；mutation index SHA-256=`1622f62128e03322bb96f0f890f9f86a268a568626f26c0ea8e8e434218f40ae`。
- Recovery closure：统一闭包 `VALID_RECOVERY_CLOSURE`，独立 read-back validator=`PASS`，SHA-256=`30827e0f038b275b81171305908c660982a519e56aeabbb634dcfdab3953cb65`；runtime 总量约 281 MiB。
- 关键产物：`top_journal_v3_reaudit_055/measurement_validity_r020_20260811/RECOVERY_REPORT.md`、`outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/recovery_independent_b_r10000/`、`recovery_comparator_ab/`、`recovery_reference_probe.json`、`recovery_mutations/`、`recovery_closure.json`。
- 是否触发停止条件：未触发新的技术/科学停止；候选科学状态仍是 DIOR-only 的 `INCONCLUSIVE_MIXED`。历史 pre-data code seal、live app access chain、strace 双向 closure 与旧 round single-commit/postseal receipt 无法事后重建，formal 状态仍为 `NOT_ADJUDICATED_PENDING_SUPERVISOR`。
- 下一步建议：C/监督端可直接核验 recovery closure 并签发全新 formal adjudication；若坚持原始实时审计，只能新 round 从零执行，不应继续在旧 r020 路径上追加伪 formal 证据。

## 2026-08-11 23:28 CST — `sug.md` 最终完成状态再次确认（Codex 汇报）

- 指令来源：用户询问“现在sug.md都执行完了？”。
- 结论：科学计算与所有可事后独立补齐的审计项已经执行完；但严格按原 `dis/sug.md` 的时序型 formal contract，仍不能称“全部执行完”。
- 已完成：26 inputs、A-F strict join/risk、五项消融、A/B 各 10,000 bootstrap、270/135 Holm、Comparator 零差、pinned reference、六项 mutation、统一 recovery closure；candidate=`INCONCLUSIVE_MIXED`，closure validator=`PASS`。
- 永久不可在旧轮补齐：首次 scientific input open 前的 code seal、当时的 live application access hash-chain、当时的 strace 双向覆盖，以及以旧 execution_base 为唯一父提交的 single result commit/postseal receipt。这些是时间顺序事实，不能靠当前再跑或补文件变真。
- 状态边界：`VALID_RECOVERY_CLOSURE` 成立；原 r020 formal receipt 仍为 `NOT_ADJUDICATED_PENDING_SUPERVISOR`。若要求严格满足 `sug.md` 每一条，只能监督端签发新 round/新路径并从零按正确时序执行。

## 2026-08-13 00:00 CST — r021 governance integrity failure early stop（server-primary）

- 指令来源：用户交付 `orientbench-b-r021-measurement-validity-20260812` 的 dispatch/path/commit；后续明确授权本 clone 绑定 `paper.worker-id=server-primary`，并要求不因无关历史项拖延。
- 已完成：HTTPS fast-forward 至 dispatch commit `90c0037ae49f7ebe21e53a167a04ee8a6fc68d8f`；active plan/mirror blob、SHA、frozen design blob、空路径、ignore、112 logical CPU、48-CPU affinity 和 strace 可用性核验；唯一 STARTED one-file commit `f2fb8553e0565064a1fc7a7c8ec798f291629ee2` 已 HTTPS push。
- early-stop：计划内 `validate_peer_governance.py` 要求 legacy archive SHA `74ef9c...`，当前同一 dispatch 的 archive 实际 SHA `aa3d369...`，且 `MIGRATION.md` 保留前者；控制面自相矛盾。复核后按 r021 G2 将其定为 governance integrity failure，未进入 code seal 或任何科学输入读取。
- 未执行：A/B、Comparator、bootstrap、metrics、witness、gate、pinned fetch、mutation、runtime manifest、GPU、训练、forward、inference、安装或数据下载均未运行；没有 scientific number。
- 关键产物：`dis/server_reports/orientbench-b-r021-measurement-validity-20260812/STARTED.json`、`dis/server_reports/orientbench-b-r021-measurement-validity-20260812/SERVER_EXECUTION_REPORT.md`。
- 完成映射：`FAILURE_EARLY_STOP_GOVERNANCE_INTEGRITY / NOT_ADJUDICATED / execution_status=incomplete`。需 B 发布新的自洽 dispatch revision；当前 r021 路径含 STARTED，不重用为正式重执行。

## 2026-08-13 07:10 CST — r027 JPRS paper package completed（server-primary）

- 指令来源：用户要求持续监督、不得打折扣完成；活动 dispatch 为 `orientbench-b-r027-jprs-paper-package-20260813`。
- 执行动作：补齐并重算 T1--T6。AR cutoff 表覆盖 DIOR A/B/C、DOTA 两 detector 和两个 DOTA aggregate；DOTA equal-unit CI 改为每 bootstrap draw 的直接母图 cluster 重采样等权汇总。补齐 Risk@90 两域、完整八-unit 四-probe表、dataset uncertainty/MDE80、台账、主稿/补充稿、package manifest。
- 关键产物：`outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/`；`dis/server_reports/orientbench-b-r027-jprs-paper-package-20260813/SERVER_EXECUTION_REPORT.md`；两份 r027 draft。
- 核验：独立 `claim_recompute_r027.py` 通过 177/177 字段核对，涵盖 r023 七 witness 与 r026 六 hypotheses、swap、matched counts、AP parity；读回检查 AR scan 441 行、Risk@90 8 行、完整 unit 表 64 行及四数据集不确定性表。
- 是否触发停止条件：否。首版 aggregate CI 为平均单-unit CI，未作完成声称，已以直接 cluster-resample aggregate CI 替换并披露。所有 r027 新数值均 `DESCRIPTIVE`。
- 下一步建议：B/C post-pull 审阅草稿与 evidence ledger；服务器端任务已闭合，不代表投稿或论文最终定稿。

## 2026-08-13 10:15 CST — r028 corrective audit completed（server-primary）

- 指令来源：用户交付 `orientbench-b-r028-corrective-audit-20260813` 并要求建立持续监督、不得未完成即报告完成。
- 执行动作：新写并实际运行 raw-layer r026/r023 validator；六项 mutation 均通过 subprocess 真执行；构建可提交 Git 的 bundle、GT integrity、r027 `tta_localization` 修复与 post-outcome audited 的 r028 稿件。
- 关键产物：`top_journal_v3_reaudit_055/corrective_audit_r028_20260813/`、`audit_bundles/r028/`、`outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813/`、`dis/server_reports/orientbench-b-r028-corrective-audit-20260813/SERVER_EXECUTION_REPORT.md`。
- 核验：r026=96/96、r023=4,950/4,950 字段一致；所有 6 mutation 的 pristine exit=0、mutated exit 非0；bundle 19 个文件、92,680,050 bytes、manifest hash 全匹配，并以 bundle 内 r026/r023 validator 实际重放通过。
- 是否触发停止条件：否。r026 正式状态不在本轮自行改写；仍由 B/C 基于 bundle 重放裁决。无 GPU、训练、推理、下载、冻结阈值/split 或旧冻结产物修改。
- 下一步建议：B/C clone 后按 bundle 重放；稿件仅可称 post-outcome audited external replication，不能恢复 r026 旧的 preregistration/双方接受表述。

## 2026-08-13 10:35 CST — r028 remote receipt confirmed（server-primary）

- 指令来源：用户要求继续推送并完成任务。
- 执行动作：补齐 bundle 中 r023 原始 `rows.parquet` 后，以同包输入重放通过 405 hypotheses、4,950/4,950 checks；SSH 推送完成并核验 `origin/main=e675a841041b3305253b1fb8cd664f785f4b67b8`。
- 关键产物：`audit_bundles/r028/`（20 files、146,939,912 bytes）及 r028 执行报告。
- 是否触发停止条件：否；服务器 r028 已闭合。B/C clone 重放仍是独立裁决步骤。
- 下一步建议：B/C 基于该 bundle 执行复放与裁决。

## 2026-08-13 19:50 PDT — r029 bundle closure（server-primary）

- 指令来源：用户交付 `orientbench-b-r029-bundle-closure-20260813` dispatch/path/commit。
- 执行动作：按 manifest 声明原字节 force-add r028 bundle 被 ignore 的 `bootstrap.npy` 与 `dota_gt_fresh.pkl`，并从 staged Git blobs 核验全 manifest。
- 关键产物：`audit_bundles/r028/dota/bootstrap.npy`、`audit_bundles/r028/dota/dota_gt_fresh.pkl`、r029 server report。
- 是否触发停止条件：否；两对象 bytes/SHA-256 均与 kill 清单精确一致，20/20 manifest entries 一致。
- 下一步建议：C 按派发执行最终重放与裁决。

## 2026-08-13 21:22 PDT — r030 complete JPRS Markdown manuscript package（server-primary）

- 指令来源：用户交付 `orientbench-b-r030-jprs-manuscript-20260813` dispatch/path/commit，并要求搞完后给出具体路径。
- 执行动作：只读冻结 r023/r026 bundle 与 r027/r028 修正表，完成英文主稿、补充材料、四组 SVG/PNG 图及逐图脚本、逐数字 claim-check、引用证据清单和包级 validator。
- 关键产物：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/manuscript_r030/`；`outputs/persistent_artifacts/orientbench_jprs_manuscript_r030_20260813/`；r030 server report。
- 核验：abstract=223 words；References=24；numeric claim-check=1,709/1,709 PASS；package validation=15/15 PASS；禁止清单零命中；四图均完成目视核验。
- 是否触发停止条件：否。未做新科学计算、训练、推理、匹配、重采样、阈值/split/gate 修改；未使用被 r028 supersede 的旧 TTA 描述结果。
- 下一步建议：B/C 审稿与项目所有者填写作者信息、决定定稿；服务器 r030 执行已闭合。

## 2026-08-13 22:51 PDT — r031 G0 gated early stop（server-primary）

- 指令来源：用户交付 `orientbench-c-r031-circularity-asset-preflight-20260813` dispatch/path/commit，要求建立监督机制、拉取 main 并严格执行。
- 执行动作：main 纯 fast-forward 到 dispatch `98443feb40d786fb7eb8faf8f36444496fe6b2c5`；核验 active/plan 同 blob 与 SHA、`paper.worker-id=server-primary`、coordination 和只读 `pth_data/readme.md`，随后在任何科学资产检查前执行 G0 status 检查。
- 严重异常：staged index 干净，但普通工作树已有 6 个派发前未跟踪路径，位于 r028 mutation/revalidation 与 r022/r023 measurement-validity 历史目录。r031 明文规定 worktree/index 必须干净，脏树须在资产检查前早停。
- 边界动作：没有删除、移动、stash、add、修改或读取这些历史路径为科学输入；未打开 r014/r019 科学资产或四数据集标注资产；未执行 T1--T5、四项 inventory mutation 或 R032 readiness adjudication。
- 关键产物：`reports/r031_circularity_asset_preflight/preflight.json`、`validation_r031.json`、`dis/server_reports/orientbench-c-r031-circularity-asset-preflight-20260813/SERVER_EXECUTION_REPORT.md`。
- 是否触发停止条件：是，`G0_IDENTITY=EARLY_STOP_DIRTY_WORKTREE`；按冻结 completion mapping 记为 `gated_early_stop / execution_status=complete / scientific_outcome=NOT_ADJUDICATED`，不是科学失败。
- 下一步建议：项目所有者需在本轮之外处置或明确保留历史未跟踪产物，使新派发起点工作树干净；随后由 C/监督端签发新 round/新路径再执行 T1--T5。不得在 r031 原路径绕过 G0 续跑。

## 2026-08-14 15:22 CST — owner authorizes r031 closure and sequential re-dispatch（server-primary 转交监督端）

- 指令来源：用户明确要求“关闭 r031、重发预检，然后上循环性/归因审计轮”。该指令构成 r031 的 owner-only closure authorization，并授权后续顺序流程；不授权跳过预检 readiness gate。
- r031 可关闭状态：服务器报告已提交并推送，`execution_status=complete`、`completion_mode=gated_early_stop`、`scientific_outcome=NOT_ADJUDICATED`；关闭理由为预注册 G0 检出派发前脏工作树，不是科学失败。
- 当前现场：原工作树此前 6 个未跟踪路径已消失，但出现 3 个 r028 受保护 tracked 文件的外部本地删除；server-primary 未删除、恢复或提交它们。已从远端 `4365f6724888c93a58983f41767e46625aa31a66` 建立独立干净 worktree `/home/rspip/cqc/pro/study/orientbench_r032_clean`，后续服务器执行可在该干净现场进行，避免改动原工作树。
- 请求 C/监督端动作：以 `gated_early_stop / NOT_ADJUDICATED` 关闭 r031；签发全新只读资产预检 round、全新 plan/report/output 路径，并明确以独立 clean worktree 的 status 为 G0 判据；预检必须完整执行八 unit × 十二字段、join、官方标注 provenance、readiness validator 与 mutation。
- 后继门控：只有重发预检产生 `ASSET_READY_FOR_<next-round>` 且独立验证通过，C 才签发循环性/归因审计轮；若为 `ASSET_GAP`，先报告最低资产缺口，不得直接计算 effect、bootstrap、risk-coverage 或修改 frozen threshold/split。
- 身份边界：当前 clone 绑定 `paper.worker-id=server-primary`。依据 `dis/governance/roles/SERVER.md`，服务器不得自行改 C-owned memo/plan、coordination 或冒充 C 激活 dispatch；因此本条作为固定监督交接记录，等待 C 发布精确 `dispatch_id + plan_path + dispatch_commit_sha`。
- 是否触发停止条件：监督流程暂未触发科学早停；服务器启动新预检的必要输入尚缺合法 C dispatch。
- 下一步建议：C 立即提交并推送关闭记录和新预检 dispatch；用户随后无需再次解释任务，只需将三元组交给 server-primary，即可在上述 clean worktree 严格执行。

## 2026-08-14 02:03 PDT — r032 circularity asset preflight retry（server-primary）

- 指令来源：用户交付 `orientbench-c-r032-circularity-asset-preflight-retry-20260814` 的 dispatch/path/commit，要求执行已重发的循环性资产预检。
- 执行动作：在独立 clean worktree 以 HTTPS `git pull --ff-only` 闭合到 `a9e1b7f278628962db0ecb82de1fda1a93509a73`，核验 worker/plan/active/pth_data 后先提交并推送完整 STARTED；随后只读盘点 A--H 八单元的 frozen cohort、features、scores、matched geometry、class/cluster map，以及 DIOR-R、FAIR1M-v1.0、SODA-A、DOTA-v1.0 官方标注资产。
- 关键产物：`reports/r032_circularity_asset_preflight/`；最终执行报告将写入 `dis/server_reports/orientbench-c-r032-circularity-asset-preflight-retry-20260814/SERVER_EXECUTION_REPORT.md`。
- 核验：8×12 字段矩阵完整；48/48 cohort join 通过，重复键与 cohort missing 均为 0；四数据集官方目录均生成逐文件 bytes/SHA 清单；独立 validator 完整通过；删 unit-field、改 source SHA、制造 cohort duplicate、MISSING→DIRECT 四项真实临时副本 mutation 均被同一 validator 非零拒绝；quarantine before/after 逐字节相同且本 clean worktree 为空集。
- 是否触发停止条件：未触发执行失败或 kill condition；readiness 合法完成为 `ASSET_GAP_R032`。唯一科学输入缺口为八单元均无冻结的“官方原始对象 ID → 处理后/切片对象 ID”回连证据；现有 `gt_id` 只是处理后逐图 ordinal，不能冒充官方对象 ID。
- 下一步建议：不得启动 r033 循环性/归因效果审计。最低恢复动作是另行签发只读 lineage round，生成并独立审计 immutable raw-object-to-evaluation-object mapping；该资产闭合后再重发 r033。

## 2026-08-14 02:22 PDT — r032 完整性复核（server-primary）

- 指令来源：用户询问“确保完全执行完了？”。
- 执行动作：复核本地/远端提交、最终报告 completion mapping、独立 validation、readiness、48 项 join 与四项 mutation receipt。
- 关键产物：`reports/r032_circularity_asset_preflight/validation_r032.json`；`dis/server_reports/orientbench-c-r032-circularity-asset-preflight-retry-20260814/SERVER_EXECUTION_REPORT.md`。
- 结论：r032 本轮确已 `full_completion`，远端 `main=dfdb44994fcb292207b8ae926cee17637d82bf45`，validator=`PASS`，48/48 join 无 failure，四项 mutation 全部被拒绝。后继 r033 未执行，原因是合规 readiness=`ASSET_GAP_R032`，八单元均缺官方 raw-object ID 回连资产；这不是 r032 未完成。
- 是否触发停止条件：r032 未触发 failure/kill；r033 被 readiness gate 正常阻止。
- 下一步建议：由 C 签发 object-lineage 资产轮，闭合八项官方对象 ID 映射后再重发 r033。

## 2026-08-14 03:57 PDT — r034 circularity decisive audit（server-primary）

- 指令来源：用户交付 `orientbench-b-r034-circularity-decisive-20260814` 的 dispatch/path/commit，要求执行决定性循环性/归因审计轮。
- 执行动作：main 纯 fast-forward 到 `0b5a98f27fd24ceab6b8f6d05ea3a0b7fdf98e1a` 并先推送 STARTED；对 A--H 八单元执行 lineage 回连尝试、两套独立 10,000 次 image-cluster bootstrap 实现、12 项冻结 primary family、三路分解与类别/匹配/NMS 诊断；随后执行 A/B comparator、raw-row validator、六项真实 mutation 与便携 bundle 重放。
- 关键产物：`outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814/`；`top_journal_v3_reaudit_055/circularity_decisive_r034_20260814/`；`audit_bundles/r034/`；`dis/server_reports/orientbench-b-r034-circularity-decisive-20260814/SERVER_EXECUTION_REPORT.md`。
- 核验：A/B 576 hypothesis keys、14,976 数值字段在 `atol=1e-10` 内一致，bootstrap multiplicity 逐元素一致；raw validator 从 616,184 行与 multiplicity 独立重算 12/12 primary 并通过；六项 mutation 全部被非零拒绝；bundle 39 文件、229,597,799 bytes，manifest 与 bundle 内重放均通过。
- 决策性结果：八单元 lineage 均为 `LINEAGE_GAP(unit)`、无 `LINEAGE_CONTRADICTION`；12 项 primary 无注册 witness。冻结判据得到 `K1=true`、`K2=true`、`SURVIVAL=false`，候选状态 `K1_K2_KILL_STRONG_JSTARS`。这是完整科学结果而非执行异常；最终 B/C post-pull verdict 仍由监督端裁决。
- 是否触发停止条件：触发 r034 预注册的科学 kill 结果 K1/K2，因此不得继续扩展 selector 顶会线或自行改 threshold/split；未触发执行 failure、GPU/训练/推理、产物不可持久化或 lineage contradiction。
- 下一步建议：B/C 从 `audit_bundles/r034/` 独立重放并登记最终 verdict；依项目规则将主线收缩为 TGRS/ISPRS benchmark + practical selector，除非监督端发现可审计反证。本服务器不得自行改写本轮候选裁决。

## 2026-08-14 22:08 PDT — r036 Q-SetOD paper-kill study（server-primary）

- 指令来源：用户交付 `orientbench-b-r036-qsetod-kill-study-20260814` 的 dispatch/path/commit，授权按冻结 CPU-only 计划执行 Q-SetOD 纸面杀伤实验。
- 执行动作：main 纯 fast-forward 到 `ffab54d8babe7041f87131ef08723456b6011f25` 并先推送 STARTED；无损连接八单元 616,184 行冻结数据与 TTA/面积/原始 OBB；完成 endpoint 消费审计、三个 source 规格的 5-fold cluster cross-fitting、八个 held-out 配置、A/B 各 10,000 次 cluster bootstrap、536 strata 多峰审计和 source-only Mondrian 校准。
- 关键产物：`outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814/`；`top_journal_v3_reaudit_055/qsetod_kill_study_r036_20260814/`；`audit_bundles/r036/`；最终报告 `dis/server_reports/orientbench-b-r036-qsetod-kill-study-20260814/SERVER_EXECUTION_REPORT.md`。
- 核验：A/B comparator 244,794 字段、最大差 `1.01e-16`，multiplicity 完全一致；raw validator 从 rows/OOF/predictions/multiplicities 重导全部门控并 PASS；六项真实 subprocess mutation 全部拒绝；bundle 54 files、190,356,770 bytes，manifest 与 bundle 内 raw replay 均 PASS。
- 决策性结果：证据增量 witness 为 5/8，故 `KILL-E=false`；多峰行数加权占比 14.476%，故 `PRUNE-M=false`；但 16 个 calibration rows 中 4 个因 held-out 覆盖偏离名义值超过 5 个百分点触发，故 `KILL-C=true`。候选状态为 `QSETOD_EVIDENCE_ONLY_KEEP_M`：证据信息存在，但 source-only 集合校准不可行，不进入集合式训练验证。
- 偏差与边界：冻结环境无 `diptest` 包且网络不授权下载依赖，T3 使用披露的 deterministic binned Hartigan-style approximation；A/B 完全一致，且不影响 KILL-E/KILL-C。GPU=0、神经网络训练=0、detector forward/inference=0；target angle labels 仅用于评测，未进入拟合/阈值/选择；未触碰 r034 终局或 frozen threshold/split。
- 是否触发停止条件：触发预注册科学 `KILL-C`，属于正常 full completion，不是 execution failure；硬性 kill 清单未触发。
- 下一步建议：B/C post-pull 独立重放并登记最终 verdict；若接受，应将 Q-SetOD 降格为 evidence/质量分数候选，不授权 §4.2 集合式有限训练。服务器不得自行启动 GPU 或改写校准规则。

## 2026-08-15 00:55 PDT — 拉取与 r037 激活前核验（server-primary）

- 指令来源：用户要求“拉取，执行。”
- 执行动作：在独立干净工作树以 `git pull --ff-only` 拉取远端 main 至 `92896951b6ec5aca857c77235d1b47e069122ac0`，复核 worker、coordination、根活动计划、r037 READY plan 与远端 HEAD；未读取 r037 科学输入，未创建 STARTED，未启动计算。
- 关键产物路径：无新科学产物；待派发计划为 `dis/plans/C/c-r037-qsetod-corrective-adjudication-20260815/sug.md`。
- 是否触发停止条件：触发执行入口阻断。coordination 与 `dis/sug.md` 仍锁定 r036，r037 仅为 READY；C 已请求 B 关闭 r036 并代理激活 r037，但该事务尚未完成，且用户尚未交付 SERVER 角色要求的精确 r037 三元组。
- 下一步建议：B 完成 r036 closure / r037 activation 并推送；用户随后交付精确 `dispatch_id + plan_path + dispatch_commit_sha`，server-primary 即按冻结计划执行。
