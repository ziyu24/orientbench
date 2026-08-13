# Claude Code 项目入口（客户端中立）

本文件不把 Claude Code 固定为 B 或 C。角色由 Git 跟踪的 `dis/governance/workers.json` 授权，并由当前 clone 的 repo-local `paper.worker-id` 一次性选择；换 Claude Code、Codex 登录账号或电脑不会改变 Git 中的项目状态。

开始任何实质任务前：

1. 运行 `git config --local --get paper.worker-id`；缺失或无效时只读并请求用户一次性绑定，禁止猜测。
2. 读取 `dis/governance/role_contract.json`、`workers.json` 和 worker 对应的 `roles/B.md`、`roles/C.md` 或 `roles/SERVER.md`。
3. 读取 `dis/PEER_START.md`、`dis/collaboration_protocol.md`、`dis/coordination.json` 与当前任务所需证据。
4. 核对 origin、main、完整 HEAD 和 clean worktree；只允许 fast-forward，同步失败时停止。

B/C 是同级合作者，均可独立发现问题、写自己的 memo/计划、主动批判对方，并按风险合同激活自己的合规计划。当前 actor 只能写自己的独占根；共享派发文件只能通过原子事务修改。L2、投稿、数据/split/metric/core claim 变化、高成本或不可逆动作必须有用户明确授权。

根 `dis/sug.md` 只在活动派发期间存在，并且必须与 READY committed plan 逐字节一致；空闲时不存在。服务器报告不等于科学裁决。旧 `dis/review_state.json` 保存迁移前科学状态，不再是派发权威。

静态规则对 B/C 双方可见。只有预先声明的 `independent_then_cross` 才隔离本轮 peer 科学材料；已经阅读时必须如实标记非独立。

提交前运行：

```text
python -X utf8 dis/governance/test_peer_governance.py -v
python -X utf8 dis/governance/validate_peer_governance.py . --check-local-worker
git diff --check
```

禁止自动 merge/rebase/reset/clean、覆盖式 checkout 与 force push。账号、机器名、token、cookie、私钥和 credential 输出不得进入仓库。
