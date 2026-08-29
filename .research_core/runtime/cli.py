from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

from . import (
    dialogue,
    durable_execution,
    execution_issues,
    execution_reviews,
    fabric_adapter,
    handoff,
    large_workspace,
    lessons,
    maintenance,
    mode_track,
    outcome_assessment,
    paper_version,
    peer_governance,
    project_admin,
    project_lock,
    research_execution,
    research_log,
    review,
    stages,
    state,
    supervision,
    user_directives,
    venue_review,
)


def main(argv=None) -> int:
    try:
        return _main(argv)
    except (FileExistsError, FileNotFoundError, OSError, RuntimeError, TypeError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


def _ensure_server_binding(root: Path) -> dict[str, str]:
    """Bootstrap an unbound SERVER worktree without making the user remember a command."""

    try:
        identity = peer_governance.current_worker(root, allow_host_default=False)
    except ValueError as error:
        if str(error) != "worktree-local paper.worker-id is not configured":
            raise
        identity = peer_governance.bind_role(root, "SERVER")
    if identity["role"] != "SERVER":
        raise ValueError("pull-execute requires the SERVER worktree")
    return identity


def _main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="research_core v1.11.3 peer collaboration")
    commands = parser.add_subparsers(dest="command", required=True)
    help_parser = commands.add_parser("help")
    help_parser.add_argument(
        "--section", choices=("all", "features", "config", "commands"), default="all"
    )
    config_parser = commands.add_parser("config")
    config_commands = config_parser.add_subparsers(dest="config_action", required=True)
    config_show = config_commands.add_parser("show")
    config_show.add_argument("--key")
    config_set = config_commands.add_parser("set")
    config_set.add_argument("--key", required=True)
    config_set.add_argument("--value", required=True)
    config_set.add_argument("--reason", required=True)
    config_set.add_argument("--authorization-ref")
    config_set.add_argument("--authorization-sha256")
    track_parser = commands.add_parser("track")
    track_commands = track_parser.add_subparsers(dest="track_action", required=True)
    for track_action in ("preview", "apply"):
        item = track_commands.add_parser(track_action)
        item.add_argument(
            "--to", required=True,
            choices=("PAPER_REPRODUCTION", "CHAT_HANDOFF"),
        )
        item.add_argument("--request-id", required=True)
        if track_action == "apply":
            item.add_argument("--preview-digest", required=True)
            item.add_argument("--confirmation", required=True)
    lock_parser = commands.add_parser("project-lock")
    lock_commands = lock_parser.add_subparsers(dest="project_lock_action", required=True)
    lock_commands.add_parser("status")
    for lock_action in ("lock", "unlock"):
        item = lock_commands.add_parser(lock_action)
        item.add_argument("--reason", required=True)
        if lock_action == "unlock":
            item.add_argument("--authorization-ref", required=True)
            item.add_argument("--authorization-sha256", required=True)
    commands.add_parser("validate-project")
    commands.add_parser("self-test")
    status = commands.add_parser("status")
    status_mode = status.add_mutually_exclusive_group(required=True)
    status_mode.add_argument("--check", action="store_true")
    status_mode.add_argument("--refresh", action="store_true")
    resume = commands.add_parser("resume")
    resume.add_argument("--evidence", action="append", default=[])
    handoff_parser = commands.add_parser("handoff")
    handoff_commands = handoff_parser.add_subparsers(
        dest="handoff_action", required=True
    )
    handoff_record = handoff_commands.add_parser("record")
    handoff_record.add_argument("--to", required=True, choices=("B", "C", "SERVER"))
    handoff_record.add_argument("--summary", required=True)
    handoff_record.add_argument("--instruction")
    handoff_commands.add_parser("verify")

    peer = commands.add_parser("peer")
    peer_commands = peer.add_subparsers(dest="peer_action", required=True)
    peer_commands.add_parser("whoami")
    peer_commands.add_parser("default-show")
    peer_bind = peer_commands.add_parser("bind")
    peer_bind.add_argument("--role", required=True, choices=("B", "C", "SERVER"))
    peer_default = peer_commands.add_parser("default")
    peer_default.add_argument("--role", required=True, choices=("B", "C", "SERVER"))

    dialogue_parser = commands.add_parser("dialogue")
    dialogue_commands = dialogue_parser.add_subparsers(
        dest="dialogue_action", required=True
    )
    dialogue_open = dialogue_commands.add_parser("open")
    dialogue_open.add_argument("--id", required=True)
    dialogue_open.add_argument("--topic", required=True)
    dialogue_open.add_argument(
        "--trigger", required=True, choices=("NORMAL", "CRITICAL", "UNCERTAIN")
    )
    dialogue_open.add_argument("--conflict", action="append", required=True)
    dialogue_post = dialogue_commands.add_parser("post")
    dialogue_post.add_argument("--id", required=True)
    dialogue_post.add_argument("--event", required=True)
    dialogue_post.add_argument(
        "--kind",
        required=True,
        choices=("MESSAGE", "PROPOSAL", "CRITIQUE", "CONCLUSION"),
    )
    dialogue_post.add_argument("--message", required=True)
    dialogue_show = dialogue_commands.add_parser("show")
    dialogue_show.add_argument("--id", required=True)
    dialogue_directive = dialogue_commands.add_parser("directive")
    dialogue_directive.add_argument("--id", required=True)
    dialogue_directive.add_argument("--role", required=True, choices=("B", "C"))
    dialogue_directive.add_argument(
        "--action",
        required=True,
        choices=("DISPATCH_AFTER_DIALOGUE", "CRITIQUE_INHERIT_AND_REPLACE"),
    )
    dialogue_directive.add_argument("--instruction", required=True)
    dialogue_directive.add_argument("--dialogue")
    dialogue_directive.add_argument("--prior-plan")
    dialogue_directive.add_argument("--prior-sha256")
    dialogue_commands.add_parser("sync")

    plan = commands.add_parser("plan")
    plan_commands = plan.add_subparsers(dest="plan_action", required=True)
    plan_validate = plan_commands.add_parser("validate")
    plan_validate.add_argument("--path", required=True)

    dispatch = commands.add_parser("dispatch")
    dispatch_commands = dispatch.add_subparsers(dest="dispatch_action", required=True)
    dispatch_show = dispatch_commands.add_parser("show")
    dispatch_show.add_argument("--recent", type=int, default=10)
    dispatch_history = dispatch_commands.add_parser("history")
    dispatch_history.add_argument("--epoch", required=True, type=int)
    deviation = dispatch_commands.add_parser("deviation")
    deviation.add_argument("--epoch", required=True, type=int)
    deviation.add_argument("--field", action="append", required=True)
    deviation.add_argument("--summary", required=True)
    deviation.add_argument("--action", required=True)
    control = dispatch_commands.add_parser("control")
    control.add_argument("--epoch", required=True, type=int)
    control.add_argument("--action", required=True, choices=("STOP", "CONTINUE"))
    control.add_argument("--instruction", required=True)
    dispatch_commands.add_parser("pull-execute")
    dispatch_claim_status = dispatch_commands.add_parser("claim-status")
    dispatch_claim_status.add_argument("--id", required=True)
    dispatch_claim_status.add_argument("--dispatch-token", required=True)
    activate = dispatch_commands.add_parser("activate")
    activate.add_argument("--plan", required=True)
    activate.add_argument("--replace", action="store_true")
    transition = dispatch_commands.add_parser("transition")
    transition.add_argument(
        "--to",
        required=True,
        choices=("RUNNING", "REPORTED", "ACCEPTED", "KILLED", "CONTESTED", "INCONCLUSIVE"),
    )
    transition.add_argument("--epoch", required=True, type=int)
    resolve = dispatch_commands.add_parser("resolve")
    resolve.add_argument("--epoch", type=int)
    notice = dispatch_commands.add_parser("notice")
    notice.add_argument("--summary", required=True)
    heartbeat = dispatch_commands.add_parser("heartbeat")
    heartbeat.add_argument("--epoch", required=True, type=int)

    fabric = commands.add_parser("fabric")
    fabric.add_argument("--anchor", default="LOCAL", choices=("LOCAL",))
    fabric.add_argument("--run-id", required=True)
    fabric.add_argument("fabric_arguments", nargs=argparse.REMAINDER)

    supervision_parser = commands.add_parser("supervision")
    supervision_commands = supervision_parser.add_subparsers(
        dest="supervision_action", required=True
    )
    supervision_bootstrap = supervision_commands.add_parser("bootstrap")
    supervision_bootstrap.add_argument("--epoch", required=True, type=int)
    supervision_bootstrap.add_argument("--run-id", required=True)
    supervision_status = supervision_commands.add_parser("status")
    supervision_status.add_argument("--run-id", required=True)
    supervision_check = supervision_commands.add_parser("check")
    supervision_check.add_argument("--run-id", required=True)
    supervision_check.add_argument("--observation", type=Path, required=True)
    supervision_check.add_argument("--log", type=Path, required=True)
    supervision_check.add_argument("--metrics", type=Path, required=True)
    supervision_check.add_argument("--checkpoints", type=Path, required=True)
    supervision_history = supervision_commands.add_parser("history")
    supervision_history.add_argument("--run-id", required=True)
    supervision_history.add_argument("--event", required=True)

    directive = commands.add_parser("directive")
    directive_commands = directive.add_subparsers(
        dest="directive_action", required=True
    )
    directive_record = directive_commands.add_parser("record")
    directive_record.add_argument("--request", type=Path, required=True)
    directive_execute = directive_commands.add_parser("execute")
    directive_execute.add_argument("--id", required=True)
    directive_result = directive_commands.add_parser("result")
    directive_result.add_argument("--id", required=True)
    directive_push = directive_commands.add_parser("push")
    directive_push.add_argument("--id", required=True)

    execution = commands.add_parser("execution")
    execution_commands = execution.add_subparsers(
        dest="execution_action", required=True
    )
    execution_status = execution_commands.add_parser("status")
    execution_status.add_argument("--id", required=True)
    execution_completion = execution_commands.add_parser("completion")
    execution_completion.add_argument("--id", required=True)
    execution_recover = execution_commands.add_parser("recover")
    execution_recover.add_argument("--id", required=True)
    execution_stop = execution_commands.add_parser("stop")
    execution_stop.add_argument("--id", required=True)
    execution_publish_abnormal = execution_commands.add_parser("publish-abnormal")
    execution_publish_abnormal.add_argument("--id", required=True)
    execution_review = execution_commands.add_parser("review")
    execution_review.add_argument("--id", required=True)
    execution_review.add_argument(
        "--verdict",
        required=True,
        choices=(
            "ISSUE_NEXT_R_CORRECTION",
            "VERIFIED_CORRECT",
            "CATASTROPHIC_REPORT_REQUIRED",
        ),
    )
    execution_review.add_argument("--summary", required=True)
    execution_review.add_argument("--evidence", action="append", required=True)
    execution_scientific_assess = execution_commands.add_parser("scientific-assess")
    execution_scientific_assess.add_argument("--request", required=True)
    execution_issue_report = execution_commands.add_parser("issue-report")
    execution_issue_report.add_argument("--request", type=Path, required=True)
    execution_issue_list = execution_commands.add_parser("issue-list")
    execution_issue_list.add_argument("--id")
    execution_issue_notice = execution_commands.add_parser("issue-notice")
    execution_issue_notice.add_argument("--issue", required=True)
    execution_issue_notice.add_argument("--summary", required=True)
    execution_issue_ack = execution_commands.add_parser("issue-ack")
    execution_issue_ack.add_argument("--issue", required=True)
    execution_issue_ack.add_argument(
        "--action",
        required=True,
        choices=("REQUEST_BC_REPLAN", "STOP_AND_WAIT_USER"),
    )
    execution_issue_ack.add_argument("--summary", required=True)
    execution_issue_resolve = execution_commands.add_parser("issue-resolve")
    execution_issue_resolve.add_argument("--issue", required=True)
    execution_issue_resolve.add_argument(
        "--verdict", required=True, choices=("RESOLVED", "SUPERSEDED_BY_NEW_PLAN")
    )
    execution_issue_resolve.add_argument("--summary", required=True)

    research = commands.add_parser("research")
    research_commands = research.add_subparsers(
        dest="research_action", required=True
    )
    for action in ("begin", "critique", "block", "adapt"):
        request_command = research_commands.add_parser(action)
        request_command.add_argument("--request", type=Path, required=True)
    research_decision = research_commands.add_parser("decision")
    research_decision.add_argument("--id", required=True)
    research_commands.add_parser("authority-show")
    research_authority = research_commands.add_parser("authority-set")
    research_authority.add_argument(
        "--level", required=True, choices=("MASTER", "DOCTORAL")
    )
    research_authority.add_argument("--authorization-ref", required=True)
    research_authority.add_argument("--authorization-sha256", required=True)

    lessons_parser = commands.add_parser("lessons")
    lessons_commands = lessons_parser.add_subparsers(
        dest="lessons_action", required=True
    )
    lessons_check = lessons_commands.add_parser("check")
    lessons_check.add_argument("--context", type=Path, required=True)
    lessons_check.add_argument("--cache-root", type=Path, required=True)
    lessons_update_preview = lessons_commands.add_parser("update-preview")
    lessons_update_preview.add_argument("--checkout", type=Path, required=True)
    lessons_update_preview.add_argument(
        "--confirm-explicit-user-request", action="store_true", required=True
    )
    lessons_update_apply = lessons_commands.add_parser("update-apply")
    lessons_update_apply.add_argument("--preview", type=Path, required=True)
    lessons_update_apply.add_argument(
        "--confirm-explicit-user-request", action="store_true", required=True
    )
    lessons_failure = lessons_commands.add_parser("failure-record")
    lessons_failure.add_argument("--request", type=Path, required=True)
    lessons_promotion_preview = lessons_commands.add_parser("promotion-preview")
    lessons_promotion_preview.add_argument("--failure", required=True)
    lessons_promotion_apply = lessons_commands.add_parser("promotion-apply")
    lessons_promotion_apply.add_argument("--preview", type=Path, required=True)
    lessons_promotion_apply.add_argument(
        "--shared-checkout", type=Path, required=True
    )
    lessons_promotion_apply.add_argument(
        "--confirm-explicit-user-request", action="store_true", required=True
    )

    workspace_parser = commands.add_parser("workspace")
    workspace_commands = workspace_parser.add_subparsers(
        dest="workspace_action", required=True
    )
    workspace_status = workspace_commands.add_parser("status")
    workspace_status.add_argument("--profile", required=True)
    workspace_expand = workspace_commands.add_parser("expand")
    workspace_expand.add_argument("--profile", required=True)
    workspace_expand.add_argument("--manifest", action="append", required=True)
    workspace_compact = workspace_commands.add_parser("compact")
    workspace_compact.add_argument("--profile", required=True)

    maintenance_parser = commands.add_parser("maintenance")
    maintenance_commands = maintenance_parser.add_subparsers(
        dest="maintenance_action", required=True
    )
    maintenance_preview = maintenance_commands.add_parser("preview")
    maintenance_preview.add_argument("--request", type=Path, required=True)
    maintenance_apply = maintenance_commands.add_parser("apply")
    maintenance_apply.add_argument("--preview", type=Path, required=True)
    maintenance_apply.add_argument(
        "--confirm-explicit-user-request", action="store_true"
    )
    maintenance_show = maintenance_commands.add_parser("show")
    maintenance_show.add_argument("--id", required=True)
    maintenance_index = maintenance_commands.add_parser("index")
    maintenance_index.add_argument("--recent", type=int, default=10)

    paper = commands.add_parser("paper")
    paper_commands = paper.add_subparsers(dest="paper_action", required=True)
    paper_init = paper_commands.add_parser("init")
    paper_init.add_argument("--format", choices=("md", "tex"), default="md")
    paper_bump = paper_commands.add_parser("bump")
    paper_bump.add_argument(
        "--level", choices=("major", "minor", "patch"), required=True
    )
    paper_commands.add_parser("validate")
    paper_commands.add_parser("export-pdf")
    paper_review = paper_commands.add_parser("review-record")
    paper_review.add_argument("--summary", required=True)
    paper_assess = paper_commands.add_parser("assess")
    paper_assess.add_argument("--request", required=True)
    paper_assessment_show = paper_commands.add_parser("assessment-show")
    paper_assessment_show.add_argument("--review", required=True)
    paper_bump_alias = commands.add_parser(
        "paper-bump", description="paper-bump compatibility command"
    )
    paper_bump_alias.add_argument(
        "--level", choices=("major", "minor", "patch"), required=True
    )

    stage = commands.add_parser("stage")
    stage.add_argument("action", choices=("init",))
    stage.add_argument("stage")
    log = commands.add_parser("log")
    log_commands = log.add_subparsers(dest="log_action", required=True)
    recommend = log_commands.add_parser("recommend")
    recommend.add_argument("--summary", required=True)
    recommend.add_argument("--rationale", required=True)
    recommend.add_argument("--uncertainty", required=True)
    recommend.add_argument("--evidence", action="append", default=[])
    recommend.add_argument("--alternative", action="append", default=[])
    recommend.add_argument("--review-role", action="append", default=[])
    recommend.add_argument("--review-conflict", action="append", default=[])
    event = log_commands.add_parser("event")
    event.add_argument("--type", required=True)
    event.add_argument("--summary", required=True)
    event.add_argument("--source", action="append", default=[])
    review_parser = commands.add_parser("review")
    review_commands = review_parser.add_subparsers(dest="review_action", required=True)
    review_recommend = review_commands.add_parser("recommend")
    review_recommend.add_argument("--task", default="")
    review_context = review_commands.add_parser("context")
    review_context.add_argument("--task", required=True)
    review_context.add_argument("--evidence", action="append", default=[])

    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    action = None
    if args.command == "status":
        action = "refresh" if args.refresh else "check"
    elif args.command == "config":
        action = args.config_action
    elif args.command == "project-lock":
        action = args.project_lock_action
    elif args.command == "track":
        action = args.track_action
    elif args.command == "handoff":
        action = args.handoff_action
    project_lock.require_operation(
        root,
        command=args.command,
        action=action,
        key=getattr(args, "key", None),
        value=getattr(args, "value", None),
    )
    if args.command == "help":
        print(json.dumps(
            project_admin.help_overview(root, section=args.section),
            ensure_ascii=False,
            sort_keys=True,
        ))
        return 0
    if args.command == "config":
        result = (
            project_admin.show_config(root, key=args.key)
            if args.config_action == "show"
            else project_admin.set_config(
                root,
                key=args.key,
                value=args.value,
                reason=args.reason,
                authorization_ref=args.authorization_ref,
                authorization_sha256=args.authorization_sha256,
            )
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "project-lock":
        if args.project_lock_action == "status":
            result = project_lock.load(root)
        else:
            result = project_lock.set_state(
                root,
                state="LOCKED" if args.project_lock_action == "lock" else "UNLOCKED",
                reason=args.reason,
                authorization_ref=getattr(args, "authorization_ref", None),
                authorization_sha256=getattr(args, "authorization_sha256", None),
            )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "track":
        result = (
            mode_track.preview(root, args.to, request_id=args.request_id)
            if args.track_action == "preview"
            else mode_track.apply(
                root,
                args.to,
                request_id=args.request_id,
                preview_digest=args.preview_digest,
                confirmation=args.confirmation,
            )
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command in {"validate-project", "self-test"}:
        errors = [*state.validate_state(root), *peer_governance.governance_errors(root)]
        try:
            project_lock.load(root)
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(str(error))
        try:
            lean = large_workspace.lean_usage(root)
            if lean["within_limit"] is not True:
                errors.append(
                    f"project working tree exceeds {lean['limit_bytes']} bytes: "
                    f"{lean['size_bytes']}"
                )
            maintenance.compact_view(root)
            if (root / "paper").exists():
                paper_version.validate(root)
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(str(error))
        if errors:
            print("\n".join(f"ERROR: {item}" for item in errors))
            return 1
        print("VALID")
        return 0
    if args.command == "status":
        if args.refresh:
            state.refresh_now(root)
            print("VALID")
            return 0
        errors = state.validate_state(root)
        if errors:
            print("\n".join(f"ERROR: {item}" for item in errors))
            return 1
        print("VALID")
        return 0
    if args.command == "resume":
        print(json.dumps(handoff.resume_bundle(root, evidence_refs=args.evidence), ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "handoff":
        result = (
            handoff.record_requirement(
                root,
                to_role=args.to,
                summary=args.summary,
                related_instruction_id=args.instruction,
            )
            if args.handoff_action == "record"
            else handoff.verify_git_finalization(root)
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "peer":
        if args.peer_action == "whoami":
            identity = peer_governance.current_worker(root)
        elif args.peer_action == "default-show":
            identity = peer_governance.host_default_worker(root)
        elif args.peer_action == "default":
            identity = peer_governance.configure_default_role(root, args.role)
        else:
            identity = peer_governance.bind_role(root, args.role)
        print(json.dumps(identity, sort_keys=True))
        return 0
    if args.command == "dialogue":
        if args.dialogue_action == "open":
            result = dialogue.open_dialogue(
                root, args.id, args.topic, args.trigger, args.conflict
            ).relative_to(root).as_posix()
        elif args.dialogue_action == "post":
            result = dialogue.post_event(
                root, args.id, args.event, args.kind, args.message
            ).relative_to(root).as_posix()
        elif args.dialogue_action == "show":
            result = dialogue.dialogue_status(root, args.id)
        elif args.dialogue_action == "directive":
            result = dialogue.record_user_directive(
                root,
                args.id,
                designated_role=args.role,
                action=args.action,
                user_instruction=args.instruction,
                dialogue_id=args.dialogue,
                prior_plan_path=args.prior_plan,
                prior_plan_sha256=args.prior_sha256,
            ).relative_to(root).as_posix()
        else:
            result = dialogue.sync_dialogue(root)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "plan":
        document = peer_governance.validate_plan(root, args.path)
        print(json.dumps(document, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "dispatch":
        if args.dispatch_action == "show":
            print(json.dumps(
                peer_governance.compact_dispatch_view(root, recent=args.recent),
                ensure_ascii=True,
                sort_keys=True,
            ))
        elif args.dispatch_action == "history":
            print(json.dumps(
                peer_governance.load_history_record(root, args.epoch),
                ensure_ascii=True,
                sort_keys=True,
            ))
        elif args.dispatch_action == "deviation":
            print(peer_governance.record_deviation(
                root,
                epoch=args.epoch,
                fields=args.field,
                summary=args.summary,
                action=args.action,
            ).relative_to(root).as_posix())
        elif args.dispatch_action == "control":
            print(peer_governance.record_user_control(
                root,
                epoch=args.epoch,
                action=args.action,
                instruction=args.instruction,
            ).relative_to(root).as_posix())
        elif args.dispatch_action == "pull-execute":
            _ensure_server_binding(root)
            intent = durable_execution.dispatch_intent(root)
            summary = intent["execution_summary"]
            if type(summary) is not str or not summary or len(summary) > 50:
                raise ValueError("execution summary must contain at most 50 characters")
            print(f"执行概述：{summary}", file=sys.stderr)
            print(json.dumps(
                durable_execution.pull_and_execute(root),
                ensure_ascii=True,
                sort_keys=True,
            ))
        elif args.dispatch_action == "claim-status":
            _ensure_server_binding(root)
            print(json.dumps(
                durable_execution.claim_status(
                    root, args.id, args.dispatch_token
                ),
                ensure_ascii=True,
                sort_keys=True,
            ))
        elif args.dispatch_action == "activate":
            print(json.dumps(peer_governance.activate_plan(
                root, args.plan, replace=args.replace
            ), ensure_ascii=True, sort_keys=True))
        elif args.dispatch_action == "transition":
            print(json.dumps(peer_governance.transition_dispatch(
                root, args.to, epoch=args.epoch
            ), ensure_ascii=True, sort_keys=True))
        elif args.dispatch_action == "resolve":
            path = peer_governance.resolve_active_plan(root, epoch=args.epoch)
            active = peer_governance.load_dispatch(root)["active"]
            print(json.dumps({
                "plan_path": path.relative_to(root).as_posix(),
                "plan_sha256": active["plan_sha256"],
                "epoch": active["epoch"],
            }, sort_keys=True))
        elif args.dispatch_action == "notice":
            print(peer_governance.record_user_notice(
                root, args.summary
            ).relative_to(root).as_posix())
        else:
            result = peer_governance.heartbeat_dispatch(root, args.epoch)
            print(json.dumps(result, ensure_ascii=True, sort_keys=True))
            if result["status"] == "MUST_STOP":
                return 3
        return 0
    if args.command == "fabric":
        arguments = list(args.fabric_arguments)
        if arguments and arguments[0] == "--":
            arguments.pop(0)
        path = fabric_adapter.invoke(
            root,
            arguments,
            anchor=args.anchor,
            run_id=args.run_id,
        )
        print(path.relative_to(root).as_posix())
        return 0
    if args.command == "supervision":
        if args.supervision_action == "bootstrap":
            result = supervision.bootstrap(
                root, epoch=args.epoch, run_id=args.run_id
            )
        elif args.supervision_action == "status":
            result = supervision.load(root, run_id=args.run_id)
        elif args.supervision_action == "history":
            result = supervision.history(
                root, run_id=args.run_id, event_id=args.event
            )
        else:
            observation = yaml.safe_load(
                args.observation.read_text(encoding="utf-8")
            )
            metrics = yaml.safe_load(args.metrics.read_text(encoding="utf-8"))
            checkpoints = yaml.safe_load(
                args.checkpoints.read_text(encoding="utf-8")
            )
            result = supervision.check(
                root,
                run_id=args.run_id,
                observation=observation,
                log_path=args.log,
                metrics=metrics,
                checkpoints=checkpoints,
            )
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "directive":
        if args.directive_action == "record":
            request = yaml.safe_load(args.request.read_text(encoding="utf-8"))
            if type(request) is not dict:
                raise ValueError("user directive request must be a mapping")
            result = user_directives.record(root, **request)
        elif args.directive_action == "execute":
            result = user_directives.execute(root, directive_id=args.id)
        elif args.directive_action == "result":
            result = user_directives.load_result(root, args.id)
        else:
            result = user_directives.publish(
                root,
                directive_id=args.id,
            )
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "execution":
        if args.execution_action == "status":
            result = durable_execution.load_journal(root, args.id)
        elif args.execution_action == "completion":
            result = durable_execution.completion_receipt(root, args.id)
        elif args.execution_action == "recover":
            result = durable_execution.recover(root, args.id)
        elif args.execution_action == "stop":
            result = durable_execution.request_stop(root, args.id)
        elif args.execution_action == "publish-abnormal":
            result = durable_execution.publish_abnormal(root, args.id)
        elif args.execution_action == "review":
            result = execution_reviews.record(
                root,
                instruction_id=args.id,
                verdict=args.verdict,
                summary=args.summary,
                evidence_refs=args.evidence,
            )
        elif args.execution_action == "scientific-assess":
            request = outcome_assessment.load_request(root, args.request)
            result = outcome_assessment.record(root, request)
        elif args.execution_action == "issue-report":
            request = yaml.safe_load(args.request.read_text(encoding="utf-8"))
            if type(request) is not dict:
                raise ValueError("execution issue request must be a mapping")
            result = execution_issues.report(root, request)
        elif args.execution_action == "issue-list":
            result = execution_issues.list_issues(root, args.id)
        elif args.execution_action == "issue-notice":
            result = execution_issues.record_notice(root, args.issue, args.summary)
        elif args.execution_action == "issue-ack":
            result = execution_issues.acknowledge(
                root, args.issue, args.action, args.summary
            )
        else:
            result = execution_issues.resolve(
                root, args.issue, args.verdict, args.summary
            )
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "research":
        if args.research_action in {"begin", "critique", "block", "adapt"}:
            request = yaml.safe_load(args.request.read_text(encoding="utf-8"))
            if type(request) is not dict:
                raise ValueError("research execution request must be a mapping")
            operations = {
                "begin": research_execution.begin_decision,
                "critique": research_execution.critique_inherit,
                "block": research_execution.record_final_blocker,
                "adapt": research_execution.record_adaptation,
            }
            result = operations[args.research_action](root, **request)
        elif args.research_action == "decision":
            result = research_execution.load_decision(root, args.id)
        elif args.research_action == "authority-show":
            result = research_execution.load_authority(root)
        else:
            result = research_execution.set_authority(
                root,
                level=args.level,
                authorization_ref=args.authorization_ref,
                authorization_sha256=args.authorization_sha256,
            )
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "lessons":
        def rooted(path: Path) -> Path:
            return path if path.is_absolute() else root / path

        if args.lessons_action == "check":
            context = lessons._read_input_mapping(
                rooted(args.context),
                label="lessons context",
                max_bytes=64 * 1024,
            )
            if not set(context).issubset(lessons._CONTEXT_DIMENSIONS):
                raise ValueError("lessons context contains undeclared dimensions")
            lessons.context_fingerprint(context)
            result = lessons.check(
                root=root,
                context=context,
                cache_root=rooted(args.cache_root),
            )
        elif args.lessons_action == "update-preview":
            result = lessons.update_preview(
                root=root,
                candidate_checkout=rooted(args.checkout),
                explicit_user_request=args.confirm_explicit_user_request,
            )
        elif args.lessons_action == "update-apply":
            result = lessons.apply_update(
                root=root,
                preview_path=rooted(args.preview),
                explicit_user_request=args.confirm_explicit_user_request,
            )
        elif args.lessons_action == "failure-record":
            request = lessons._read_input_mapping(
                rooted(args.request),
                label="lessons failure request",
                max_bytes=64 * 1024,
            )
            result = lessons.record_failure(root=root, request=request)
        elif args.lessons_action == "promotion-preview":
            result = lessons.promotion_preview(
                root=root,
                failure_id=args.failure,
            )
        else:
            result = lessons.apply_promotion(
                root=root,
                preview_path=rooted(args.preview),
                shared_checkout=rooted(args.shared_checkout),
                explicit_user_request=args.confirm_explicit_user_request,
            )
        if isinstance(result, Path):
            result = result.relative_to(root).as_posix()
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "workspace":
        if args.workspace_action == "status":
            result = large_workspace.status(root, profile=args.profile)
        elif args.workspace_action == "expand":
            result = large_workspace.expand(
                root, profile=args.profile, manifests=args.manifest
            )
        else:
            result = large_workspace.compact(root, profile=args.profile)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "maintenance":
        if args.maintenance_action == "preview":
            result = maintenance.preview(root, args.request).relative_to(root).as_posix()
        elif args.maintenance_action == "apply":
            result = maintenance.apply(
                root,
                args.preview,
                explicit_user_request=args.confirm_explicit_user_request,
            ).relative_to(root).as_posix()
        elif args.maintenance_action == "show":
            result = maintenance.show(root, args.id)
        else:
            result = maintenance.compact_view(root, recent=args.recent)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "paper":
        if args.paper_action == "init":
            result = paper_version.initialize(root, source_format=args.format)
        elif args.paper_action == "bump":
            result = paper_version.bump(root, level=args.level)
        elif args.paper_action == "validate":
            result = paper_version.validate(root)
        elif args.paper_action == "export-pdf":
            result = paper_version.export_pdf(root)
        elif args.paper_action == "assess":
            request = venue_review.load_assessment_request(root, args.request)
            path = venue_review.record_assessment(root, request)
            result = {
                "review_path": path.relative_to(root).as_posix(),
                "review_version": path.stem.removeprefix("review-"),
            }
        elif args.paper_action == "assessment-show":
            result = venue_review.load_assessment(root, args.review)
        else:
            result = paper_version.record_review(
                root, summary=args.summary
            ).relative_to(root).as_posix()
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    if args.command == "paper-bump":
        print(json.dumps(
            paper_version.bump(root, level=args.level),
            ensure_ascii=True,
            sort_keys=True,
        ))
        return 0
    if args.command == "stage":
        print(stages.initialize(root, args.stage).relative_to(root).as_posix())
        return 0
    if args.command == "log":
        if args.log_action == "recommend":
            print(research_log.append_recommendation(
                root,
                summary=args.summary,
                rationale=args.rationale,
                uncertainty=args.uncertainty,
                evidence=args.evidence,
                alternatives=args.alternative,
                review_roles=[review.parse_role(value)["name"] for value in args.review_role],
                unresolved_conflicts=args.review_conflict,
            ))
        else:
            print(research_log.append_event(root, event_type=args.type, summary=args.summary, source_refs=args.source))
        return 0
    if args.review_action == "recommend":
        recommendation = review.recommendation(args.task, state.load_state(root))
        if recommendation is not None:
            print(recommendation)
        return 0
    print(json.dumps(review.context_bundle(root, task=args.task, evidence_refs=args.evidence), ensure_ascii=True, sort_keys=True))
    return 0
