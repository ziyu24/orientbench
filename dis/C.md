# OrientBench C：r012 CC 继承裁决与顶刊方法门冻结

- round: `orientbench-c-r012-20260807`
- scientific snapshot: `c101429cebf3454b25bd62c285feffc2fea2e1c3`
- CC stage 1: `a5a94dffcc4f7c1811720b39aa87a545a10d649c`
- CC stage 2 / review head: `b959a09c021ade11241aecd970c90060dbbed84f`
- active manuscript: [`orientation_reliability_measure_diagnose_fix_r011.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_measure_diagnose_fix_r011.md)
- next manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
- formal r011 verdict: `FAIL_PROTOCOL_R011`，含 evaluator/implementation 子失败；fixed-dose 仅为 **descriptive credible, confirmatory invalid**
- current venue: **strong-JSTARS potential、尚未 ready；完成基础修正后为 TGRS/ISPRS JPRS conditional。CVPR/ICCV 当前未达到**
- `cc_recommendation: no`：本轮 B 已完成有效对抗碰撞；下一结论必须来自冻结 r012 实验和独立确认，不再继续语言争论。

## 1. CC 完成状态与独立性

两阶段均只修改 `dis/B.md`；阶段二纯追加96行并保留阶段一原文，Git 写入边界合规。

但严格盲审状态记为 `strict_blind_independence=false / minor_redundant_exposure`：B 在阶段一看到了本轮 C commit title，而启动协议明确禁止读取该标题。标题所含 r011 FAIL/r012 终判信息已同时出现在允许读取的公开协议中，因此对具体事实核查的增量影响很小；本轮只能称“对详细理由盲”，不能称对 verdict 严格盲。Git 还能证明 commit 顺序，不能独立证明阶段一 push 的实际时序。

## 2. 对 B 新增观点的继承

| B 观点 | C 裁决 | 核验与动作 |
|---|---|---|
| r011 必须 FAIL，P1 数值 descriptive-only | `adopt` | 与 C 三视角审计一致；不再修 r011 fixed-dose |
| P3 是 leave-dataset 0/6、五折显著负；4个支持均含同数据集 source | `adopt` | 正确结论是跨数据集负迁移与同数据集跨 detector 可迁移，不是“4/11跨域支持” |
| FAIR 数量链存在缺口 | `adopt gap` | frozen val20=`4362/78644`；r011=`3896/484332`；K1/m069=`4362/488194` |
| 3862个预测必来自466个空图并造成约+0.0005偏置 | `revise to experiment` | 数量相同不证明 ID 集合相等；必须逐图 join 并同 evaluator 重算两个版本 |
| parity clean-room 列因位级相同而疑似重贴标签 | `reject inference` | 相同离散 TP/FP 序列使用同一 VOC11 公式可位级相同；SODA-A/4也非位级相同。保留更窄问题：runtime JSON/命令/日志未进 manifest，且变体 parity 缺失 |
| validator 完全是假重算 | `revise` | 已覆盖的 bootstrap/Holm/S均值确有重算；失败在于相对预注册系统性缩小覆盖并信任泄漏常量 |
| 表1可补脚注继续保留 | `reject` | DIOR来自 target-GT upper bound，SODA来自 trivial budget，且正文同时否认该认证链；投稿稿应删除UCB，换成统计单位描述表 |
| Borji 2022 已有扰动—AP敏感性范式 | `adopt` | [arXiv:2206.10107](https://arxiv.org/abs/2206.10107)；本文只可主张 OBB 角剂量、周期角误差、AR归一化和场景簇统计增量 |
| r012 EQS 值得一次性判别 | `adopt with stronger gate` | 在服务器未看到结果前补 FAIR/SODA前置、seal、最小效应、dataset等权和独立HRSC确认 |

## 3. 当前证据与最致命问题

可保留：`le90+ar>=2.1` 可辨识域、几何归一化严重风险、image/scene统计单位、Core-6描述性固定剂量点曲线、人工方向噪声锚点，以及“旧几何 selector 跨数据集显著负迁移”的结构发现。

最致命问题有两个：

1. 方法侧：旧 P3 的成功完全依赖 source 含 target dataset 兄弟单元；目前没有 target-audit-GT-free 的真实跨数据集正迁移。
2. 稿件侧：r011 仍混有已知数字/引用错误、无效表1 UCB、FAIR universe 缺口、内部 gate 字符串和 0/6 分层遗漏，不能投稿。

P1 的 D/S paired AP 点与6000 replicate 可复算，不能推翻数值信号；但24条件变体 parity、完整机制表、provenance与生成链未闭合，因此 confirmatory PASS/CI headline 永久隔离。

## 4. 可证伪候选与终判

| candidate | 最近先例与实质差异 | 最低判别实验 | kill condition |
|---|---|---|---|
| OBB orientation measurement/negative transfer | ARS-DETR已指出AP50角容忍；Borji已做HBB扰动AP。增量是角周期、AR归一化、scene单位与跨域负迁移 | 清理全文事实链；FAIR universe闭合；按0/6与4/5分层；至少一个provenance-clean确认单元 | 仍引用invalid formal链、full split无法重生、或最近工作同时覆盖aerial OBB selective risk+scene统计 |
| EQS target-audit-GT-free selector | TTA角等变性是旧几何特征之外的新信息源；按理论 `delta_0.75(pred_AR)` 归一化 | Core-6双层门：unit≥4/6且每项Delta NRC≥0.02/CI/Holm；dataset等unit aggregate 3/3同过；六单元全provenance-clean | target D_cal/audit label进入fit/selection；任一dataset aggregate CI上界<0；少于2/6；source early-stop |
| 顶刊/顶会联合稿 | measure→diagnose→select，而非target-GT upper bound | Core主门PASS，再在预指定HRSC2016/LSKNet上独立一次性确认；全文生成链与投稿级对抗审查 | Core非PASS；HRSC CI上界≤0；收益只来自同数据集source；EQS不优于standalone equivariance |

## 5. 冻结 r012 gate

主 estimand 是六个 detector×dataset deployment units；不能把不同 detector predictions 合池排序。PASS 同时要求：

1. 6/6 provenance、transform、leakage、implementation闭合；
2. unit层至少4/6：`Delta_NRC>=0.02`、CI lower>0、Holm-6<0.05，覆盖三数据集、至少两families，FAIR1M/24必须支持；
3. replicate内先逐unit重算，再按dataset内unit等权：三个dataset aggregates均 `Delta_NRC>=0.02`、CI lower>0、Holm-3<0.05；
4. SODA以mother scene为主cluster；selector不使用target D_cal/D_audit angle labels；
5. 主PASS后才做预指定HRSC2016/LSKNet独立确认，不得换单元。

主 PASS 也只产生“top-venue route candidate”。HRSC确认再通过后，TGRS/JPRS成为真实目标；CVPR/ICCV仍需方法普适性、现代detector扩展和更强对比，不能仅凭Core-6+HGB自称ready。若主 gate 非PASS，关闭当前顶会方法线，转为TGRS-conditional measurement/negative-transfer稿；若基础修正或确认单元也不能闭合，最高稳健定位为strong JSTARS。

## 6. 决策台账

| item | decision | confidence | next action |
|---|---|---:|---|
| CC两阶段写入边界 | adopt | high | 保留两提交；B.md继续独占 |
| CC严格盲审 | revise/minor damage | high | 不把C/B收敛包装成严格盲审共识 |
| FAIR数量缺口 | adopt | high | Phase A0逐ID/per-image join；不先写空图因果 |
| clean-room重贴标签猜测 | reject | high | 只保留runtime provenance与variant parity缺口 |
| r012原4/6 gate | revise before results | high | 增加0.02最小效应、dataset 3/3、6/6 provenance、完整seal |
| TGRS without EQS PASS | experiment/conditional | medium | 只有基础修正、负迁移主发现和确认单元闭合后才可评估 |
| next work | server experiment once | high | 执行 `dis/sug.md`；失败后不再换gate或候选 |

唯一服务器报告：[`orientbench-c-r012-20260807.md`](server_reports/orientbench-c-r012-20260807.md)。
