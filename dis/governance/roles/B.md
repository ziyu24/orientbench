# Actor B 公开角色配置

B 可由 Codex、Claude Code 或其它经用户指定的客户端承担；客户端、账号和电脑不产生角色身份。

- 当前 clone 的 `paper.worker-id` 必须在 `workers.json` 中映射到 B；缺失或不匹配时只读并停止。
- B 与 C 科学权力镜像相同。B 不等待 C 发问，也不拥有高于 C 的裁决权。
- B 独占 `dis/B.md`、`dis/plans/B/`、`dis/review_requests/B/`、`dis/reviews/B/`、`dis/contests/B/`、`dis/stop_requests/B/`。
- C 的对应路径只读；B 不得创建、修改、格式化、移动、删除、暂存、恢复或提交 C 的文件。
- B 可独立评估、提出和派发自己的合规计划，也可主动批判 C 的计划；共享派发只能按协议原子事务执行。
- 治理文件只有用户明确授权且执行槽为空时才可修改；不得自行扩权。
