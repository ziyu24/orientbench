#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


class GovernanceError(ValueError):
    pass


ACTORS = ("B", "C")
EXPECTED_WORKERS = {
    "peer-b-primary": "B",
    "peer-c-primary": "C",
    "server-primary": "SERVER",
}


def fail(message):
    raise GovernanceError(message)


def require(condition, message):
    if not condition:
        fail(message)


def actor_roots(actor):
    return {
        "memo": f"dis/{actor}.md",
        "plan_root": f"dis/plans/{actor}",
        "request_root": f"dis/review_requests/{actor}",
        "review_root": f"dis/reviews/{actor}",
        "contest_root": f"dis/contests/{actor}",
        "stop_request_root": f"dis/stop_requests/{actor}",
    }


def contract_roots(actor):
    roots = actor_roots(actor)
    return {
        "memo": roots["memo"],
        "plans": roots["plan_root"],
        "review_requests": roots["request_root"],
        "reviews": roots["review_root"],
        "contests": roots["contest_root"],
        "stop_requests": roots["stop_request_root"],
    }


def validate_documents(contract, workers, coordination):
    require(contract.get("schema_version") == 1, "unsupported role contract schema")
    require(workers.get("schema_version") == 1, "unsupported worker registry schema")
    require(coordination.get("schema_version") == 4, "unsupported coordination schema")
    project_ids = {contract.get("project_id"), workers.get("project_id"), coordination.get("project_id")}
    require(project_ids == {"OrientBench"}, "project_id mismatch")

    selector = workers.get("selector", {})
    require(selector.get("git_config_key") == "paper.worker-id", "wrong selector key")
    require(selector.get("scope") == "repo_local", "selector must be repo-local")
    require(selector.get("missing_behavior") == "fail_closed", "missing selector must fail closed")
    registry = workers.get("workers", {})
    for worker_id, role in EXPECTED_WORKERS.items():
        require(worker_id in registry, f"missing worker {worker_id}")
        require(registry[worker_id].get("role") == role, f"wrong role for {worker_id}")
        require(registry[worker_id].get("status") == "active", f"inactive worker {worker_id}")

    actors = contract.get("actors", {})
    require(set(actors) == set(ACTORS), "role contract actors must be exactly B and C")
    require(actors["B"].get("capabilities") == actors["C"].get("capabilities"), "B/C capabilities are asymmetric")
    require(len(actors["B"].get("capabilities", [])) > 0, "empty actor capabilities")
    for actor, peer in (("B", "C"), ("C", "B")):
        require(actors[actor].get("owned_roots") == contract_roots(actor), f"wrong owned roots for {actor}")
        require(actors[actor].get("peer_read_only_roots") == contract_roots(peer), f"wrong peer roots for {actor}")
    visibility = contract.get("visibility", {})
    require(visibility.get("role_rules_mutually_visible") is True, "role rules must be mutually visible")
    require(visibility.get("blind_review_hides_governance") is False, "blind review cannot hide governance")
    for name in ("AGENTS.md", "CLAUDE.md", "CC_PROMPT.md"):
        require(contract.get("client_entrypoints", {}).get(name, {}).get("default_actor") is None, f"{name} binds an actor")

    require(coordination.get("governance_mode") == "B_C_PEER_EQUAL", "wrong governance mode")
    require(coordination.get("single_active_dispatch") is True, "multiple dispatches are forbidden")
    coord_actors = coordination.get("actors", {})
    require(set(coord_actors) == set(ACTORS), "coordination actors must be exactly B and C")
    for actor in ACTORS:
        require(coord_actors[actor] == actor_roots(actor), f"coordination roots are asymmetric for {actor}")
    risk = coordination.get("risk_policy", {})
    require(risk.get("L0", {}).get("configured") is True, "L0 policy must be configured")
    require(risk.get("L2", {}).get("requires_user_authorization") is True, "L2 must require user authorization")
    return True


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot load {path}: {exc}")


def validate_active(root, coordination):
    active = coordination.get("active_dispatch")
    active_path = root / "dis" / "sug.md"
    if active is None:
        require(not active_path.exists(), "idle coordination must not retain dis/sug.md")
        return
    required = {
        "dispatch_id", "plan_id", "initiator", "activated_by", "plan_path",
        "plan_commit_sha", "plan_blob_oid", "plan_sha256", "active_plan_path",
        "active_sha256", "risk_class", "server_report_path", "status",
        "resource_scope", "conflict_keys", "user_authorization"
    }
    require(required.issubset(active), "active dispatch is missing required fields")
    initiator = active.get("initiator")
    require(initiator in ACTORS and active.get("activated_by") in ACTORS, "invalid active actor")
    expected = f"dis/plans/{initiator}/{active['plan_id']}/sug.md"
    require(active.get("plan_path") == expected, "active plan path does not belong to initiator")
    require(active.get("active_plan_path") == "dis/sug.md", "wrong active mirror path")
    require(active.get("status") == "DISPATCHED", "active record must remain immutable DISPATCHED")
    require(active_path.is_file(), "active dispatch lacks dis/sug.md mirror")
    digest = hashlib.sha256(active_path.read_bytes()).hexdigest()
    require(digest == active.get("plan_sha256") == active.get("active_sha256"), "active plan hash mismatch")
    report = active.get("server_report_path", "")
    require(report.startswith("dis/server_reports/") and active["dispatch_id"] in report, "invalid server report path")
    risk_class = active.get("risk_class")
    require(risk_class in ("L0", "L1", "L2"), "invalid risk class")
    if risk_class in ("L0", "L1"):
        require(coordination["risk_policy"].get(risk_class, {}).get("configured") is True, f"{risk_class} is not configured")
    else:
        auth = active.get("user_authorization", {})
        require(auth.get("required") is True and auth.get("status") == "granted" and auth.get("reference"), "L2 lacks user authorization")
    require(bool(active.get("conflict_keys")), "active dispatch lacks conflict keys")


def validate_repository(root, check_local_worker=False):
    root = root.resolve()
    gov = root / "dis" / "governance"
    contract = load_json(gov / "role_contract.json")
    workers = load_json(gov / "workers.json")
    coordination = load_json(root / "dis" / "coordination.json")
    validate_documents(contract, workers, coordination)
    validate_active(root, coordination)

    required = [
        root / "AGENTS.md", root / "CLAUDE.md", root / "CC_PROMPT.md",
        root / "dis" / "PEER_START.md", root / "dis" / "collaboration_protocol.md",
        root / "dis" / "B.md", root / "dis" / "C.md",
        gov / "roles" / "B.md", gov / "roles" / "C.md", gov / "roles" / "SERVER.md",
    ]
    require(all(path.is_file() for path in required), "required governance entrypoint is missing")
    for path in (root / "AGENTS.md", root / "CLAUDE.md", root / "CC_PROMPT.md", root / "dis" / "PEER_START.md"):
        require("paper.worker-id" in path.read_text(encoding="utf-8"), f"{path.name} lacks worker selector")
    protocol = (root / "dis" / "collaboration_protocol.md").read_text(encoding="utf-8")
    require("B/C 同级" in protocol, "peer protocol marker missing")
    require("C 维护 active 合同与共享状态" not in protocol, "legacy C-only authority remains active")

    archive = root / "dis" / "sug" / "orientbench-c-r020-measurement-validity-20260811-server-returned.md"
    require(archive.is_file(), "legacy r020 plan archive missing")
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == "74ef9c65eb660aa36fa6c7f5d78043a4f68540bff3d9903a9303ad6603c9abf5", "legacy r020 plan archive changed")

    if check_local_worker:
        result = subprocess.run(
            ["git", "-C", str(root), "config", "--local", "--get", "paper.worker-id"],
            capture_output=True, text=True, encoding="utf-8"
        )
        worker_id = result.stdout.strip() if result.returncode == 0 else ""
        require(worker_id in workers["workers"], "local paper.worker-id is missing or unknown")
        require(workers["workers"][worker_id].get("status") == "active", "local worker is inactive")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--check-local-worker", action="store_true")
    args = parser.parse_args()
    try:
        validate_repository(args.root, check_local_worker=args.check_local_worker)
    except GovernanceError as exc:
        print(f"PEER_GOVERNANCE_ERROR: {exc}")
        return 1
    print("PEER_GOVERNANCE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
