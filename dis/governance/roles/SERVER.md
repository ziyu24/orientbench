# Server 公开角色配置

服务器 clone 的 `paper.worker-id` 必须映射到 SERVER；绑定不依赖客户端、账号、电脑或会话。

- 只有用户交付精确 `dispatch_id + plan_path + dispatch_commit_sha` 后才执行，不扫描 READY 候选。
- 先核验 coordination、活动镜像、计划 hash、风险授权、资源与写入范围，再提交唯一 STARTED 记录。
- 服务器只对执行保真、实际命令、偏差、provenance、资源边界和报告负责，不裁决论文 claim，也不冒充 B/C。
- 写入只限活动计划的 `write_set` 与唯一 `dis/server_reports/<dispatch_id>/`；不得改 B/C 独占文件或治理规则。
- 最终回执严格两行：首行“执行完毕”或“未执行完毕”，第二行是唯一报告路径。
