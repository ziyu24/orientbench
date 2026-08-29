"""No-sudo Linux execution guard for a single SERVER_PLAN command.

The guard uses Landlock to make write/delete access an allow-list. When the plan
does not declare network access it also starts the command in a fresh network
namespace. It is a cooperative-agent safety boundary: a process deliberately
started outside the research_core runner is outside this boundary.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


LANDLOCK_CREATE_RULESET_VERSION = 1
LANDLOCK_RULE_PATH_BENEATH = 1
PR_SET_NO_NEW_PRIVS = 38

ACCESS_FS_EXECUTE = 1 << 0
ACCESS_FS_WRITE_FILE = 1 << 1
ACCESS_FS_REMOVE_DIR = 1 << 4
ACCESS_FS_REMOVE_FILE = 1 << 5
ACCESS_FS_MAKE_CHAR = 1 << 6
ACCESS_FS_MAKE_DIR = 1 << 7
ACCESS_FS_MAKE_REG = 1 << 8
ACCESS_FS_MAKE_SOCK = 1 << 9
ACCESS_FS_MAKE_FIFO = 1 << 10
ACCESS_FS_MAKE_BLOCK = 1 << 11
ACCESS_FS_MAKE_SYM = 1 << 12
WRITE_ACCESS = (
    ACCESS_FS_WRITE_FILE
    | ACCESS_FS_REMOVE_DIR
    | ACCESS_FS_REMOVE_FILE
    | ACCESS_FS_MAKE_CHAR
    | ACCESS_FS_MAKE_DIR
    | ACCESS_FS_MAKE_REG
    | ACCESS_FS_MAKE_SOCK
    | ACCESS_FS_MAKE_FIFO
    | ACCESS_FS_MAKE_BLOCK
    | ACCESS_FS_MAKE_SYM
)
CAPABILITIES = [
    "LANDLOCK_ABI_1_WRITE_DELETE_ALLOWLIST",
    "NETWORK_NAMESPACE_WHEN_UNDECLARED",
    "AMBIENT_SECRET_ENV_SCRUB",
    "NO_SUDO_REQUIRED",
]
SECRET_ENV = re.compile(
    r"(?:^|_)(?:TOKEN|PASSWORD|PASSWD|SECRET|PRIVATE_KEY|API_KEY|ACCESS_KEY)(?:$|_)",
    re.IGNORECASE,
)
REQUEST_KEYS = {
    "schema_version",
    "instruction_id",
    "label",
    "repository_root",
    "plan_sha256",
    "authority_sha256",
    "placement",
    "resources",
    "datasets",
    "execution_scope",
    "resolved_repo_write_roots",
    "resolved_host_write_roots",
    "required_permissions",
    "hard_boundaries",
    "command",
}


class RulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class PathBeneathAttr(ctypes.Structure):
    _fields_ = [
        ("allowed_access", ctypes.c_uint64),
        ("parent_fd", ctypes.c_int32),
    ]


def _syscall(number: int, *arguments: object) -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    result = int(libc.syscall(number, *arguments))
    if result < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


def _landlock_abi() -> int:
    if sys.platform != "linux":
        return 0
    libc = ctypes.CDLL(None, use_errno=True)
    result = int(libc.syscall(444, 0, 0, LANDLOCK_CREATE_RULESET_VERSION))
    return result if result >= 0 else 0


def _network_namespace_available() -> bool:
    executable = shutil.which("unshare")
    if executable is None:
        return False
    completed = subprocess.run(
        [executable, "--user", "--map-root-user", "--net", "true"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        shell=False,
    )
    return completed.returncode == 0


def probe() -> dict[str, object]:
    abi = _landlock_abi()
    network = _network_namespace_available() if abi >= 1 else False
    return {
        "schema_version": 1,
        "available": abi >= 1 and network,
        "trust_model": "PLAN_SOURCE_COMMIT_BOUND_COOPERATIVE_AGENT",
        "landlock_abi": abi,
        "network_namespace": network,
        "capabilities": CAPABILITIES,
    }


def _plain_directory(value: str, label: str) -> Path:
    if type(value) is not str or not value:
        raise ValueError(f"invalid {label}")
    path = Path(value)
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ValueError(f"{label} must be an existing plain absolute directory")
    resolved = path.resolve()
    if str(resolved) == resolved.anchor:
        raise ValueError(f"{label} cannot be a filesystem root")
    return resolved


def _load_request(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("guard request must be a plain file")
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("guard request is too large")
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict or set(value) != REQUEST_KEYS or value.get("schema_version") != 2:
        raise ValueError("invalid guard request")
    command = value.get("command")
    if (
        type(command) is not list
        or not command
        or any(type(argument) is not str or not argument for argument in command)
    ):
        raise ValueError("invalid guarded command")
    scope = value.get("execution_scope")
    if type(scope) is not dict or scope.get("secret_read_scopes") != []:
        raise ValueError("no-sudo guard does not authorize secret reads")
    for key in ("resolved_repo_write_roots", "resolved_host_write_roots"):
        roots = value.get(key)
        if type(roots) is not list or any(type(item) is not str for item in roots):
            raise ValueError("invalid resolved write roots")
    return value


def _validate_write_roots(request: dict[str, object]) -> list[Path]:
    repository = _plain_directory(str(request["repository_root"]), "repository root")
    repo_roots = [
        _plain_directory(value, "repository write root")
        for value in request["resolved_repo_write_roots"]
    ]
    for path in repo_roots:
        if path != repository and repository not in path.parents:
            raise ValueError("repository write root escapes repository")
    host_roots = [
        _plain_directory(value, "host write root")
        for value in request["resolved_host_write_roots"]
    ]
    home = Path.home().resolve()
    shared_memory = Path("/dev/shm").resolve()
    for path in host_roots:
        if path in {home, shared_memory}:
            raise ValueError("host write root is too broad")
        if home not in path.parents and shared_memory not in path.parents:
            raise ValueError("host write root must stay below home or /dev/shm")
    return [*repo_roots, *host_roots]


def _apply_landlock(write_roots: list[Path]) -> None:
    if _landlock_abi() < 1:
        raise RuntimeError("Landlock ABI 1 is unavailable")
    ruleset_attr = RulesetAttr(handled_access_fs=WRITE_ACCESS)
    ruleset_fd = _syscall(
        444,
        ctypes.byref(ruleset_attr),
        ctypes.sizeof(ruleset_attr),
        0,
    )
    try:
        for path in write_roots:
            parent_fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                rule = PathBeneathAttr(
                    allowed_access=WRITE_ACCESS,
                    parent_fd=parent_fd,
                )
                _syscall(
                    445,
                    ruleset_fd,
                    LANDLOCK_RULE_PATH_BENEATH,
                    ctypes.byref(rule),
                    0,
                )
            finally:
                os.close(parent_fd)
        libc = ctypes.CDLL(None, use_errno=True)
        if int(libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        _syscall(446, ruleset_fd, 0)
    finally:
        os.close(ruleset_fd)


def _scrub_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key != "SSH_AUTH_SOCK"
        and SECRET_ENV.search(key) is None
    }


def _enter_network_namespace(arguments: list[str]) -> int:
    executable = shutil.which("unshare")
    if executable is None:
        raise RuntimeError("unshare is required when network scope is empty")
    command = [
        executable,
        "--user",
        "--map-root-user",
        "--net",
        "--fork",
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).resolve()),
        "--stage",
        *arguments,
    ]
    return subprocess.run(command, check=False, shell=False).returncode


def run(request_path: Path, command: list[str], *, stage: bool) -> int:
    request = _load_request(request_path)
    if request["command"] != command:
        raise ValueError("guarded command differs from request")
    network_scopes = request["execution_scope"].get("network_scopes")
    if type(network_scopes) is not list:
        raise ValueError("invalid network scope")
    if not network_scopes and not stage:
        return _enter_network_namespace(["--request", str(request_path), "--", *command])
    if not network_scopes and stage:
        fields = Path("/proc/self/uid_map").read_text(encoding="ascii").split()
        if os.getuid() != 0 or len(fields) < 3 or fields[:3] == ["0", "0", "4294967295"]:
            raise RuntimeError("unprivileged user/network namespace was not established")
    write_roots = _validate_write_roots(request)
    _apply_landlock(write_roots)
    environment = _scrub_environment()
    environment["CQC_PROJECT_ROOT"] = str(request["repository_root"])
    host_roots = list(request["resolved_host_write_roots"])
    environment["CQC_HOST_WRITE_ROOTS_JSON"] = json.dumps(host_roots)
    environment["CQC_DATASET_ROUTES_JSON"] = json.dumps(
        request["placement"].get("dataset_routes", []),
        sort_keys=True,
    )
    if len(host_roots) == 1:
        environment["CQC_LARGE_WORKSPACE"] = host_roots[0]
    os.execvpe(command[0], command, environment)
    return 127


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--request", type=Path)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.probe:
        result = probe()
        print(json.dumps(result, sort_keys=True))
        return 0 if result["available"] else 2
    if args.request is None:
        raise ValueError("--request is required")
    command = list(args.arguments)
    if command and command[0] == "--":
        command.pop(0)
    return run(args.request, command, stage=args.stage)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"GUARD_ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
