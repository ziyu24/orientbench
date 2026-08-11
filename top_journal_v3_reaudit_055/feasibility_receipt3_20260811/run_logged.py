#!/usr/bin/env python3
"""Run one receipt command and retain truthful stdout/stderr/timing metadata."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--inputs", default="")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise SystemExit("missing command")

    logs = args.runtime / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    stdout_path = logs / f"{args.phase}.stdout"
    stderr_path = logs / f"{args.phase}.stderr"
    started = now()
    result = subprocess.run(command, cwd=args.cwd, env=os.environ.copy(), capture_output=True)
    ended = now()
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    event = {
        "phase": args.phase,
        "command": command,
        "cwd": str(args.cwd.resolve()),
        "inputs": args.inputs,
        "started_at": started,
        "ended_at": ended,
        "exit_code": result.returncode,
        "stdout_path": str(stdout_path.relative_to(args.runtime)),
        "stdout_bytes": len(result.stdout),
        "stdout_sha256": sha256(result.stdout),
        "stderr_path": str(stderr_path.relative_to(args.runtime)),
        "stderr_bytes": len(result.stderr),
        "stderr_sha256": sha256(result.stderr),
    }
    ledger = args.runtime / "execution_events.jsonl"
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(event, ensure_ascii=False, sort_keys=True))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
