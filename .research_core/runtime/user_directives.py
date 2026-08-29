"""Auditable user-to-SERVER special directives and fixed-anchor publication."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

import yaml


DIRECTIVE_ID = re.compile(r"r(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\Z")
SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
RECORD_KEYS = {
    "schema_version",
    "directive_id",
    "instruction",
    "base_sha",
    "node_id",
    "argv",
    "read_set",
    "write_set",
    "resource_set",
    "expected_results",
    "external_write",
    "dangerous",
    "status",
}
RESULT_KEYS = {
    "schema_version",
    "directive_id",
    "status",
    "exit_code",
    "argv",
    "stdout_tail",
    "stdout_sha256",
    "stderr_tail",
    "stderr_sha256",
    "result_files",
    "missing_results",
    "executed_at",
}
SMALL_RESULT_MAX_BYTES = 1024 * 1024
MAX_STREAM_BYTES = 65536
CREDENTIAL_SIGNATURES = (
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"ghp_[A-Za-z0-9]{20,}"),
    re.compile(
        rb"(?i)(?:password|api[_-]?key|secret[_-]?key)\s*[:=]\s*\S+"
    ),
)


def _module(name: str):
    path = Path(__file__).with_name(f"{name}.py")
    specification = importlib.util.spec_from_file_location(
        f"research_core_user_directive_{name}", path
    )
    if specification is None or specification.loader is None:
        raise ValueError(f"cannot load runtime module: {name}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _governance():
    return _module("peer_governance")


def _research_execution():
    return _module("research_execution")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _directory(root: Path, directive_id: str) -> Path:
    if type(directive_id) is not str or DIRECTIVE_ID.fullmatch(directive_id) is None:
        raise ValueError("invalid user directive id")
    return Path(root) / "coordination/instructions" / directive_id


def _relative(value: str, label: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"invalid {label}")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
    ):
        raise ValueError(f"invalid {label}")
    return path.as_posix()


def _string_list(value, label: str, *, paths: bool) -> list[str]:
    if type(value) is not list or any(
        type(item) is not str or not item or "\x00" in item for item in value
    ):
        raise ValueError(f"invalid user directive {label}")
    if paths:
        return [_relative(item, label) for item in value]
    return list(value)


def _git(
    root: Path, arguments: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    if check and completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or "Git directive operation failed")
    return completed


def _require_https_origin(root: Path) -> str:
    url = _git(root, ["remote", "get-url", "--push", "origin"]).stdout.strip()
    if re.fullmatch(r"https://[^\s]+", url, flags=re.IGNORECASE) is None:
        raise ValueError("production origin push URL must use HTTPS")
    return url


def _write_exclusive(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, sort_keys=False)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def validate_record(root: Path, document: dict) -> dict:
    if (
        type(document) is not dict
        or set(document) != RECORD_KEYS
        or document.get("schema_version") != 1
        or DIRECTIVE_ID.fullmatch(str(document.get("directive_id"))) is None
        or SHA.fullmatch(str(document.get("base_sha"))) is None
        or type(document.get("instruction")) is not str
        or not document["instruction"].strip()
        or type(document.get("node_id")) is not str
        or not document["node_id"]
        or type(document.get("external_write")) is not bool
        or type(document.get("dangerous")) is not bool
        or document.get("status") != "RECORDED"
    ):
        raise ValueError("invalid user directive fields")
    argv = _string_list(document["argv"], "argv", paths=False)
    if not argv:
        raise ValueError("user directive argv is empty")
    for field in ("read_set", "write_set", "expected_results"):
        _string_list(document[field], field, paths=True)
    _string_list(document["resource_set"], "resource_set", paths=False)
    if _git(
        root,
        ["cat-file", "-e", f'{document["base_sha"]}^{{commit}}'],
        check=False,
    ).returncode != 0:
        raise ValueError("user directive base SHA is not committed")
    return document


def load_record(root: Path, directive_id: str) -> dict:
    path = _directory(root, directive_id) / "USER_DIRECTIVE.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return validate_record(root, document)


def _require_server(root: Path) -> None:
    if _governance().current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER handles user directives")


def _require_no_user_stop(root: Path) -> None:
    active = _governance().load_dispatch(root)["active"]
    if active is not None and active["user_control"]["state"] == "PAUSED":
        raise ValueError("USER_STOP")


def record(
    root: Path,
    *,
    directive_id: str | None,
    instruction: str,
    base_sha: str,
    node_id: str,
    argv: list[str],
    read_set: list[str],
    write_set: list[str],
    resource_set: list[str],
    expected_results: list[str],
    external_write: bool,
    dangerous: bool,
    confirmed: bool,
) -> dict:
    root = Path(root).resolve()
    _require_server(root)
    if (dangerous or external_write) and not confirmed:
        raise ValueError("exact confirmation is required")
    allocated_id, directory = _research_execution().reserve_numeric_instruction(
        root, expected_id=directive_id, kind="USER_DIRECTIVE"
    )
    document = {
        "schema_version": 1,
        "directive_id": allocated_id,
        "instruction": instruction,
        "base_sha": base_sha,
        "node_id": node_id,
        "argv": argv,
        "read_set": read_set,
        "write_set": write_set,
        "resource_set": resource_set,
        "expected_results": expected_results,
        "external_write": external_write,
        "dangerous": dangerous,
        "status": "RECORDED",
    }
    validate_record(root, document)
    try:
        _write_exclusive(directory / "USER_DIRECTIVE.yaml", document)
    except BaseException:
        raise
    return document


def _tail(value: str) -> tuple[str, str]:
    encoded = value.encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    tail = encoded[-MAX_STREAM_BYTES:].decode("utf-8", errors="replace")
    return tail, digest


def _result_files(root: Path, record: dict) -> tuple[list[dict], list[str]]:
    files = []
    missing = []
    for relative in record["expected_results"]:
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.exists():
            missing.append(relative)
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("directive result must be a plain file")
        size = path.stat().st_size
        if size > SMALL_RESULT_MAX_BYTES:
            raise ValueError(
                "large directive result cannot be published; record a small artifact manifest"
            )
        files.append(
            {
                "path": relative,
                "size_bytes": size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return files, missing


def _dirty_paths(root: Path) -> set[str]:
    lines = _git(
        root, ["status", "--porcelain", "--untracked-files=all"]
    ).stdout.splitlines()
    return {line[3:].replace("\\", "/") for line in lines}


def _require_execution_base(root: Path, record: dict) -> None:
    if _git(root, ["rev-parse", "HEAD"]).stdout.strip() != record["base_sha"]:
        raise ValueError("user directive execution base changed")
    directory = _directory(root, record["directive_id"])
    allowed = {
        (directory / "RESERVATION.yaml").relative_to(root).as_posix(),
        (directory / "USER_DIRECTIVE.yaml").relative_to(root).as_posix()
    }
    if not _dirty_paths(root).issubset(allowed):
        raise ValueError("unrelated worktree changes block directive execution")


def execute(root: Path, *, directive_id: str, runner=subprocess.run) -> dict:
    root = Path(root).resolve()
    _require_server(root)
    _require_no_user_stop(root)
    document = load_record(root, directive_id)
    _require_execution_base(root, document)
    completed = runner(
        document["argv"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    stdout_tail, stdout_sha256 = _tail(completed.stdout or "")
    stderr_tail, stderr_sha256 = _tail(completed.stderr or "")
    result_files, missing = _result_files(root, document)
    status = "SUCCEEDED" if completed.returncode == 0 else "FAILED"
    if status == "SUCCEEDED" and missing:
        status = "INCOMPLETE"
    receipt = {
        "schema_version": 1,
        "directive_id": directive_id,
        "status": status,
        "exit_code": completed.returncode,
        "argv": document["argv"],
        "stdout_tail": stdout_tail,
        "stdout_sha256": stdout_sha256,
        "stderr_tail": stderr_tail,
        "stderr_sha256": stderr_sha256,
        "result_files": result_files,
        "missing_results": missing,
        "executed_at": _utc_now(),
    }
    _write_exclusive(_directory(root, directive_id) / "RESULT.yaml", receipt)
    return receipt


def load_result(root: Path, directive_id: str) -> dict:
    path = _directory(root, directive_id) / "RESULT.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if (
        type(document) is not dict
        or set(document) != RESULT_KEYS
        or document.get("schema_version") != 1
        or document.get("directive_id") != directive_id
        or document.get("status") not in {"SUCCEEDED", "FAILED", "INCOMPLETE"}
        or type(document.get("exit_code")) is not int
        or type(document.get("argv")) is not list
        or not document["argv"]
        or any(type(value) is not str or not value for value in document["argv"])
        or type(document.get("stdout_tail")) is not str
        or re.fullmatch(r"[0-9a-f]{64}", str(document.get("stdout_sha256")))
        is None
        or type(document.get("stderr_tail")) is not str
        or re.fullmatch(r"[0-9a-f]{64}", str(document.get("stderr_sha256")))
        is None
        or type(document.get("result_files")) is not list
        or type(document.get("missing_results")) is not list
        or type(document.get("executed_at")) is not str
        or not document["executed_at"]
    ):
        raise ValueError("invalid user directive result")
    for item in document["result_files"]:
        if (
            type(item) is not dict
            or set(item) != {"path", "size_bytes", "sha256"}
            or type(item.get("size_bytes")) is not int
            or item["size_bytes"] < 0
            or re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256"))) is None
        ):
            raise ValueError("invalid user directive result file")
        _relative(item.get("path"), "result path")
    missing = _string_list(
        document["missing_results"], "missing results", paths=True
    )
    result_paths = [item["path"] for item in document["result_files"]]
    if len(set(result_paths)) != len(result_paths) or set(result_paths) & set(missing):
        raise ValueError("invalid user directive result paths")
    return document


def _reject_credentials(path: Path) -> None:
    payload = path.read_bytes()
    if any(signature.search(payload) for signature in CREDENTIAL_SIGNATURES):
        raise ValueError(f"credential material blocks publication: {path.name}")


def _fixed_primary_config(path: Path, record: dict) -> dict:
    try:
        from cqc_fabric import API_VERSION as fabric_api_version
        from cqc_fabric.inventory import load_inventory

        if fabric_api_version != "1.1":
            raise ValueError("global fabric API version mismatch")
        document = load_inventory(Path(path))
    except (ImportError, OSError, ValueError) as error:
        raise ValueError("valid fixed anchor fabric config is required") from error
    primaries = [
        node
        for node in document["nodes"]
        if node["class"] == "STABLE_PRIMARY" and node["enabled"]
    ]
    if len(primaries) != 1:
        raise ValueError("fixed anchor is not enabled")
    if record["node_id"] not in {node["node_id"] for node in document["nodes"]}:
        raise ValueError("directive execution node is absent from fabric config")
    return primaries[0]


def _fabric_config_path() -> Path:
    return Path.home() / ".config/cqc-fabric/fabric.local.yaml"


def _validate_artifact_result(root: Path, relative: str) -> None:
    parts = PurePosixPath(relative).parts
    if parts[:2] != ("artifacts", "manifests"):
        return
    if PurePosixPath(relative).suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("artifact manifest result must be YAML")
    try:
        from cqc_fabric import API_VERSION as fabric_api_version
        from cqc_fabric.artifacts import load_manifest

        if fabric_api_version != "1.1":
            raise ValueError("global fabric API version mismatch")
        load_manifest(
            root.joinpath(*parts),
            manifests_root=root / "artifacts/manifests",
        )
    except (ImportError, OSError, ValueError) as error:
        raise ValueError("invalid rebuildable artifact manifest") from error


def publish(root: Path, *, directive_id: str) -> dict:
    root = Path(root).resolve()
    _require_server(root)
    _require_https_origin(root)
    _require_no_user_stop(root)
    directory = _directory(root, directive_id)
    if not (directory / "RESULT.yaml").is_file():
        raise ValueError("directive result receipt is required")
    record = load_record(root, directive_id)
    _fixed_primary_config(_fabric_config_path(), record)
    result = load_result(root, directive_id)
    if result["argv"] != record["argv"]:
        raise ValueError("directive result command does not match record")
    result_paths = {item["path"] for item in result["result_files"]}
    missing_paths = set(result["missing_results"])
    if result_paths | missing_paths != set(record["expected_results"]):
        raise ValueError("directive result does not cover expected results")
    expected_status = (
        "FAILED"
        if result["exit_code"] != 0
        else "INCOMPLETE" if missing_paths else "SUCCEEDED"
    )
    if result["status"] != expected_status:
        raise ValueError("directive result status is inconsistent")
    directory_relative = directory.relative_to(root).as_posix()
    allowed = {
        f"{directory_relative}/RESERVATION.yaml",
        f"{directory_relative}/USER_DIRECTIVE.yaml",
        f"{directory_relative}/RESULT.yaml",
    }
    for item in result["result_files"]:
        relative = _relative(item["path"], "result path")
        if relative not in record["expected_results"]:
            raise ValueError("directive result was not declared")
        path = root.joinpath(*PurePosixPath(relative).parts)
        if (
            path.is_symlink()
            or not path.is_file()
            or path.stat().st_size != item["size_bytes"]
            or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]
        ):
            raise ValueError("directive result changed after execution")
        if item["size_bytes"] > SMALL_RESULT_MAX_BYTES:
            raise ValueError("directive result exceeds publication limit")
        _validate_artifact_result(root, relative)
        allowed.add(relative)
    for relative in sorted(allowed):
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.is_file():
            _reject_credentials(path)
    for relative in _dirty_paths(root):
        if relative not in allowed:
            raise ValueError("unrelated worktree changes block directive publication")
    if _git(root, ["rev-parse", "HEAD"]).stdout.strip() != record["base_sha"]:
        raise ValueError("directive publication base changed")
    _git(root, ["ls-remote", "--quiet", "origin"])
    branch = f"exec/{directive_id}"
    if _git(
        root,
        ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        check=False,
    ).returncode == 0:
        raise ValueError("directive branch already exists")
    _git(root, ["switch", "-c", branch])
    for relative in sorted(allowed):
        path = root.joinpath(*PurePosixPath(relative).parts)
        if path.exists():
            _git(root, ["add", "--", relative])
    _git(root, ["commit", "-m", f"exec: record {directive_id} result"])
    _git(root, ["push", "-u", "origin", branch])
    commit = _git(root, ["rev-parse", "HEAD"]).stdout.strip()
    remote = _git(
        root, ["ls-remote", "--heads", "origin", f"refs/heads/{branch}"]
    ).stdout.strip().split()
    if len(remote) != 2 or remote[0] != commit or remote[1] != f"refs/heads/{branch}":
        raise ValueError("directive result branch remote verification failed")
    return {
        "branch": branch,
        "pushed": True,
        "result_commit": commit,
        "remote_commit": remote[0],
    }
