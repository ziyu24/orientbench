from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

import yaml


PLAN_ID = re.compile(r"([BC])[0-9]{4}\Z")
SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PEER_ROLES = {"PEER_B": "B", "PEER_C": "C"}
ROLE_WORKERS = {
    "B": "peer-b-primary",
    "C": "peer-c-primary",
    "SERVER": "server-primary",
}
TERMINAL = {"ACCEPTED", "KILLED", "CONTESTED", "INCONCLUSIVE"}
HISTORY_LIFECYCLES = TERMINAL | {"SUPERSEDED"}
PLAN_KEYS = {
    "schema_version", "plan_id", "revision", "owner_role", "status",
    "base_sha", "scientific_sha", "evidence", "scientific_scope",
    "minimum_discriminating_experiment", "kill_condition", "budget",
    "risk_level", "read_set", "write_set", "resource_set", "conflict_set",
    "required_permissions", "report_path", "completion_receipt",
    "exception_receipt", "critique", "authorization", "consultation",
    "inheritance", "execution_policy",
    "supervision",
}
DISPATCH_RECORD_KEYS = {
    "plan_id", "owner_role", "plan_path", "plan_sha256", "report_path",
    "lifecycle", "risk_level", "critique", "epoch", "user_notice",
    "supersedes", "superseded_by", "server_stop", "user_control",
    "supervision",
}
BINDING_KEYS = {"required", "status", "receipt_path", "receipt_sha256"}
PLAN_LINK_KEYS = {"plan_path", "plan_sha256", "epoch"}
USER_CONTROL_KEYS = {"state", "event_path", "event_sha256"}
SUPERVISION_BINDING_KEYS = {
    "required", "status", "run_id", "record_path", "record_sha256"
}
SUPERVISION_KEYS = {
    "task_kind", "estimated_minutes", "required", "interval_minutes",
    "scientific_stage",
}
SCIENTIFIC_SCOPE_KEYS = {
    "objective", "dataset", "primary_metric", "control_group"
}
FLEXIBLE_EXECUTION_FIELDS = {
    "command",
    "parameters",
    "batch_size",
    "scheduling",
    "temporary_path",
    "retry",
    "checkpoint",
    "dependency_recovery",
    "equivalent_implementation",
    "logging",
}
APPROVED_PROJECT_ROOTS = {
    "research",
    "dis",
    "coordination",
    "artifacts",
    "paper",
    "runs",
    "src",
    "configs",
    "scripts",
    "tests",
    "docs",
    "tools",
}
APPROVED_PROJECT_FILES = {
    "README.md",
    "project.yaml",
    "AGENTS.md",
    "CLAUDE.md",
    ".gitignore",
    ".gitattributes",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _dialogue_module():
    if __package__:
        return importlib.import_module(f"{__package__}.dialogue")
    path = Path(__file__).with_name("dialogue.py")
    spec = importlib.util.spec_from_file_location(
        f"research_core_dialogue_{id(path)}", path
    )
    if spec is None or spec.loader is None:
        raise ValueError("dialogue runtime is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _history_module():
    path = Path(__file__).with_name("dispatch_history.py")
    spec = importlib.util.spec_from_file_location(
        f"research_core_dispatch_history_{id(path)}", path
    )
    if spec is None or spec.loader is None:
        raise ValueError("dispatch history runtime is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _safe_relative(value: str, label: str) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError(f"invalid {label}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"invalid {label}")
    return path.as_posix()


def _approved_project_relative(value: str, label: str) -> str:
    relative = _safe_relative(value, label)
    parts = PurePosixPath(relative).parts
    if relative not in APPROVED_PROJECT_FILES and parts[0] not in APPROVED_PROJECT_ROOTS:
        raise ValueError(f"{label} must use an approved project root")
    return relative


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(data) is not dict:
        raise ValueError(f"YAML mapping required: {path}")
    return data


def _front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        marker, front, _ = text.split("---", 2)
    except ValueError as error:
        raise ValueError("plan front matter required") from error
    if marker:
        raise ValueError("plan front matter required")
    data = yaml.safe_load(front)
    if type(data) is not dict:
        raise ValueError("plan front matter must be a mapping")
    return data


def _atomic_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(
        prefix=f".{path.name}-", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(data, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _exclusive_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        yaml.safe_dump(data, stream, allow_unicode=True, sort_keys=False)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def _workers(root: Path) -> dict[str, dict[str, str]]:
    document = _load_yaml(Path(root) / "coordination/governance/WORKERS.yaml")
    if set(document) != {"schema_version", "selector", "workers"}:
        raise ValueError("invalid worker registry")
    if document["schema_version"] != 1 or document["selector"] != "git-config-worktree:paper.worker-id":
        raise ValueError("invalid worker registry")
    expected = {
        "peer-b-primary": {"role": "PEER_B"},
        "peer-c-primary": {"role": "PEER_C"},
        "server-primary": {"role": "SERVER"},
    }
    if document["workers"] != expected:
        raise ValueError("invalid worker registry")
    return document["workers"]


def _configured_worker(root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "config", "--worktree", "--get", "paper.worker-id"],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    worker_id = completed.stdout.strip()
    return worker_id if completed.returncode == 0 and worker_id else None


def _worker_record(root: Path, worker_id: str, *, label: str) -> dict[str, str]:
    record = _workers(root).get(worker_id)
    if record is None:
        raise ValueError(f"unknown {label} worker: {worker_id}")
    return {"worker_id": worker_id, "role": record["role"]}


def host_default_worker(root: Path) -> dict[str, str]:
    completed = subprocess.run(
        ["git", "config", "--global", "--get", "paper.default-worker-id"],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    worker_id = completed.stdout.strip()
    if completed.returncode != 0 or not worker_id:
        raise ValueError("host-local paper.default-worker-id is not configured")
    return _worker_record(root, worker_id, label="host-default")


def current_worker(
    root: Path, *, allow_host_default: bool = True
) -> dict[str, str]:
    worker_id = _configured_worker(root)
    if worker_id is not None:
        return _worker_record(root, worker_id, label="worktree")
    if not allow_host_default:
        raise ValueError("worktree-local paper.worker-id is not configured")
    default = host_default_worker(root)
    role = PEER_ROLES.get(default["role"], default["role"])
    return bind_role(root, role)


def _require_exact_repository_root(root: Path) -> Path:
    root = Path(root).resolve()
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    if completed.returncode != 0 or Path(completed.stdout.strip()).resolve() != root:
        raise ValueError("role binding requires the exact repository root")
    _workers(root)
    return root


def bind_role(root: Path, role: str) -> dict[str, str]:
    root = _require_exact_repository_root(root)
    normalized = str(role).upper()
    worker_id = ROLE_WORKERS.get(normalized)
    if worker_id is None:
        raise ValueError("role must be B, C, or SERVER")
    enabled = subprocess.run(
        ["git", "config", "--local", "extensions.worktreeConfig", "true"],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    if enabled.returncode != 0:
        raise ValueError("worktree-local role binding could not be enabled")
    configured = subprocess.run(
        ["git", "config", "--worktree", "paper.worker-id", worker_id],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    if configured.returncode != 0:
        raise ValueError("worktree-local role binding failed")
    return _worker_record(root, worker_id, label="worktree")


def configure_default_role(root: Path, role: str) -> dict[str, str]:
    root = _require_exact_repository_root(root)
    normalized = str(role).upper()
    worker_id = ROLE_WORKERS.get(normalized)
    if worker_id is None:
        raise ValueError("role must be B, C, or SERVER")
    completed = subprocess.run(
        ["git", "config", "--global", "paper.default-worker-id", worker_id],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    if completed.returncode != 0:
        raise ValueError("host-local default role configuration failed")
    return host_default_worker(root)


def _validate_string_list(value: object, label: str, *, paths: bool) -> list[str]:
    if type(value) is not list or not value:
        raise ValueError(f"{label} must be a non-empty list")
    if any(type(item) is not str or not item for item in value) or len(value) != len(set(value)):
        raise ValueError(f"invalid or duplicate {label}")
    if paths:
        return [_approved_project_relative(item, label) for item in value]
    return value


def _validate_required_permissions(value: object) -> list[str]:
    allowed = {"real_experiment", "external_write", "resource_expansion", "publish"}
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError("required_permissions must be a list")
    if len(value) != len(set(value)) or not set(value).issubset(allowed):
        raise ValueError("invalid required_permissions")
    return value


def _require_repository_commit(root: Path, value: str, label: str) -> None:
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{value}^{{commit}}"],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"{label} must resolve to a repository commit")


def _plan_path(root: Path, relative: str) -> Path:
    relative = _safe_relative(relative, "plan_path")
    match = re.fullmatch(r"dis/plans/([BC])/([BC][0-9]{4})/sug\.md", relative)
    if match is None or match.group(2)[0] != match.group(1):
        raise ValueError("plan_path is not role-owned")
    root = Path(root).resolve()
    path = root.joinpath(*PurePosixPath(relative).parts)
    if path.resolve().parent.parent.parent != (root / "dis/plans").resolve():
        raise ValueError("plan_path escapes project")
    return path


def _validate_file_hash(root: Path, relative: str, expected: str, label: str) -> Path:
    relative = _safe_relative(relative, label)
    if SHA256.fullmatch(str(expected)) is None:
        raise ValueError(f"invalid {label} SHA256")
    path = Path(root).joinpath(*PurePosixPath(relative).parts)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} file is missing")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"{label} SHA256 mismatch")
    return path


def _validate_consultation(root: Path, document: dict) -> None:
    consultation = document["consultation"]
    if type(consultation) is not dict or set(consultation) != {
        "dialogue_id", "user_directive_ref", "user_directive_sha256"
    }:
        raise ValueError("invalid consultation binding")
    values = tuple(consultation.values())
    if all(value is None for value in values):
        return
    if any(value is None for value in values):
        raise ValueError("incomplete consultation designation")
    dialogue = _dialogue_module()
    status = dialogue.dialogue_status(root, consultation["dialogue_id"])
    if status["status"] != "DESIGNATED":
        raise ValueError("consultation is awaiting user designation")
    path = _validate_file_hash(
        root,
        consultation["user_directive_ref"],
        consultation["user_directive_sha256"],
        "consultation directive",
    )
    directive = dialogue.validate_user_directive(
        root, path.relative_to(root).as_posix()
    )
    if (
        directive["action"] != "DISPATCH_AFTER_DIALOGUE"
        or directive["dialogue_id"] != consultation["dialogue_id"]
        or directive["designated_role"] != document["owner_role"]
    ):
        raise ValueError("consultation directive does not designate plan owner")


def _validate_inheritance(root: Path, document: dict) -> None:
    inheritance = document["inheritance"]
    keys = {
        "mode", "prior_plan_path", "prior_plan_sha256", "critique_ref",
        "critique_sha256", "user_directive_ref", "user_directive_sha256",
    }
    if type(inheritance) is not dict or set(inheritance) != keys:
        raise ValueError("invalid inheritance binding")
    if inheritance["mode"] == "NONE":
        if any(value is not None for key, value in inheritance.items() if key != "mode"):
            raise ValueError("NONE inheritance must not carry references")
        return
    if inheritance["mode"] != "CRITIQUE_INHERITANCE":
        raise ValueError("invalid inheritance mode")
    if (
        inheritance["user_directive_ref"] is None
        or inheritance["user_directive_sha256"] is None
    ):
        raise ValueError("critique inheritance requires a user directive")
    if any(inheritance[key] is None for key in keys if key != "mode"):
        raise ValueError("critique inheritance requires complete references")
    _plan_path(root, inheritance["prior_plan_path"])
    if SHA256.fullmatch(str(inheritance["prior_plan_sha256"])) is None:
        raise ValueError("invalid prior plan SHA256")
    _validate_file_hash(
        root, inheritance["critique_ref"], inheritance["critique_sha256"], "critique"
    )
    directive_path = _validate_file_hash(
        root,
        inheritance["user_directive_ref"],
        inheritance["user_directive_sha256"],
        "user directive",
    )
    directive = _dialogue_module().validate_user_directive(
        root, directive_path.relative_to(root).as_posix()
    )
    if (
        directive["action"] != "CRITIQUE_INHERIT_AND_REPLACE"
        or directive["designated_role"] != document["owner_role"]
        or directive["prior_plan_path"] != inheritance["prior_plan_path"]
        or directive["prior_plan_sha256"] != inheritance["prior_plan_sha256"]
    ):
        raise ValueError("replacement user directive does not match inheritance")


def validate_plan(root: Path, relative: str) -> dict:
    root = Path(root).resolve()
    path = _plan_path(root, relative)
    document = _front_matter(path)
    if set(document) != PLAN_KEYS or document.get("schema_version") != 4:
        raise ValueError("invalid immutable plan fields")
    match = PLAN_ID.fullmatch(str(document["plan_id"]))
    if match is None or document["owner_role"] != match.group(1):
        raise ValueError("plan owner identity mismatch")
    expected = f"dis/plans/{document['owner_role']}/{document['plan_id']}/sug.md"
    if relative != expected:
        raise ValueError("plan owner path mismatch")
    if type(document["revision"]) is not int or document["revision"] < 1:
        raise ValueError("invalid plan revision")
    if document["status"] not in {"DRAFT", "READY"}:
        raise ValueError("new plan status must be DRAFT or READY")
    if SHA.fullmatch(str(document["base_sha"])) is None or SHA.fullmatch(str(document["scientific_sha"])) is None:
        raise ValueError("invalid base/scientific SHA")
    _require_repository_commit(root, document["base_sha"], "base_sha")
    _require_repository_commit(root, document["scientific_sha"], "scientific_sha")
    _validate_string_list(document["evidence"], "evidence", paths=True)
    scientific_scope = document["scientific_scope"]
    if (
        type(scientific_scope) is not dict
        or set(scientific_scope) != SCIENTIFIC_SCOPE_KEYS
        or any(
            type(scientific_scope[key]) is not str
            or not scientific_scope[key].strip()
            for key in SCIENTIFIC_SCOPE_KEYS
        )
    ):
        raise ValueError("invalid scientific scope")
    if document["execution_policy"] != "ADAPTIVE_WITHIN_HARD_BOUNDARIES":
        raise ValueError("invalid execution policy")
    supervision = document["supervision"]
    if type(supervision) is not dict or set(supervision) != SUPERVISION_KEYS:
        raise ValueError("invalid supervision declaration")
    if supervision["task_kind"] not in {"GPU", "CPU"}:
        raise ValueError("invalid supervision task kind")
    if (
        type(supervision["estimated_minutes"]) is not int
        or supervision["estimated_minutes"] <= 0
        or type(supervision["required"]) is not bool
        or supervision["interval_minutes"] != 20
        or type(supervision["scientific_stage"]) is not str
        or not supervision["scientific_stage"].strip()
    ):
        raise ValueError("invalid supervision declaration")
    long_task = (
        supervision["task_kind"] == "GPU"
        or supervision["estimated_minutes"] > 30
    )
    if long_task and not supervision["required"]:
        raise ValueError("long task requires supervision")
    _validate_string_list(document["read_set"], "read_set", paths=True)
    write_set = _validate_string_list(document["write_set"], "write_set", paths=True)
    _validate_string_list(document["resource_set"], "resource_set", paths=False)
    _validate_string_list(document["conflict_set"], "conflict_set", paths=False)
    _validate_required_permissions(document["required_permissions"])
    for field in (
        "minimum_discriminating_experiment", "kill_condition", "report_path",
        "completion_receipt", "exception_receipt",
    ):
        if type(document[field]) is not str or not document[field].strip():
            raise ValueError(f"invalid {field}")
    report_paths = [
        _approved_project_relative(document[field], field)
        for field in ("report_path", "completion_receipt", "exception_receipt")
    ]
    if any(not item.startswith("dis/reports/") for item in report_paths):
        raise ValueError("report and receipt paths must use dis/reports")
    if len(set(report_paths)) != 3 or any(item not in write_set for item in report_paths):
        raise ValueError("unique report and receipt paths must be in write_set")
    budget = document["budget"]
    if type(budget) is not dict or set(budget) != {
        "level", "max_gpu_count", "max_hours", "max_cost_usd"
    }:
        raise ValueError("invalid budget")
    if document["risk_level"] not in {"L0", "L1", "L2"} or budget["level"] != document["risk_level"]:
        raise ValueError("risk and budget level mismatch")
    for field in ("max_gpu_count", "max_hours", "max_cost_usd"):
        if type(budget[field]) not in {int, float} or budget[field] < 0:
            raise ValueError("invalid budget value")
    critique = document["critique"]
    if type(critique) is not dict or set(critique) != {"status", "mode", "peer_role"}:
        raise ValueError("invalid critique attribute")
    if critique["status"] not in {"NOT_REQUESTED", "REQUESTED", "RECEIVED", "CONTESTED"}:
        raise ValueError("invalid critique status")
    if critique["mode"] not in {"OPTIONAL", "independent_then_cross"}:
        raise ValueError("invalid critique mode")
    if critique["peer_role"] not in {"B", "C"} or critique["peer_role"] == document["owner_role"]:
        raise ValueError("invalid critique peer")
    authorization = document["authorization"]
    if type(authorization) is not dict or set(authorization) != {"route", "user_authorization_ref"}:
        raise ValueError("invalid authorization")
    if authorization["route"] not in {"ROLE_CONTRACT", "EXPLICIT_USER"}:
        raise ValueError("invalid authorization route")
    if authorization["user_authorization_ref"] is not None:
        _safe_relative(authorization["user_authorization_ref"], "user authorization")
    _validate_consultation(root, document)
    _validate_inheritance(root, document)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    dispatch = load_dispatch(root)
    records = [dispatch["active"]] if dispatch["active"] is not None else []
    records.extend(_history_module().load_index(root)["entries"])
    for record in records:
        if record["plan_path"] == relative and record["plan_sha256"] != digest:
            raise ValueError("immutable dispatched plan hash drift")
    return document


def write_plan(root: Path, document: dict) -> Path:
    root = Path(root).resolve()
    worker = current_worker(root)
    owner = PEER_ROLES.get(worker["role"])
    if owner is None or document.get("owner_role") != owner:
        raise ValueError("worker does not own requested plan path")
    plan_id = str(document.get("plan_id", ""))
    relative = f"dis/plans/{owner}/{plan_id}/sug.md"
    path = _plan_path(root, relative)
    if path.exists():
        raise FileExistsError("immutable plan already exists")
    path.parent.mkdir(parents=True, exist_ok=False)
    front = yaml.safe_dump(document, allow_unicode=True, sort_keys=False).rstrip()
    text = f"---\n{front}\n---\n\n# Immutable plan {plan_id}\n"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        validate_plan(root, relative)
        for other in (root / "dis/plans").glob("[BC]/*/sug.md"):
            if other == path:
                continue
            if _front_matter(other).get("report_path") == document["report_path"]:
                raise ValueError("report_path must be unique")
    except BaseException:
        path.unlink(missing_ok=True)
        try:
            path.parent.rmdir()
        except OSError:
            pass
        raise
    return path


def write_opinion(root: Path, *, owner_role: str, opinion_id: str, text: str) -> Path:
    root = Path(root).resolve()
    worker = current_worker(root)
    owner = PEER_ROLES.get(worker["role"])
    if owner is None or owner_role != owner:
        raise ValueError("worker does not own requested opinion path")
    if re.fullmatch(rf"{owner}[0-9]{{4}}", opinion_id) is None:
        raise ValueError("invalid opinion identity")
    if type(text) is not str or not text.strip() or "\x00" in text:
        raise ValueError("opinion text is required")
    path = root / "dis/opinions" / owner / f"{opinion_id}.md"
    if path.parent.resolve() != (root / "dis/opinions" / owner).resolve():
        raise ValueError("opinion path escapes owner directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text.rstrip() + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return path


def _check_required_permissions(root: Path, document: dict) -> None:
    state = _load_yaml(Path(root) / "coordination/STATE.yaml")
    permissions = state.get("permissions")
    if type(permissions) is not dict:
        raise ValueError("authoritative permission gates are invalid")
    denied = [
        name for name in document["required_permissions"]
        if permissions.get(name) is not True
    ]
    if denied:
        raise ValueError(f"permission gate is closed: {', '.join(denied)}")


def _validate_binding(value: object, label: str) -> None:
    if type(value) is not dict or set(value) != BINDING_KEYS:
        raise ValueError(f"invalid {label}")
    if type(value["required"]) is not bool:
        raise ValueError(f"invalid {label}")
    allowed = {"PENDING", "RECORDED"} if value["required"] else {"NOT_REQUIRED"}
    if value["status"] not in allowed:
        raise ValueError(f"invalid {label} status")
    if value["status"] == "RECORDED":
        _safe_relative(value["receipt_path"], f"{label} receipt")
        if SHA256.fullmatch(str(value["receipt_sha256"])) is None:
            raise ValueError(f"invalid {label} receipt SHA256")
    elif value["receipt_path"] is not None or value["receipt_sha256"] is not None:
        raise ValueError(f"unexpected {label} receipt")


def _validate_plan_link(value: object, label: str) -> None:
    if type(value) is not dict or set(value) != PLAN_LINK_KEYS:
        raise ValueError(f"invalid {label}")
    _safe_relative(value["plan_path"], f"{label} plan path")
    if SHA256.fullmatch(str(value["plan_sha256"])) is None:
        raise ValueError(f"invalid {label} plan SHA256")
    if type(value["epoch"]) is not int or value["epoch"] < 1:
        raise ValueError(f"invalid {label} epoch")


def _validate_user_control(root: Path, value: object, epoch: int) -> dict | None:
    if type(value) is not dict or set(value) != USER_CONTROL_KEYS:
        raise ValueError("invalid user control")
    if value["state"] not in {"RUN", "PAUSED"}:
        raise ValueError("invalid user control state")
    if value["event_path"] is None and value["event_sha256"] is None:
        if value["state"] != "RUN":
            raise ValueError("paused user control requires an event")
        return None
    if value["event_path"] is None or value["event_sha256"] is None:
        raise ValueError("incomplete user control event binding")
    relative = _safe_relative(value["event_path"], "user control event")
    match = re.fullmatch(
        r"coordination/controls/(B|C|SERVER)/E([0-9]{6})/U([0-9]{4})\.yaml",
        relative,
    )
    if match is None or int(match.group(2)) != epoch:
        raise ValueError("invalid user control event path")
    path = _validate_file_hash(
        root,
        relative,
        value["event_sha256"],
        "user control event",
    )
    event = _load_yaml(path)
    keys = {
        "schema_version",
        "epoch",
        "plan_path",
        "plan_sha256",
        "action",
        "instruction",
        "recorded_by",
        "actor_role",
        "recorded_at",
    }
    if type(event) is not dict or set(event) != keys or event["schema_version"] != 1:
        raise ValueError("invalid user control event")
    expected_worker = ROLE_WORKERS[match.group(1)]
    expected_role = {
        "B": "PEER_B",
        "C": "PEER_C",
        "SERVER": "SERVER",
    }[match.group(1)]
    expected_action = "STOP" if value["state"] == "PAUSED" else "CONTINUE"
    if (
        event["epoch"] != epoch
        or event["action"] != expected_action
        or event["recorded_by"] != expected_worker
        or event["actor_role"] != expected_role
        or type(event["instruction"]) is not str
        or not event["instruction"].strip()
    ):
        raise ValueError("user control event does not match active state")
    return event


def _validate_dispatch_record(root: Path, record: object, *, history: bool) -> None:
    if type(record) is not dict or set(record) != DISPATCH_RECORD_KEYS:
        raise ValueError("invalid dispatch record")
    plan_id = str(record["plan_id"])
    owner = record["owner_role"]
    match = PLAN_ID.fullmatch(plan_id)
    if match is None or owner != match.group(1):
        raise ValueError("invalid dispatch plan identity")
    expected = f"dis/plans/{owner}/{plan_id}/sug.md"
    if record["plan_path"] != expected:
        raise ValueError("invalid dispatch plan path")
    _plan_path(root, expected)
    if SHA256.fullmatch(str(record["plan_sha256"])) is None:
        raise ValueError("invalid dispatch plan SHA256")
    _safe_relative(record["report_path"], "dispatch report_path")
    allowed = HISTORY_LIFECYCLES if history else {"DISPATCHED", "RUNNING", "REPORTED"}
    if record["lifecycle"] not in allowed:
        raise ValueError("invalid dispatch lifecycle")
    if record["risk_level"] not in {"L0", "L1", "L2"}:
        raise ValueError("invalid dispatch risk level")
    if type(record["epoch"]) is not int or record["epoch"] < 1:
        raise ValueError("invalid dispatch epoch")
    critique = record["critique"]
    if type(critique) is not dict or set(critique) != {"status", "mode", "peer_role"}:
        raise ValueError("invalid dispatch critique")
    _validate_binding(record["user_notice"], "user notice")
    if (record["risk_level"] == "L2") != record["user_notice"]["required"]:
        raise ValueError("L2 user notice binding mismatch")
    _validate_binding(record["server_stop"], "server stop")
    supervision = record["supervision"]
    if (
        type(supervision) is not dict
        or set(supervision) != SUPERVISION_BINDING_KEYS
        or type(supervision["required"]) is not bool
        or supervision["status"] not in {"NOT_REQUIRED", "PENDING", "RECORDED"}
    ):
        raise ValueError("invalid supervision binding")
    if supervision["required"]:
        if supervision["status"] == "NOT_REQUIRED":
            raise ValueError("required supervision cannot be NOT_REQUIRED")
    elif supervision != {
        "required": False,
        "status": "NOT_REQUIRED",
        "run_id": None,
        "record_path": None,
        "record_sha256": None,
    }:
        raise ValueError("optional supervision binding must be empty")
    if supervision["status"] == "RECORDED":
        if (
            type(supervision["run_id"]) is not str
            or not supervision["run_id"]
            or SHA256.fullmatch(str(supervision["record_sha256"])) is None
        ):
            raise ValueError("invalid recorded supervision binding")
        _safe_relative(supervision["record_path"], "supervision record")
    elif any(
        supervision[key] is not None
        for key in ("run_id", "record_path", "record_sha256")
    ):
        raise ValueError("pending supervision binding must be empty")
    control_event = _validate_user_control(
        root,
        record["user_control"],
        record["epoch"],
    )
    if control_event is not None and (
        control_event["plan_path"] != record["plan_path"]
        or control_event["plan_sha256"] != record["plan_sha256"]
    ):
        raise ValueError("user control event does not match active plan")
    if record["supersedes"] is not None:
        _validate_plan_link(record["supersedes"], "supersedes")
    if record["superseded_by"] is not None:
        _validate_plan_link(record["superseded_by"], "superseded_by")
    if not history and record["superseded_by"] is not None:
        raise ValueError("active dispatch cannot be superseded")
    if record["lifecycle"] == "SUPERSEDED":
        if record["superseded_by"] is None or not record["server_stop"]["required"]:
            raise ValueError("superseded history requires server stop")
    elif record["server_stop"]["required"]:
        raise ValueError("only superseded history requires server stop")


def load_dispatch(root: Path) -> dict:
    root = Path(root).resolve()
    document = _load_yaml(root / "coordination/DISPATCH.yaml")
    if (
        set(document) != {"schema_version", "epoch", "active"}
        or document["schema_version"] != 4
    ):
        raise ValueError("invalid dispatch state")
    if type(document["epoch"]) is not int or document["epoch"] < 0:
        raise ValueError("invalid dispatch epoch")
    if document["active"] is not None and type(document["active"]) is not dict:
        raise ValueError("invalid active dispatch")
    if document["active"] is not None:
        _validate_dispatch_record(root, document["active"], history=False)
        if document["active"]["epoch"] != document["epoch"]:
            raise ValueError("active dispatch epoch mismatch")
    index = _history_module().load_index(root)
    epochs = [entry["epoch"] for entry in index["entries"]]
    if document["active"] is not None and document["active"]["epoch"] in epochs:
        raise ValueError("active dispatch epoch is already archived")
    if any(epoch > document["epoch"] for epoch in epochs):
        raise ValueError("future dispatch history epoch")
    return document


def compact_dispatch_view(root: Path, *, recent: int = 10) -> dict:
    root = Path(root).resolve()
    dispatch = load_dispatch(root)
    return _history_module().compact_view(
        root,
        dispatch["active"],
        recent=recent,
    )


def load_history_record(root: Path, epoch: int) -> dict:
    root = Path(root).resolve()
    record = _history_module().load_archive(root, epoch)
    _validate_dispatch_record(root, record, history=True)
    entry = next(
        (
            item
            for item in _history_module().load_index(root)["entries"]
            if item["epoch"] == epoch
        ),
        None,
    )
    if entry is None:
        raise ValueError("dispatch archive is absent from the compact index")
    for key in (
        "epoch",
        "plan_id",
        "owner_role",
        "lifecycle",
        "plan_path",
        "plan_sha256",
        "report_path",
    ):
        if entry[key] != record[key]:
            raise ValueError("dispatch archive does not match compact index")
    return record


class _DispatchLock:
    def __init__(self, root: Path):
        self.path = Path(root) / ".research_core/tmp/dispatch.lock"

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.path.mkdir()
        except FileExistsError as error:
            raise ValueError("dispatch update already in progress") from error
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.path.rmdir()


def _binding(required: bool) -> dict:
    return {
        "required": required,
        "status": "PENDING" if required else "NOT_REQUIRED",
        "receipt_path": None,
        "receipt_sha256": None,
    }


def _user_control() -> dict:
    return {
        "state": "RUN",
        "event_path": None,
        "event_sha256": None,
    }


def _link(record: dict) -> dict:
    return {
        "plan_path": record["plan_path"],
        "plan_sha256": record["plan_sha256"],
        "epoch": record["epoch"],
    }


def _check_dialogue_gate(root: Path, document: dict) -> None:
    dialogue = _dialogue_module()
    relevant = dialogue.relevant_dialogues(root, document["conflict_set"])
    if not relevant:
        return
    if len(relevant) != 1:
        raise ValueError("multiple critical dialogues require explicit resolution")
    status = relevant[0]
    if status["status"] != "DESIGNATED":
        raise ValueError("critical dialogue requires user designation")
    if document["consultation"]["dialogue_id"] != status["dialogue_id"]:
        raise ValueError("plan is missing the relevant user designation")


def activate_plan(root: Path, relative: str, *, replace: bool = False) -> dict:
    root = Path(root).resolve()
    worker = current_worker(root)
    owner = PEER_ROLES.get(worker["role"])
    if owner is None:
        raise ValueError("SERVER cannot activate plans")
    with _DispatchLock(root):
        dispatch = load_dispatch(root)
        previous = dispatch["active"]
        if previous is not None and not replace:
            raise ValueError("an active dispatch already exists")
        if previous is None and replace:
            raise ValueError("replace requires an active dispatch")
        if (
            previous is not None
            and previous["user_notice"]["required"]
            and previous["user_notice"]["status"] != "RECORDED"
        ):
            raise ValueError("required user notice must be recorded before replacement")
        document = validate_plan(root, relative)
        if document["owner_role"] != owner:
            raise ValueError("worker does not own plan activation")
        if document["status"] != "READY":
            raise ValueError("only READY plans may be dispatched")
        _check_required_permissions(root, document)
        _check_dialogue_gate(root, document)
        if previous is not None:
            inheritance = document["inheritance"]
            if inheritance["mode"] != "CRITIQUE_INHERITANCE":
                raise ValueError("replacement requires critique inheritance")
            if (
                inheritance["prior_plan_path"] != previous["plan_path"]
                or inheritance["prior_plan_sha256"] != previous["plan_sha256"]
            ):
                raise ValueError("replacement prior plan does not match active dispatch")
        elif document["inheritance"]["mode"] != "NONE":
            raise ValueError("critique inheritance requires replace mode")
        path = _plan_path(root, relative)
        epoch = dispatch["epoch"] + 1
        active = {
            "plan_id": document["plan_id"],
            "owner_role": owner,
            "plan_path": relative,
            "plan_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "report_path": document["report_path"],
            "lifecycle": "DISPATCHED",
            "risk_level": document["risk_level"],
            "critique": document["critique"],
            "epoch": epoch,
            "user_notice": _binding(document["risk_level"] == "L2"),
            "supersedes": _link(previous) if previous is not None else None,
            "superseded_by": None,
            "server_stop": _binding(False),
            "user_control": _user_control(),
            "supervision": {
                "required": document["supervision"]["required"],
                "status": (
                    "PENDING"
                    if document["supervision"]["required"]
                    else "NOT_REQUIRED"
                ),
                "run_id": None,
                "record_path": None,
                "record_sha256": None,
            },
        }
        if previous is not None:
            archived = dict(previous)
            archived["lifecycle"] = "SUPERSEDED"
            archived["superseded_by"] = _link(active)
            archived["server_stop"] = _binding(True)
            _history_module().archive_record(
                root,
                archived,
                result_code="SUPERSEDED",
                summary=f"{archived['plan_id']} superseded by {active['plan_id']}",
            )
        dispatch["epoch"] = epoch
        dispatch["active"] = active
        _atomic_yaml(root / "coordination/DISPATCH.yaml", dispatch)
        result = dict(active)
        result["user_notice_signal"] = (
            "USER_NOTICE_REQUIRED"
            if active["user_notice"]["required"]
            else "NO_USER_NOTICE_REQUIRED"
        )
        return result


def _verify_active_plan(root: Path, active: dict) -> tuple[Path, dict]:
    path = _plan_path(root, active["plan_path"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != active["plan_sha256"]:
        raise ValueError("active plan SHA256 mismatch")
    document = validate_plan(root, active["plan_path"])
    _check_required_permissions(root, document)
    return path, document


def resolve_active_plan(root: Path, *, epoch: int | None = None) -> Path:
    root = Path(root).resolve()
    worker = current_worker(root)
    if worker["role"] != "SERVER":
        raise ValueError("only SERVER resolves an active plan")
    active = load_dispatch(root)["active"]
    if active is None:
        raise ValueError("no active dispatch")
    if epoch is not None and active["epoch"] != epoch:
        raise ValueError("dispatch epoch is no longer active")
    if active["user_control"]["state"] == "PAUSED":
        raise ValueError("user control is paused")
    return _verify_active_plan(root, active)[0]


def _git_output(root: Path, arguments: list[str], label: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        encoding="utf-8",
        capture_output=True,
        shell=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(f"{label} failed: {detail}")
    return completed.stdout.strip()


def pull_and_resolve_active_plan(root: Path) -> dict:
    root = Path(root).resolve()
    if current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER may pull and resolve an active plan")
    top = Path(_git_output(root, ["rev-parse", "--show-toplevel"], "repository root"))
    if top.resolve() != root:
        raise ValueError("pull-execute requires the exact repository root")
    branch = _git_output(root, ["branch", "--show-current"], "branch check")
    if branch != "main":
        raise ValueError("pull-execute requires main")
    if _git_output(
        root,
        ["status", "--porcelain", "--untracked-files=all"],
        "worktree check",
    ):
        raise ValueError("pull-execute requires a clean worktree")
    remote = _git_output(
        root,
        ["config", "--get", "branch.main.remote"],
        "upstream remote check",
    )
    merge_ref = _git_output(
        root,
        ["config", "--get", "branch.main.merge"],
        "upstream branch check",
    )
    if not remote or remote == "." or not merge_ref.startswith("refs/heads/"):
        raise ValueError("main requires a configured remote upstream")
    _git_output(root, ["fetch", "--", remote], "fetch")
    counts = _git_output(
        root,
        ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
        "fast-forward check",
    ).split()
    if len(counts) != 2 or any(not value.isdigit() for value in counts):
        raise ValueError("invalid fast-forward comparison")
    local_ahead, remote_ahead = (int(value) for value in counts)
    if local_ahead and remote_ahead:
        raise ValueError("main and upstream are diverged")
    if local_ahead:
        raise ValueError("local main is ahead; push before pull-execute")
    if remote_ahead:
        _git_output(root, ["merge", "--ff-only", "@{upstream}"], "fast-forward")
    if _git_output(root, ["rev-parse", "HEAD"], "HEAD check") != _git_output(
        root,
        ["rev-parse", "@{upstream}"],
        "upstream HEAD check",
    ):
        raise ValueError("main did not reach its upstream exactly")
    path = resolve_active_plan(root)
    active = load_dispatch(root)["active"]
    return {
        "status": "READY_TO_EXECUTE",
        "plan_path": path.relative_to(root).as_posix(),
        "plan_sha256": active["plan_sha256"],
        "epoch": active["epoch"],
    }


def record_user_control(
    root: Path,
    *,
    epoch: int,
    action: str,
    instruction: str,
) -> Path:
    root = Path(root).resolve()
    worker = current_worker(root)
    actor_directory = {
        "PEER_B": "B",
        "PEER_C": "C",
        "SERVER": "SERVER",
    }.get(worker["role"])
    if actor_directory is None:
        raise ValueError("unknown worker role")
    normalized = str(action).upper()
    if normalized not in {"STOP", "CONTINUE"}:
        raise ValueError("user control action must be STOP or CONTINUE")
    if type(instruction) is not str or not instruction.strip() or "\x00" in instruction:
        raise ValueError("user control instruction is required")
    with _DispatchLock(root):
        dispatch = load_dispatch(root)
        active = dispatch["active"]
        if active is None or type(epoch) is not int or active["epoch"] != epoch:
            raise ValueError("dispatch epoch is no longer active")
        _verify_active_plan(root, active)
        current_state = active["user_control"]["state"]
        if normalized == "STOP" and current_state != "RUN":
            raise ValueError("dispatch is already paused by user control")
        if normalized == "CONTINUE" and current_state != "PAUSED":
            raise ValueError("dispatch is not paused by user control")
        directory = root / (
            f"coordination/controls/{actor_directory}/E{epoch:06d}"
        )
        sequence = 1
        while (directory / f"U{sequence:04d}.yaml").exists():
            sequence += 1
        path = directory / f"U{sequence:04d}.yaml"
        relative = path.relative_to(root).as_posix()
        _exclusive_yaml(
            path,
            {
                "schema_version": 1,
                "epoch": epoch,
                "plan_path": active["plan_path"],
                "plan_sha256": active["plan_sha256"],
                "action": normalized,
                "instruction": instruction.strip(),
                "recorded_by": worker["worker_id"],
                "actor_role": worker["role"],
                "recorded_at": _utc_now(),
            },
        )
        try:
            active["user_control"] = {
                "state": "PAUSED" if normalized == "STOP" else "RUN",
                "event_path": relative,
                "event_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            dispatch["active"] = active
            _atomic_yaml(root / "coordination/DISPATCH.yaml", dispatch)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return path


def record_deviation(
    root: Path,
    *,
    epoch: int,
    fields: list[str],
    summary: str,
    action: str,
) -> Path:
    root = Path(root).resolve()
    if current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER records execution deviations")
    if (
        type(fields) is not list
        or not fields
        or any(type(field) is not str or not field for field in fields)
        or len(fields) != len(set(fields))
        or not set(fields).issubset(FLEXIBLE_EXECUTION_FIELDS)
    ):
        raise ValueError("requested deviation crosses a principle boundary")
    for value, label in ((summary, "deviation summary"), (action, "deviation action")):
        if type(value) is not str or not value.strip() or "\x00" in value:
            raise ValueError(f"{label} is required")
    with _DispatchLock(root):
        dispatch = load_dispatch(root)
        active = dispatch["active"]
        if active is None or type(epoch) is not int or active["epoch"] != epoch:
            raise ValueError("dispatch epoch is no longer active")
        _verify_active_plan(root, active)
        directory = root / f"coordination/deviations/E{epoch:06d}"
        sequence = 1
        while (directory / f"D{sequence:04d}.yaml").exists():
            sequence += 1
        path = directory / f"D{sequence:04d}.yaml"
        return _exclusive_yaml(
            path,
            {
                "schema_version": 1,
                "epoch": epoch,
                "plan_path": active["plan_path"],
                "plan_sha256": active["plan_sha256"],
                "recorded_by": "server-primary",
                "classification": "NON_PRINCIPLE",
                "fields": fields,
                "summary": summary.strip(),
                "action": action.strip(),
                "recorded_at": _utc_now(),
            },
        )


def record_user_notice(root: Path, summary: str) -> Path:
    root = Path(root).resolve()
    worker = current_worker(root)
    owner = PEER_ROLES.get(worker["role"])
    if owner is None:
        raise ValueError("only a peer records user notice")
    if type(summary) is not str or not summary.strip() or "\x00" in summary:
        raise ValueError("user notice summary is required")
    with _DispatchLock(root):
        dispatch = load_dispatch(root)
        active = dispatch["active"]
        if active is None or active["owner_role"] != owner:
            raise ValueError("only the dispatch owner records user notice")
        notice = active["user_notice"]
        if not notice["required"] or notice["status"] != "PENDING":
            raise ValueError("no pending user notice")
        relative = f"coordination/notices/{owner}/{active['plan_id']}.yaml"
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.parent.resolve() != (root / "coordination/notices" / owner).resolve():
            raise ValueError("user notice path escapes project")
        _exclusive_yaml(
            path,
            {
                "schema_version": 1,
                "plan_id": active["plan_id"],
                "dispatch_epoch": active["epoch"],
                "notified_by": owner,
                "summary": summary.strip(),
                "notified_at": _utc_now(),
            },
        )
        try:
            active["user_notice"] = {
                "required": True,
                "status": "RECORDED",
                "receipt_path": relative,
                "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            dispatch["active"] = active
            _atomic_yaml(root / "coordination/DISPATCH.yaml", dispatch)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return path


def _validate_execution_receipts(root: Path, document: dict) -> None:
    report = Path(root).joinpath(*PurePosixPath(document["report_path"]).parts)
    if report.is_symlink() or not report.is_file() or not report.read_bytes():
        raise ValueError("non-empty execution report is required")
    receipts = []
    for field, status in (("completion_receipt", "COMPLETE"), ("exception_receipt", "EXCEPTION")):
        path = Path(root).joinpath(*PurePosixPath(document[field]).parts)
        if path.exists():
            if path.is_symlink() or not path.is_file():
                raise ValueError("execution receipt must be a plain file")
            if _load_yaml(path).get("status") != status:
                raise ValueError("execution receipt status mismatch")
            receipts.append(path)
    if len(receipts) != 1:
        raise ValueError("exactly one completion or exception receipt is required")


def _require_supervision_record(root: Path, active: dict) -> None:
    binding = active["supervision"]
    if not binding["required"]:
        return
    if binding["status"] != "RECORDED":
        raise ValueError("required supervision is not recorded")
    expected = (
        f"coordination/supervision/{binding['run_id']}/SUPERVISION.yaml"
    )
    if binding["record_path"] != expected:
        raise ValueError("supervision record path mismatch")
    path = root.joinpath(*PurePosixPath(expected).parts)
    if path.is_symlink() or not path.is_file():
        raise ValueError("supervision record is missing")
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["record_sha256"]:
        raise ValueError("supervision record SHA256 mismatch")
    record = _load_yaml(path)
    if (
        record.get("run_id") != binding["run_id"]
        or record.get("epoch") != active["epoch"]
        or record.get("plan_path") != active["plan_path"]
        or record.get("plan_sha256") != active["plan_sha256"]
        or record.get("created_by") != "SERVER"
        or record.get("status") != "ACTIVE"
    ):
        raise ValueError("supervision record does not match active dispatch")


def heartbeat_dispatch(root: Path, epoch: int) -> dict:
    root = Path(root).resolve()
    if current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER sends dispatch heartbeat")
    if type(epoch) is not int or epoch < 1:
        raise ValueError("invalid dispatch epoch")
    with _DispatchLock(root):
        dispatch = load_dispatch(root)
        active = dispatch["active"]
        if active is not None and active["epoch"] == epoch:
            _verify_active_plan(root, active)
            if active["user_control"]["state"] == "PAUSED":
                return {
                    "status": "MUST_STOP",
                    "reason": "USER_STOP",
                    "epoch": epoch,
                    "event_path": active["user_control"]["event_path"],
                }
            return {"status": "CONTINUE", "epoch": epoch, "plan_path": active["plan_path"]}
        try:
            record = load_history_record(root, epoch)
        except (FileNotFoundError, ValueError) as error:
            raise ValueError("dispatch epoch is unknown or no longer executable")
        if record["lifecycle"] != "SUPERSEDED":
            raise ValueError("dispatch epoch is unknown or no longer executable")
        document = validate_plan(root, record["plan_path"])
        relative = document["exception_receipt"]
        path = root.joinpath(*PurePosixPath(relative).parts)
        stop = record["server_stop"]
        if stop["status"] == "PENDING":
            if path.exists():
                raise ValueError("supersession exception receipt already exists")
            _exclusive_yaml(
                path,
                {
                    "schema_version": 1,
                    "status": "EXCEPTION",
                    "reason": "DISPATCH_SUPERSEDED",
                    "dispatch_epoch": epoch,
                    "superseded_by": record["superseded_by"],
                    "recorded_at": _utc_now(),
                },
            )
            try:
                record["server_stop"] = {
                    "required": True,
                    "status": "RECORDED",
                    "receipt_path": relative,
                    "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                _history_module().update_archive(root, epoch, record)
            except BaseException:
                path.unlink(missing_ok=True)
                raise
        return {
            "status": "MUST_STOP",
            "epoch": epoch,
            "superseded_by": record["superseded_by"],
            "receipt_path": record["server_stop"]["receipt_path"],
        }


def transition_dispatch(root: Path, lifecycle: str, *, epoch: int) -> dict:
    root = Path(root).resolve()
    worker = current_worker(root)
    with _DispatchLock(root):
        dispatch = load_dispatch(root)
        active = dispatch["active"]
        if active is None:
            raise ValueError("no active dispatch")
        if type(epoch) is not int or active["epoch"] != epoch:
            raise ValueError("dispatch epoch is no longer active")
        current = active["lifecycle"]
        if active["user_control"]["state"] == "PAUSED":
            raise ValueError("user control is paused")
        if worker["role"] == "SERVER":
            allowed = {"DISPATCHED": "RUNNING", "RUNNING": "REPORTED"}
            if allowed.get(current) != lifecycle:
                raise ValueError("SERVER has execution authority only")
            _, document = _verify_active_plan(root, active)
            if lifecycle == "RUNNING":
                _require_supervision_record(root, active)
            if lifecycle == "REPORTED":
                _validate_execution_receipts(root, document)
        elif worker["role"] in PEER_ROLES:
            if current != "REPORTED" or lifecycle not in TERMINAL:
                raise ValueError("peer may only decide a reported dispatch")
            document = validate_plan(root, active["plan_path"])
            _validate_execution_receipts(root, document)
            if active["user_notice"]["required"] and active["user_notice"]["status"] != "RECORDED":
                raise ValueError("required user notice is still pending")
        else:
            raise ValueError("unknown role")
        active = dict(active, lifecycle=lifecycle)
        if lifecycle in TERMINAL:
            exception = root.joinpath(
                *PurePosixPath(document["exception_receipt"]).parts
            ).exists()
            if exception and lifecycle not in {"CONTESTED", "INCONCLUSIVE"}:
                result_code = "FAILED"
            else:
                result_code = {
                    "ACCEPTED": "SUCCEEDED",
                    "KILLED": "KILLED",
                    "CONTESTED": "CONTESTED",
                    "INCONCLUSIVE": "INCONCLUSIVE",
                }[lifecycle]
            _history_module().archive_record(
                root,
                active,
                result_code=result_code,
                summary=f"{active['plan_id']} finished as {lifecycle}",
            )
            dispatch["active"] = None
        else:
            dispatch["active"] = active
        _atomic_yaml(root / "coordination/DISPATCH.yaml", dispatch)
        return active


def governance_errors(root: Path) -> list[str]:
    try:
        _workers(root)
        dispatch = load_dispatch(root)
        records = [dispatch["active"]] if dispatch["active"] is not None else []
        for entry in _history_module().load_index(root)["entries"]:
            records.append(load_history_record(root, entry["epoch"]))
        for record in records:
            path = _plan_path(root, record["plan_path"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != record["plan_sha256"]:
                raise ValueError("dispatched plan hash drift")
            document = validate_plan(root, record["plan_path"])
            expected = {
                "plan_id": document["plan_id"],
                "owner_role": document["owner_role"],
                "report_path": document["report_path"],
                "risk_level": document["risk_level"],
                "critique": document["critique"],
            }
            if any(record.get(key) != value for key, value in expected.items()):
                raise ValueError("dispatch plan identity mismatch")
            for label in ("user_notice", "server_stop"):
                binding = record[label]
                if binding["status"] == "RECORDED":
                    _validate_file_hash(
                        root,
                        binding["receipt_path"],
                        binding["receipt_sha256"],
                        label,
                    )
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        return [str(error)]
    return []
