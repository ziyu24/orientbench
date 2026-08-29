# 功能清单

- `/goal` 是长任务的唯一用户入口；项目内部只保留最小运行凭据，不再要求用户维护另一套 journal 或 supervision 流程。
- B/C 可质疑任何对方结论，期刊评级也必须带证据与最强拒稿理由；只允许一次质疑，随后执行或形成明确阻塞。
- `NEW_RESEARCH` 可单向进入论文复现或聊天交接工作轨道，但创建身份和登记证据不变，不能来回切换。
- 46 对26挂载只查询不执行；精确数据子集复制到46的tmpfs缓存，按项目指令租约共享，引用数为零时仅删除该子集。
- 机器验收仍是完成证据；心跳只服务长任务存活判断，训练 checkpoint 仅在程序支持时使用，不强制结果分支。
- 其他按需能力包括角色绑定、证据与期刊基准、敏感权限、项目锁/STOP、论文版本与PDF导出、可重建大文件、经验卡、维护归档和旧项目迁移；默认流程不要求用户逐项操作。
- 工厂创建的是可审计、可在单台GPU服务器持续推进的科研Git项目；不是通用任务平台、数据仓库或集群调度器。

- B/C 是同级科研合作者；SERVER 默认 MASTER，只在冻结科学路线内自主解决工程问题。
- MASTER在科学路线不变时自主修复环境、依赖、代码、配置与恢复问题，不反复请示。
- `main` 是长期权威分支，敏感用户控制的权威仓库URL由首个project.yaml身份提交固定；SERVER默认把结果收敛到`main`，短期`exec/rNNN`只承载异常证据，生产Git只用HTTPS。
- 用户说“拉取，执行”时，SERVER 在 clean `main` 上 fast-forward，领取唯一 READY 的 `rNNN`，先显示不超过50字的执行概述，再在本机执行。
- 项目固定在一台服务器。B/C、桌面端和Git内容都不探测26/46，不选择节点，不启动对端GPU；运行时没有SSH、rsync、双节点回退或placement策略。
- 该规则即单服务器本机执行：一个项目只有一个执行主机。
- SERVER 可从项目路径自动识别26/46；路径不能唯一识别时，只在该服务器本地设置 `cqc.server-profile=26|46`。46挂载点不采用固定路径时，可在本机设置绝对的 `cqc.dataset-root`。
- GPU物理卡号不进入SERVER_PLAN或Git。快速验证为1卡，正常训练默认2卡，4卡必须有绑定当前`rNNN`的`resource_expansion`授权；SERVER在启动前按逐卡可用显存择优设置`CUDA_VISIBLE_DEVICES`。不设跨项目GPU独占租约或等待队列：剩余卡优先，更多任务继续复用最空闲卡并行，只有真实OOM才触发同编号工程适配。
- 训练仍绑定 `research/configuration-baselines/` 中的官方/项目基线，并优先保持官方全局batch与优化器学习率。
- 26固定读取`/home/rspip/cqc/study/pth_data/readme.md`，46固定读取`/home/rspip/zy/study/pth_data/readme.md`。其中pth来自4卡训练，可在合适的快速验证中参考。
- 26官方数据根是`/home/rspip/cqc/data/dataset`，26本机shm根是`/dev/shm/cqc/data/dataset`。46读取挂载到本机的26数据树；46新增下载、复制或转换数据只能写到`/dev/shm/zy/data/dataset`。
- 数据集默认视为官方。B/C只写`dataset_id + version`和可选shards；SERVER只做本地路径可读、目录非空检查，不计算digest、tree hash或provenance。
- 科学上可行时，数据流程必须先从HRSC2016起步；不适用时SERVER_PLAN要说明原因。DOTA、FAIR1M等大数据集不能无理由成为默认第一步。
- `/goal`管理持续目标；STOP、项目锁、`max_hours`、机器验收和最小运行凭据继续有效。心跳只对长任务启用，checkpoint仅在任务支持时使用。
- 外部写入、4卡资源扩大、发布与DOCTORAL仍使用摘要绑定、限时、一次性用户控制；SERVER不能自签。
- `help --section all`显示能力与当前配置；`config show`显示本机执行模式、固定数据/pth路线、GPU规则及权限。
- `validate-project`和`self-test`限制精简Git工作树不超过100MiB；大内容只进入本机项目专属`large-workspaces/<profile>/`，`/dev/shm`镜像保留账号名与项目路径，恢复步骤必须作为受guard的SERVER_PLAN命令运行。
- B/C必须复核SERVER异常终态和结果正确性；普通执行错误由下一条`rNNN`更正，颠覆性错误才通知用户。

## 命令与状态索引

- 派发审计：`dispatch history --epoch`；活动任务返回`MUST_STOP`时必须停止。
- B/C可以怀疑并批判继承对方的任何内容，尤其是期刊评级；一次质疑后立即签发最小方案、记录硬阻塞或请求用户一次决定。
- 大文件闭环：`workspace expand`只核验重建结果，`workspace compact`按manifest回瘦。
- `execution completion`只基于机器验收；自然语言声明不是完成证据。
