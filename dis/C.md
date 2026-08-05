# OrientBench C 侧 r003 裁决与 r004 TGRS 杀死门

- round: `orientbench-c-r004-20260805`
- scientific snapshot: `cb0a259f81d9d0cd3af27f514a9e94c75ddf9cbd`
- evidence cutoff: `2026-08-05`
- active manuscript: [`orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md)
- 当前科学状态: A=`A_MEASUREMENT_ONLY`；原 A6=`NO_ELIGIBLE_CONFIRMATORY_UNIT`；B=`RETIRED_FAIL_CANDIDATE_GATE`；submission=`NOT_READY`。
- 当前投稿上限: **strong JSTARS；TGRS high-risk borderline，尚不 credible/ready**。
- `cc_recommendation: no`

当前缺口可以由功效分解、前瞻资产门和一手文献直接裁决。CC 已完成 r001；在新的科学包冻结前再调用不会替代实验，也不会提高证据强度。

## 1. r003 服务器回执裁决

服务器提交 `cb0a259f81d9d0cd3af27f514a9e94c75ddf9cbd`，唯一报告为 [`orientbench-c-r003-20260805.md`](server_reports/orientbench-c-r003-20260805.md)。C 的独立复核结论如下。

| 事项 | 裁决 | 证据与边界 |
|---|---|---|
| `FAIL_NO_A6R_ASSET` | adopt | 38 个项目 checkpoint 与原 A6 的 3 个候选共 41 个精确记录；首失败门为 38 个 prior protocol/outcome participation、2 个 prior outcome exposure、1 个 checkpoint/full-universe 缺失；eligible=0，selected=`NONE` |
| 训练/推理/风险/下载均为 0 | revise | 静态控制流未发现上述操作或 outcome 打开，结论可信；但计数和 `protocol_drift=False` 是硬编码，不是系统调用级 instrumentation |
| “当前服务器没有任何可用模型” | revise | 证据只覆盖已审计的项目 38 个 `.pth`、原 A6 三候选及固定外部资产根；不能外推到服务器所有目录和所有 checkpoint 扩展名 |
| “r003 完全合规” | reject | 新脚本把带账号段的服务器绝对路径写入 Git，违反本轮共享边界；旧结果本身不因此变成可用候选，但该脚本必须先做最小合规修复 |

候选清单、overlap registry 与 gate JSON 的 41 个 ID 完全一致。107 个登记输入中，本机可直接取得的 9 个 tracked 输入及 4 个非自引用输出都与 SHA/Git blob 相符；其余 98 个服务器侧原物约 5.95 GB，C 不能跨机重哈希。置信度：41 候选与首失败门 `0.97`；科学 `FAIL_NO_A6R_ASSET` `0.91`；零 outcome/执行 `0.86`；全部服务器原物哈希链 `0.72`。

因此 r003 是一个有效的“现有资产不足”负门，不是一次成功复现，也不是论文理论失败。A 仍为 measurement-only。

## 2. TGRS 级最强攻击

[TGRS 官方范围](https://www.grss-ieee.org/publications/transactions-on-geoscience-remote-sensing/)要求 novel methodological advancement、significant research，并要求实验数据与条件完整（核查于 `2026-08-05`）。v077 当前有六个优先于扩实验规模的问题。

1. **estimand 不是全检测部署风险。** 风险只在 GT-matched prediction 和“至少一个 eligible match”的场景宇宙中定义，排除了 FP、FN 和真正空场景。正文的 `deployable score` 应改为 `inference-available score`；保证应称为 conditional matched-orientation feasibility audit，而不是全输出认证。
2. **142/144 不可行尚未完成归因。** 现有 calibration scene 数约 `646–1886`；在 `delta=0.1` 时，即使二元 scene event 零失败，`alpha=.001` 也至少需要 2302 个场景。当前负结果混合了样本量上限、事件基率/网格、分数排序和 practical coverage，不能统称“分数失败”。
3. **AP@0.5 零下降部分由构造保证。** 自适应扰动被限制在 IoU 0.50 匹配边界内；缺少完整固定剂量 full-evaluator 曲线时，`ΔAP@0.5=0` 不能单独作为强发现。
4. **实验完整性仍有明示缺口。** 固定剂量原始预测不全，原 A6 无合格单元，第三标注者没有完成；这与 TGRS 的完整性要求直接冲突。
5. **近期直接工作压缩 novelty。** [AQE-Detector](https://www.nature.com/articles/s41598-025-31034-w) 已做角度质量与 NMS，[EAV-DETR](https://hub.hku.hk/handle/10722/372539) 已把 OBB 与 Mondrian conformal guarantee 结合，[SeqCRC](https://arxiv.org/abs/2505.24038) 处理目标检测匹配、空预测和联合风险控制，[航空/卫星目标检测 conformal 工作](https://proceedings.mlr.press/v230/copley24a.html) 已在 2024 年公开。本文不能声称首个角度不确定性或首个遥感 conformal；可守增量只能是 OBB-specific、scene-aware、conditional matched-orientation 的系统测量与功效边界。
6. **TTA 事实口径冲突。** 冻结协议保持 eligible universe 并把非有限 TTA 排到末位，正文却写“NaN 不进入指标”。主稿后续必须披露 DIOR-R `298/48282=0.617%`、SODA-A `2104/193045=1.090%` 的缺失率。

## 3. 可证伪候选与最低 gate

| 候选 | 实质差异 | 最低判别实验 | 杀死条件 |
|---|---|---|---|
| C1：OBB-specific conditional orientation measurement | 明确把检测正确性、朝向风险、几何可辨识性和场景相关性分层，不声称通用部署认证 | 固定 matched-only estimand；增加 full-output joint-risk 敏感性，并验证二者结论是否同向 | full-output 与 matched-only 方向冲突，或必须隐去 FP/FN 才成立 |
| C2：scene-aware finite-sample feasibility/power boundary | 把“分数排序差”与“样本量下任何分数都不可能认证”分开，形成可复算负结果 | r004 对 576 行执行 zero-loss、oracle、score、practical 四层分解；按预先固定的多数门裁决 | target-GT-free 主风险不可行行中，`SCORE_RANKING_LIMIT` 不占多数，则删除“分数主导不可认证”的归因 |
| C3：RSAR×S2ANet 前瞻外部复现 | 新 SAR 数据域与未参与协议设计的新 detector/head exact unit；不是从旧个人项目回收结果 | 先做官方资产 acquisition gate；通过后仅运行一次冻结综合实验 | 许可/字节身份不清、8467 个 val 图像与标注不闭环、split overlap、母景身份不可恢复、checkpoint 严格载入失败或 raw→final 不可持久化 |

### C3 的冻结候选身份

- official repository: [`zhasion/RSAR`](https://github.com/zhasion/RSAR/tree/6594e685de1e592bd66bff5451763380d0d36c53)，commit `6594e685de1e592bd66bff5451763380d0d36c53`
- primary paper: [CVPR 2025 RSAR](https://openaccess.thecvf.com/content/CVPR2025/papers/Zhang_RSAR_Restricted_State_Angle_Resolver_and_Rotated_SAR_Benchmark_CVPR_2025_paper.pdf)
- dataset object: [official Google Drive file `1v-HXUSmwBQCtrq0MlTOkCaBQ_vbz5_qs`](https://drive.google.com/file/d/1v-HXUSmwBQCtrq0MlTOkCaBQ_vbz5_qs/view?usp=sharing)，服务端元数据显示 `5,632,030,720` bytes；官方未给 checksum
- unit: RSAR validation × S2ANet-R50-FPN-le90；[pinned config](https://github.com/zhasion/RSAR/blob/6594e685de1e592bd66bff5451763380d0d36c53/configs/s2anet/s2anet-le90_r50_fpn_1x_rsar.py)
- checkpoint: [official Google Drive file `1xju1PGARP8h767Xr0yNpxNlan8E8hezJ`](https://drive.google.com/file/d/1xju1PGARP8h767Xr0yNpxNlan8E8hezJ/view?usp=sharing)，服务端元数据显示 `166,360,749` bytes；官方未给 checksum
- official public facts: train/val/test images=`78,837/8,467/8,538`，val instances=`16,860`，6 classes，reported val mAP=`33.11`，repository license=`CC BY-NC 4.0`

该身份目前只是 `TIER1_PROVISIONAL`。RSAR 基于十个来源组成的 SARDet-100K，部分来源被切片；官方材料没有提供完整 mother-scene 映射。缺少公开 checksum 也意味着下载后只能冻结“官方 file ID + 本地计算 hash”，不能伪称作者发布 checksum。r004 先裁决现有 headline 的归因；只有 C2 不被杀死，下一轮才获取 C3，避免用 50–60 GB 资产掩盖核心统计问题。

## 4. 决策台账

| 决策 | 状态 | 理由 | 下一步 |
|---|---|---|---|
| 接受 r003 科学 gate | adopt | 41 个已知候选全部在 outcome 之前被硬门排除 | 保留 `FAIL_NO_A6R_ASSET`，不降低标准 |
| 接受 r003 完全合规表述 | reject | 共享脚本泄露服务器绝对路径，且 drift/零操作计数为硬编码 | r004 先做最小源代码合规修复 |
| 立即训练或推理 RSAR | reject-now | 当前 142/144 的因果归因尚未分解，先扩数据可能放大错误故事 | 先执行零 GPU r004 功效门 |
| r004 power attribution | experiment | 最低成本且能直接杀死或保留 TGRS 叙事 | 执行 [`sug.md`](sug.md) |
| RSAR×S2ANet acquisition | revise/defer | 官方候选明确，但 mother-scene/checksum/empty-image 仍未知 | r004 不死后进入 r005；结果出现后不得换模型 |
| 恢复 B 或下载旧个人项目 | reject | 不能创造前瞻独立性，也不改变当前统计门 | 保持停止 |
| 再次调用 CC | reject-now | 当前分歧由代码、功效界和实物资产裁决 | 科学包冻结后投稿前再审 |

## 5. TGRS 路线的顺序与停止条件

1. r004：零 GPU 功效/归因分解；若 score-limit 不占预注册多数，立刻改写为 sample-size/feasibility boundary，不再写“现有分数导致 142/144 失败”。
2. r005：只做 RSAR 官方 acquisition/provenance gate；母景不可恢复时只允许 image-level measurement replication，不得称严格 scene-level certification。
3. r006：仅一次综合前瞻运行，持久化 raw、pre-NMS、final，并同时跑 0/2/5/10/15/20/25/30° full evaluator、NRC、conditional scene gate 与 full-output sensitivity；看见结果后不换 unit。
4. 完成冻结的第三标注者/仲裁，或把人工部分降为两人探索性锚点。
5. 最后才重写主稿与补近期相关工作；治理、哈希和工作流移入补充材料。

即使全部通过，也只是让 TGRS 从“高风险 borderline”变为“可认真尝试”，不保证录用。若 C2、Tier-1 资产、固定剂量复现或 full-output sensitivity 中任一关键门失败，按 strong JSTARS 收敛，不通过换阈值、换 unit 或删失败行续命。
