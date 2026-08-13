# B/C 同级治理迁移记录

- migration base: `c78deabcaa54a4c9fd761541430440dcc98067c8`
- user authorization: 当前总控任务明确批准迁移全部旧项目治理
- legacy r020 report: `dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md`
- legacy formal execution: `FAILURE_EARLY_STOP / NOT_ADJUDICATED`
- recovery evidence: 保持原字节与原语义，不倒签旧 formal receipt
- archived active plan: `dis/sug/orientbench-c-r020-measurement-validity-20260811-server-returned.md`
- archived plan SHA-256: `74ef9c65eb660aa36fa6c7f5d78043a4f68540bff3d9903a9303ad6603c9abf5`
- archived old protocol: `dis/governance/legacy/collaboration_protocol.pre-peer-20260812.md`
- archived old B entry: `dis/governance/legacy/B_START_PROMPT.pre-peer-20260812.md`
- new dispatch slot: idle

迁移只改变未来治理。未修改 `dis/B.md`、`dis/C.md`、`dis/review_state.json`、服务器报告、论文、代码或科学数字。

## 更正（2026-08-13，用户授权，B 执行）

上表 `archived plan SHA-256: 74ef9c65…` 系在 CRLF Windows 工作树上计算，不是归档 blob 的字节哈希；该常量曾冻结进治理校验，导致任何 LF checkout（如 Linux 服务器）校验必然失败（见 `dis/server_reports/orientbench-b-r021-measurement-validity-20260812/SERVER_EXECUTION_REPORT.md` 与 `dis/dispatch_history/orientbench-b-r021-measurement-validity-20260812.json`）。

归档 blob 的字节级 SHA-256（`git show HEAD:dis/sug/orientbench-c-r020-measurement-validity-20260811-server-returned.md | sha256sum` 可复核）为：

`aa3d369863843c2548131a6b9f0fd8ff6de4b6e21a73488102a8feb6140a4141`

治理校验（validator 与测试）自本日起按 canonical-LF 内容哈希核对，预期值即上述 blob 哈希；归档文件字节未被改动。
