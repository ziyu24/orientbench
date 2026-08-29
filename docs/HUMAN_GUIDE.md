# 使用说明

## 现在只记四件事

1. 用 `/goal <目标与停止条件>` 管理整个长任务；同一时间只保留一个目标和一个活动运行。
2. B/C 可以怀疑对方的任何科研判断，尤其是期刊级别，但只允许一次质疑；随后必须下发最小实验、记录硬阻塞或请用户作一次决定，不来回拉扯。
3. SERVER 只保存机器验收所需的最小运行凭据。心跳仅用于超过30分钟任务的内部存活判断；训练程序支持续训时才记录训练 checkpoint。
4. 结果默认收敛到 `main`，不强制结果分支；短期 `exec/rNNN`只承载异常证据。

`NEW_RESEARCH` 的创建身份不会被改写，但可一次性进入 `PAPER_REPRODUCTION` 或 `CHAT_HANDOFF` 工作轨道，只补该轨道的少量入口文件，不允许反向或反复切换。

Codex先为同一份`MTdddd`请求运行 `track preview` 查看精确变更；用户回复“批准创建”后，用同一请求号和预览摘要调用 `track apply`。用户不需要记忆或手工输入这些参数。

## 角色与入口

B/C负责科研问题、对照、指标、数据集名称、GPU层级和验收口径；SERVER负责项目所在服务器上的本机工程执行。用户只需说“拉取，执行”，可转交：

```text
/goal 拉取，执行
```

SERVER实际运行：

```text
python -m tools.workflow dispatch pull-execute
```

入口会先同步clean `main`，只领取唯一READY的`rNNN`，并直接显示B/C写入的不超过50字执行概述。它不会连接另一台服务器。

## 单服务器原则

一个项目固定在一台服务器，执行永远发生在该项目工作副本所在的本机。已彻底移除双节点inventory、节点探针、SSH控制、rsync传输、远端GPU启动、节点自动选择和失败回退。B/C、桌面端和Git内容都不得探测26或46。

SERVER从固定项目路径识别本机profile；若路径不能唯一识别，只需在该服务器项目工作副本内设置一次：

```text
git config --local cqc.server-profile 26
```

或设为`46`。这不是节点发现，也不会读取对端状态。

## GPU

- 快速验证：1卡。
- 正常训练：默认2卡。
- 大资源任务：4卡，但必须先有绑定具体`rNNN`的`resource_expansion`授权。

B/C只能写GPU层级和数量，不能写0/1/2/3等物理卡号。SERVER在启动前运行本机`nvidia-smi`，按逐卡可用显存择优选择卡并设置`CUDA_VISIBLE_DEVICES`。GPU不设跨项目独占租约或等待队列：已有2卡任务时新任务优先使用其余卡，更多任务继续复用当时最空闲的卡立即并行。显存需求按每张卡判断，不把多卡显存相加；即使当前低于偏好值也不等待，只有真实OOM才在同一`rNNN`内降低单卡batch、增加梯度累积、换卡或重试。计划仍需绑定官方/项目训练配置基线，并优先保持官方全局batch和优化器学习率。

## 数据集

46 上挂载的26数据只用于查询和复制，正式命令不得直接读取挂载路径。首次使用时，把精确子集复制到 `/dev/shm/zy/data/dataset/<规范数据集名>/<规范子集名>`；已有缓存就直接命中。每个项目指令持有一个租约，最后一个租约释放时只删除该子集。例如 `dota/dota1.0` 与 `dota/dota1.5` 分别计数，不能用 `dota` 父目录表示长期占用。

数据目录中的内容默认按官方数据使用，不再做数据身份digest、整树hash、来源或镜像一致性校验。SERVER只检查本地目录可打开且非空。

- 26官方数据：`/home/rspip/cqc/data/dataset`
- 26本机shm：`/dev/shm/cqc/data/dataset`
- 46：读取挂载到46本机的26数据树
- 46新增下载、复制或转换：只能写入`/dev/shm/zy/data/dataset`

若46的实际挂载点不同，SERVER只在46本机项目工作副本设置绝对路径：

```text
git config --local cqc.dataset-root /实际挂载点
```

B/C只在SERVER_PLAN声明数据集名称、版本和可选shards。科学上可行时必须先用HRSC2016完成科学试验或工程通链，再进入其他数据集；不适用时必须写明理由。不能默认先跑DOTA浪费时间和算力。

## pth参考

固定路线如下：

- 26：`/home/rspip/cqc/study/pth_data/readme.md`
- 46：`/home/rspip/zy/study/pth_data/readme.md`

`pth_data`里的pth来自4卡训练，可在兼容且有价值的快速验证中参考。README缺失不会触发跨节点搜索，也不会让B/C补服务器拓扑。

## SERVER_PLAN新增约束

每条新计划必须包含：

- `execution_summary`：中文概述，非空且不超过50字；
- `startup_dataset`：HRSC2016为`SCIENTIFIC`或`ENGINEERING_CHAIN`，不适用为`NOT_APPLICABLE`并说明原因；
- `resources.gpu_tier`：`CPU_ONLY | QUICK_VALIDATION | NORMAL_TRAINING | EXPANDED_TRAINING`；
- 数据项只含`dataset_id`、`version`和可选`shards`，不含digest。

已签发的旧`rNNN`会在内存中适配，不改写原计划：旧4卡默认降为正常2卡，保持全局batch时调整梯度累积；需要数据训练时先加入HRSC2016本地可用性通链；旧digest被忽略。

## 仍然有效的门禁

项目锁、用户STOP、权限快照、源提交绑定guard、`max_hours`、机器验收、非空结果、结果提交HTTPS推送与远端ref核验仍然有效。长任务另保留内部心跳，程序支持时保留训练checkpoint。敏感用户控制的权威仓库URL由首个project.yaml身份提交固定。只有这些最小机器证据闭环后才能报告执行完成。

B/C回复涉及具体执行时使用证据化状态行：

- `rNNN：执行完成（成功）`
- `rNNN：执行结束（失败）`
- `rNNN：未执行完成（状态：<STATE>）`

外部写入、4卡资源扩大、发布和DOCTORAL仍须摘要绑定、限时、一次性用户控制；SERVER不能自行启用。普通工程错误由MASTER在同一非终态`rNNN`中修复恢复，异常终态由B/C审阅后发行下一条更正指令。
