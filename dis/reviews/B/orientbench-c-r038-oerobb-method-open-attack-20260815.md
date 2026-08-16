---
schema_version: 1
actor: B
review_id: b-attack-c-r038-oerobb-20260815
request_id: orientbench-c-r038-oerobb-method-open-attack-20260815
review_mode: open_attack
evidence_head: c2abba26817233d3ab1220a6a9a6a205558f9f80
overall: REVISE_THEN_CHEAP_KILL_EXPERIMENT
created_at: 2026-08-15T20:10:00-07:00
---

# B 对 OER-OBB 的攻击与升级重构

总裁定：**REVISE + CHEAP_KILL_EXPERIMENT**。OER-OBB 是三个方法候选里第一个把刀口对准真问题的：它只押注 r036/r037 唯一存活的信号，放弃了全部已死组件。但按 C 自己的 Q8 标准衡量，**它现在的交付物形态撑不起 JPRS/TGRS**——就算全部门槛通过，产出是"一个需要 3 次 forward 的更好标量分数"，这是 strong-JSTARS+ 的形态。B 的重构：OER 保留为 Stage A 杀伤实验（照跑），但顶刊载体改为 **OER-D：把多视图等变残差蒸馏成单次 forward 的自监督方向可靠性头**。逐问作答：

## Q1 新颖性

**现状 = DML 正交化 + TTA uncertainty 的拼接，方法级新颖性单薄。** "cross-fitted orthogonalization of equivariance residuals" 是把两个成熟工具在新对象上组合，审稿人一句 "residualized TTA uncertainty" 就能拆掉。可辩护的新颖性必须来自交付物升级：**OER-D 蒸馏头**——用冻结检测器自身的多视图分歧作为自监督目标（全程零 GT 角标签），训练一个单 forward 推理的可靠性头，推理零额外成本。这个 artifact（自监督来源 + 零标签 + 零推理开销 + 跨域验证）才是方法论文的骨架；OER 降为它的教师信号与分析工具。**REVISE。**

## Q2 交叉拟合是否挡得住捷径

挡得住过拟合型泄漏，挡不住**表征泄漏**（E 与 score 同源：score dispersion、association ambiguity 天然携带 confidence/class 信息）。C 的窄层内置换 `tilde_E` 负控制是决定性的——**升格为 binding gate**：置换后增益残存 > 30% 即 FAIL。补两条：(i) 从 `tilde_E` 线性重构 Z 的 R² 随报告披露（r036 已有先例）；(ii) 逐成分剥离消融（去掉每个 E 成分后的增量），防单一泄漏成分撑全局。**ADOPT+补强。**

## Q3 estimand 选择偏差

matched-TP + GT_AR≥2.1 把主张限定在"已检出且方向可辨识"的目标上——这不是缺陷，但**主张措辞必须显式限定**："对 matched TP 的方向失效排序"，部署价值经 full-detection guard（FP/FN/mAP 不恶化）兜底。all-AR 敏感性保留。风险在 Y 本身：`d_π/90°` 对近 90° 混淆和 180° 翻转赋同权，机制上是两类不同失效——**revise：按 [0,30°)/[30,60°)/[60,90°] 分段报告失效构成**，不改主标签。**ADOPT+限定语。**

## Q4 门槛是否事后贴合 r037

**是，4/8 恰等于 r037 已观察值——这是事后贴合，必须收紧。** B 修订：**≥5/8 unit witnesses 且必须含 ≥1 个 DOTA unit（G/H）**（r037 的 4 个恰好全非 DOTA：A/B/E/F——新门要求信号走出它已被观察到的舒适区）。`Delta_AUGRC ≥ 0.005` 保留（是旧 ε 下限的 10 倍，够严）。两 target dataset 的 Stage C 门保留。**REVISE。**

## Q5 最强杀手基线

**同预算 generic TTA variance**——它用同样的三次 forward、不做任何正交化。若 OER 赢不了它，全部 DML 机械是装饰。公平性冻结：同视图集、同匹配、同 source worst-group 容量选择协议；conf+AR+size+class 基线额外配 source 内 isotonic 校准（防"基线没调好"的批评）。OER ≤ generic TTA variance → 直接 FAIL，不许改叫工具箱续命。**ADOPT 并指定其为头号处刑者。**

## Q6 清白 endpoint 是否真实存在

r036 T1 审计：**DOTA-v2.0 val 标注与 SODA-A official test 标注在盘、无历史科学消费**——两个 dataset ✓。检测器族：这两个 endpoint 上尚无预测产物，Stage C 需要 GPU inference（orcnn/rtmdet/psc checkpoint 在盘）→ 材料上可行，需用户授权算力。**确认存在，但 Stage C 前必须按 §5.3 做资产/许可/历史 outcome 闭合预检。**

## Q7 最便宜最狠的一击

**Stage A 本身已是最小杀伤实验，一次 CPU 运行**，B 只加一条执行约束：直接复用 r036 已冻结的 616,184 行 enriched rows 与既有 TTA 特征（禁止重提取），nested leave-dataset × leave-detector 交叉拟合 + 六排序器对照 + 置换负控制，全套数小时。**它一旦失败，OER 与 OER-D 同死**（学生蒸馏不出教师没有的信息），项目回到 r038 稿收口——零 GPU 损失。

## Q8 就算全过，够顶刊吗

**OER 单独：不够，strong-JSTARS+。** 要到 JPRS/TGRS 需四件套齐备：① OER-D 单 forward 蒸馏头（零标签零开销的可部署 artifact）；② Stage B 机制结论（哪个冻结干预变量预测 held-out 方向）；③ Stage C 两清白 endpoint × ≥2 检测器族的密封确认；④ 随稿发布评测协议工具箱。四缺一则如实降档。TPAMI/IJCV：不承诺，域太窄。**这是对用户"顶刊新方案"要求的诚实答案：路线存在、分段可杀、每段都有止损点。**

## 裁定汇总与阶段重构

| 阶段 | 内容 | 裁定 | 成本 |
|---|---|---|---|
| Stage A（r039） | OER source-only 杀伤实验（C §5.1 + B 修订门槛：5/8 含 DOTA、置换 gate、复用 r036 行） | **cheap_kill_experiment，计划已就绪** | CPU 数小时，零 GPU |
| Stage B | OER-D 蒸馏头训练 + 机制干预族（C §5.2 + 蒸馏交付物） | adopt in principle，Stage A 过后需用户 GPU 授权 | ~1-3 GPU 天 |
| Stage C | 两清白 endpoint 密封确认（C §5.3 + §6 gate，B 修订后） | adopt in principle | ~1 GPU 天 + 密封轮 |
| venue 语言 | 全程禁止 prospective 语汇；确认轮身份按实际时序如实标注 | binding | — |

Stage A 可执行规格：`dis/plans/B/b-r039-oer-stageA-kill-20260815/sug.md`（READY，待 r038 成稿轮释放执行槽后激活）。杀死即回 r038 稿止损；存活则携带本攻击的全部修订进入 Stage B 规格评审。
