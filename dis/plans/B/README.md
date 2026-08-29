# B-owned immutable plans

Only `PEER_B` may create plans below this directory. Every plan declares `required_permissions`; activation and SERVER resolution check those gates in `coordination/STATE.yaml`. Dispatched plans are immutable; revisions use a new plan ID or revision directory.

Plans use `execution_policy: CONTINUE_AND_LOG_WITHIN_HARD_BOUNDARIES` and freeze `scientific_scope`, `minimum_discriminating_experiment`, and `kill_condition`. Every `rNNN` SERVER_PLAN also declares the exact repo/host write, secret, network, and resource `execution_scope` enforced by the source-commit-bound no-sudo guard. They also state novelty, strongest-prior difference, top-venue relevance, the decisive question, minimum experiment, and decision-change condition. MASTER uses `CONTINUE_AND_LOG` for full engineering autonomy—including proactive discovery of existing files/environments/data, dependencies, code/configuration, launch, resources and recovery—while preserving the scientific route.

B 聚焦创新、方向、科学假设和结果解释。普通计划声明最小必要验证，不默认要求生产级加固、重复大规模测试或全库测试；SERVER 负责执行和针对性测试。

发现 SERVER 非正常或结果不正确时必须核查。先用 append-only `execution review` 绑定 terminal journal、`ABNORMAL-<attempt>.yaml` 与日志摘要；普通错误直接签发下一条 `rNNN` 更正方案，回执只允许消费一次，并在执行后绑定 `RESULT.yaml` 与验收 checkpoint 记录验证通过。不建 issue、不通知用户、不再讨论；只有颠覆性错误进入 catastrophic issue 并通知用户。
