execution_completion: FULL_COMPLETION
scientific_verdict: PASS_DEPLOYABLE_EQS_R014
last_completed_phase: manifest_validator_commit_push
early_stop_trigger: NONE
unrun_required_phases: []
core_status: PASS
hrsc_status: INCONCLUSIVE
push_status: PUSHED

# OrientBench r014 服务器执行报告

## 1. 决策结论

本轮完成 FAIR1M 完整总体修复、Core-6 EQS 全流程和条件式 HRSC 独立确认。Core 为 `PASS_DEPLOYABLE_EQS_R014`：6/6 evaluation units 与 3/3 dataset aggregates 均满足冻结的 Delta NRC、区间和 Holm 门。HRSC2016/LSKNet 为 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`：点估计为正但区间跨零。因此可以写 Core 内无需目标域角标签的选择改善，不能写跨 host 的普遍迁移。

r012 的历史分类不变：`execution_completion=INCOMPLETE_EARLY_STOP`、`scientific_verdict=FAIL_PROVENANCE_R012`、`r012_eqs=NOT_EVALUATED`、`r012_hrsc=NOT_EVALUATED`。r014 是来源修复后的新证据轮次，不是改判 r012。

## 2. 前置清理与来源闭合

用户授权删除的 12 个 warning-only、未跟踪 `risk_logs/*.err` 已删除；对应 JSONL 科学结果未删除。之后工作树满足科学执行前置要求。

FAIR1M frozen val universe 实测为 4,362 images / 78,644 GT。历史 3,896-row raw 不再进入 r014；使用冻结 FAIR/24 config、checkpoint、阈值、NMS 和 class map，以 4×A30 重建 identity/hflip/vflip。identity 为 4,362 rows / 488,194 predictions，AP50/AP75=0.3461586/0.2422395，与权威 0.3462/0.2422 的绝对差均小于 0.002。DIOR-R 三单元和 SODA-A 两单元 official evaluator parity 也全部通过。SODA-A 22,994 tiles 到 576 mother scenes 的映射无缺失、歧义或重复。

## 3. EQS 实现与封存

三视图关联在逆 h/v 变换后按同类 rotated-IoU>=0.3 做确定性一对一匹配。预测侧特征包含双视图支持、归一化角轴差、IoU 损失、中心/宽高/分数离散、匹配余量与缺失率；feature schema 不含 GT、angle error 或 risk 字段。source-only nested CV 共 12 行，未触发 early stop。

每个目标模型完全排除目标数据集，只使用其它数据集的 `D_cal-fit`；feature、model 和 target score 在目标 `D_audit` 角标签接入前以 SHA-256 封存。比较使用 1,000 次配对 image/mother-scene bootstrap，同一 replicate 在 selector 间同步；unit 和 dataset 分别 Holm-6/Holm-3。

## 4. Core 科学结果

| evaluation unit | Delta NRC | 95% CI | Holm-6 p | support |
|---|---:|---:|---:|---:|
| DIOR-R/22 | 0.1608 | [0.1261, 0.1958] | 0.0060 | yes |
| DIOR-R/3 | 0.0925 | [0.0562, 0.1301] | 0.0060 | yes |
| DIOR-R/61 | 0.2667 | [0.2343, 0.3030] | 0.0060 | yes |
| FAIR1M-v1.0/24 | 0.2436 | [0.2043, 0.2845] | 0.0060 | yes |
| SODA-A/23 | 0.2450 | [0.1657, 0.3168] | 0.0060 | yes |
| SODA-A/4 | 0.0839 | [0.0371, 0.1448] | 0.0060 | yes |

| dataset aggregate | Delta NRC | 95% CI | Holm-3 p | support |
|---|---:|---:|---:|---:|
| DIOR-R | 0.1733 | [0.1530, 0.1936] | 0.0030 | yes |
| FAIR1M-v1.0 | 0.2436 | [0.2043, 0.2845] | 0.0030 | yes |
| SODA-A | 0.1645 | [0.1190, 0.2150] | 0.0030 | yes |

所有 unit 点估计超过冻结的 0.02 最小效应，CI 下界大于零；支持覆盖三个数据集与三个 detector families。FAIR/24 明确支持。Core gate 因而通过。

## 5. HRSC 独立确认

唯一既有资产绑定为 HRSC2016 test 453 images、LSKNet-S Oriented R-CNN、epoch-33 checkpoint。使用原训练尺度 800×800 和冻结 checkpoint 做 4-GPU 三视图推理；identity 得到 1,634 predictions，official AP50/AP75=0.90524/0.89452，与训练日志 0.905/0.894 一致。

EQS 使用全部 Core 数据集 `D_cal-fit`，三数据集总权各 1/3；HRSC feature 和 score 在读取 HRSC GT 前封存。`ar>=2.1` eligible matches 为 1,217，来自 438 images。相对 linear 的 Delta NRC=0.06017，95% image-cluster CI=[-0.01432, 0.14380]；EQS 相对 standalone equivariance 的点差为 0.00997。由于确认区间跨零，判定为不确定，而非 PASS 或性能失败。

## 6. 稿件与主张边界

r014 稿改为 measurement→diagnose→select：保留 full-validation AP、`ar>=2.1`、场景统计、人工双标、旧 leave-dataset 0/6 与 identifiable leave-detector 4/5；新增 Core EQS 结果及 HRSC 不确定边界。删除 r012 中“FAIR raw 未闭合、EQS 未运行”的 superseded 文字。仍禁止宣称 universal general transfer、distribution-free target guarantee 或 HRSC confirmation PASS。

## 7. 资源、合规与复现

- detector training：0；仅冻结 checkpoint inference。
- GPU forward：FAIR、DIOR 三单元和 HRSC 均使用 4×A30；没有 OOM 降卡。
- feature build：38 workers，BLAS threads=1；bootstrap 配置 38 workers。
- Core paired bootstrap：6,000 unit replicates + 3,000 dataset replicates；HRSC：1,000 image replicates。
- thresholds、D_cal/D_audit、split、class map、NMS 和历史 r009-r013 资产均未修改。
- runtime raw、features、models、scores、seal 与日志均持久化在 gitignored `outputs/persistent_artifacts/orientbench_r014/`，无 `/dev/shm` 主依赖。
- `dis/B.md` blob 保持 `3181a862137918f1dd41677893937c12b3c39c28`。
- 本轮曾发现并清理两个由本项目旧 evaluator 调试遗留的无产出睡眠进程；最终无 r014 后台进程。

只读 validator 动态核对完整 FAIR universe、raw prediction count、AP parity、transform、prediction-only feature schema、prelabel seal、source CV、1,000 replicates、Holm/minimum effect、Core/HRSC gate、稿件 claim hash、写入范围及受保护 blob。最终输出应为 `VALID_R014_FULL_COMPLETION`。

## 8. Git

最终仅显式暂存 r014 精确授权集合，执行 `git diff --check`、validator、单一中文 commit，并推送当前 `main`。push 完成后再发送唯一最终汇报。
