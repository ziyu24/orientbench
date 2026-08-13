# OrientBench B/C 同级启动入口

角色由 Git 跟踪的 worker registry 授权、由 repo-local `paper.worker-id` 选择。每个 clone 只绑定一次；换 Codex、Claude Code 或账号不改变角色。缺失、未知、停用或冲突时只读并停止写入。

## 每次启动

1. `git pull --ff-only`，记录 origin、main、完整 HEAD 与工作树；dirty、非 fast-forward 或意外远端立即停止。
2. 读取 `dis/governance/workers.json`、`role_contract.json`、B/C 两份公开配置、协作协议和 `dis/coordination.json`。
3. 只写当前 actor 独占根。B 不改 C 的 memo/plans/reviews；C 不改 B 的对应路径。
4. `dis/review_state.json` 与迁移前协议归档仅是历史科学证据，不产生当前派发权。

## 同级权力

- B 或 C 均可从最新 Git/服务器证据独立更新自己的 memo、提出 DRAFT/READY plan、请求或不请求对方批判。
- 任一方可主动审查对方计划；critique 不自动形成 veto，对方沉默不否决合规 L0/L1。
- 执行槽空闲且计划满足项目风险政策时，owner 可激活自己的 L0/L1。未配置的风险层级按 L2 处理，L2 必须有用户授权。
- 报告后双方可分别给 verdict/contest。科学分歧保持 contested 或转最小判别实验，不能靠身份或语气裁决。

## 原子派发

- READY 计划正文首次提交后永久冻结；实质修改新建 revision/id。
- 活动根 `dis/sug.md` 是 owner READY plan 的逐字节镜像，空闲时不存在。
- 任一时刻最多一个 active dispatch。服务器只接受用户交付的精确 dispatch、plan path 和 dispatch commit SHA。
- 普通问题不强制盲审；核心贡献冻结、异常结果、昂贵 L2 或投稿前可预先声明对称的 `independent_then_cross`。
- 没有新证据时只做一次建设—最强攻击—综合，然后实验、核查、保持 contested 或停止。
