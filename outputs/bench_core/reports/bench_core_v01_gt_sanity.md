# Bench-Core v0.1 GT Sanity Report

> 生成时间: 2026-06-25 16:43 CST
> 范围: 指令 004 — 接真实数据 GT，完成 Bench-Core-0 数据层 sanity。
> 状态: 数据层 sanity 完成；只读解析，未改数据；阈值未冻结，未开正式实验；未启动 detector 推理/训练/下载。

---

## 1. 固定路径 & 环境

| 路径 | 状态 |
|---|---|
| /home/rspip/cqc/data/dataset | ok |
| /home/rspip/cqc/pro/study/pth_data | ok |
| /home/rspip/cqc/pro/study/pth_data/readme.md | ok |
| /home/rspip/cqc/pro/study/orientbench | ok |
| /home/rspip/cqc/pro/study/third_party | ok |

依赖: numpy 1.24.4 / cv2 4.13.0 / shapely 2.0.7 / python 3.8.20（均已存在，未安装/下载任何东西）。

---

## 2. Dataset Inventory 摘要

来源根: `/home/rspip/cqc/data/dataset`。known=7，**present=5，missing=2**。

| dataset | exists | annotation_dirs | image_dirs | splits | format |
|---|---|---|---|---|---|
| DOTA-v1.0 | ✓ | split_ss_dota10/{train,val}/annfiles | {train,val}/images | — | DOTA poly8 txt |
| DOTA-v1.5 | ✓ | split_ss_dota15/{train,val}/annfiles | {train,val}/images | — | DOTA poly8 txt |
| DIOR-R | ✓ | annfiles/{obb,hbb} | images/{trainval,test} | 4 (train/val/trainval/test) | robndbox XML |
| HRSC2016 | ✓ | annfiles | images | 4 | XML mbox(cx,cy,w,h,ang rad) |
| FAIR1M-v1.0 | ✓ | split/{train_80,val_20}/annfiles | split/{…}/images | — | XML points polygon |
| **SODA-A** | **✗ MISSING** | — | — | — | 未在 dataset 根出现 |
| **ICDAR-MLT** | **✗ MISSING** | — | — | — | 未在 dataset 根出现 |

产物: `outputs/bench_core/dataset_inventory.{json,csv}`。

注：`dota/` 下还存在 `dota2.0` 与 src/split 共享目录及大量符号链接；本轮只索引 v1.0/v1.5（项目目标范围），未触碰符号链接目标。

---

## 3. GT Index 基础模块

实现（共享几何路径，R7）：
- `orientbench/data/dota.py` — DOTA txt poly8 解析（跳过 imagesource/gsd、容错短行）。
- `orientbench/data/dior.py` — DIOR obb XML robndbox 4 角点解析。
- `orientbench/data/gt_index.py` — 统一 `poly8_to_obb`（cv2.minAreaRect → θ 归一化到 [-π/2,π/2)，cv2 缺失走 edge-fallback）、HRSC mbox 直接 OBB、FAIR1M points 解析、dataset registry、`--max-files` 抽样、schema、`build_gt_index`。
- `scripts/00_env_check.py`、`scripts/02_prepare_gt_index.py`（参数 `--dataset --data-root --split --out-dir --max-files --strict`，默认轻量 sanity）。

GT schema（每实例一行）: `dataset, split, image_id, image_path, annotation_path, class_name, obb_cx, obb_cy, obb_w, obb_h, obb_theta, angle_unit, angle_version, source_format, valid_geometry, warnings`。

### angle/version 不确定项（不伪造确定性）
- **DOTA / DIOR / FAIR1M**：θ 由多边形经 `cv2.minAreaRect` 推导，记 `angle_version="le90_derived_from_poly(cv2.minAreaRect)"`。GV-obliquity 与 aspect ratio 对 θ 符号不变，故 sanity 不受 le90 精确符号约定影响；但与 detector 预测做 angle-error 对齐前，**le90 符号一致性需另行核验**。
- **HRSC2016**：`mbox_ang`（弧度，opencv-like），记 `angle_version="mbox_ang_rad(opencv-like, UNVERIFIED le90 equivalence)"`，le90 等价性**未核验**。
- DIOR `<angle>` 原值已保留（解析层）但不作为权威 θ。

---

## 4. 真实 GT 轻量 GV Sanity

每数据集 `--max-files 60` 抽样：

| 数据集/split | files_ok | objects | valid OBB | invalid geom | GV median | GV mean | GV p10 | near-square* |
|---|---|---|---|---|---|---|---|---|
| DOTA-v1.0 / train | 60 | 959 | 959 | 0 | 0.456 | 0.575 | 0.332 | 9 (0.9%) |
| DIOR-R / trainval | 60 | 338 | 338 | 0 | 1.000 | 0.863 | 0.524 | 48 (14.2%) |

\* near-square 为 placeholder 阈值（aspect ratio ≤ 1.15，`PENDING_THRESHOLD_FREEZE`），仅占位计数。

解读：DIOR-R 多为近正/近轴对齐目标（中位 GV=1.0，OBB 需求低）；DOTA-v1.0 富含倾斜细长目标（车辆/船，中位 GV=0.456，OBB 需求高）。两者 GV 形态差异符合 OBB 朝向可靠性直觉，模块工作正常。invalid geometry = 0/全部，无退化。

产物: `outputs/bench_core/gt_index/{dota10_train,dior_trainval}.{jsonl,csv,meta.json}`。

---

## 5. 缺失 / unsupported 清单

- **缺失数据集**：SODA-A、ICDAR-MLT（不在 `/home/rspip/cqc/data/dataset`）。readme baseline 引用了 SODA-A / ICDAR-MLT 训练，但本地 dataset 根未提供其 GT；如需相关 GT 诊断，需合作者提供路径或确认不在范围。
- **unsupported_format**：本轮 5 个 present 数据集格式均已可解析，无 unsupported_format 记录。未知 dataset 名经 `build_gt_index` 返回 `supported=False` 并记 warning（不退出）。
- **angle_version 不确定**：HRSC mbox le90 等价性未核验；DOTA/DIOR/FAIR1M 的 le90 符号一致性待与预测对齐前核验（见 §3）。

---

## 6. 测试结果

命令: `python -m pytest tests/ -q` → **33 passed**（0.19s）。
- `test_baseline_readme.py` 7 + `test_bench_core0.py` 17 + `test_data_layer.py` 9。
- 数据层覆盖：DOTA poly8 解析、poly→OBB→HBB→GV 流程（轴对齐 GV≈1、45° GV≈0.5）、invalid geometry、missing annotation 容错、GT schema 完整性、`--max-files` 抽样、unsupported dataset 记录。

脚本运行：`00_env_check.py`、`02_prepare_gt_index.py --dataset dota10/dior` 均成功。

---

## 7. 停止条件检查

| 停止条件 | 状态 |
|---|---|
| /home/rspip/cqc/data/dataset 不存在 | 否（存在）|
| readme 消失 | 否 |
| 需要改项目固定路径 | 否 |
| 需要安装/下载依赖 | 否（cv2/numpy/shapely 已具备）|
| 需要改动原始数据 | 否 |
| R1–R8 冲突 | 否 |
| 真实 GT 的 OBB 口径与项目定义根本冲突 | 否（poly→OBB、GV 与定义一致）|

**未触发任何停止条件。**

---

## 8. 下一步

1. **angle_version 核验**：在接 detector 预测前，核验 DOTA/DIOR/FAIR1M poly→le90 与 HRSC mbox_ang 的符号一致性（影响 angle_error，对 GV 无影响）。
2. **GV baseline 全量**：经确认后对选定 dataset/split 出 `gv_obliquity_baseline.csv`（去 `--max-files` 或加大抽样，CPU 并行）。
3. **缺失数据集裁示**：SODA-A / ICDAR-MLT 是否需要、路径何在，待合作者确认。
4. **Bench-Core-1**：layout/background source、class-conditional 桶；阈值经 R8 冻结后再开正式实验。
5. **C1/B**：RHINO host 仍缺失，待裁示；不阻塞 D2，不以 ARS-DETR 替代。
