# SERVER 角色规则

本文件只补充根 `AGENTS.md` 的公共铁律，不得覆盖公共安全、证据、项目锁和Git规则。

SERVER默认使用MASTER权限。有效B/C方案、用户指令或显式DOCTORAL方案中的`rNNN`已经构成
项目所在本机的普通GPU/CPU训练授权，不得再为`real_experiment`申请或停工。SERVER不得探测
或启动另一节点；快速验证1卡、正常训练2卡，4卡只在resource_expansion授权后使用，物理卡号
由本机运行时按逐卡空闲显存动态选择。GPU不设跨项目独占租约或等待队列：先用剩余空闲卡，
仍有任务就复用当时最空闲的卡立即并行，只有真实OOM才在同一编号内工程恢复。科学路线不变时，SERVER自主处理环境、依赖、代码、配置、并行、
GPU/CPU、临时盘、checkpoint、重试和同编号恢复。外部写入、秘密、不可逆破坏、未授权资源
扩大和用户STOP仍是硬边界；SERVER不得创建、消费或推送敏感权限、项目解锁凭据。B/C必须在
领取前用权威远端`main`的一次性控制完成权限事务；SERVER只能核验领取快照，不能靠角色重绑自签。

SERVER只从clean `main` fast-forward领取任务。正常结果直接形成受机器验收约束的`main`提交；
短期`exec/rNNN`仅用于异常证据。完成命令、机器验收、结果摘要、HTTPS push和
远端ref核验后结束；不得建立永久SERVER分支。MASTER
不评价刊会等级。REPORTING阶段的Git子进程也必须持续heartbeat、响应STOP/项目锁、服从预算与
单步超时，并只在远端ref精确一致后完成。DOCTORAL必须由用户明确启用，启用后才可从内置四区
期刊库进行科研评级；MASTER即使准备了完整请求也不能决定分区或期刊。

结束工作前，有给B/C的要求先写`handoff record`；有修改就精确暂存、提交并通过HTTPS推送
当前计划声明的合法结果ref，再运行`handoff verify`核对远端SHA。SERVER只能通过受约束的结果
发布流程推送`main`，不得借此创建或修改敏感控制，不得等待用户追问是否提交，也不得自动暂存未知文件。

禁止用`while true`、`tail -f`、`watch`、循环`pgrep`或反复询问状态来“看守”任务；长任务由`/goal`和内部有界心跳管理。没有新证据时不产生新讨论或新观察进程。
