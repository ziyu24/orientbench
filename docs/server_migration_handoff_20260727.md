# OrientBench 服务器迁移与续作交接报告

首次生成：2026-07-27 10:48 CST

复核修订：2026-07-27（迁移后会话复核）

源项目根目录：`/home/rspip/cqc/pro/study/orientbench`

Git 仓库：`git@github-ziyu24:ziyu24/orientbench.git`

迁移基线分支：`agent/publish-orientation-reliability`

归档内嵌 Git 提交：`298c9cc1187fcbfa76fc65aca107c124c774c241`

报告首次提交：`010f15c5c5d59f366d707852007c676af6f47959`

## 1. 交接结论

项目已经完成到命令 079：

- A 工作线已冻结为 `A_MEASUREMENT_ONLY`，正式中文稿已完成。
- B 工作线已完成外部 PSC variant 验证，机制门控为
  `PASS_MECHANISM_BOUNDED`。
- 下一正式任务应为 080，即 B6 修复级门控；B6/B7 尚未执行。
- 2026-07-27 复核时没有本项目训练、推理、复算或 watcher 进程；新服务器
  接手时仍须重新检查。
- `thresholds.yaml`、`D_cal`、`D_audit` 均保持冻结。
- 迁移归档包含 Git 工作区、忽略文件、持久化结果、保留 checkpoint、
  人工标注和日志；不包含外部数据集、外部 baseline 库、conda 环境和
  third-party 源码。

仅从 Git clone 不能恢复完整项目。Git 中约有 1,594 个文件、26.4 MB；
完整工作区中不含 `.git` 和迁移分片时约为 23.1 GB，其中持久化科学产物
约 14.6 GB、保留模型约 5.9 GB。

### 1.1 接手规则优先级

新会话不要只读根目录 `README.md`，它目前仅有极简项目标识。接手顺序必须是：

1. `AGENTS.md`：当前项目执行规则和硬禁区；
2. 本迁移报告：物理资产、环境和最新科学状态；
3. `claude_code_and_supervisor.md`：按时间追溯正式命令与裁决；
4. A/B/shared 三个 `README_SCOPE.md` 与 `AB_ASSET_BOUNDARY.md`；
5. 各工作区最新 decision/reproduction 表。

`AGENTS.md` 仍将长期科学主题定义为 measure -> diagnose -> fix；074 以后又
建立了 A/B 物理隔离。二者的正确兼容方式是：科学问题可以保持联合主线，
但在下一条正式命令改变边界前，文件写入、主表和结论仍必须遵守 A/B 隔离，
不得为了“联合主线”撤销已完成的物理边界或把 B 机制表写回 A。

## 2. 迁移包状态

现有迁移包位于：

```text
.orientbench_transfer_parts/
```

它由 5 个分片组成，打包完成时间为 `2026-07-24T19:19:36Z`。打包发生在
两轮低风险磁盘清理之后，因此不包含已经删除的非最佳 epoch、R1 旧工作区、
K2 pilot、preflight 和 superseded 训练目录。

归档创建早于本迁移报告，因此归档本身不包含本报告及其后续修订。解压后
必须执行 Git pull；否则新服务器只能看到 298c9cc 时点的工作区。

| 分片 | 字节数 | SHA-256 |
|---|---:|---|
| `part-0000` | 2,147,483,648 | `197961601f735bb5d00a6e996e3d1bc6192e09cbac95e88a20e251db6b597282` |
| `part-0001` | 2,147,483,648 | `f313d03db5199322c606cf68a5469f20b3b2f1b2b629479f3dc42857934ad9e2` |
| `part-0002` | 2,147,483,648 | `301e66a6046223ef223d3931b2567630f7f37b269cd5b0083aab7f4b5e08656f` |
| `part-0003` | 2,147,483,648 | `7223b931b243234ae859013df96248b52211bb872b3edf94264021c3aa689e9e` |
| `part-0004` | 1,361,703,203 | `db394eb9da00113d7c0262f9c2335e13736cba4070de3d6547571ce831d9c50a` |

源服务器已完成两类完整性检查：

1. 5 个分片逐个 SHA-256 与 `SHA256SUMS` 一致；
2. 拼接后的 zstd 流通过 `zstd -t` 完整性检查。

### 2.1 新服务器恢复命令

在存放迁移分片的目录执行：

```bash
sha256sum -c SHA256SUMS
cat orientbench.tar.zst.part-* | zstd -t -q
mkdir -p /NEW/PROJECT/PARENT/orientbench
cat orientbench.tar.zst.part-* \
  | zstd -dc \
  | tar -xf - -C /NEW/PROJECT/PARENT/orientbench
```

归档内已经包含 `.git`。恢复后必须拉取本报告所在的最新分支：

```bash
cd /NEW/PROJECT/PARENT/orientbench
git remote set-url origin git@github-ziyu24:ziyu24/orientbench.git
git fetch origin
git checkout agent/publish-orientation-reliability
git pull --ff-only origin agent/publish-orientation-reliability
```

不要把 `.orientbench_transfer_parts/` 解压进项目内部第二次，也不要将它提交
Git。确认新服务器完整恢复后，迁移分片可以放到项目外的冷存储。

## 3. Git 状态

归档内嵌的 Git 状态：

```text
branch: agent/publish-orientation-reliability
commit: 298c9cc1187fcbfa76fc65aca107c124c774c241
remote branch: origin/agent/publish-orientation-reliability
origin/main: 1915340415d144222d56efd5372022866562a9b8
```

`origin/main` 已包含 079 的科学产物；发布分支另外包含两次磁盘清理记录。
本报告提交后，新服务器必须以发布分支最新提交为准，不要从旧 `master`
或只从 `origin/main` 开始续作。

报告首次存在于 `010f15c`。当前权威提交不要写死为 010f15c，而应在新服务器
执行 `git pull --ff-only` 后以如下命令得到：

```bash
git rev-parse origin/agent/publish-orientation-reliability
git rev-parse HEAD
```

两者必须相同。

源工作区在生成本报告前除未跟踪的 `.orientbench_transfer_parts/` 外是干净的。

## 4. 当前科学状态

### 4.1 A：通用朝向可靠性测量

工作区：

```text
top_journal_v3_reaudit_055/paper_A_orientation_protocol/
```

最终定位：

```text
A_MEASUREMENT_ONLY
```

权威论文：

```text
top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/
orientation_reliability_paper_A_zh_v077.md
```

当前裁决：

| 模块 | 结论 | 含义 |
|---|---|---|
| 风险预算前沿 | `PARTIAL_FRONTIER` | 576 个 score-budget rows 中 554 个不可行；主风险仅一个 practical point |
| 场景统计 | `PASS_TILE_ONLY_WITH_LIMITATION` | DIOR-R/FAIR1M 可恢复母景；SODA-A 只能作 tile/image-level 正式结论 |
| score menu | `PARTIAL_SCORE_MENU` | 可部署 score 在主风险下没有稳定非平凡认证 |
| 扰动几何 | `PARTIAL_ALIGNMENT` | AP50 弱敏感与 AP75 更敏感成立，但统一 AP75 knee 未可靠识别 |
| 人工标注 | `PARTIAL_TWO_ANNOTATOR_WITH_GT` | 两名真人与 official GT 对照完成；第三标注员未完成 |
| 独立确认单元 | `NO_ELIGIBLE_CONFIRMATORY_UNIT` | 无满足全部 provenance 条件的独立确认单元 |
| 总体 | `A_MEASUREMENT_ONLY` | 保留测量协议，不恢复广泛 deployable risk-control claim |

A 的正式贡献边界：

- canonical le90 angle error；
- `ar>=2.1` 主协议；
- geometry-normalized severe event；
- NRC、AURC、risk-coverage；
- full-evaluator 扰动审计；
- image/tile/mother-scene 统计审计；
- 严格风险预算下的可行性前沿与负结果；
- 真人标注不确定性审计；
- 可复算 orientation reliability 工具箱。

不得写回：

- 广泛可部署风险认证；
- target-GT geometry 为 deployable score；
- 完整 PSC/CSL/DCL 多种子机制表；
- PSC 修复结论。

### 4.2 人工标注状态

权威 primary：

- 600 个 canonical targets，DIOR-R/FAIR1M/SODA-A 各 200；
- 450 对双方均给出数值角度；
- mean circular disagreement：2.3112 度；
- image-cluster bootstrap 95% CI：1.9970--2.7854 度；
- median：1.6359 度；
- `P(>5°)=8.00%`；
- `P(>10°)=0.89%`；
- `ar>=2.1` 子集 308 对，mean 2.2823 度。

第三标注员 150 项任务已经冻结，但真人结果为 0。状态仍是
`PENDING_REAL_ANNOTATOR_3`，不得把 test outputs 当成真人结果，也不得生成
三人 consensus。

权威位置：

```text
top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation/
top_journal_v3_reaudit_055/paper_A_orientation_protocol/annotation_tools/annotator_3/
top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a5_*.csv
```

### 4.3 B：PSC 机制

工作区：

```text
top_journal_v3_reaudit_055/paper_B_psc_mechanism/
```

共同法证：

```text
top_journal_v3_reaudit_055/shared_forensics/g0/
```

G0 结论：

```text
PASS_RISK_FUNCTIONAL_DEPENDENT
```

必须持续分开两个 endpoint：

- Endpoint C：continuous le90 circular angle error；
- Endpoint E：`angle_error > delta_theta_0.75(aspect_ratio)`。

B1--B3 状态：

- H1 径向解码敏感：`SUPPORTED`；
- H2 wrapping/boundary-conditioned failure：`PARTIALLY_SUPPORTED`；
- H3 multi-frequency disagreement：`SUPPORTED`；
- H4 directional confidence mismatch：`PARTIALLY_SUPPORTED`。

B4 外部变体：

- host：RotatedFCOS-PSCD；
- dataset：DOTA-v1.0 train -> val；
- seeds：0/1/2；
- 三个 seed 均为 `HEALTHY_COMPARABLE`；
- AP50：0.629/0.627/0.632；
- AP75：0.324/0.323/0.333；
- H1/H3 跨 host 复现，H2/H4 部分复现；
- 外部 host 的 `phase_mod` 在 Endpoint C 为 informative，
  与原 RetinaNet 的反序方向不同。

B5 最终结论：

```text
PASS_MECHANISM_BOUNDED
```

允许的结论：

- secondary-frequency decoding 与 modulation gate 对角度输出具有跨 host 的
  可重复结构影响；
- 机制结论必须 host-qualified 和 endpoint-qualified；
- 可以进入 B6 修复级门控。

禁止的结论：

- 所有 PSC 实现普遍反序；
- Endpoint C 的结果自动外推到 Endpoint E；
- 改变 angle box/NMS/AP 的干预属于 ranking-only repair；
- 冻结候选已经稳定优于 detection score；
- B6 修复已经成功。

下一正式编号为 080。080 应执行 B6，不应重做 B1--B5，也不应修改 A。

### 4.4 必须保持的科学不变量

- 正文主几何口径保持 `ar>=2.1`；`ar>=1.6/1.3` 仅为 sensitivity；
- DIOR 正式结果使用 full-val lineage，旧 partial-GT 数字不得恢复；
- DOTA#20 不进入正式结果；
- image/scene 是风险审计的 exchangeable unit，instance-i.i.d. 仅作经验对照；
- 空 selected scene 记为 abstained，不得以零风险稀释总体；
- SODA-A 无严格 mother-scene guarantee；
- target-GT-fitted nonlinear geometry 只是 diagnostic/calibration upper bound；
- formal/exploratory 标签保持不变；
- 正式主表不得依赖 `/dev/shm`。

## 5. A/B 资产边界

必须继续遵守：

```text
top_journal_v3_reaudit_055/shared_forensics/AB_ASSET_BOUNDARY.md
top_journal_v3_reaudit_055/shared_forensics/ab_asset_boundary_manifest.csv
```

- A 只写 `paper_A_orientation_protocol/`；
- B 只写 `paper_B_psc_mechanism/`；
- G0 共同事实只写 `shared_forensics/g0/`；
- B 的完整机制表不得回流 A；
- A 的完整风险控制和人工标注主表不得复制到 B；
- 历史 raw artifacts 只读。

## 6. 关键资产清单

### 6.1 项目内已随归档迁移

| 资产 | 规模 | 说明 |
|---|---:|---|
| `outputs/persistent_artifacts/` | 275 文件，14.58 GB | 主复算依赖，必须保留 |
| 项目内 `.pth` | 38 个，5.95 GB | K2 final、B4、host 等保留 checkpoint |
| `top_journal_v3_reaudit_055/work_dirs/k2/` | 24 个 final best | 18 个 PSC/CSL/DCL 正式单元，加 6 个 direct-regression 失败审计单元 |
| `paper_B_psc_mechanism/artifacts/b4_training/` | 3 个 best | B4 外部 variant 三 seeds |
| `paper_B_psc_mechanism/artifacts/b4_external/` | 三 seed dumps | B4/B5 复算输入 |
| `paper_B_psc_mechanism/artifacts/b3_*` | B3 dumps/cache | B1--B3 机制复算输入 |
| `top_journal_v3/reports/*.csv` | 含两个大型 CSV | 旧但仍被脚本引用，不能随意删除 |
| 人工标注原始输出 | 已持久化 | test/formal/secondary 必须保持区分 |

以下内容已经在迁移前清理，不应在新服务器寻找：

- 全部非最佳 `epoch_*.pth`；
- R1 旧工作目录；
- K2 pilot 工作目录；
- B4 非最佳 epoch；
- RHINO/A4 host 末轮 checkpoint；
- preflight/superseded 训练目录；
- Python/test caches。

38 个项目内 checkpoint 的主要构成为：

- K2 final：24 个；
- B4 external variant：3 个；
- M4 FAIR1M 第三数据集：9 个；
- RHINO/A4 host best：2 个。

不得把 K2 的 6 个 direct-regression 失败审计 checkpoint 当作 native-score
正式比较单元；它们仅用于训练披露和失败 lineage。

### 6.2 项目外、未包含在归档

| 外部资产 | 源路径 | 源端规模 | 新服务器要求 |
|---|---|---:|---|
| baseline 库 | `/home/rspip/cqc/pro/study/pth_data` | 25 GB，80 个 pth | 需要新推理/训练时必须单独迁移 |
| third-party 源码 | `/home/rspip/cqc/pro/study/third_party` | 185 MB | 必须迁移或按相同 commit 重建 |
| ai4rs editable clone | `/home/rspip/cqc/pro/study/ai4rs_clone` | 49 MB | `ai4rs_train` 环境使用 |
| 数据集 | `/home/rspip/cqc/data/dataset` | 现有约 114 GB | 必须单独迁移或挂载 |
| conda 环境 | `/home/rspip/anaconda3/envs/*` | 未统计 | 不在项目归档内 |

当前源端数据规模：

- DOTA：约 72 GB；
- FAIR1M：约 31 GB；
- DIOR：约 7.5 GB；
- HRSC2016：约 3.9 GB；
- SODA-A 原始目录在源端已经不存在，必须从其它副本恢复；项目内持久化
  matched/native artifacts 仍在。

`pth_data/readme.md` 是 baseline 身份、valid 状态、训练超参和 checkpoint
短哈希的权威入口。新服务器在运行任何新推理前必须先恢复并核对该库。

迁移包中的 `orientbench/pth_data/` 只是项目内占位目录，不是外部 25 GB
baseline 库，不能据此判断 baseline 已经迁移。

## 7. 路径和软链接迁移

项目共有 4,847 个软链接：

- 4,816 个绝对链接；
- 31 个相对链接；
- DOTA 数据链接 2,680 个；
- DIOR 数据链接 602 个；
- FAIR1M 数据链接 522 个；
- SODA-A 数据链接 408 个；
- HRSC2016 数据链接 4 个；
- 指向旧项目根的内部链接 600 个。

源端已有 408 个 broken links，全部来自缺失的 SODA-A 原始数据。迁移后若
新路径不同，其余绝对链接也会失效。

最稳妥方案是让新服务器保持以下逻辑路径：

```text
/home/rspip/cqc/pro/study/orientbench
/home/rspip/cqc/pro/study/pth_data
/home/rspip/cqc/pro/study/third_party
/home/rspip/cqc/data/dataset
```

若实际存储位置不同，建议在上述位置建立受控软链接或 bind mount。若必须
重写项目内链接，先备份并只替换链接 target，不要批量替换 CSV/JSON 中的
科学 lineage 字段。

检查命令：

```bash
find . -type l | wc -l
find -L . -type l -print
rg -l '/home/rspip/cqc' scripts configs top_journal_v3_reaudit_055
```

项目中约 233 个非日志、非大型结果文件仍含旧绝对路径。许多脚本已经通过
相对 `ROOT` 解析，但旧脚本、配置和 lineage 文档并未全部去绝对路径。继续
执行前应优先修正实际会运行的脚本，不要机械改写历史报告。

## 8. 冻结资产校验

### 8.1 阈值

```text
configs/thresholds.yaml
b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae
```

### 8.2 D_cal / D_audit

| 文件 | SHA-256 |
|---|---|
| `D_cal_dior_trainval.csv` | `f624a21451de394a35041af35c9a910c3a1bdc11fb5c942d15416e04e0e6f632` |
| `D_audit_dior_trainval.csv` | `11c61be3a03c922b5e00e4cf9e866cf73e18eff44bd6b868b53f54612065669b` |
| `D_cal_dota10_train.csv` | `48a0319a1ea51fcbadf43e7e632d5a77f77d3db73442acfd639acb0c455daed4` |
| `D_audit_dota10_train.csv` | `d4fb9a793a4c2f31ddd42cde0ba8c571114e78b2ab0d3af36002f201fafc1eb7` |
| `D_cal_dota15_train.csv` | `aa59e4266872c2f3f48b6c027798255e21fae64b09519a895d3ba8deb85b9364` |
| `D_audit_dota15_train.csv` | `ac97d1f3f2a780f79019612fce6f7f93d13aa9f7a65c4f1c14aa96447e743856` |
| `D_cal_fair1m_train.csv` | `84b32cb5e0bd9a7afdc772f824e1b64f9daaca54fccdbbb98750180bc04b16a0` |
| `D_audit_fair1m_train.csv` | `140ef6855909cdca2904656ad76baca31ff11d8c571e3978e005d945440c335e` |
| `D_cal_hrsc_trainval.csv` | `bbaf79002ad683893292101744e32e379d711f14ab7c187ae5bad42d2e37bdb0` |
| `D_audit_hrsc_trainval.csv` | `55734ae8aa3f49350186fd066a761a54fe1a99921897012c5e59ca1fdf9f6679` |

新服务器必须在任何计算前运行：

```bash
sha256sum configs/thresholds.yaml
sha256sum outputs/bench_core/splits/D_cal_*.csv
sha256sum outputs/bench_core/splits/D_audit_*.csv
```

任一哈希不一致时停止，不得重新生成 split 或修改阈值。

## 9. 软件环境

源服务器硬件：

- 4 x NVIDIA A30 24 GB；
- NVIDIA driver 550.54.15；
- CPU 48 核。

使用过三个主要环境：

| 环境 | Python | PyTorch/CUDA | OpenMMLab |
|---|---|---|---|
| `mr` | 3.8.20 | torch 1.12.1+cu113 | mmcv 1.7.2, mmdet 2.28.2, mmrotate 0.3.4 |
| `mr_dev1x` | 3.10.20 | torch 2.4.0+cu121 | mmcv 2.2.0, mmengine 0.10.7, mmdet 3.3.0, mmrotate 1.0.0rc1 |
| `ai4rs_train` | 3.10.20 | torch 2.4.0+cu121 | mmcv 2.2.0, mmengine 0.10.7, mmdet 3.3.0, mmrotate 1.0.0rc1 |

公共科学栈：

```text
numpy 1.24.4 / 1.26.4
pandas 2.0.3 / 2.3.3
scipy 1.10.1 / 1.15.3
opencv 4.13.0
matplotlib 3.7.5 / 3.10.8
shapely 2.1.2 (1.x environments)
```

editable 源码身份：

| 环境 | 源码 | Git commit |
|---|---|---|
| `mr` | `third_party/mmrotate_034` | `7755aa53b6e2d9c61fd765e67a60daa7ed8a1e05` |
| `mr_dev1x` | `third_party/ai4rs` | `6095d3a3155570324e9e01c88cd2e4a3b55ae7c3` |
| `ai4rs_train` | `ai4rs_clone` | `6095d3a3155570324e9e01c88cd2e4a3b55ae7c3` |
| ARS-DETR | `third_party/ARS-DETR` | `0d96c5e792dcca34793570c7acd67bb1068561c1` |

建议优先使用 `conda-pack` 搬运现有环境；若重建环境，必须先 checkout 上表
commit，再 editable install。不要让 mmrotate 0.x 与 1.x 在同一环境互相覆盖。

脚本中的固定解释器需要迁移适配：

- `reproduce_B1_B3.sh` 固定使用 `mr_dev1x`；
- `reproduce_A4_A6.sh` 固定使用 `ai4rs_train`；
- B4 训练和 instrumented dump 使用 `ai4rs_train` 与 ai4rs 1.x 源码；
- 一些旧脚本默认当前 `python` 或固定 `/home/rspip/anaconda3/...`。

环境验收至少执行：

```bash
/path/to/envs/mr/bin/python -c \
  "import torch, mmcv, mmdet, mmrotate; print(torch.__version__, mmrotate.__version__)"
/path/to/envs/mr_dev1x/bin/python -c \
  "import torch, mmcv, mmengine, mmdet, mmrotate; print(torch.__version__, mmrotate.__version__)"
/path/to/envs/ai4rs_train/bin/python -c \
  "import torch, mmcv, mmengine, mmdet, mmrotate; print(torch.__version__, mmrotate.__version__)"
```

## 10. 复算入口

### 10.1 A

```text
top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/reproduce_A1_A3.sh
top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/reproduce_A4_A6.sh
```

工具箱最小验证：

```bash
cd top_journal_v3_reaudit_055/paper_A_orientation_protocol/toolbox
PYTHONPATH=. python -m unittest discover -s tests -v
PYTHONPATH=. python -m orientation_reliability.cli \
  examples/synthetic.csv --ap75 0.50
```

### 10.2 B

```text
top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/reproduce_B1_B3.sh
top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/reproduce_B4_B5.sh
```

注意：

- `reproduce_B1_B3.sh` 包含 FAIR1M instrumented forward，需要 GPU、数据和
  `mr_dev1x`，不是纯文本 smoke test；
- `reproduce_B4_B5.sh` 使用持久化 B4 dumps 做统计复算，可作为 B 迁移验收；
- 不应为了迁移验证重训 K2、host 或 B4；
- 项目根 `scripts/reproduce_all_main_tables.sh` 是历史全链入口，执行前必须先
  修复数据和解释器路径。

已有复算状态：

- A1--A3：完成；
- A4--A6：完成；
- B1--B3：完成；
- B4--B5：15 项检查全部通过；
- 073 历史全链：10/10 steps 通过，但其广泛风险控制写法已被 075--077
  的 measurement-only 裁决 supersede。

## 11. 新服务器验收顺序

严格按以下顺序执行：

1. 校验 5 个迁移分片 SHA-256 和 zstd stream。
2. 解压项目，checkout/pull 发布分支最新提交。
3. 阅读 `AGENTS.md`、本报告和 A/B scope，不以极简 README 代替接手审计。
4. 恢复或挂载 `pth_data`、third-party、ai4rs clone 和数据集。
5. 保持旧逻辑路径，或仅重建绝对软链接。
6. 校验 `thresholds.yaml` 与 10 个 split 哈希。
7. 确认 24 个 K2 final best、3 个 B4 best、两个 host best 存在。
8. 确认 `outputs/persistent_artifacts/` 有 275 个文件。
9. 导入 `mr`、`mr_dev1x`、`ai4rs_train` 并核对核心版本。
10. 重新审计本项目后台进程。
11. 运行 A toolbox unit/synthetic tests。
12. 在正确 1.x 环境运行 `reproduce_B4_B5.sh`，确认 15 项为 PASS。
13. 只在原始数据路径完整后运行需要 instrumented inference 的链。
14. 验收完成后才开始 080；不要重做 075--079。

建议验收命令：

```bash
git status --short
git rev-parse HEAD
git rev-parse origin/agent/publish-orientation-reliability
find top_journal_v3_reaudit_055/work_dirs/k2 \
  -type f -name 'best*.pth' | wc -l
find top_journal_v3_reaudit_055/paper_B_psc_mechanism/artifacts/b4_training \
  -type f -name 'best*.pth' | wc -l
find outputs/persistent_artifacts -type f | wc -l
find -L . -type l -print
ps -eo pid,lstart,cmd | rg 'orientbench|torchrun|distributed|reproduce_[AB]'
```

预期关键数量：

```text
K2 final best checkpoints: 24
B4 best checkpoints: 3
persistent artifact files: 275
```

`find -L` 仍显示 SODA-A 的 408 个链接时，说明原始 SODA-A 尚未恢复；这不
影响读取已经持久化的统计产物，但会阻止依赖原图的推理、标注和部分复算。

## 12. 禁止事项与续作起点

迁移后不得因为路径变化或环境缺失而：

- 修改 frozen thresholds；
- 重建或改变 `D_cal/D_audit`；
- 重训 host；
- 重跑 K2；
- 追 DOTA public mAP；
- 把旧 partial-GT 结果恢复为正式结果；
- 把 instance-i.i.d. exact binomial 恢复为正式主保证；
- 把 target-GT upper bound 称为 deployable；
- 把 B 的 bounded mechanism 外推为通用 PSC failure；
- 把第三标注员 test outputs 当真人标注；
- 将 A/B 工作区重新混写。

新服务器的真实续作起点：

```text
最新完成：079
下一编号：080
任务方向：B6 修复级门控
A 状态：A_MEASUREMENT_ONLY，保持冻结
B 状态：PASS_MECHANISM_BOUNDED，可进入 endpoint/host-qualified B6
```

080 之前应先完成本报告第 11 节的迁移验收。若验收失败，只修复路径、环境
和缺失外部资产，不得借迁移重新选择数据、阈值、checkpoint 或协议。
