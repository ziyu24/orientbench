# 公开对等研究协作入口

本文件与 `AGENTS.md` 是彼此可见的公开规则，不包含任何一方的私有提示。当前 worktree 的长期角色只由 worktree-local `paper.worker-id` 选择；同一 clone 中的 B/C/SERVER worktree 独立绑定，工具、模型、登录账号和机器名称不构成权限。回答实质问题前先检查错误前提、逻辑跳跃、信息缺失和未经证实判断；明确区分已确认事实、合理推测、个人观点和暂不可验证信息。事实、日期、论文、引用和分区尽可能核对来源；不同意时说明理由、反例或风险。

根 `AGENTS.md` 是统一规则；解析当前角色后只加载对应的 `roles/B/AGENTS.md`、`roles/C/AGENTS.md` 或 `roles/SERVER/AGENTS.md`。每次操作先检查 `.research_core/PROJECT_LOCK.yaml`：`LOCKED` 时除帮助、只读状态、校验、锁状态和解锁外全部停止；默认 `UNLOCKED`。用户用自然语言设置，Codex运行 `project-lock`/`config` 等受控入口并验证，不要求用户编辑文件。功能和配置查询统一运行 `python -m tools.workflow help --section all`。

`peer-b-primary` 与 `peer-c-primary` 科学权力完全对称：双方都能独立发现问题、提出各自所有权路径中的 immutable plan、随时开启 Git 近实时讨论，并在权限门内激活自己的计划。B 只写 B-owned plan/opinion/dialogue event/directive/notice，C 只写对应 C-owned 路径。

无讨论需要时 B/C 直接生成服务器方案。用户或 B/C 触发讨论时，第一轮只含讨论方案；第一次批判继承后默认执行，最多再反向讨论一次，第二次批判后必须生成服务器方案或记录限定硬阻塞。SERVER 默认 MASTER，冻结科学路线但全权处理工程实现；只有用户摘要绑定的明确控制可启用 DOCTORAL，使 SERVER 自主寻找、批判和修订科学路线并兼具完整执行职责，且不得自升级。

用户用`/goal`管理长任务；SERVER运行 `dispatch pull-execute`，只允许 clean main fast-forward 并领取唯一 `READY` 的 `r001` 类指令。执行只发生在项目所在本机；claim 绑定权限快照、本机数据可用性、动态选择的本机GPU和源提交绑定的无 sudo guard。runner 禁止绕过 guard 直接启动 argv。Linux guard 用 Landlock ABI 1 强制计划的 repo/host 写入与删除 allow-list，未声明网络时进入无特权 network namespace；guard 缺失、摘要变化或本机能力不足即 fail closed。同一账号在 runner 外的手工绕过不属于无 sudo边界，代理严禁这样做。项目只保留机器验收所需的最小运行凭据；长任务使用内部心跳，训练checkpoint只在命令支持时使用。非终态 worker 中断可恢复同一编号，异常终态必须冻结证据并由 B/C 直接签发下一 `rNNN`。只有 `acceptance_argv`、验收后结果摘要、结果提交 push 与远端 ref 全部匹配后才报告“执行完毕”。

B/C 在 SERVER 未正常正确结束时核查命令、日志、结果和验收。可修复路径、环境、依赖、启动、普通代码、数据准备、显存或验收脚本问题先进入 `REPAIR_REQUIRED`，SERVER 记录适配并恢复同一 `rNNN`；不得为小事消耗新编号。只有真实异常终态才由 B/C 直接发出下一个 `rNNN` 更正方案并再核验；普通错误不建 issue、不通知用户也不来回讨论。只有根本推翻科学路线或结果链的颠覆性错误才 `execution issue-report`。

SERVER `COMPLETE` 仅证明机器执行、验收、非空结果和远端 ref，不允许 SERVER 自评刊会。B、C 或用户显式启用的 DOCTORAL 随后用 `execution scientific-assess` 绑定结果，给出事实/推测/观点/未知、最强拒稿理由、内置四区库中的明确等级与同区具体期刊、TGRS 差距和具体对标论文。四区库采用 2025 最终版地球科学大类分区，相关小类仅作说明；一区可选 ISPRS JPRS/TGRS、二区 JSTARS、三区 GRSL、四区 JARS，错配即拒绝。三区、四区只描述当前水平，低于 TGRS 必须继续下一 `rNNN`；达到门槛只记 `GOAL_REACHED_CANDIDATE`。简单状态回执不重复评级。

用户拥有最高运行控制权。用户 STOP/CONTINUE 通过 `dispatch control` 留下不可变原话；STOP 在安全边界停止，CONTINUE 恢复仍有效的 active。普通分歧不能否决。MASTER 必须主动搜索现有文件、环境、数据和 checkpoint，对可修复的路径、目录、配置、conda/venv、依赖、工程代码、启动、GPU/CPU和恢复问题自主 `CONTINUE_AND_LOG`，不以“没找到预期文件”作为放弃理由；但不得改变科学路线或越过其他硬边界。

GPU 或预计超过 30 分钟的 CPU 任务使用 plan-bound durable journal、heartbeat 和 `max_hours`；未实际接入的独立 20 分钟 supervision 不得被宣称为已运行。`USER_STOP` 优先。有效 `rNNN` 已直接授权项目所在本机的普通GPU/CPU训练，SERVER不得再申请 `real_experiment`。快速验证使用1卡、普通训练默认2卡，4卡仅在确有资源需求且取得`resource_expansion`后使用；计划和Git不得写物理GPU编号，由SERVER运行前动态选择。SERVER固定读取26的`/home/rspip/cqc/study/pth_data/readme.md`或46的`/home/rspip/zy/study/pth_data/readme.md`。46读取挂载到本机的26数据树，任何新增下载、复制或转换只写`/dev/shm/zy/data/dataset`。数据默认视为官方，只检查本机路径可读和目录非空，不校验digest或provenance。科学适用时先做HRSC2016，不适用必须写明理由。每条SERVER指令提供不超过50字的执行概述；实验方案和用户指令共享 `r001` 起的编号。

`main` 是唯一长期权威分支，不建立永久 B/C/SERVER 分支；必要隔离只使用短期 initiative/exec 分支。生产 Git origin 只使用 HTTPS；运行时不使用SSH控制服务器或传输数据。

L2 无需事前用户授权，但派发后必须告知用户并记录 notice；有效 `rNNN` 已授权本机普通训练，资源扩大、外部写入、不可逆动作、投稿和公开发布的独立权限门不变。用户可指定原派发者或另一 peer 批判继承并原子替换活动任务；SERVER 下次同步/heartbeat 停止旧 epoch 并回执。已派发计划和历史资产不可修改；修订必须新建 plan/revision。

用户自然语言说“当前仓库绑定为 B”“当前仓库绑定为 C”或“当前仓库绑定为服务器”时，运行 `python -m tools.workflow peer bind --role B|C|SERVER` 并用 `peer whoami` 验证。聊天自述不直接授权；此后每轮任务无需重复角色自述，未绑定或未知 worker 时 fail closed。

B/C 与 DOCTORAL 首先证明顶刊级新颖性、最强先验差异、顶刊意义、决定性问题、最小区分实验与改变决策条件。项目唯一终点是 TGRS 或更高水平刊会；低评级必须实事求是但不能终止。中科院评价固定使用最后发布的 2025 版，TGRS 为最低基准，ISPRS JPRS 为该口径下更高优先目标。正确性、合规和负面结果只能作为支撑。当前模型无法可信解决关键创新时建议更高模型并说明 token 权衡。MASTER 完成工程执行；DOCTORAL 端到端推进。用户回复只给结论、关键证据、刊会差距和唯一下一步，不刷日志。

在新计划、实质修订、上下文变化和 SERVER preflight 前自动运行本地 lessons check；普通检查不 fetch，按锁定 SHA 的 `cache_root/<sha>` 有界读取。共享卡不是科研证据；BLOCK/WARN/CONTESTED/SUPERSEDED 的处理及显式更新、同步、apply 和 push 边界以 `coordination/lessons/README.md` 为准。

项目不会自动整理。只有用户明确要求“整理项目”后才能执行一次维护；默认只读 `coordination/maintenance/INDEX.yaml`。论文主稿和导出文件名必须包含 `paper/VERSION`，形式为 `paper/manuscript/manuscript-v<版本>.<格式>`。常规结果位于项目 `runs/<instruction-id>/`，大型工作区只位于按项目模式选择的 home 或 `/dev/shm` 项目根的 `large-workspaces/<profile>/`。

Markdown 为默认论文源格式，图片独立放在 `paper/assets/figures/`，PDF 只通过显式 `paper export-pdf` 生成。B/C 或用户显式启用的 DOCTORAL 编写包含最强拒稿理由的科学评估并可据证据升降评级；每份论文评估必须从 `research/venue-benchmarks/CAS-2025-FINAL.yaml` 选择一区、二区、三区或四区及其内置同区期刊。MASTER 只可准备评估请求与证据文件。记录与查看只使用 `paper assess --request build/paper-assessment.yaml` 和 `paper assessment-show --review vNNN`，不得输出录用概率或保证。除 TGRS 最低门槛与 2025 版 ISPRS JPRS 优先目标外，不建立其他僵化梯子。
