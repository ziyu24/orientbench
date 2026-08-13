# OrientBench B/C 同级协作协议

本协议只规定治理、文件所有权与服务器派发，不改变论文 claim、数据、结果或投稿判断。迁移前科学状态继续以 `dis/review_state.json`、`dis/B.md`、`dis/C.md` 和服务器报告为证据；旧协议原文保存在 `dis/governance/legacy/`，但不再产生当前角色层级或派发权。

## 1. 身份与可见性

- Git 中只登记稳定 worker ID 和 B/C/SERVER 角色，不登记客户端账号、机器或凭据。
- 每个 clone 通过 repo-local `paper.worker-id` 一次绑定；缺失、未知、停用或冲突时 fail closed。
- B/C 的角色规则互相可见。盲审只隔离预先声明的本轮 peer 科学材料，不隐藏治理规则。
- B/C 使用独立 clone；同一 clone 不切换或同时承担两者。

## 2. 对等权力与所有权

B/C 能力完全镜像：独立评估、维护自己的 memo、提出候选计划、主动或受邀批判、激活自己的合规计划、提交 verdict/contest/stop request。任何一方不需要等待另一方提问。

文件所有权以 `dis/governance/role_contract.json` 为准：

- B 独占 `dis/B.md` 与 `dis/.../B/` 对应根；C 只读。
- C 独占 `dis/C.md` 与 `dis/.../C/` 对应根；B 只读。
- 服务器独占活动 dispatch 的报告目录；B/C 只读报告。
- `AGENTS.md`、`CLAUDE.md`、`CC_PROMPT.md`、本协议、role contract、workers、roles 与 coordination 是受保护共享治理文件，只有用户明确授权且执行槽为空时可改。

完全对等不等于共写同一文件。任何 actor 不得覆盖 peer memo/plan，也不得靠最后写入根 `sug.md` 垄断事实。

## 3. 候选计划

- 候选位于 `dis/plans/<B|C>/<plan_id>/sug.md`，sidecar 位于同目录 `STATE.json`。
- DRAFT 仅本地未提交；READY 首次提交后正文永久不可变。改变 gate、预算、数据、科学含义、报告路径或授权时新建 revision/id。
- 计划必须包含 base/scientific SHA、证据与 unknown、最小判别实验、kill/early-stop、read/write/resource/conflict sets、唯一报告路径和完成映射。
- critique 可 requested 或 unsolicited；每条结论只能 adopt/revise/reject/experiment，并给证据或最小反证。沉默不形成否决。
- 每个候选最多一次建设、一次最强攻击、一次综合；没有新证据就转实验/一手核查/保持 contested/关闭。

## 4. 风险与授权

- L0：静态审计、重算或测试；无训练、无 GPU、无数据/split/metric/core claim 改变，并受 coordination 五类资源上限约束。任一 owner 可自主激活自己的合规 L0。
- L1：只有 coordination 明确配置完整上限时才可自主激活；当前未配置，按 L2 处理。
- L2：高成本、协议/数据/split/metric/core claim/投稿/不可逆动作，或风险不清；必须有用户已授权的非空 reference。
- 只有协议污染、泄漏、受保护路径、预算越界或决定性反证可硬阻断；普通科学分歧转 contest 或判别实验。

## 5. 原子派发与服务器

- `dis/coordination.json` 是唯一当前派发权威；`dis/review_state.json` 不再控制服务器。
- 任一时刻最多一个 `active_dispatch`。空闲时根 `dis/sug.md` 必须不存在。
- 激活事务把 owner READY committed blob 逐字节复制为根 `dis/sug.md`，并在 coordination 绑定 plan path、commit、blob OID、SHA-256、dispatch id、risk、资源和唯一报告路径。
- 默认只有 owner 激活/关闭。代激活/代关闭必须在冻结计划中登记 delegate/reference，或持用户明确授权。
- 服务器只执行用户交付的精确 dispatch id、plan path 与 dispatch commit SHA，不自行扫描或挑计划；先写唯一 STARTED，再执行和报告。
- 服务器没有科学裁决权。报告首行/状态只表示执行完整性，不能决定论文 claim。

## 6. 生命周期与分歧

计划：`DRAFT -> READY -> DISPATCHED -> RUNNING -> REPORTED -> COMPLETED|INCOMPLETE`；`READY -> BLOCKED_CONFLICT -> READY|WITHDRAWN`。科学状态与执行状态分离，可为 `PENDING|ACCEPTED|KILLED|CONTESTED|INCONCLUSIVE`。

- 报告核验后可以 `PENDING` 关闭并释放执行槽，不必等待双方 verdict。
- ACCEPTED/KILLED 需要 B/C 双方可追溯 verdict；分歧进入 CONTESTED。
- CONTESTED 只能由新判别实验、决定性一手证据或用户停止投入而变化，不靠再写一轮口头意见消失。
- scientific negative 不是服务器失败；协议漂移/部分执行不能伪装完成。

## 7. Git

- 只保留一个长期 `main`。必要时使用短期 `initiative/B/<id>`、`initiative/C/<id>` 或 `exec/<id>`，受控集成后删除；禁止永久 B/C/server 分支。
- 每次开始只 fast-forward；禁止自动 merge/rebase/reset/clean、覆盖式 checkout 与 force push。
- 只显式暂存 owner 文件或合法共享事务，禁止无差别暂存。

## 8. 迁移边界

- 迁移基线：`c78deabcaa54a4c9fd761541430440dcc98067c8`。
- 旧 r020 正式报告为 `FAILURE_EARLY_STOP / NOT_ADJUDICATED`；后续 recovery 证据保持原样，不倒签旧 formal receipt。
- 旧活动 `dis/sug.md` 已逐字节归档，SHA-256 为 `74ef9c65eb660aa36fa6c7f5d78043a4f68540bff3d9903a9303ad6603c9abf5`。新 coordination 从空闲槽启动。
- 更正（2026-08-13，用户授权）：上一条 SHA-256 系 CRLF Windows 工作树哈希；归档 blob 的字节级 SHA-256 为 `aa3d369863843c2548131a6b9f0fd8ff6de4b6e21a73488102a8feb6140a4141`，治理校验按 canonical-LF 核对（详见 `dis/governance/MIGRATION.md` 更正节）。归档字节未变。
- 不把旧 C-first/B-response 历史重解释为同级协议，也不修改历史 B/C memo 或服务器报告。
