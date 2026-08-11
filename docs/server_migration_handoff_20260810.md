# OrientBench 服务器迁移、清理审计与 Codex 接手报告

审计时间：2026-08-10（Asia/Shanghai）

源项目根目录：`/home/rspip/cqc/pro/study/orientbench`

目标用途：迁移到基础配置相近的新服务器，并由 Codex 在不丢失科学 lineage、冻结协议和可复算资产的前提下继续接手。

本报告取代 `docs/server_migration_handoff_20260727.md` 作为当前迁移入口。旧报告保留为历史快照，但其中“发布分支”“迁移分片”“下一步 080/B6”等内容已经被 2026-08-05 至 2026-08-09 的后续工作覆盖，不得再作为当前执行依据。

## 1. 结论摘要

1. 当前项目实际占用约 **34 GiB**。Git 跟踪工作区只有 1,905 个文件、38,802,713 bytes；约 42,268 个 ignored 文件包含绝大多数 raw data、checkpoint、人工标注介质和持久化科学产物。因此 **仅 clone Git 无法恢复项目**。
2. 本轮只做清理审计，**没有删除、移动、覆盖或压缩任何项目文件**。
3. 立即可清理的低风险内容不足 3 MiB，几乎不能降低迁移体积。可选冷归档约 6.5 GiB，但会损失部分历史轮次的原位复算能力，必须取得用户明确授权后才能处理。
4. 最新权威科学裁决不是旧报告中的 B6 路线，而是 2026-08-09 顶刊可行性审计的：

   ```text
   Track M = METRIC_REVERSAL
   Track D eligible remote-sensing candidates = 0
   joint gate = FAIL_TO_MEASUREMENT_ONLY
   ```

   当前只允许 measurement-only 写作或等待新正式指令；不得自行继续方法设计、训练、推理、目标标签访问或数据集扩展。
5. 当前存在三个迁移前硬问题：
   - 远端 `main` 与本地 Git 引用尚未完成新一轮同步核验；
   - `/home/rspip/cqc/pro/study/pth_data/readme.md` 及外部 baseline 库当前缺失；
   - `mr_dev1x` 环境实际位于 `/dev/shm`，且其 editable `mmrotate` 指向当前不存在的 `third_party/ai4rs`。

   在这三项恢复前，新服务器可以继续只读审计和 measurement-only 写作，但不能声称训练/推理环境已经无缝恢复。

## 2. 当前权威科学状态

### 2.1 最新完成轮次

最新服务器结果入口：

```text
dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md
```

对应持久化证据：

```text
outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/
```

该轮已完整执行 Track M、Track D、独立 validator 和四项 mutation test，完成分类为 `FULL_COMPLETION`，不是技术早停。

核心结果：

- Track M：`METRIC_REVERSAL`；S0 在部分 NRC/AURC 上占优，但在固定 coverage 风险或 AUGRC 上出现反向结论，不能支持稳定方法候选。
- Track D：AI-TOD-R=`LICENSE_BLOCKED`、UAV-OBB=`MISSING_ASSET`、ShipRSImageNet=`LICENSE_BLOCKED`、ICDAR-MLT=`CONTAMINATED`。
- 联合门控：`FAIL_TO_MEASUREMENT_ONLY`。
- 未授权下一轮方法实验，也未授权新目标域 outcome。

### 2.2 必须保留的历史裁决

- `r014`：`FAIL_PROTOCOL_R014`。
- `r015`：数值仅可标记为 `EXPLORATORY_CORE_SUPPORT_R015`。
- `r016/r017/r018`：保留其独立复核和协议漂移审计，不能把它们改写成正式方法成功。
- `r019`：后续权威裁决为 `INVALIDATED_R019 / PROTOCOL_DRIFT_R019 / FAIL_IMPLEMENTATION_R019 / FAIL_TIMELOCK_R019`；其数字只能作为 descriptive-only 历史记录。
- G2_double_prime：仍只是 target-GT-fitted diagnostic upper bound，不是 deployable selector。
- A 工作线的 measurement protocol、几何归一化风险、scene-aware 统计和人工标注审计仍有效；广泛 deployable risk-control claim 不成立。
- 旧 B 机制的 `PASS_MECHANISM_BOUNDED` 是历史结果，不能越过最新 `FAIL_TO_MEASUREMENT_ONLY` gate 自动启动后续修复工作。

### 2.3 当前稿件与执行状态

当前最新活动稿件：

```text
top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md
```

其定位必须保持 measurement/diagnostic，r015 数值必须明确为 exploratory。不能恢复顶会、强可部署或跨域正式保证表述。

当前 `dis/sug.md` 对应的可行性审计已经执行完毕，**新服务器不得重复执行**。`dis/review_state.json` 中仍残留 `NOT_STARTED/READY_FOR_SERVER_FEASIBILITY_GATE` 字段，是未在受限写路径中回填的旧控制状态；判断完成状态时应以最新服务器报告、持久化 `joint_gate.json` 和 `claude_code_and_supervisor.md` 的最终记录为准。

新服务器的第一科学动作应是：等待用户或监督员下发新的正式指令。不得从旧迁移报告推断下一编号，也不得自行恢复 B6、Deployable 或新数据集路线。

## 3. 冻结不变量

以下内容迁移前后都不得修改：

- `configs/thresholds.yaml`：SHA-256 `b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`。
- 正文几何主口径：`ar>=2.1`；`ar>=1.6/1.3` 仅为 sensitivity。
- D_cal / D_audit split 及其正式/探索性身份。
- DIOR 正式结果的 full-val lineage；旧 partial-GT 数字不得恢复。
- DOTA#20 不得进入正式结果。
- image/scene 是风险审计的 exchangeable unit；instance-i.i.d. 只能作经验对照。
- 阈值后空 selected scene 记为 abstained，不得以零风险稀释总体。
- SODA-A 不得声称严格 mother-scene guarantee。
- target-GT-fitted nonlinear geometry 只能称 diagnostic/calibration upper bound。
- 正式主表不得依赖 `/dev/shm`。

冻结 split 的 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `D_cal_dior_trainval.csv` | `f624a21451de394a35041af35c9a910c3a1bdc11fb5c942d15416e04e0e6f632` |
| `D_audit_dior_trainval.csv` | `11c61be3a03c922b5e00e4cf9e866cf73e18eff44bd6b868b53f54612065669b` |
| `D_cal_fair1m_train.csv` | `84b32cb5e0bd9a7afdc772f824e1b64f9daaca54fccdbbb98750180bc04b16a0` |
| `D_audit_fair1m_train.csv` | `140ef6855909cdca2904656ad76baca31ff11d8c571e3978e005d945440c335e` |
| `D_cal_dota10_train.csv` | `48a0319a1ea51fcbadf43e7e632d5a77f77d3db73442acfd639acb0c455daed4` |
| `D_audit_dota10_train.csv` | `d4fb9a793a4c2f31ddd42cde0ba8c571114e78b2ab0d3af36002f201fafc1eb7` |
| `D_cal_dota15_train.csv` | `aa59e4266872c2f3f48b6c027798255e21fae64b09519a895d3ba8deb85b9364` |
| `D_audit_dota15_train.csv` | `ac97d1f3f2a780f79019612fce6f7f93d13aa9f7a65c4f1c14aa96447e743856` |
| `D_cal_hrsc_trainval.csv` | `bbaf79002ad683893292101744e32e379d711f14ab7c187ae5bad42d2e37bdb0` |
| `D_audit_hrsc_trainval.csv` | `55734ae8aa3f49350186fd066a761a54fe1a99921897012c5e59ca1fdf9f6679` |

这些文件位于 `outputs/bench_core/splits/`，属于 Git ignored runtime，必须随非 Git 资产迁移。

## 4. 项目物理盘点

### 4.1 总体

| 路径 | 当前占用 | 处理原则 |
|---|---:|---|
| 项目总计 | 34 GiB | 迁移主体 |
| `outputs/` | 27 GiB | 必须迁移，除非按本报告逐项授权删减 |
| `outputs/persistent_artifacts/` | 25 GiB | 主要科学证据，默认全部保留 |
| `top_journal_v3_reaudit_055/` | 5.7 GiB | A/B/G0、K2、人工标注与论文资产，必须迁移 |
| `top_journal_v3_reaudit_055/work_dirs/k2/` | 3.5 GiB | 正式 K2 checkpoint 和失败审计，默认保留 |
| `top_journal_v3_reaudit_055/paper_A_orientation_protocol/risk_logs/` | 1.1 GiB | 名称虽含 logs，实际为风险复算输入，不得按普通日志删除 |
| `top_journal_v3_reaudit_055/paper_B_psc_mechanism/artifacts/` | 614 MiB | 历史 B 机制/外部变体证据，保留 |
| `top_journal_v3/` | 1.2 GiB | 含仍被脚本引用的大型表，保留 |
| `.git/` | 661 MiB 左右 | 不在源树清理；新服务器建议重新 clone |

项目内共有约 43,485 个普通文件、3,841 个软链接。Git ignored 文件约 42,268 个，是迁移不可省略的主体。

### 4.2 必须迁移的关键科学资产

至少包括：

- `outputs/persistent_artifacts/m069_psc_phase1/`（约 5.7 GiB）；
- `outputs/persistent_artifacts/orientbench_v2/`（约 3.9 GiB）；
- `outputs/persistent_artifacts/m069_fullval_reliability/`；
- `outputs/persistent_artifacts/m4_third_dataset_070/`；
- `outputs/persistent_artifacts/orientbench_r014/`；
- `outputs/persistent_artifacts/orientbench_r019/`；
- `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/`；
- `outputs/persistent_artifacts/orientbench_real_052/`、`orientbench_v2_047/`、`k1_table1_fullval_065/`；
- `top_journal_v3_reaudit_055/work_dirs/k2/` 中 PSC/CSL/DCL 正式 checkpoint；
- A 的 scene/risk 原始表、toolbox 和人工标注原始输出；
- B 的 b3/b4 persistent dumps、checkpoint、identity/AP audit；
- `top_journal_v3/reports/tta_circular_variance_full_052.csv` 和 `psc_phase_mod_permatched_full_052.csv`；
- `dis/`、`docs/`、`reports/`、`scripts/`、`configs/`、`p3_selector/`、`claude_code_and_supervisor.md`；
- `outputs/bench_core/splits/` 中的冻结 D_cal/D_audit。

最新证据的关键哈希：

| 对象 | SHA-256 |
|---|---|
| `AGENTS.md` | `421b83ddd8b326f187753795be0682974e9b99bdbeb9b0369b7f1b31fd7a4034` |
| 当前 `dis/sug.md` | `3448a1c61ecff35c3dd04de4d76db51a12784c3f46a84170f3076c7a700096a8` |
| 最新 server report | `43a7ee2a99590db6a54cc7fcbc7598a8f12e746719f2c682e01d22d2753c0c3a` |
| 最新 feasibility evidence manifest | `acad47663d20df3425e69b4a71496557cc4d98f14f44a1c1d8dce5b1e6203a04` |
| 当前活动稿 r015 | `d71e7875b0d8ba78badd2112cc8e52a1fa2838880a3e620f9deebab4ffed03ae` |

## 5. 清理审计：本轮未执行删除

### 5.1 低风险候选：授权后可删除

这些内容不会改变科学数字，但回收空间很小：

| 候选 | 规模/数量 | 风险与建议 |
|---|---:|---|
| `__pycache__`、`.pytest_cache`、`*.pyc` | 约 1 MiB | 可重建 |
| `.dist_test/` | 空目录，4 KiB allocation | 可删除 |
| 其它明确空目录 | 约 40 个 | 排除带 `.gitkeep` 或结构约定后可删 |
| `CLAUDE.md.bak` | 10,230 bytes | 已由 `AGENTS.md` 取代 |
| `项目执行文件.md.bak` | 18,552 bytes | 已由 v2 和正式记录取代 |
| `top_journal_v3_orientation.log` | 827 bytes | 根目录旧日志，可删除 |
| `realign_sgd_v2_20260515/` | 约 380 KiB | Git ignored、当前无路径引用的旧 scratch，可删除 |
| `outputs/training/_preflight_subset15/` | 约 992 KiB | 旧 smoke/preflight 软链接树，可在保留报告后删除 |
| 失效 FAIR1M 软链接 | 522 条 | 521 条位于 `outputs/predictions/.../_root`，1 条位于 `data_prep`；不占实际图片空间，可重建 |

全部低风险项预计仅释放 **小于 3 MiB**，主要价值是减少迁移噪声，而不是节约磁盘。

### 5.2 条件候选：可冷归档，但不建议直接删除

| 候选 | 规模 | 当前角色 | 删除代价 |
|---|---:|---|---|
| `outputs/persistent_artifacts/orientbench_r010/` | 3.6 GiB | r010 历史完整复算输入 | r011 科学上后继，但 r010 的旧 SODA payload 和运行身份将不能原位复算 |
| K2 `direct_regression_le90` 六个失败 checkpoint | 894,963,712 bytes | 失败训练法证 | 结论可由表/日志保留，但物理 checkpoint identity 和旧 candidate gate 会变为缺失 |
| `outputs/probes/c1_cross_view_real/` | 1.2 GiB | P2/C1 appendix/negative evidence | 失去 C1 物理 cross-view 原位复算能力 |
| `measure_fix_v2/artifacts/` | 490 MiB | 旧 measure/fix 资产 | 多个历史脚本仍有路径引用，删除后只能保留摘要结果 |

`orientbench_r010` 与 `orientbench_r011` 中有 10 个逐字节相同文件，共 **2,522,133,322 bytes**；r010 仍有 **1,312,790,020 bytes** 是独有或不同版本。不得只按文件名删除重复项，因为两轮 manifest 和脚本引用各自路径。更合理的选择是：保留原目录、在迁移归档层使用 hard-link/dedup，或将整个 r010 冷归档。

上述条件候选合计约 **6.5 GiB**。只有用户明确接受“历史轮次不能原位完整复算”后，才能生成精确删除清单并执行。

### 5.3 当前禁止删除

- 所有最新 feasibility、r019、r014、m069、K1/K2 正式证据；
- `paper_A_orientation_protocol/risk_logs/`；
- 人工标注原始 CSV/JSON、匿名映射、crops/images 和 recheck；
- K2 PSC/CSL/DCL 正式 checkpoint；
- B4 三 seed checkpoint 和 instrumented dumps；
- `top_journal_v3` 两个大型 052 表；
- thresholds、D_cal/D_audit、manifest、validator、bootstrap 和 mutation evidence；
- `claude_code_and_supervisor.md`；
- Git history。

`/dev/shm/cqc/orientbench` 不在项目根内。它已另行审计为约 88 MiB scratch，三份 DIOR raw 均有 SHA-256 相同的持久化副本；可单独授权删除，但它不进入本项目迁移包。

## 6. Git 状态与迁移前阻塞

审计时本地状态：

```text
branch: main
local HEAD: cdf764c5a974030739a9992079bedb8b970fb2a7
local cached origin/main: ef1b2cd93cfb2ebcb8625befd15bf561add2c10e
remote main observed by git ls-remote: 9588a095cc459acbd5de54d756343ad7db945956
```

本地 `origin/main` 引用未刷新，因此此前显示的 `ahead 6` 不能直接用于迁移决策。远端已经出现本地未核验的新 SHA。迁移前必须在不丢弃本地工作的前提下执行：

```bash
git fetch origin main
git log --graph --oneline --decorate --left-right HEAD...origin/main
git merge-base --is-ancestor HEAD origin/main
git merge-base --is-ancestor origin/main HEAD
```

不得用 `reset --hard`、`clean`、force-push 或 checkout 丢弃任一侧。若远端是本地 HEAD 的后继，使用 `git pull --ff-only`；若确实分叉，必须先报告用户并单独裁决。

生成本报告前，既有工作树只有 `claude_code_and_supervisor.md` 的审计追加记录；没有其它未跟踪非 ignored 文件。生成本报告后，本报告本身和新的追加记录也必须在迁移前形成明确 commit 并推送。未完成 Git 同步前，不得删除源服务器项目。

旧 `.orientbench_transfer_parts/` 当前不存在，2026-07-24 的五分片迁移包不能作为本次恢复来源。

## 7. 项目外必须迁移或重建的依赖

### 7.1 数据集

数据集不在 Git 项目内，当前源路径及占用：

| 数据集路径 | 规模 |
|---|---:|
| `/home/rspip/cqc/data/dataset/fair1m1.0` | 80 GiB |
| `/home/rspip/cqc/data/dataset/dota` | 72 GiB |
| `/home/rspip/cqc/data/dataset/SODA-A` | 25 GiB |
| `/home/rspip/cqc/data/dataset/DIOR` | 7.5 GiB |
| `/home/rspip/cqc/data/dataset/HRSC2016` | 3.9 GiB |

合计约 188 GiB（`du -sh` 口径）。建议目标服务器保持完全相同的绝对路径，否则项目内 3,841 条软链接和大量历史 config 需要统一重映射。

当前 522 条 FAIR1M 链接指向不存在的 `fair1m1.0/split/val_20/images` 文件；迁移时不要把“数据集根存在”误判为所有派生 split 完整。可在目标服务器从 frozen split manifest 重建这些链接，不能以其它 FAIR1M split 静默替换。

### 7.2 pth_data baseline 库：当前缺失，属于硬 blocker

项目规则要求先读：

```text
/home/rspip/cqc/pro/study/pth_data/readme.md
```

该路径在 2026-08-10 审计时不存在，项目内 `pth_data/` 也为空。2026-08-09 最新审计曾读取到：

```text
bytes: 89032
sha256: eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c
```

因此迁移前必须从可靠备份恢复整个外部 `pth_data` baseline 库，并首先核验 `readme.md` 的 bytes/SHA。只恢复 readme 而不恢复其登记的 config/log/checkpoint 不能算 baseline 环境闭合。该库未恢复前，Codex 必须停止任何新训练、推理或 baseline 实验设计。

### 7.3 third-party / ai4rs：当前 editable 安装断开

主要运行环境 `mr_dev1x` 的 `mmrotate==1.0.0rc1` 是 editable 安装，指向：

```text
/home/rspip/cqc/pro/study/third_party/ai4rs
```

该源码目录当前不存在，所以 `import mmrotate` 失败。历史报告登记的 ai4rs source commit 为：

```text
6095d3a3155570324e9e01c88cd2e4a3b55ae7c3
```

新服务器应从可靠备份或项目上游恢复该精确版本到上述路径，再执行 editable install。部分旧脚本还引用 `/home/rspip/cqc/pro/study/ai4rs_clone`；若需复放这些旧训练/推理脚本，应把它映射到同一核验后的源码，而不是下载任意最新版本。

第三方源码不得直接改；配置仍应复制进 OrientBench 后再改。

## 8. Python/CUDA 环境

### 8.1 当前主要统计/新框架环境

`mr_dev1x`：

- Python 3.10.20；
- PyTorch 2.4.0+cu121；
- torchvision 0.19.0+cu121；
- mmengine 0.10.7；
- mmcv 2.2.0；
- mmdet 3.3.0；
- mmrotate 1.0.0rc1（editable，当前 source 缺失）；
- numpy 1.26.4；
- pandas 2.3.3；
- pyarrow 17.0.0；
- scipy 1.15.3；
- scikit-learn 1.7.2。

该环境在 `/home/rspip/anaconda3/envs/mr_dev1x` 下表现为环境，但物理路径实际解析到：

```text
/dev/shm/cqc/data/conda_envs/mr_dev1x
```

因此不能把 `/home/rspip/anaconda3/envs/mr_dev1x` 当作持久化资产直接迁移。应在目标服务器持久磁盘重建环境，并重新安装已核验的 ai4rs source。

### 8.2 历史框架环境

- `mr`：Python 3.8.20、torch 1.12.1+cu113、mmcv-full 1.7.2、mmdet 2.28.2；用于部分 0.x/legacy 资产。
- `arsdetr`：Python 3.8.20、torch 1.9.0+cu111、mmcv-full 1.5.0、mmdet 2.25.1；仅在复放 ARS-DETR 历史单元时需要。

不要强行把所有 checkpoint 放进同一个环境加载。根据 manifest/config 中的 framework lineage 选择对应环境。

### 8.3 硬件基线

源服务器：4 x NVIDIA A30 24 GiB，driver 550.54.15。项目规则要求训练默认 4 GPU；CPU 密集 bootstrap 至少使用 48 核中的 39 核。新服务器即使配置相近，也必须重新记录 GPU、driver、CUDA、CPU 核数和实际环境路径。

## 9. 推荐迁移流程

### 9.1 源服务器迁移前

1. 等待用户批准清理级别；未批准前不删除任何候选。
2. 恢复或定位 `pth_data` 和 ai4rs source。
3. 核验无本项目训练、推理、bootstrap、annotation server 或 watcher 进程。
4. `git fetch` 后解决本地/远端 main 关系；提交并推送本报告及记录。
5. 生成迁移时点的文件清单和 SHA-256。大文件可优先依赖已有 evidence manifest，再对迁移归档本身做整体 SHA-256。

### 9.2 目标服务器 Git 初始化

只有源端 Git 已经同步完成后才执行：

```bash
mkdir -p /home/rspip/cqc/pro/study
cd /home/rspip/cqc/pro/study
git clone git@github-ziyu24:ziyu24/orientbench.git orientbench
cd orientbench
git switch main
git pull --ff-only origin main
git rev-parse HEAD
git status --short --branch
```

如果新服务器用户名或根路径不同，先不要批量替换历史报告中的绝对路径；只修复运行 config、环境和软链接。历史 provenance 文本中的源路径必须原样保留。

### 9.3 迁移 Git ignored 科学资产

推荐在 Git checkout 完成后，以 `rsync` 传输项目内非 Git 大资产。最稳妥方式是复制整个工作区但排除 `.git` 和明确批准的缓存项：

```bash
rsync -aH --numeric-ids --info=progress2 \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='.pytest_cache/' \
  --exclude='*.pyc' \
  /home/rspip/cqc/pro/study/orientbench/ \
  NEW_HOST:/home/rspip/cqc/pro/study/orientbench/
```

在源端 Git 尚未同步时，不要运行该命令，以免用旧 tracked 文件覆盖目标端新 commit。若只传 ignored 文件，应先固定并保存列表：

```bash
cd /home/rspip/cqc/pro/study/orientbench
git ls-files -z --others -i --exclude-standard > /tmp/orientbench_ignored_files.zlist
rsync -aH --from0 --files-from=/tmp/orientbench_ignored_files.zlist ./ \
  NEW_HOST:/home/rspip/cqc/pro/study/orientbench/
```

迁移工具必须保留软链接本身，不能默认跟随链接把 188 GiB 外部数据集重复打进项目包。

### 9.4 外部资产

按独立任务迁移：

- `/home/rspip/cqc/data/dataset/`；
- `/home/rspip/cqc/pro/study/pth_data/`；
- `/home/rspip/cqc/pro/study/third_party/ai4rs/`；
- 必要的 conda 环境导出文件或 package lock，而不是 `/dev/shm` 环境目录本身。

外部数据集不应提交 Git，也不应混入 OrientBench 项目归档。

## 10. 目标服务器验收

### 10.1 文件与 Git

```bash
cd /home/rspip/cqc/pro/study/orientbench
git status --short --branch
git rev-parse HEAD
du -sh . outputs outputs/persistent_artifacts top_journal_v3_reaudit_055
find . -xdev -type f | wc -l
find . -xdev -type l | wc -l
find -L . -xdev -type l | wc -l
```

broken symlink 数量可以因重建 FAIR1M `val_20` 派生目录而减少，但不能通过把链接随意改到另一 split 来“清零”。

### 10.2 冻结资产

```bash
sha256sum configs/thresholds.yaml
sha256sum outputs/bench_core/splits/D_cal_* outputs/bench_core/splits/D_audit_*
sha256sum AGENTS.md dis/sug.md
sha256sum dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md
sha256sum outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/evidence_manifest.json
```

结果必须与本报告第 3、4 节一致。

### 10.3 环境 smoke test

```bash
/home/rspip/anaconda3/envs/mr_dev1x/bin/python - <<'PY'
import torch, mmengine, mmcv, mmdet, mmrotate
import numpy, pandas, pyarrow, scipy, sklearn
print(torch.__version__)
print(mmengine.__version__, mmcv.__version__, mmdet.__version__)
print(mmrotate.__file__)
PY
```

`mmrotate.__file__` 必须解析到目标服务器持久化的 ai4rs source，而不是 `/dev/shm` 或源服务器路径。

### 10.4 只读 evidence validation

在新服务器第一次接手时，只运行已有只读 validator，不重跑训练/推理或产生新 outcome。优先验证最新 feasibility evidence manifest 和 frozen hashes。任何 validator 因绝对路径变化失败时，先区分：

- 科学输入哈希/行集合真的改变；
- 仅 source host 绝对路径被历史 manifest 固定。

不得为通过 validator 而修改已冻结 manifest。必要时新增迁移层 path mapping，并把旧 manifest 保持只读。

## 11. 新服务器 Codex 接手顺序

Codex 必须按以下顺序读取：

1. `AGENTS.md`；
2. 本报告；
3. `/home/rspip/cqc/pro/study/pth_data/readme.md`；若缺失立即停止实验设计；
4. `claude_code_and_supervisor.md` 的末尾记录；
5. `dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`；
6. `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/joint_gate.json`、`validator.json`、`evidence_manifest.json`；
7. `dis/C.md`、`dis/B.md` 和 `dis/collaboration_protocol.md`，只用于理解监督与证据关系；
8. 当前 measurement-only 稿件和对应 claim 边界。

接手后的第一轮只能做：

- Git/文件/hash/环境/数据路径/后台进程审计；
- 确认迁移完整性；
- 报告缺失资产和路径差异。

在用户下发新正式命令前，不得：

- 重跑 `dis/sug.md`；
- 训练、推理、下载新数据或访问新目标标签；
- 恢复 r019 正式性；
- 继续 B6/Deployable/Track A；
- 修改 thresholds 或 D_cal/D_audit；
- 将 exploratory 改成 formal；
- 追 DOTA public mAP；
- 宣称项目、论文或投稿已经完成。

## 12. 已知 blocker 与迁移放行条件

### 12.1 当前 blocker

1. **Git 未闭合**：远端 main SHA 与本地缓存引用不同，尚未在本轮 fetch 后验证祖先关系。
2. **pth_data 缺失**：违反新实验前置规则。
3. **ai4rs source 缺失**：`mr_dev1x` 的 editable mmrotate 无法导入。
4. **conda 环境在 `/dev/shm`**：不能作为持久化迁移源。
5. **522 条 FAIR1M 派生图片链接失效**：虽不阻塞最新只读统计，但阻塞相应图像级复放。

### 12.2 放行条件

只有以下全部满足，才能认为“新服务器可无缝接手”：

- [ ] 用户批准并完成选定清理项，或明确选择完整迁移；
- [ ] 本地与远端 main 关系闭合，迁移报告已提交并推送；
- [ ] 项目 ignored 科学资产完成传输并通过校验；
- [ ] 五个外部数据集路径存在且 split/schema 可读；
- [ ] `pth_data/readme.md` 恢复为 89,032 bytes 和登记 SHA，相关 baseline 资产可读；
- [ ] ai4rs source 恢复到登记 commit，`mmrotate` 可导入；
- [ ] `mr_dev1x` 在持久磁盘重建，关键包版本通过 smoke test；
- [ ] thresholds、D_cal/D_audit 和最新 evidence manifest 哈希一致；
- [ ] 无遗留训练、推理、bootstrap 或 annotation server 进程；
- [ ] 新 Codex 已确认最新 gate 为 `FAIL_TO_MEASUREMENT_ONLY`，并等待下一条正式指令。

## 13. 本轮审计合规

- 未删除任何内容；
- 未移动或覆盖历史资产；
- 未训练、推理、评估或重算科学结果；
- 未修改 thresholds、D_cal/D_audit 或 formal/exploratory 标签；
- 未写入新的方法结论；
- 只新增本迁移/清理/接手文档，并按项目规则追加监督记录。
