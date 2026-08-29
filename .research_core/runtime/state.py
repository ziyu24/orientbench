from __future__ import annotations

from pathlib import Path

from . import authorization
from .storage import load_yaml, write_text_atomic
from .workstreams import checkpoint_errors


SENSITIVE_PERMISSIONS = {"external_write", "resource_expansion", "publish"}


def load_state(root: Path) -> dict:
    return load_yaml(Path(root) / "coordination/STATE.yaml")


def render_now(state: dict) -> str:
    blockers = state.get("blockers", [])
    blocker_text = "无" if not blockers else "；".join(str(item) for item in blockers)
    return (
        "# 当前状态\n\n"
        f"- 阶段：`{state['stage']}`\n"
        f"- 阻塞项：{blocker_text}\n"
        f"- 唯一下一步：`{state['next_action']}`\n"
        "- 状态来源：`coordination/STATE.yaml`\n"
    )


def validate_state(root: Path) -> list[str]:
    state = load_state(root)
    errors: list[str] = []
    if type(state) is not dict or state.get("schema_version") != 1:
        return ["invalid authoritative state"]
    if type(state.get("blockers")) is not list or type(state.get("risks")) is not list:
        errors.append("blockers and risks must be lists")
    permissions = state.get("permissions")
    if type(permissions) is not dict or any(type(value) is not bool for value in permissions.values()):
        errors.append("permissions must be a boolean mapping")
    permission_values = permissions if type(permissions) is dict else {}
    authorizations = state.get("permission_authorizations")
    if type(authorizations) is not dict or set(authorizations) != SENSITIVE_PERMISSIONS:
        errors.append("permission authorizations must cover every sensitive permission")
    else:
        for permission in sorted(SENSITIVE_PERMISSIONS):
            authorization_record = authorizations[permission]
            if permission_values.get(permission) is False:
                if authorization_record is not None:
                    errors.append(f"disabled permission retains authorization: {permission}")
                continue
            if (
                type(authorization_record) is not dict
                or set(authorization_record) != {"ref", "sha256"}
            ):
                errors.append(f"enabled permission lacks authorization: {permission}")
                continue
            try:
                authorization.permission_snapshot(
                    Path(root),
                    permission=permission,
                    authorization_ref=authorization_record.get("ref"),
                    authorization_sha256=authorization_record.get("sha256"),
                    plan=None,
                    online=False,
                )
            except (OSError, UnicodeError, ValueError) as error:
                errors.append(
                    f"permission authorization proof changed: {permission}: {error}"
                )
    errors.extend(checkpoint_errors(root, state.get("active_workstream")))
    expected = render_now(state)
    actual = (Path(root) / "coordination/NOW.md").read_text(encoding="utf-8")
    if actual != expected:
        errors.append("NOW drift")
    return errors


def refresh_now(root: Path) -> None:
    write_text_atomic(
        Path(root) / "coordination/NOW.md",
        render_now(load_state(root)),
        overwrite=True,
    )
