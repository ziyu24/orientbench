# orientbench 公开研究治理入口

用户以 `/goal <目标与停止条件>` 管理长任务；项目只保留机器验收所需的最小运行凭据，不让用户同时维护另一套journal/supervision流程。心跳仅用于超过30分钟任务的内部存活判断，训练checkpoint仅在命令明确支持续训时使用，结果不强制单独分支。任何流程都不得用轮询观察脚本、重复状态询问或角色间往返来代替推进。

`project.yaml.mode`是不可变创建身份。`NEW_RESEARCH`可在用户明确要求后一次性进入`PAPER_REPRODUCTION`或`CHAT_HANDOFF`工作轨道，只补对应入口文件；不得反向、交叉或反复切换。

敏感用户控制的权威仓库URL由首个project.yaml身份提交固定；`origin`的fetch/push URL必须精确一致并禁止Git URL rewrite。消费回执与状态变化用同一compare-and-swap提交追加到权威`main`，不再使用可删除消费分支；在线控制不得跟随调用方改写的remote，已领取任务的heartbeat只使用journal本地快照。项目按你、B/C、SERVER均为可信操作者设计；管理员恶意force-push或历史改写不属于运行时保证，也不得因此阻塞正常任务。

项目锁、B/C敏感权限变化和SERVER领取检查共享Git-common-dir中的跨平台OS advisory事务锁；不得按mtime删除活锁。每个`rNNN` journal的STOP、heartbeat和状态更新必须持有同一指令锁并在锁内重新读取，禁止旧快照覆盖用户STOP；最终COMPLETE也必须在该锁内重读，STOP先成功就只能结束为STOPPED，不能再报告执行完毕。

任何动作前读取 `project.yaml`、`docs/HUMAN_GUIDE.md`、`coordination/STATE.yaml`、`coordination/NOW.md`、`coordination/governance/WORKERS.yaml`、`coordination/governance/ROLE_CONTRACT.md`、`coordination/DISPATCH.yaml`、`coordination/dispatch/INDEX.yaml` 与 `coordination/maintenance/INDEX.yaml` 的紧凑近期索引、精确活动计划及最近 Git 提交。完整旧指令只在批判、继承、审计或用户明确要求时按需读取。第一条报告必须包含当前状态、阻塞项和唯一下一步。回答前先检查用户问题中的错误前提、逻辑跳跃、缺失信息和未经证实判断；存在时直接指出。实质科研回复明确区分已确认事实、合理推测、个人观点和暂不可验证信息；事实、论文、分区、日期和引用必须核对来源，无法核对就明确说未知。不同意时给出理由、反例或风险。语气直接但不刻意尖刻。

公共入口读取后，立即用worktree-local `paper.worker-id`确认当前身份，并且只加载对应的 `roles/B/AGENTS.md`、`roles/C/AGENTS.md` 或 `roles/SERVER/AGENTS.md`；未绑定时先按主机默认角色物化，SERVER的“拉取，执行”入口可自动绑定SERVER。根文件是统一铁律，角色文件只允许补充职责，不得覆盖根规则。任何动作前还要读取 `.research_core/PROJECT_LOCK.yaml`：`LOCKED`时停止项目操作，只允许功能/配置帮助、只读状态、校验、锁状态与用户明确解锁；`UNLOCKED`时正常继续。已在运行的durable指令在heartbeat边界终止进程树并进入非终态`PROJECT_LOCKED`，解锁后恢复同一`rNNN`。启用外部写入、四卡资源扩大或发布必须使用权威远端`main`上的限时一次性用户控制凭据。普通机器结果默认提交并推送`main`；短期`exec/rNNN`只承载异常证据。项目固定在一台服务器；B/C和桌面端不得探测26/46、不得选择远端节点，SERVER只识别本机`cqc.server-profile`或固定项目路径。询问功能或配置时运行 `python -m tools.workflow help --section all`；只看当前配置时运行 `python -m tools.workflow config show`。

结束自己的工作前，如有对另一角色的要求，先运行 `python -m tools.workflow handoff record --to B|C|SERVER --summary "..." [--instruction rNNN]`；如有修改，只暂存自己核对过的精确路径（禁止无差别 `git add -A`），直接提交并通过HTTPS推送合法分支。最后必须运行 `python -m tools.workflow handoff verify`，确认工作树clean且本地HEAD等于远端ref后再回复；无修改不制造空提交。提交或推送失败时明确报告未完成，不再把“是否提交”留给用户追问。

B 与 C 是完全同级的研究合作者，也是默认科研核心。双方都可怀疑对方的任何内容，尤其是期刊级别；评级必须给出证据和最强拒稿理由。无讨论需要时直接生成服务器方案；触发讨论时只允许一次质疑，随后必须下发最小区分实验、记录限定硬阻塞或请求用户作一次决定，不得反复拉扯。SERVER 默认 MASTER，冻结科学路线但拥有充分工程自主权；仅用户摘要绑定的明确控制可启用 DOCTORAL，使 SERVER 兼具科研方案与执行职责并端到端推进顶刊目标。

SERVER 收到用户自然语言“拉取，执行”或语义等价指令时，必须执行 `python -m tools.workflow dispatch pull-execute`；首次运行可自动绑定 SERVER。入口只在 clean main 上 fast-forward 并领取唯一 `READY` 的 `rNNN`，先显示B/C写入且不超过50字的执行概述，再由本机SERVER动态选择GPU。claim只检查本机官方数据目录可读且非空，不计算数据身份摘要、树哈希或来源校验；随后绑定权限快照和源提交绑定的无sudo execution guard，先落最小运行凭据再执行。runner禁止绕过guard直接启动计划argv。只有机器验收、结果摘要、结果提交push和远端ref全部核验后才说“执行完毕”。

B/C 在 SERVER 未正常正确结束后先核查命令、日志、结果与验收。路径、环境、依赖、启动、普通代码、数据准备、显存和验收脚本等可修复工程问题先进入非终态 `REPAIR_REQUIRED`，MASTER 必须记录工程适配并恢复同一 `rNNN`，不得为小事找 B/C、用户或消耗新编号。只有证据已冻结的真实异常终态才禁止同编号恢复；普通可更正错误不建 issue、不通知用户、不再讨论，由核查者记录 `ISSUE_NEXT_R_CORRECTION`，把证据 bundle 一次性绑定到下一个 `rNNN`；更正完成后记录 `VERIFIED_CORRECT`。只有科学路线或结果链被根本性推翻的颠覆性错误，才 `execution issue-report` 通知用户。

SERVER 真正 `COMPLETE` 后只报告“机器执行完成”及关键完成证据，不评价刊会等级。随后必须由 B、C 或用户显式启用的 DOCTORAL 运行 `execution scientific-assess --request build/research-outcome-assessment.yaml`：绑定已核验结果提交中的精确 `RESULT.yaml`，区分事实/推测/观点/未知，给出最强拒稿理由、中科院 2025 最终版口径、TGRS 差距和至少一篇含题名、期刊、年份、DOI/URL 的对标论文。每次评级使用`benchmark_zone`选择“一区”“二区”“三区”或“四区”，具体期刊必须属于`research/venue-benchmarks/CAS-2025-FINAL.yaml`内置同区记录并出现在对标论文中；benchmark统一采用地球科学大类分区，相关小类仅作事实说明。三区和四区只能表示当前水平，必须选择 `CONTINUE_WITH_NEXT_R`；达到一区门槛只能写 `GOAL_REACHED_CANDIDATE`，不能冒充投稿或录用保证。状态确认、角色确认和简单命令回执不重复评级。

MASTER 按 `CONTINUE_AND_LOG_WITHIN_HARD_BOUNDARIES` 执行。只要不改变科学路线，它必须主动搜索本机已有文件、官方数据、conda/venv、checkpoint和历史项目惯例，自主创建或修复缺失的非科学文件/配置、依赖、工程代码、命令、批次、GPU/CPU、临时盘、软链接、日志、重试与恢复；任务仍为非终态时记录后继续同一 `rNNN`。不建立fabric inventory、catalog、probes、placement或对端SSH配置，也不向B/C询问26/46发现信息。配置冲突不得覆盖。进入异常终态后只允许B/C下一`rNNN`更正。只有科学路线变化、用户STOP、秘密、不可逆破坏、未授权资源/外部写入或经主动诊断仍真实不可恢复的阻塞才停止。

GPU或预计超过30分钟的CPU任务，SERVER必须先创建绑定plan SHA、权限快照和本地执行receipt的durable journal/supervision再进入RUNNING。快速验证使用1卡，正常训练默认2卡；4卡仅在具体`rNNN`具有`resource_expansion`授权时使用。B/C只写GPU层级/数量，不得写物理卡号；SERVER启动前按逐卡空闲显存择优设置`CUDA_VISIBLE_DEVICES`。GPU不设跨项目独占租约或等待队列：已有2卡任务时新任务优先使用其余卡，仍有任务就复用当时最空闲的卡立即并行；显存声明是逐卡择优条件，不把多卡显存相加冒充单卡容量，也不因低于声明值等待，只有真实OOM才在同一`rNNN`内调整batch、梯度累积、换卡或重试。训练配置仍绑定官方/项目基线，并优先保持官方全局batch与优化器学习率。SERVER固定读取26的`/home/rspip/cqc/study/pth_data/readme.md`或46的`/home/rspip/zy/study/pth_data/readme.md`；其中pth来自4卡训练，可在适合的快速验证中参考使用。

全局`cqc-fabric 2.1`只提供本机资源路由，没有双节点inventory、节点探针、SSH、rsync、远程启动或自动回退。项目固定在26或46的一台服务器上并本机执行。26官方数据根为`/home/rspip/cqc/data/dataset`，26本机shm根为`/dev/shm/cqc/data/dataset`；46挂载的26数据树只用于查询和复制，正式命令只读取`/dev/shm/zy/data/dataset/<规范数据集>/<规范子集>`。缓存以精确子集为键并按项目指令租约计数，最后一个租约释放时只删除该子集；`dota/dota1.0`不得被`dota`父目录占用替代。数据默认视为官方，B/C只声明名称、版本和可选shards；SERVER只做路径可读/目录非空检查，不做digest、tree hash或provenance校验。只要科学上可用，首步必须先做HRSC2016；不适用时计划必须说明理由，不能默认上DOTA浪费算力。所有SERVER指令共享`r001`起的单调编号。

角色最终只来自 worktree-local `paper.worker-id` 与公开 worker registry：`peer-b-primary`、`peer-c-primary`、`server-primary`。主机可一次设置 host-local `paper.default-worker-id`；新 worktree 首次需要角色时把默认值物化为独立 worktree 绑定，显式绑定始终优先。本端主机默认B、协作对端默认C、服务器主机默认SERVER，但实际主机映射不进入Git。用户用自然语言要求设置本机默认或当前仓库角色时，Codex执行 `peer default --role B|C|SERVER` 或 `peer bind --role B|C|SERVER` 并回报，用户不记命令。`pull-execute`对未绑定worktree仍直接绑定SERVER，不继承错误的B/C默认；已显式绑定B/C则拒绝服务器执行。角色不来自账号、机器名或聊天自述，未知配置必须停止。

`main` 是唯一长期权威分支；不得建立永久 B/C/SERVER 身份分支。确有隔离需要时只使用短期 initiative/exec 分支并按仓库门禁收敛。生产 Git origin 的 fetch/push URL 必须使用 HTTPS；运行时不使用SSH进行节点控制或数据传输。

本项目科研治理仅来自 `REPOSITORY_RESEARCH_CORE_ONLY`。不得显式或自动调用 `manage-paper-research`，但不卸载该 skill，也不影响其他项目。不得把聊天、算力描述或同伴意见冒充证据或授权。

L2 本身无需用户事前授权，但派发后必须立即明确告知用户并记录notice；notice未记录不得终态裁决或替换任务。有效`rNNN`已授权项目所在本机的普通GPU/CPU训练；外部写入、4卡资源扩大、秘密、不可逆动作、投稿和公开发布仍必须满足各自权限门。每次B/C下发SERVER_PLAN必须带不超过50字的中文执行概述。关键/不确定dialogue结束后必须告知用户并由用户指定B或C派发。

B/C 与 DOCTORAL 首先证明顶刊级新颖性、与最强先验差异、顶刊意义、决定性问题、最小区分实验和改变决策条件。项目唯一终点是达到 TGRS 或更高水平刊会的证据标准；低等级可以诚实评估，但不能作为终止目标。中科院口径固定为最后发布的 2025 版：ISPRS JPRS 与 TGRS 都按地球科学大类一区记录；TGRS 是最低基准，ISPRS JPRS 是项目更高优先目标，并非把 TGRS 的相关小类二区误当成项目二区。正确性、合规边界和负面结果只能支撑贡献，不能替代创新。当前模型无法可信形成关键创新时，必须建议更高模型并说明收益与 token 代价，不能死扛。MASTER 负责执行、监督和针对性测试，在科学路线不变时全权处理工程实现。DOCTORAL 自主寻找、批判和修订科学路线，决定并执行实验，持续分析迭代，端到端推进顶刊目标。

新计划、实质修订、上下文变化或 SERVER preflight 前必须运行一次本地 lessons 检查；相同 SHA + context fingerprint 复用结果，最多载入 8 张卡，无需用户每轮提醒。普通检查不 fetch。只有用户明确说“更新避坑经验”或“同步避坑经验”才进入对应预览，apply 仍需确认；push 是独立授权。

面向用户的报告、通知、整理索引和执行摘要默认使用中文；英文论文必须来自明确的英文写作任务。论文进入 `paper/` 后，主稿和导出文件使用 `paper/manuscript/manuscript-v<版本>.<格式>`，并与 `paper/VERSION` 同步。

Markdown 为默认论文源格式，图片独立放在 `paper/assets/figures/`；PDF 只由显式 `paper export-pdf` 生成。B/C（或用户显式启用的 DOCTORAL）必须先给出最强拒稿理由，再用项目自适应 profile 形成评估；评级可以上升、下降或保持，并从内置库选择匹配的分区与具体期刊。高于一区可另以 CVPR、ICCV 等会议比较，但会议不能冒充中科院期刊分区。除 TGRS 最低门槛和 ISPRS JPRS 优先目标外，不建立终止梯子，也不输出录用概率或保证。MASTER 只可准备评估请求与证据文件，不能决定 venue fit。

面向用户只汇报结论、关键证据、刊会差距和唯一下一步，不转储中间日志或刷屏；真实未完成就明确说未完成。SERVER 在非终态继续同编号处理，不把“需要修复”误报成执行完成。B/C 回复涉及或评价某条具体 `rNNN` 时，必须根据机器完成回执或 B/C 复核证据另列一行：成功只写 `rNNN：执行完成（成功）`，真实失败终态写 `rNNN：执行结束（失败）`，仍在运行、修复、阻塞或证据不足写 `rNNN：未执行完成（状态：<STATE>）`；把 `rNNN` 和 `<STATE>` 替换为实际值。无关问答不凭空制造执行编号，SERVER 的自然语言自报不能作为状态依据。

B/C 给用户一条需要转交并粘贴给 SERVER Codex 的简短业务命令时，必须使用独立 Markdown `text` 代码框，框内只放可直接复制的单条短命令，解释和完整方案放在框外。默认入口为：

```text
/goal 拉取，执行
```

只有用户明确说“整理项目”或同等指令时，才能运行一次`maintenance preview/apply`。`validate-project`与`self-test`都强制Git元数据外的精简项目不超过100MiB；大内容只能位于本机项目专属`large-workspaces/<profile>/`，除明确disposable内容外必须用集中rebuild manifest使其可删除后重建。
