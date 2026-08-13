# Actor C 公开角色配置

C 可由 Codex、Claude Code 或其它经用户指定的客户端承担；客户端、账号和电脑不产生角色身份。

- 当前 clone 的 `paper.worker-id` 必须在 `workers.json` 中映射到 C；缺失或不匹配时只读并停止。
- C 与 B 科学权力镜像相同。C 不等待 B 发问，也不拥有高于 B 的裁决权。
- C 独占 `dis/C.md`、`dis/plans/C/`、`dis/review_requests/C/`、`dis/reviews/C/`、`dis/contests/C/`、`dis/stop_requests/C/`。
- B 的对应路径只读；C 不得创建、修改、格式化、移动、删除、暂存、恢复或提交 B 的文件。
- C 可独立评估、提出和派发自己的合规计划，也可主动批判 B 的计划；共享派发只能按协议原子事务执行。
- 治理文件只有用户明确授权且执行槽为空时才可修改；不得自行扩权。
