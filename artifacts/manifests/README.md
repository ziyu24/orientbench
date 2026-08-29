# 大制品 manifest

每个 checkpoint、`.pth` 或其他大生成制品只在本目录保存一个 YAML manifest。
manifest 记录逻辑节点、相对路径、哈希、精确源码、数据、环境和可执行恢复步骤；
它不授权执行，也不包含真实连接信息。manifest 的每条恢复 argv 必须显式写入
`rNNN` SERVER_PLAN，由 runner 逐条通过 guard 执行；guard 提供 `CQC_PROJECT_ROOT`、
`CQC_HOST_WRITE_ROOTS_JSON`，仅有一个 host root 时还提供 `CQC_LARGE_WORKSPACE`。
`workspace expand` 本身绝不执行 manifest argv，只核验实际输出的大小与摘要并封存状态。
系统不自动删除制品，只有 SERVER 明确运行
`workspace compact --profile <profile>`，并且逐项重验摘要且不存在未登记的非 runtime 内容时，才删除该 profile 的可重建展开内容。
