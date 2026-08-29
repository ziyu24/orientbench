"""Thin project adapter for the local-only cqc-fabric runtime."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import yaml


API_VERSION = "2.1"
COMMAND_FAMILIES = {"local", "gpu", "workspace", "artifacts"}
PUBLIC_RESULT_KEYS = {
    "api_version",
    "profile",
    "dataset_roots",
    "download_root",
    "pth_readme",
    "items",
    "status",
    "device_indexes",
    "target",
    "path",
}
SAFE_ARGUMENT = re.compile(r"[A-Za-z0-9_./:=+,@%-]+\Z")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


def command_arguments(arguments: list[str], *, anchor: str = "LOCAL") -> list[str]:
    if anchor != "LOCAL":
        raise ValueError("cqc-fabric execution is local-only")
    if (
        type(arguments) is not list
        or not arguments
        or arguments[0] not in COMMAND_FAMILIES
        or any(
            type(value) is not str or SAFE_ARGUMENT.fullmatch(value) is None
            for value in arguments
        )
    ):
        raise ValueError("invalid local fabric arguments")
    return [sys.executable, "-m", "cqc_fabric", *arguments]


def _write_exclusive(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, sort_keys=False)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def invoke(
    root: Path,
    arguments: list[str],
    *,
    anchor: str,
    run_id: str,
    runner=subprocess.run,
) -> Path:
    if SAFE_ID.fullmatch(str(run_id)) is None:
        raise ValueError("invalid fabric run id")
    command = command_arguments(arguments, anchor=anchor)
    completed = runner(
        command,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or "local fabric invocation failed")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ValueError("local fabric returned invalid JSON") from error
    if type(result) is not dict or result.get("api_version") != API_VERSION:
        raise ValueError("local fabric API version mismatch")
    public = {key: result[key] for key in PUBLIC_RESULT_KEYS if key in result}
    public["api_version"] = API_VERSION
    target = Path(root) / "coordination/executions" / f"{run_id}.yaml"
    _write_exclusive(target, {"schema_version": 1, "fabric": public})
    return target
