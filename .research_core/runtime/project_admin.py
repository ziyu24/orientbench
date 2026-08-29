from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any

import yaml

from . import (
    authorization,
    journal_benchmarks,
    peer_governance,
    project_lock,
    research_execution,
    state,
    transactions,
)


CAPABILITY_IDS = (
    "ACCOUNT_INDEPENDENT_WORKERS", "SYMMETRIC_PEER_INITIATION",
    "OWNER_SEPARATED_PLANS", "IMMUTABLE_DISPATCHED_PLANS",
    "SINGLE_HASH_BOUND_DISPATCH", "FAIL_CLOSED_AUTHORIZATION",
    "MASTER_EXECUTION_ONLY", "THREE_MODE_INTAKE", "SELF_CONTAINED_RUNTIME",
    "NATURAL_LANGUAGE_ROLE_BINDING", "HOST_LOCAL_DEFAULT_ROLE_BINDING",
    "WORKTREE_LOCAL_ROLE_BINDING", "GIT_NEAR_REALTIME_DIALOGUE",
    "L2_POST_DISPATCH_NOTICE", "USER_DESIGNATED_CRITIQUE_INHERITANCE",
    "EPOCH_REPLACEABLE_DISPATCH", "ADAPTIVE_SERVER_EXECUTION",
    "NATURAL_LANGUAGE_PULL_EXECUTE", "USER_SUPREME_RUNTIME_CONTROL",
    "COMPACT_DISPATCH_HISTORY", "NATIVE_GOAL_PRIMARY_MINIMAL_RUN_RECEIPT",
    "A_RESILIENT_COMPUTE_ASSETS", "USER_SPECIAL_DIRECTIVE_EXECUTION",
    "UNIFORM_REBUILDABLE_ARTIFACTS", "EXPLICIT_PROJECT_MAINTENANCE",
    "ROLE_FOCUSED_VALIDATION", "CHINESE_USER_MATERIALS",
    "PROJECT_CONTAINED_EXECUTION_LAYOUT", "VERSIONED_PAPER_FILENAMES",
    "PINNED_RESEARCH_LESSONS", "MARKDOWN_FIRST_PAPER", "EXPLICIT_PDF_EXPORT",
    "ADVERSARIAL_VENUE_ASSESSMENT", "SINGLE_HOST_LOCAL_EXECUTION",
    "FIXED_SERVER_PROFILE", "OFFICIAL_LOCAL_DATASET_ROUTING",
    "HRSC2016_FIRST_WHEN_APPLICABLE", "LOCAL_DYNAMIC_GPU_SELECTION",
    "PLAN_BOUND_MACHINE_ACCEPTANCE", "ASYMMETRIC_DATASET_COLLECTIONS",
    "SINGLE_CHALLENGE_THEN_ACTION", "R_PREFIXED_SERVER_INSTRUCTIONS",
    "MASTER_DEFAULT_AUTHORITY", "MASTER_ENGINEERING_AUTONOMY",
    "EXPLICIT_DOCTORAL_AUTHORITY", "DOCTORAL_TOP_VENUE_END_TO_END_OWNERSHIP",
    "BC_POST_EXECUTION_REVIEW_AND_CORRECTION", "CATASTROPHIC_EXECUTION_ERROR_REPORTING",
    "DETERMINISTIC_SHM_HOME_MIRROR", "LEAN_REBUILDABLE_LARGE_WORKSPACE",
    "NO_SUDO_LANDLOCK_EXECUTION_GUARD", "DURABLE_PULL_EXECUTE",
    "GIT_REF_VERIFIED_COMPLETION", "TOP_VENUE_INNOVATION_PRIORITY",
    "TGRS_MINIMUM_PUBLICATION_GOAL", "FINAL_2025_CAS_VENUE_BASELINE",
    "EXPLICIT_CAS_ZONE_AND_REFERENCE_JOURNAL",
    "BUILT_IN_FOUR_ZONE_JOURNAL_BENCHMARK_LIBRARY",
    "EPISTEMICALLY_LABELED_RESEARCH_RESPONSES",
    "BC_SCIENTIFIC_POST_COMPLETION_ASSESSMENT", "SAME_R_ENGINEERING_REPAIR",
    "ONE_TWO_FOUR_LOCAL_GPU_TIERS", "HOST_LOCAL_SERVER_RESOURCE_INVENTORY",
    "HTTPS_ONLY_GIT_REMOTE", "CONCISE_USER_REPORTING",
    "MODEL_ESCALATION_RECOMMENDATION", "PLAN_AUTHORIZES_LOCAL_COMPUTE",
    "ROLE_LAYERED_AGENT_INSTRUCTIONS", "DEFAULT_UNLOCKED_PROJECT_OPERATION_LOCK",
    "CODEX_MANAGED_CONFIGURATION_AND_HELP", "BC_EXPLICIT_RNNN_EXECUTION_STATUS",
    "COPYABLE_SERVER_SHORT_INSTRUCTION", "REMOTE_MAIN_ONE_TIME_USER_CONTROL",
    "ROOT_COMMIT_PINNED_USER_CONTROL_REPOSITORY",
    "LINEARIZABLE_PROJECT_CONTROL_TRANSACTIONS",
    "AUTHORITATIVE_MAIN_NORMAL_OPERATION_CONTROL_LEDGER",
    "DURABLE_JOURNAL_TRANSACTION_LOCK",
    "ROLE_END_GIT_FINALIZATION", "CONCISE_EXECUTION_SUMMARY",
    "SERVER_46_SUBSET_CACHE_LEASES", "IMMUTABLE_MODE_ONE_WAY_WORK_TRACK",
)


FEATURE_GROUPS = (
    {
        "id": "research-governance",
        "name": "B/C科研治理与顶刊目标",
        "description": "前提审查、证据分栏、一次质疑后推进、TGRS最低目标，以及带一区至四区和具体参考期刊的B/C评估。",
    },
    {
        "id": "server-execution",
        "name": "SERVER持续执行",
        "description": "原生/goal、rNNN、MASTER同编号工程恢复、最小运行凭据、机器验收和远端完成证据。",
    },
    {
        "id": "compute-and-configuration",
        "name": "计算与训练配置",
        "description": "项目在固定服务器本机执行；快速验证1卡、普通训练2卡，4卡需资源扩大权限。",
    },
    {
        "id": "local-data-storage",
        "name": "本机数据与空间",
        "description": "固定数据/pth路线、HRSC2016优先、46精确子集租约缓存和可回瘦大文件。",
    },
    {
        "id": "roles-and-git",
        "name": "角色与Git",
        "description": "worktree-local B/C/SERVER身份、main唯一权威、短期initiative/exec分支和HTTPS Git。",
    },
    {
        "id": "project-control",
        "name": "项目控制与帮助",
        "description": "默认UNLOCKED项目锁、Codex自然语言配置代理、完整功能/配置帮助。",
    },
    {
        "id": "paper-lessons-maintenance",
        "name": "论文、避坑与整理",
        "description": "Markdown优先论文、显式PDF、私有避坑库和仅由用户触发的项目整理。",
    },
)


def _root(root: Path) -> Path:
    root = Path(root).resolve()
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True,
        text=True, encoding="utf-8", check=False, shell=False,
    )
    if completed.returncode != 0 or Path(completed.stdout.strip()).resolve() != root:
        raise ValueError("project administration requires the exact repository root")
    return root


def _git_config(root: Path, scope: str, key: str) -> str | None:
    completed = subprocess.run(
        ["git", "config", f"--{scope}", "--get", key], cwd=root,
        capture_output=True, text=True, encoding="utf-8", check=False, shell=False,
    )
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else None


def _host_setting(root: Path, key: str, *, default: str = "UNCONFIGURED") -> str:
    return _git_config(root, "local", key) or default


def _permission_authorization(
    root: Path,
    *,
    key: str,
    authorization_ref: str | None,
    authorization_sha256: str | None,
    plan: dict[str, Any] | None = None,
    require_issuer_role: str | None = None,
    require_consumed: bool = False,
) -> dict[str, Any]:
    return authorization.validate_permission_authorization(
        root,
        permission=key.removeprefix("permission."),
        authorization_ref=authorization_ref,
        authorization_sha256=authorization_sha256,
        plan=plan,
        require_issuer_role=require_issuer_role,
        require_consumed=require_consumed,
    )


def _set_sensitive_permission(
    root: Path,
    *,
    key: str,
    normalized: str,
    raw_value: str,
    authorization_ref: str | None,
    authorization_sha256: str | None,
) -> dict[str, Any]:
    if normalized not in {"TRUE", "FALSE"}:
        raise ValueError("permission configuration value must be TRUE or FALSE")
    permission = key.removeprefix("permission.")
    for attempt in range(4):
        try:
            with transactions.project_control(root):
                authorization.synchronize_authority_main(root)
                if _current_role(root) not in {"B", "C"}:
                    raise ValueError(
                        "only B or C may commit a sensitive permission transition"
                    )
                # The CLI precheck is advisory; this is the linearization check.
                project_lock.require_operation(
                    root,
                    command="config",
                    action="set",
                    key=key,
                    value=raw_value,
                )
                document = state.load_state(root)
                permissions = document.get("permissions")
                authorizations = document.get("permission_authorizations")
                if (
                    type(permissions) is not dict
                    or type(permissions.get(permission)) is not bool
                ):
                    raise ValueError("project permissions configuration is invalid")
                if type(authorizations) is not dict or set(authorizations) != {
                    "external_write", "resource_expansion", "publish",
                }:
                    raise ValueError("project permission authorizations are invalid")
                before = permissions[permission]
                after = normalized == "TRUE"
                authorization_record = None
                if after is True:
                    authorization_record = _permission_authorization(
                        root,
                        key=key,
                        authorization_ref=authorization_ref,
                        authorization_sha256=authorization_sha256,
                    )
                next_authorization = (
                    {
                        "ref": authorization_record["ref"],
                        "sha256": authorization_record["sha256"],
                    }
                    if authorization_record is not None
                    else None
                )
                if before != after or authorizations[permission] != next_authorization:
                    state_path = root / "coordination/STATE.yaml"
                    before_sha256 = hashlib.sha256(state_path.read_bytes()).hexdigest()
                    permissions[permission] = after
                    authorizations[permission] = next_authorization
                    updated_payload = yaml.safe_dump(
                        document, allow_unicode=True, sort_keys=False
                    ).encode("utf-8")
                    if authorization_record is not None:
                        authorization.consume_control(
                            root,
                            authorization_record,
                            purpose=f"PERMISSION_ENABLE:{permission}",
                            before_state_sha256=before_sha256,
                            expected_files={"coordination/STATE.yaml": before_sha256},
                            updated_files={"coordination/STATE.yaml": updated_payload},
                        )
                    else:
                        authorization.commit_project_transition(
                            root,
                            purpose=f"disable permission.{permission}",
                            expected_files={"coordination/STATE.yaml": before_sha256},
                            updated_files={"coordination/STATE.yaml": updated_payload},
                        )
                    state.refresh_now(root)
                result: dict[str, Any] = {
                    "permission": permission,
                    "before": before,
                    "after": after,
                }
                if authorization_record is not None:
                    result["authorization_ref"] = authorization_record["ref"]
                    result["authorization_sha256"] = authorization_record["sha256"]
                return result
        except authorization.ConcurrentControlTransaction:
            if attempt == 3:
                raise
    raise RuntimeError("sensitive permission transaction retry loop is invalid")


def _current_role(root: Path) -> str:
    try:
        role = peer_governance.current_worker(root, allow_host_default=False)["role"]
    except ValueError:
        return "UNBOUND"
    return {"PEER_B": "B", "PEER_C": "C", "SERVER": "SERVER"}.get(role, "UNBOUND")


def _default_role(root: Path) -> str:
    try:
        role = peer_governance.host_default_worker(root)["role"]
    except ValueError:
        return "UNCONFIGURED"
    return {"PEER_B": "B", "PEER_C": "C", "SERVER": "SERVER"}.get(role, "UNCONFIGURED")


def _configuration_values(root: Path) -> list[dict[str, Any]]:
    lock = project_lock.load(root)["state"]
    authority = research_execution.load_authority(root)["level"]
    project_state = state.load_state(root)
    permissions = project_state.get("permissions")
    permission_authorizations = project_state.get("permission_authorizations")
    if type(permissions) is not dict or any(
        type(permissions.get(key)) is not bool
        for key in {"real_experiment", "external_write", "resource_expansion", "publish"}
    ) or type(permission_authorizations) is not dict or set(permission_authorizations) != {
        "external_write", "resource_expansion", "publish",
    }:
        raise ValueError("project permissions configuration is invalid")
    for permission in ("external_write", "resource_expansion", "publish"):
        authorization_record = permission_authorizations[permission]
        if permissions[permission] is False:
            if authorization_record is not None:
                raise ValueError("disabled project permission retains authorization")
            continue
        if (
            type(authorization_record) is not dict
            or set(authorization_record) != {"ref", "sha256"}
        ):
            raise ValueError("enabled project permission lacks user authorization")
        authorization.permission_snapshot(
            root,
            permission=permission,
            authorization_ref=authorization_record["ref"],
            authorization_sha256=authorization_record["sha256"],
            plan=None,
            online=False,
        )
    return [
        {
            "key": "project.lock", "current": lock, "scope": "PROJECT_GIT",
            "mutable": True, "accepted_values": ["UNLOCKED", "LOCKED"],
            "setter": "project-lock lock|unlock", "description": "锁定时停止项目操作。",
        },
        {
            "key": "role.current", "current": _current_role(root), "scope": "WORKTREE_LOCAL",
            "mutable": True, "accepted_values": ["B", "C", "SERVER"],
            "setter": "config set or peer bind", "description": "当前worktree角色。",
        },
        {
            "key": "role.host_default", "current": _default_role(root), "scope": "HOST_LOCAL",
            "mutable": True, "accepted_values": ["B", "C", "SERVER"],
            "setter": "config set or peer default", "description": "本机新worktree默认角色。",
        },
        {
            "key": "server.authority", "current": authority, "scope": "PROJECT_GIT",
            "mutable": True, "accepted_values": ["MASTER", "DOCTORAL"],
            "setter": "config set with digest-bound user authorization",
            "description": "DOCTORAL只能由用户明确授权，SERVER不能自升级。",
        },
        {
            "key": "server.execution_mode", "current": "LOCAL_ONLY",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": ["LOCAL_ONLY"], "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "项目固定在一台服务器，只能由该服务器本机执行。",
        },
        {
            "key": "server.profile",
            "current": _host_setting(root, "cqc.server-profile", default="AUTO_FROM_PROJECT_PATH"),
            "scope": "HOST_LOCAL", "mutable": True, "accepted_values": ["26", "46"],
            "setter": "SERVER binds cqc.server-profile locally when the path is not self-identifying",
            "description": "只识别本机身份；B/C不探测26或46，也不选择远端节点。",
        },
        {
            "key": "server.dataset_root_override",
            "current": _host_setting(root, "cqc.dataset-root"),
            "scope": "HOST_LOCAL", "mutable": True, "accepted_values": "ABSOLUTE_LOCAL_MOUNT_PATH",
            "setter": "SERVER may bind the already-mounted official dataset root locally",
            "description": "仅用于46上26数据集挂载点不同于固定路径时；不做目录身份摘要校验。",
        },
        {
            "key": "dataset.server_26_roots",
            "current": ["/home/rspip/cqc/data/dataset", "/dev/shm/cqc/data/dataset"],
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": "FIXED_LOCAL_PATHS", "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "26本机官方数据与本机shm数据根。",
        },
        {
            "key": "dataset.server_46_download_root",
            "current": "/dev/shm/zy/data/dataset", "scope": "CORE_CONTRACT",
            "mutable": False, "accepted_values": ["/dev/shm/zy/data/dataset"],
            "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "46新增下载、复制或转换数据只能写入此目录。",
        },
        {
            "key": "checkpoint.pth_readme_routes",
            "current": {
                "26": "/home/rspip/cqc/study/pth_data/readme.md",
                "46": "/home/rspip/zy/study/pth_data/readme.md",
            },
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": "FIXED_BY_SERVER_PROFILE", "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "SERVER按本机固定路线读取四卡pth说明，可用于快速验证。",
        },
        {
            "key": "workspace.materialization_root",
            "current": _host_setting(
                root, "cqc.large-workspace-root", default="AUTO_DETERMINISTIC_HOME_OR_SHM"
            ),
            "scope": "HOST_LOCAL", "mutable": True,
            "accepted_values": "EXACT_PROJECT_HOME_OR_DETERMINISTIC_SHM_MIRROR",
            "setter": "Codex runs cqc-fabric storage-plan and validates the exact mirror",
            "description": "项目专属large-workspaces的home或/dev/shm物化根。",
        },
        {
            "key": "permission.real_experiment", "current": permissions["real_experiment"],
            "scope": "CORE_CONTRACT", "mutable": False, "accepted_values": [True],
            "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "固定节点普通GPU/CPU训练由有效rNNN直接授权。",
        },
        {
            "key": "permission.external_write", "current": permissions["external_write"],
            "scope": "PROJECT_GIT", "mutable": True, "accepted_values": [False, True],
            "setter": "config set",
            "description": "是否允许计划在边界内写项目仓库以外路径。",
        },
        {
            "key": "permission.resource_expansion",
            "current": permissions["resource_expansion"], "scope": "PROJECT_GIT",
            "mutable": True, "accepted_values": [False, True], "setter": "config set",
            "description": "是否允许单次计划从正常两卡扩大到本机四卡。",
        },
        {
            "key": "permission.publish", "current": permissions["publish"],
            "scope": "PROJECT_GIT", "mutable": True, "accepted_values": [False, True],
            "setter": "config set",
            "description": "是否允许向HTTPS远端发布已验收结果。",
        },
        {
            "key": "training.preferred_gpu_count", "current": 2, "scope": "SERVER_PLAN",
            "mutable": True, "accepted_values": [1, 2, 4],
            "setter": "B/C writes only gpu_tier/count; SERVER dynamically selects local device IDs",
            "description": "快速验证一卡、正常训练两卡；四卡必须有resource_expansion授权。",
        },
        {
            "key": "training.separate_authorization", "current": False,
            "scope": "CORE_CONTRACT", "mutable": False, "accepted_values": [False],
            "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "有效rNNN直接授权固定节点普通训练，不再单独申请。",
        },
        {
            "key": "training.busy_gpu_policy", "current": "RUN_UNLESS_PREDICTED_OR_ACTUAL_OOM",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": ["RUN_UNLESS_PREDICTED_OR_ACTUAL_OOM"],
            "setter": "CONTRACT_UPGRADE_ONLY", "description": "GPU繁忙仍运行。",
        },
        {
            "key": "publication.minimum", "current": "TGRS", "scope": "CORE_CONTRACT",
            "mutable": False, "accepted_values": ["TGRS_OR_HIGHER"],
            "setter": "CONTRACT_UPGRADE_ONLY", "description": "唯一最低发表目标。",
        },
        {
            "key": "reporting.journal_rating",
            "current": "CAS_ZONE_1_TO_4_WITH_CONCRETE_REFERENCE_JOURNAL",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": ["一区", "二区", "三区", "四区"],
            "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "B/C或显式DOCTORAL必须从内置地球科学大类四区库选择匹配的分区和期刊；三区、四区不能终止。",
        },
        {
            "key": "reporting.mode", "current": "KEY_INFORMATION_ONLY",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": ["KEY_INFORMATION_ONLY"], "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "只反馈结论、关键证据、等级差距和下一步。",
        },
        {
            "key": "reporting.bc_execution_status",
            "current": "EXPLICIT_SUCCESS_FAILURE_OR_NOT_COMPLETE",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": ["EXPLICIT_SUCCESS_FAILURE_OR_NOT_COMPLETE"],
            "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "B/C回复涉及具体rNNN时按机器或复核证据明确成功、失败或未完成。",
        },
        {
            "key": "reporting.server_short_instruction_format",
            "current": "MARKDOWN_FENCED_TEXT_BLOCK",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": ["MARKDOWN_FENCED_TEXT_BLOCK"],
            "setter": "CONTRACT_UPGRADE_ONLY",
            "description": "给用户转交SERVER的单条短命令使用可复制text代码框。",
        },
        {
            "key": "git.transport", "current": "HTTPS_ONLY", "scope": "CORE_CONTRACT",
            "mutable": False, "accepted_values": ["HTTPS_ONLY"],
            "setter": "CONTRACT_UPGRADE_ONLY", "description": "生产Git fetch/push只用HTTPS。",
        },
        {
            "key": "git.role_finalization",
            "current": "CLEAN_COMMITTED_PUSHED_REMOTE_REF_MATCH",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": ["CLEAN_COMMITTED_PUSHED_REMOTE_REF_MATCH"],
            "setter": "handoff record then exact-path commit/push then handoff verify",
            "description": "B/C/SERVER结束工作前自行提交、推送并核验远端SHA。",
        },
        {
            "key": "control.sensitive_trust",
            "current": "ROOT_COMMIT_REMOTE_BLOB_AT_CONSUME_CLAIM_LOCAL_RUN_SNAPSHOT",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": [
                "ROOT_COMMIT_REMOTE_BLOB_AT_CONSUME_CLAIM_LOCAL_RUN_SNAPSHOT"
            ],
            "setter": "external controller publishes exact control event on authoritative main",
            "description": "根提交固定权威仓库；远端只在消费和任务领取核验，运行心跳校验本地journal快照。",
        },
        {
            "key": "control.transaction_model",
            "current": "AUTHORITATIVE_MAIN_CAS_AND_OS_ADVISORY_LOCKS",
            "scope": "CORE_CONTRACT", "mutable": False,
            "accepted_values": ["AUTHORITATIVE_MAIN_CAS_AND_OS_ADVISORY_LOCKS"],
            "setter": "contract-fixed",
            "description": "权限、项目锁和领取共享项目事务锁；STOP、heartbeat与最终COMPLETE按rNNN锁内重读；正常协作的消费记录追加到权威main。管理员历史改写不属于运行时保证。",
        },
    ]


def show_config(root: Path, *, key: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
    root = _root(root)
    values = _configuration_values(root)
    if key is None:
        return values
    for item in values:
        if item["key"] == key:
            return item
    raise ValueError(f"unknown configuration key: {key}")


def set_config(
    root: Path,
    *,
    key: str,
    value: str,
    reason: str,
    authorization_ref: str | None = None,
    authorization_sha256: str | None = None,
) -> dict[str, Any]:
    root = _root(root)
    if type(reason) is not str or len(reason.strip()) < 12:
        raise ValueError("configuration reason must contain at least 12 characters")
    normalized = str(value).upper()
    if key == "project.lock":
        result = project_lock.set_state(
            root,
            state=normalized,
            reason=reason,
            authorization_ref=authorization_ref,
            authorization_sha256=authorization_sha256,
        )
    elif key == "role.current":
        result = peer_governance.bind_role(root, normalized)
    elif key == "role.host_default":
        result = peer_governance.configure_default_role(root, normalized)
    elif key == "server.authority":
        if authorization_ref is None or authorization_sha256 is None:
            raise ValueError("server authority requires a digest-bound user authorization")
        result = research_execution.set_authority(
            root, level=normalized, authorization_ref=authorization_ref,
            authorization_sha256=authorization_sha256,
        )
    elif key in {
        "permission.external_write", "permission.resource_expansion", "permission.publish",
    }:
        result = _set_sensitive_permission(
            root,
            key=key,
            normalized=normalized,
            raw_value=value,
            authorization_ref=authorization_ref,
            authorization_sha256=authorization_sha256,
        )
    elif key.startswith("training."):
        raise ValueError(
            "training configuration is plan-bound; Codex must update SERVER_PLAN "
            "configuration_alignment and its baseline instead of a loose project setting"
        )
    else:
        current = show_config(root, key=key)
        if current["mutable"] is False:
            raise ValueError(f"configuration is contract-fixed: {key}")
        raise ValueError(f"unsupported configuration setter: {key}")
    current = show_config(root, key=key)["current"]
    return {"key": key, "current": current, "reason": reason.strip(), "result": result}


def help_overview(root: Path, *, section: str = "all") -> dict[str, Any]:
    root = _root(root)
    if section not in {"all", "features", "config", "commands"}:
        raise ValueError("help section must be all, features, config or commands")
    embedded = yaml.safe_load(
        (root / ".research_core/contract.yaml").read_text(encoding="utf-8")
    )
    if type(embedded) is not dict or type(embedded.get("research_core_version")) is not str:
        raise ValueError("embedded research contract is invalid")
    result: dict[str, Any] = {
        "research_core_version": embedded["research_core_version"],
        "project_lock": project_lock.load(root)["state"],
        "current_role": _current_role(root),
        "role_instruction": (
            None if _current_role(root) == "UNBOUND" else f"roles/{_current_role(root)}/AGENTS.md"
        ),
    }
    if section in {"all", "features"}:
        result["feature_groups"] = list(FEATURE_GROUPS)
        result["capability_ids"] = list(CAPABILITY_IDS)
    if section in {"all", "features", "config"}:
        result["journal_benchmarks"] = journal_benchmarks.help_entries(root)
    if section in {"all", "config"}:
        result["configurations"] = _configuration_values(root)
    if section in {"all", "commands"}:
        result["commands"] = {
            "help": "python -m tools.workflow help --section all|features|config|commands",
            "config_show": "python -m tools.workflow config show [--key KEY]",
            "config_set": "python -m tools.workflow config set --key KEY --value VALUE --reason TEXT",
            "lock": "python -m tools.workflow project-lock lock|unlock|status",
            "handoff_record": (
                "python -m tools.workflow handoff record --to B|C|SERVER "
                "--summary TEXT [--instruction rNNN]"
            ),
            "handoff_verify": "python -m tools.workflow handoff verify",
            "execute": "python -m tools.workflow dispatch pull-execute",
        }
    return result
