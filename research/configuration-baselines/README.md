# 训练配置基线

GPU 训练前由 B/C 冻结科学口径，SERVER 在 MASTER 权限内建立一个项目内、小体积、可审计
的 YAML 基线并由 `SERVER_PLAN.configuration_alignment` 绑定其 SHA256。每个基线文件使用
以下闭合字段，计划中的官方总 batch、优化器学习率和引用必须与之完全一致：

```yaml
schema_version: 1
baseline_id: official-method-dataset
task: 具体训练任务
official_gpu_count: 4
official_global_batch_size: 16
official_optimizer_learning_rate: 0.0001
official_config_refs: [https://example.org/official-config]
prior_project_config_refs: []
verified_at: YYYY-MM-DD
notes: 官方口径及同项目继承关系说明
```

计划另外记录实际 GPU 数、每卡 batch、梯度累积和偏离理由。基线至少记录：

- 官方仓库或论文配置的可核验 URL/项目相对路径与读取日期；
- 同项目上一轮配置引用（首轮可为空）；
- 官方与计划的 GPU 数、全局 batch、每卡 batch、梯度累积和优化器学习率；
- 默认四卡后如何保持官方全局 batch 与优化器学习率；
- 任何偏离官方或同项目历史配置的科学理由。

默认优先四卡，但不得为凑四卡破坏官方训练语义。SERVER 优先读取主机本地
`~/cqc/study/pth_data/readme.md` 或 `~/zy/study/pth_data/readme.md` 中已有权重与配置；取消
旧 `/pro/` 路径。真实绝对路径和资源清单内容不提交 Git。清单缺失时主动查找官方配置、
项目历史和已有 checkpoint，不能因此停工。
