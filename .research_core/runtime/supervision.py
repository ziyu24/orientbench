"""SERVER-created, plan-bound supervision for long project runs."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import tempfile

import yaml


SUPERVISION_KEYS = {
    "schema_version",
    "run_id",
    "epoch",
    "plan_path",
    "plan_sha256",
    "plan_owner",
    "created_by",
    "interval_minutes",
    "scientific_stage",
    "status",
    "no_progress_cycles",
    "last_check_at",
    "latest_summary",
    "recent_event_ids",
}
OBSERVATION_KEYS = {
    "progress",
    "process_state",
    "gpu_state",
    "cpu_state",
    "disk_free_gib",
    "heartbeat_state",
    "node_state",
    "scientific_stage",
    "checkpoint_state",
    "log_state",
}
MAX_LOG_BYTES = 65536
MAX_SUMMARY_BYTES = 65536
RECENT_EVENT_LIMIT = 10
DISK_WARNING_GIB = 5
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


def _module(name: str):
    path = Path(__file__).with_name(f"{name}.py")
    specification = importlib.util.spec_from_file_location(
        f"research_core_supervision_{name}", path
    )
    if specification is None or specification.loader is None:
        raise ValueError(f"cannot load runtime module: {name}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _governance():
    return _module("peer_governance")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _directory(root: Path, run_id: str) -> Path:
    if type(run_id) is not str or RUN_ID.fullmatch(run_id) is None:
        raise ValueError("invalid run id")
    return Path(root) / "coordination/supervision" / run_id


def _load_yaml(path: Path) -> dict:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(document) is not dict:
        raise ValueError(f"YAML mapping required: {path}")
    return document


def _atomic_yaml(path: Path, document: dict, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not overwrite:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                yaml.safe_dump(document, stream, sort_keys=False)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, sort_keys=False)
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def load(root: Path, *, run_id: str) -> dict:
    document = _load_yaml(_directory(root, run_id) / "SUPERVISION.yaml")
    if (
        set(document) != SUPERVISION_KEYS
        or document.get("schema_version") != 1
        or document.get("run_id") != run_id
        or document.get("created_by") != "SERVER"
        or document.get("interval_minutes") != 20
        or document.get("status") not in {"ACTIVE", "STOPPED", "TERMINAL"}
        or type(document.get("no_progress_cycles")) is not int
        or document["no_progress_cycles"] < 0
        or type(document.get("recent_event_ids")) is not list
        or len(document["recent_event_ids"]) > RECENT_EVENT_LIMIT
    ):
        raise ValueError("invalid supervision record")
    return document


def bootstrap(root: Path, *, epoch: int, run_id: str) -> dict:
    root = Path(root).resolve()
    governance = _governance()
    if governance.current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER creates supervision")
    dispatch = governance.load_dispatch(root)
    active = dispatch["active"]
    if active is None or active["epoch"] != epoch:
        raise ValueError("supervision epoch is not active")
    if active["supervision"]["status"] != "PENDING":
        raise ValueError("supervision is not pending")
    plan = governance.validate_plan(root, active["plan_path"])
    if not plan["supervision"]["required"]:
        raise ValueError("plan does not require supervision")
    directory = _directory(root, run_id)
    directory.mkdir(exist_ok=False)
    try:
        (directory / "events").mkdir()
        record = {
            "schema_version": 1,
            "run_id": run_id,
            "epoch": epoch,
            "plan_path": active["plan_path"],
            "plan_sha256": active["plan_sha256"],
            "plan_owner": active["owner_role"],
            "created_by": "SERVER",
            "interval_minutes": plan["supervision"]["interval_minutes"],
            "scientific_stage": plan["supervision"]["scientific_stage"],
            "status": "ACTIVE",
            "no_progress_cycles": 0,
            "last_check_at": None,
            "latest_summary": None,
            "recent_event_ids": [],
        }
        path = directory / "SUPERVISION.yaml"
        _atomic_yaml(path, record, overwrite=False)
        active["supervision"] = {
            "required": True,
            "status": "RECORDED",
            "run_id": run_id,
            "record_path": path.relative_to(root).as_posix(),
            "record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        governance._atomic_yaml(root / "coordination/DISPATCH.yaml", dispatch)
    except BaseException:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return load(root, run_id=run_id)


def _tail(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("supervision log must be a plain file")
    size = path.stat().st_size
    with path.open("rb") as stream:
        stream.seek(max(0, size - MAX_LOG_BYTES))
        return stream.read(MAX_LOG_BYTES)


def _bounded(value, label: str) -> None:
    encoded = yaml.safe_dump(value, sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_SUMMARY_BYTES:
        raise ValueError(f"{label} exceeds bounded supervision view")


def check(
    root: Path,
    *,
    run_id: str,
    observation: dict,
    log_path: Path,
    metrics: dict,
    checkpoints: list[dict],
) -> dict:
    root = Path(root).resolve()
    governance = _governance()
    if governance.current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER checks supervision")
    record = load(root, run_id=run_id)
    dispatch = governance.load_dispatch(root)
    active = dispatch["active"]
    if (
        active is None
        or active["epoch"] != record["epoch"]
        or active["lifecycle"] != "RUNNING"
    ):
        raise ValueError("supervised dispatch is not RUNNING")
    heartbeat = governance.heartbeat_dispatch(root, record["epoch"])
    payload = _tail(Path(log_path))
    if type(metrics) is not dict or type(checkpoints) is not list:
        raise ValueError("invalid bounded supervision inputs")
    _bounded(metrics, "metrics summary")
    _bounded(checkpoints, "checkpoint list")
    if (
        type(observation) is not dict
        or set(observation) != OBSERVATION_KEYS
        or observation["scientific_stage"] != record["scientific_stage"]
        or type(observation["progress"]) is not bool
        or type(observation["disk_free_gib"]) not in {int, float}
    ):
        raise ValueError("invalid or changed supervision observation scope")
    if heartbeat["status"] == "MUST_STOP":
        action = "MUST_STOP"
    elif observation["node_state"] == "NODE_UNREACHABLE":
        action = "DIAGNOSE_AND_RECOVER_LOCAL_CHECKPOINT"
    elif observation["process_state"] == "COMPLETE":
        action = "REPORT_TERMINAL"
    elif (
        observation["checkpoint_state"] == "AVAILABLE"
        and observation["process_state"] == "STOPPED"
    ):
        action = "RESUME_CHECKPOINT"
    elif (
        observation["heartbeat_state"] == "STALE"
        or observation["process_state"] not in {"RUNNING", "COMPLETE"}
        or observation["gpu_state"] == "STOPPED_UNEXPECTEDLY"
        or observation["cpu_state"] == "STOPPED_UNEXPECTEDLY"
        or observation["log_state"] == "STALLED"
        or not observation["progress"]
    ):
        action = "DIAGNOSE"
    else:
        action = "CONTINUE"
    record["no_progress_cycles"] = (
        0 if observation["progress"] else record["no_progress_cycles"] + 1
    )
    disk_warning = observation["disk_free_gib"] < DISK_WARNING_GIB
    notify_user = (
        record["no_progress_cycles"] == 3
        or action == "MUST_STOP"
    )
    sequence = (
        1
        if not record["recent_event_ids"]
        else int(record["recent_event_ids"][-1][1:]) + 1
    )
    event_id = f"E{sequence:04d}"
    event = {
        "schema_version": 1,
        "event_id": event_id,
        "checked_at": _utc_now(),
        "action": action,
        "notify_user": notify_user,
        "disk_warning": disk_warning,
        "loaded_log_bytes": len(payload),
        "log_tail": payload.decode("utf-8", errors="replace"),
        "metrics": metrics,
        "checkpoints": checkpoints,
        "observation": observation,
    }
    _atomic_yaml(
        _directory(root, run_id) / "events" / f"{event_id}.yaml",
        event,
        overwrite=False,
    )
    record["last_check_at"] = event["checked_at"]
    record["latest_summary"] = {
        "action": action,
        "notify_user": notify_user,
        "disk_warning": disk_warning,
    }
    record["recent_event_ids"] = [
        *record["recent_event_ids"],
        event_id,
    ][-RECENT_EVENT_LIMIT:]
    _atomic_yaml(
        _directory(root, run_id) / "SUPERVISION.yaml",
        record,
        overwrite=True,
    )
    return {
        "action": action,
        "notify_user": notify_user,
        "disk_warning": disk_warning,
        "loaded_log_bytes": len(payload),
        "no_progress_cycles": record["no_progress_cycles"],
        "event_id": event_id,
    }


def history(root: Path, *, run_id: str, event_id: str) -> dict:
    if re.fullmatch(r"E[0-9]{4}", str(event_id)) is None:
        raise ValueError("invalid supervision event id")
    return _load_yaml(_directory(root, run_id) / "events" / f"{event_id}.yaml")
