# Git near-real-time dialogues

`BDdddd`/`CDdddd` 会话与 `events/B|C/` 事件均为 append-only。B/C 只写自己的事件目录，通过 `dialogue sync` 在 clean main 上 fast-forward 同步；分叉时停止，不自动 merge 或 rebase。
