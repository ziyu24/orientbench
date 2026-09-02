# 当前状态

- 阶段：`R003_AIRO_STAGE_A_READY`；活动 workstream 为 `r003`。
- 持续目标：已建立 `/goal`，目标是严格支持或否证一个区别于既有失败路线、具有 TGRS 或更高潜力的新假设；不得把计划或负结果包装成顶刊完成。
- r002 终态不变：正式机器结果为 `FAILED_ACCEPTANCE`，科学状态为 `INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE`；GR-EQS 仅负向冻结，G2 从未授权。r002 不再继续修复，也不阻塞全新的 r003。
- B/C 选择：唯一入场候选为 AIRO（Axial Image Rotational Observability）。全局 `M_15` 必须在局部 `J_eff` 和经典基线之外解释盲人工方向歧义；detector 端则要求 `J_eff` 与 `M_15` 各自在另一机制之外、按“可观测性越高风险越低”的注册方向解释 raw axial error。
- 明确排除：集合值/conformal 路线与 r035--r037 Q-SetOD 重复；关系方向场与 r040/r041 已消费的信息源及 2025 Angle-Synchronized Graph 直接碰撞；候选矩形边界扫描与失败的 r049rev2 PEF 重叠。三者均不得作为 r003 替代路线。
- 新颖性边界：structure tensor、旋转配准 CRLB、全局 ZZB、Lie derivative 和 detector equivariance 都有强先验。AIRO 不宣称新数学理论；只检验 OBB 特有的人机共同、跨域测量命题。
- r003 冻结资产：M4 只准使用钉死 SHA 的 600-row manifest/labels；二元端点排除任一 `SKIP` 后为 576 行（126 ambiguous、450 双 LABELED），对应 585 张唯一图。detector 总体固定为 r036 qset A--F 515559 matched keys，不得改用 full M069、过滤缺图后补抽或混入 1500-row pending M4 文件。
- r003 资产阻塞：Git 不含真实 pixels；A--F geometry/TTA assets 也只知历史 SHA。SERVER 第一动作只能做 G0 只读核验。本轮 current pixel SHA 将封存并做跨 unit/M4-overlap 锚定，其余历史像素身份必须标为 unsealed，因此 Stage-A 永远是回顾性探索证据。
- r003 科学门：固定像素信息墙与合成/插值 fixtures；M4 leave-dataset 人工门；DIOR 同图五折 OOF 与跨数据六配置 detector 门；强基线包含完整 TTA、结构张量、`J_raw/M_raw`；主风险为 independently rebuilt raw `le90/90`；AUGRC 使用预测风险升序的 whole-tie generalized risk mass。J/M 条件门各有 Holm-6 unit、Holm-3 dataset 和至少两 detector-family 覆盖。
- 推断边界：10000 次 bootstrap 是按 `(analysis_family,dataset)` 同步 mother-scene multiplicity 对冻结 target predictions 重权，不重拟合；CI 只代表 `conditional-on-frozen-source-fit`。unit 先算 delta，再等权聚合 dataset 和三数据集，禁止跨 unit 拼分数重排。
- r003 权限：CPU-only、零 GPU、零训练、零 detector inference、零下载、零新数据、零论文修改。像素特征必须先封存，人工/GT label 后挂接；禁止 predicted-theta 预对齐、候选框角扫描、refined angle、score fusion、`delta_0.75` 风险和旧路线复活。
- 治理边界：r003 是经 B/C 裁决后手工物化、由本地 `load_server_plan` 验证可加载的 READY 计划；r002 的 `FAILED_ACCEPTANCE` 与旧 helper 仅接受 `SUCCEEDED` 结果形成签发死锁，因此两个 prior-assessment 字段保持 `null`，没有伪造 receipt，也不声称完成旧 decision-chain helper 签发。SERVER 是否执行只以 HTTPS main、`cqc-fabric 2.5` 状态和发布 RESULT 为准。
- 裁决顺序：M4 asset/实现/synthetic -> human；只有 HUMAN PASS 后才让 detector asset 缺失产生 INCONCLUSIVE；随后 detector full、J/M 双条件与 specificity。充分资产、两实现一致时的科学失败必须 KILL，不能包装成 INCONCLUSIVE。
- PASS 含义：最多为 `ADMIT_AIRO_CAUSAL_STAGE_B`，只允许 B/C 另开受控模糊/降采样/噪声/旋转再推理计划；不自动授权下一轮，更不提升期刊判断。
- 期刊水平：仍为中科院 2025 地球科学大类二区 JSTARS 对标，尚非 TGRS；ISPRS JPRS 仍是更高优先终点。
- 唯一下一步：SERVER 按 `coordination/instructions/r003/SERVER_PLAN.yaml` 执行 r003；B 不控制服务器。SERVER 发布 RESULT 后，B/C 再对 exact remote ref 做独立科学裁决。
