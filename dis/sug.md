# OrientBench r013：投稿稿基础事实修订与可执行文本门

- round: `orientbench-c-r013-20260808`
- evidence snapshot: `d76e3837c43987bfdcf134ceecc5f7ff3ab9f292`
- input manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r013.md`
- unique report: `dis/server_reports/orientbench-c-r013-20260808.md`
- mode: **manuscript-only foundation repair；无新科学计算**

本轮只回答一个问题：在不新增实验、不更改 r012 科学裁决的前提下，measurement→diagnose 稿能否清除已知事实错误、失效证据与估计总体混淆，形成可进入投稿前对抗审查的干净草稿？

开始前只允许 `git pull --ff-only`。核对 origin、当前/默认/upstream 分支、完整 HEAD、工作树与 index；execution HEAD 必须包含 evidence snapshot `d76e3837...`。禁止 merge/rebase/reset/clean/force。

## 1. 冻结科学裁决

- r012 科学门为 `FAIL_PROVENANCE_R012`：FAIR1M raw仅3,896/4,362 image rows，EQS未执行fit、target label attach、bootstrap或独立确认。
- 当前 EQS/顶会方法线永久关闭。禁止重跑r012、补FAIR forward、换selector、换unit、换gate、修改0.02最小效应或从旧TTA续命。
- 历史leave-dataset为0/6；可识别leave-detector为4/5且fit含同数据集sibling units。只可写负迁移结构。
- r011 fixed-dose只可称 single-evaluator descriptive candidates；不得恢复confirmatory CI、统一knee、NMS因果或formal certification。
- 当前 venue 仍为 strong-JSTARS potential、尚未 ready。r013 PASS不等于TGRS/ISPRS/CVPR/ICCV-ready。

## 2. 硬禁止

- 训练、推理、transform smoke、feature build、selector fit、target label attach、bootstrap、evaluator或HRSC确认一律为0。
- 不读取或修改dataset、checkpoint、raw prediction、D_cal/D_audit、threshold、split、NMS、class map、r009/r010/r011/r012科学资产。
- 不修改 `dis/B.md`，不启动CC，不改历史稿件；只创建新的r013稿及其文本审计资产。
- 不引入新的科学数字。若现有数字无法从冻结来源闭合，删除或降级，不得猜测。

## 3. 必须完成的稿件修订

### 3.1 删除无效认证消费

完整删除 r012 §6.5 的 instance/tile/mother UCB 数字表及所有依赖该失效历史认证链的 `unique practical point`、certified/certification 成功叙述。可以保留不带这些失效数字的原则性结论：统计单位与abstention会改变风险解释；正式认证需要独立生成链。

不得在其它章节、摘要、图注、claim ledger中重贴以下表头组合：`instance-i.i.d. UCB`、`tile/image UCB`、`mother UCB`。

### 3.2 闭合估计总体

在连续角风险排序与固定尺寸分箱的章节标题、表注或紧邻正文中明确写出：这些结果使用冻结 `D_audit` 估计总体；selector fit（如有）只用独立 `D_cal-fit`。明确区分：

- full-validation AP/经验容忍角表；
- `D_audit` 上的NRC/AURC与size-bin诊断；
- target-GT geometry只为diagnostic upper bound。

解释同一单元 full-validation tolerance n 与 D_audit retained n 不同的原因，禁止再用笼统 `full-validation matched predictions` 覆盖两种估计对象。

### 3.3 修正一手引用

通过一手论文页面、官方CVF/IEEE/期刊记录核对并修正：

1. DIOR基础数据集论文；
2. AOPG发布DIOR-R的一手论文；
3. PSC官方论文作者为 Yi Yu 与 Feipeng Da。

2016 RICNN不得继续承担DIOR/DIOR-R数据集出处；若正文确实需要作为检测方法先例，可在准确语境另行引用。参考文献条目必须包含可唯一识别的题名、venue、年份与DOI或官方URL。禁止使用期刊首页、会议首页、`arXiv.org/`根页或未来会议占位链接支撑novelty。

### 3.4 保留已完成修正

- FAIR1M本地train_80/val_20=`18,505/4,362 images`；
- DOTA统一 `ar>=2.1` NRC=`0.7544/0.7113`；
- leave-dataset `0/6` 与可识别leave-detector `4/5`分层；
- r012 provenance stop不是EQS性能结果；
- 固定剂量descriptive-only；
- 不含内部round/PASS/FAIL/venue-ready/authorized-path/validator术语。

### 3.5 Claim ledger与novelty matrix

新建 `claim_ledger_r013.csv`，至少绑定：几何阈值、K1约束扰动、D_audit排序、size-bin诊断上界、0/6与4/5、r012来源早停、真人双标。每条保存精确原句SHA、证据row keys、generator/input identity与gate action。

新建 `novelty_matrix_r013.csv`。每个用于正文的工作必须有精确一手来源；身份未闭合的 O2-DFINE、Fourier Angle Alignment 或泛称WACV calibration只可标 `unknown/excluded`，不得作为已核实引用或优先权依据。

## 4. 可执行 validator

新增只读 `validate_submission_r013.py` 与 `manuscript_gate_r013.json`，必须从稿件、ledger、matrix和Git真实内容重算，至少检查：

1. r013稿存在且r012历史稿未变；
2. 无UCB失效表头组合，无内部gate/round/venue-ready token；
3. `D_audit` 在NRC与size-bin两处明确出现，且full-validation与D_audit语义分开；
4. 错误PSC作者字符串 `Yu Y, Yang X, Li Q` 不存在，正确作者存在；
5. RICNN不承担DIOR/DIOR-R出处，DIOR与AOPG条目可由精确一手标识核对；
6. 0.7544/0.7113、18,505/4,362、0/6与4/5口径保留；
7. ledger每条 exact claim存在且SHA重算一致；
8. novelty matrix的正文引用均为精确primary source，unknown项未进入正文；
9. 训练/inference/evaluator/bootstrap/model-fit/target-label计数全为0；
10. 真实Git diff恰为授权集合，`dis/B.md` blob不变。

validator不得只查文件存在，不得信任CSV中的PASS字符串。将每项布尔结果与失败witness写入 `manuscript_gate_r013.json`。

## 5. 合法状态

- `PASS_MANUSCRIPT_FOUNDATION_R013`：全部硬修与validator条件通过。只表示可进入投稿前对抗审查。
- `FAIL_MANUSCRIPT_FOUNDATION_R013`：任一旧错误、失效UCB、估计总体混淆、错误引用、ledger/hash或写入边界失败。
- `INCONCLUSIVE_BIBLIOGRAPHY_R013`：一手来源不可访问或身份冲突；不得用二手来源强行PASS。
- `FAIL_PROTOCOL_R013`：运行任何禁用科学计算、修改历史资产/受保护文件、生成新数字或范围外写入。

不得另造PASS。

## 6. 精确写入集合（8）

只允许创建或修改：

1. `claude_code_and_supervisor.md`（恰好append一个r013 section）
2. `dis/server_reports/orientbench-c-r013-20260808.md`
3. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r013.md`
4. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r013.csv`
5. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r013.csv`
6. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/manuscript_gate_r013.json`
7. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/validate_submission_r013.py`
8. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/manuscript_diff_r013.csv`

只做一个最终中文commit；LF；`git diff --check`零输出；manifest可合并写入gate JSON，不增加第9条路径。只显式暂存上述8条。禁止修改 `dis/B.md`、r012稿/报告/代码、历史论文和其它任何路径。push当前分支，禁止force；失败保留本地commit并报告。

## 7. 唯一最终回复

首行只能是 `执行完毕` 或 `未执行完毕`。

第二行必须且只能是：`dis/server_reports/orientbench-c-r013-20260808.md`
