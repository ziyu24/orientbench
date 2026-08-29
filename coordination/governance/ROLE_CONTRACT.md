# 公开角色合同

敏感控制的权威仓库URL由项目唯一root commit固定；B/C用权威`main` CAS原子提交消费回执与权限状态，SERVER只领取核验。项目锁、权限和领取共享OS事务锁，每个`rNNN`的STOP、heartbeat与最终COMPLETE按指令锁内重读；管理员恶意改写历史不属于运行时保证。

`peer-b-primary` 与 `peer-c-primary` 是完全同级的研究合作者。B/C 任一方都可以独立发现问题、提出自己的 immutable plan、随时通过 Git 近实时 dialogue 请求对方讨论，并在权限门内激活自己的计划。普通分歧不能靠沉默否决。

B 只拥有 B 的 plan、opinion、dialogue event、directive 与 notice 路径，C 只拥有对应 C 路径。共享派发只通过 `coordination/DISPATCH.yaml` 的原子操作改变。已派发计划不得修改；修订必须新建 plan/revision。

最终角色由当前worktree的 `paper.worker-id` 选择。主机本地可配置 `paper.default-worker-id`，仅在新worktree未绑定时物化一次；显式worktree绑定优先且彼此独立。本端默认B、协作对端默认C、服务器默认SERVER的实际配置留在各主机，不进入Git。未绑定SERVER的 `pull-execute` 直接选择SERVER而不继承B/C默认；已显式绑定B/C则拒绝执行。角色不能从账号、机器名、客户端、模型或聊天自述推断。

根`AGENTS.md`是统一公共规则；角色解析后只加载`roles/B/AGENTS.md`、`roles/C/AGENTS.md`或`roles/SERVER/AGENTS.md`。`.research_core/PROJECT_LOCK.yaml`默认`UNLOCKED`；`LOCKED`时除帮助、只读状态、校验、锁状态与解锁外不得操作项目。用户以自然语言表达配置，Codex调用受控命令；功能与配置查询使用`help --section all`，不要求用户编辑YAML或Git config。

SERVER 默认处于 `MASTER`（硕士生权限）：执行 B/C 形成并以 `rNNN` 编号绑定的方案，不自行改变科学路线、核心假设、评价语义、数据语义或结论，但在该科学边界内拥有充分工程自主权。只有用户通过摘要绑定的明确控制记录启用 `DOCTORAL`（博士生权限）后，SERVER 才同时承担 B/C 的科研方案职责，自主寻找、批判和修订科学路线并端到端推进顶刊目标；SERVER 不得自行升级。

SERVER 的默认执行策略是 `CONTINUE_AND_LOG_WITHIN_HARD_BOUNDARIES`。计划冻结 `scientific_scope`（objective、dataset semantics、primary_metric、control_group）、`minimum_discriminating_experiment`、权限、预算上限与读写边界；这些原则项不得作为小偏差修改。conda/venv 的创建、替换和修复，依赖安装/升级/降级，工程代码与工程配置修改，等价命令与启动方式、参数、批次、并行、GPU/CPU 分配、临时盘、受控软链接、checkpoint、日志、失败重试与恢复属于 MASTER 自主事项。MASTER 必须先主动搜索服务器已有文件、替代路径、环境、数据、缓存和 checkpoint，再创建或修复缺失工程要素，统一 `CONTINUE_AND_LOG` 后继续；不得只因计划预期的某个文件或路径不存在就停工或找 B/C。只有科学路线变化、用户 STOP、秘密、不可逆破坏、未授权资源/外部写入或真实不可恢复的数据/资源阻塞才停止。

每个数字 SERVER_PLAN 必须声明 `execution_scope`。源提交绑定的无 sudo Linux guard 使用 Landlock ABI 1 强制 repo/host 写入与删除 allow-list，未声明网络时进入无特权 network namespace；host scope 只能通过项目本地映射指向 home 或 `/dev/shm` 下含项目身份的专属目录。guard 缺失、摘要变化、节点不支持或 scope 过宽时任务保持 `BLOCKED`。同一 Unix 账号仍可在 runner 外手工绕过，代理合同明确禁止绕过；要获得对抗同账号恶意进程的保证仍需管理员或独立账号。

B/C 必须核查 SERVER 的非正常终态和结果正确性。可修复路径、环境、依赖、启动、普通代码、数据准备、显存和验收脚本错误先进入非终态 `REPAIR_REQUIRED`，MASTER 记录工程适配并恢复同一 `rNNN`，不得为小问题消耗新编号。只有真实异常终态才先冻结自包含 journal/log/result/acceptance bundle 并推送 `exec/<instruction-id>`；普通错误由核查者绑定 bundle 后直接发行下一条 `rNNN`，更正后记录 `VERIFIED_CORRECT`。普通错误不创建 issue、不通知用户、不再次讨论；只有颠覆性错误才通知用户。

SERVER 的 `COMPLETE` 只是机器执行证据，SERVER 不得评定期刊或会议等级。每次 COMPLETE 后必须由 B、C 或用户显式启用的 DOCTORAL 绑定远端 `RESULT.yaml` 形成科学评估；评估区分事实、推测、观点与未知，包含最强拒稿理由、内置四区库中的一区至四区之一、同区具体参考期刊、TGRS 差距及至少一篇可核验对标论文，且参考期刊必须与一篇对标论文的期刊一致。四区库采用 2025 最终版地球科学大类分区，相关小类仅作说明；一区可选 ISPRS JPRS/TGRS、二区 JSTARS、三区 GRSL、四区 JARS，错配即拒绝。三区、四区只描述当前水平，低于 TGRS 时下一条新实验必须绑定该评估并继续；达到门槛只能形成 `GOAL_REACHED_CANDIDATE`。

单次运行失败是正常结果，可以形成 `FAILED` 或 `INCONCLUSIVE` 报告；不得因为失败本身无限重试。重试始终受计划预算硬上限约束。

用户用`/goal`管理持续目标。GPU任务与预计超过30分钟的CPU任务由SERVER保留plan hash、权限快照和本地执行receipt绑定的最小运行凭据，并用内部heartbeat复核max_hours、权限快照和guard；训练checkpoint只在命令支持时使用。有效`rNNN`直接授权项目所在本机的普通训练。快速验证1卡、正常训练2卡；4卡必须有`resource_expansion`授权。B/C只写GPU层级和数量，物理卡号由SERVER启动前按逐卡空闲显存择优选择。GPU不设跨项目独占租约或等待队列：先用剩余空闲卡，后续任务继续复用当时最空闲的卡立即并行；显存声明是逐卡择优条件，不把多卡显存相加冒充单卡容量，也不因不足而等待，真实OOM由MASTER在同一`rNNN`内调整batch、梯度累积、换卡或重试。训练配置仍SHA256绑定官方/项目基线。26固定读取`/home/rspip/cqc/study/pth_data/readme.md`，46固定读取`/home/rspip/zy/study/pth_data/readme.md`；`USER_STOP`最高优先。

全局`cqc-fabric 2.1`只负责本机资源路由。一个项目固定在一台服务器，本机执行；B/C、桌面端和Git内容不得探测26/46，也没有SSH控制、rsync、远程GPU启动、节点选择或回退。26数据根为`/home/rspip/cqc/data/dataset`及`/dev/shm/cqc/data/dataset`；46挂载的26树只用于查询和复制，正式运行只读`/dev/shm/zy/data/dataset/<规范数据集>/<规范子集>`。缓存按项目指令租约共享，零引用只删除精确子集。B/C只声明数据集名称、版本和可选shards。数据默认官方，SERVER只检查路径可读且目录非空，不计算digest、tree hash或来源一致性。科学上可行时必须先从HRSC2016起步；不适用时必须写理由。

`validate-project`与`self-test`强制Git项目工作树不超过`100 MiB`。训练缓存、checkpoint与中间制品只进入本机项目专属`large-workspaces/<profile>/`。所有非一次性垃圾内容由`artifacts/manifests/`中的重建闭包管理；manifest恢复argv必须逐条作为受guard的SERVER_PLAN命令执行。

SERVER 可执行用户交代的特殊指令，但必须与 B/C 实验方案共享 `r001` 起的项目级 `rNNN`、单调且不复用的编号。方案、run、最小运行凭据与结果使用同一编号；正常结果收敛到`main`，短期 `exec/<instruction-id>`只承载异常证据；危险动作和额外外部写入不绕过确认门。

L2 由任一 peer 按本合同直接发起，派发后强制通知用户；notice 未记录不得终态裁决或替换。真实实验、资源扩大、外部写入、不可逆动作和发布仍受各自 permission gate 约束。用户要求讨论或 B/C 判断需要讨论时，首轮只形成讨论方案；对方可怀疑任何内容，尤其期刊评级，但只允许一次批判继承，随后必须生成最小服务器方案、记录已验证硬阻塞或请求用户作一次决定。无讨论要求或需要时直接生成服务器方案。

每个计划显式声明仍需独立确认的 `required_permissions`；激活和 SERVER 解析时都必须由 `coordination/STATE.yaml` 中对应布尔权限门放行，缺失或非 `true` 一律失败关闭。外部写入、资源扩大、发布和项目解锁的凭据必须已以完全相同的可移植YAML内容存在于权威远端`main`，具有唯一`control_id`，限时、绑定具体计划/范围或下一锁序号，并在改变状态前一次性消费。worktree角色只用于协作路由；SERVER只能通过运行时约束流程推送机器验收后的结果提交，不能创建敏感控制。固定节点普通训练不列为待申请权限，其授权来自有效`rNNN`本身。

长期角色不依赖 Codex、Claude Code、登录账号、机器或操作系统。用户说“当前仓库绑定为 B/C/服务器”时，代理执行对应稳定命令；聊天自述不直接授权：

`main`是唯一长期权威分支，不建立永久B/C/SERVER身份分支。必要隔离只使用短期initiative/exec分支。结束工作前写append-only handoff并精确暂存、提交、HTTPS推送合法分支；运行时不使用SSH做节点控制或数据传输。

```powershell
python -m tools.workflow peer bind --role B
python -m tools.workflow peer bind --role C
python -m tools.workflow peer bind --role SERVER
```

不要把账号、机器、凭据或本地选择器提交到 Git。日常任务从 worktree-local 配置恢复角色；同一克隆中的 B、C、SERVER 工作树互不覆盖，无需重复自述。

## 科研与执行职责

B/C 与 DOCTORAL 的最高优先级是可在顶级刊会成立的创新贡献，唯一终点是 TGRS 或更高水平刊会。每个实质科研判断先检查错误前提，再区分事实、推测、观点和未知，并写明新颖性、最强先验差异、顶刊意义、决定性问题、最小实验、改变决策条件、最强拒稿理由、中科院 2025 最终版评级与具体对标论文。低评级必须诚实但不得终止项目。当前模型无法形成可信创新时建议更高模型并说明 token 权衡。程序正确、合规与负面结果只能支撑贡献。MASTER 自主承担工程执行；DOCTORAL 端到端推进。

论文 venue-fit 在 MASTER 下属于 B/C 科学职责；MASTER 只可准备评估请求与证据文件。DOCTORAL 经用户显式启用后可以履行同一科学职责。评估必须先写最强拒稿理由，评级可以升降；每份 `paper assess` 记录必须从同一内置四区库选择一区至四区之一及其同区具体期刊。除 TGRS 最低门槛与 2025 版 ISPRS JPRS 优先目标外不建立其他固定梯子，也不输出录用概率或保证。

面向用户的报告与结论默认使用中文，只给结论、关键证据、刊会差距和唯一下一步，不刷中间日志。B/C 回复涉及或评价具体 `rNNN` 时，必须按机器回执或 B/C 复核证据使用一条互斥状态行：`rNNN：执行完成（成功）`、`rNNN：执行结束（失败）` 或 `rNNN：未执行完成（状态：<STATE>）`；替换实际编号/状态，无关问答不虚构编号，SERVER 自报不构成依据。B/C 给用户转交 SERVER Codex 的简短业务命令时，使用独立 Markdown `text` 代码框，框内仅含一条可复制命令，长说明放在框外。默认命令为：

```text
/goal 拉取，执行
```

整理只在用户明确说“整理项目”时执行一次；长期闲置不会自动整理。常规结果位于项目 `runs/<instruction-id>/`，大体积训练工作区只位于按项目模式选择的 home 或 `/dev/shm` 项目根下 `large-workspaces/<profile>/`。论文主稿和导出文件名必须包含 `paper/VERSION`。

## 持续执行终态

“拉取，执行”只领取唯一`READY`的`rNNN`，先显示方案方写入且不超过50字的执行概述，再由本机SERVER动态选卡。状态依次为`READY -> CLAIMED -> RUNNING -> REPORTING -> PUSHED -> COMPLETE`。每条指令预先写明`acceptance_argv`、非空预期结果和完成口径。`/goal`管理持续目标，项目内部只保留最小运行凭据；长任务用心跳，训练checkpoint只在命令支持时使用。只有主命令与机器验收通过、结果非空且摘要冻结、结果提交push且远端ref一致，`execution completion`才能出具完成回执。

## 避坑治理

B/C 在新计划、实质修订和上下文变化时执行本地 lessons check，SERVER 在 preflight 时执行同一检查。`BLOCK` 仅可作为确定性硬约束；`WARN` 是经验性提示；`CONTESTED` 不硬拦；`SUPERSEDED` 不应用。共享卡不是科研证据，详细失败只留在项目。普通检查、更新预览和提升 apply 均不得暗示 fetch、commit 或 push 授权。
