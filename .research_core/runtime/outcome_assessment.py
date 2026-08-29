"""B/C-only scientific assessment of a machine-verified SERVER completion."""

from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any
from urllib.parse import urlsplit

import yaml

from . import journal_benchmarks, research_execution


INSTRUCTION_ID = re.compile(r"r(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\Z")
RECEIPT_FILE = re.compile(r"(B|C|DOCTORAL)-([0-9]{3,})\.yaml\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
ASSESSMENT_PATH = "build/research-outcome-assessment.yaml"
MAX_EVIDENCE_FILE_BYTES = 8 * 1024 * 1024
MAX_EVIDENCE_TOTAL_BYTES = 16 * 1024 * 1024
REQUEST_KEYS = {
    "instruction_id",
    "result_ref",
    "result_sha256",
    "evidence_refs",
    "premise_check",
    "confirmed_facts",
    "reasonable_inferences",
    "personal_judgments",
    "currently_unverifiable",
    "disagreement",
    "venue_assessment",
    "comparable_papers",
    "strongest_rejection_case",
    "gap_to_goal",
    "next_action",
    "next_scientific_question",
    "model_recommendation",
    "concise_summary",
}
RECEIPT_KEYS = REQUEST_KEYS | {
    "schema_version",
    "assessment_id",
    "reviewed_by",
    "result_commit",
    "evidence",
    "reviewed_at",
}
FACT_KEYS = {"claim", "evidence_refs"}
INFERENCE_KEYS = {"claim", "basis_refs"}
DISAGREEMENT_KEYS = {"position", "reasons", "counterexamples_or_risks"}
VENUE_INPUT_KEYS = {
    "ranking_system",
    "ranking_edition",
    "reference_journal",
    "benchmark_zone",
    "benchmark_zone_label",
    "level_vs_tgrs",
    "goal_reached",
}
VENUE_DERIVED_KEYS = {
    "reference_journal_short_name",
    "partition_basis",
    "partition_category",
    "partition_source_url",
    "scope_source_url",
    "verified_at",
    "project_level",
}
VENUE_KEYS = VENUE_INPUT_KEYS | VENUE_DERIVED_KEYS
PAPER_KEYS = {"title", "venue", "year", "doi_or_url", "verified_at", "comparison"}
MODEL_KEYS = {"action", "reason", "expected_benefit", "token_tradeoff"}
SUMMARY_KEYS = {"conclusion", "key_evidence", "venue_gap", "unique_next_action"}
LEVELS = {"BELOW_TGRS", "TGRS_LEVEL", "ABOVE_TGRS"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _root(value: Path) -> Path:
    root = Path(value).resolve()
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=root, check=True,
        capture_output=True, text=True, encoding="utf-8", shell=False,
    )
    if Path(completed.stdout.strip()).resolve() != root:
        raise ValueError("scientific assessment requires the exact project root")
    return root


def _actor(root: Path) -> str:
    return research_execution._actor_role(root)


def _require_https_origin(root: Path) -> str:
    completed = subprocess.run(
        ["git", "remote", "get-url", "--push", "origin"],
        cwd=root, capture_output=True, text=True, encoding="utf-8",
        check=False, shell=False,
    )
    value = completed.stdout.strip()
    if completed.returncode != 0 or re.fullmatch(r"https://[^\s]+", value) is None:
        raise ValueError("production Git origin must use HTTPS")
    return value


def _string(value: object, label: str, *, limit: int = 4096) -> str:
    if type(value) is not str or len(value.strip()) < 8:
        raise ValueError(f"invalid {label}")
    if len(value.encode("utf-8")) > limit:
        raise ValueError(f"oversize {label}")
    return value.strip()


def _strings(value: object, label: str, *, empty: bool = False) -> list[str]:
    if type(value) is not list or (not empty and not value) or len(value) > 32:
        raise ValueError(f"invalid {label}")
    result = [_string(item, label) for item in value]
    if len(result) != len(set(item.casefold() for item in result)):
        raise ValueError(f"duplicate {label}")
    return result


def _relative(value: object, label: str) -> str:
    if type(value) is not str or not value or "\\" in value or "\x00" in value:
        raise ValueError(f"invalid {label}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise ValueError(f"invalid {label}")
    return pure.as_posix()


def _url(value: object, label: str) -> str:
    value = _string(value, label, limit=2048)
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid {label} URL")
    return value


def _date(value: object, label: str) -> str:
    if type(value) is not str:
        raise ValueError(f"invalid {label}")
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError as error:
        raise ValueError(f"invalid {label}") from error
    return value


def _safe_evidence(instruction_id: str, value: object) -> str:
    relative = _relative(value, "assessment evidence")
    parts = PurePosixPath(relative).parts
    if not (
        parts[:3] == ("coordination", "executions", instruction_id)
        or parts[:3] == ("coordination", "instructions", instruction_id)
        or parts[:2] == ("runs", instruction_id)
    ):
        raise ValueError("assessment evidence is not bound to the completed instruction")
    return relative


def load_request(root: Path, relative: str) -> dict[str, Any]:
    root = _root(root)
    if relative != ASSESSMENT_PATH:
        raise ValueError(f"request must be {ASSESSMENT_PATH}")
    path = Path(root) / relative
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1048576:
        raise ValueError("scientific assessment request is unavailable")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _validate_request(root, value)


def _validate_request(root: Path, value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != REQUEST_KEYS:
        raise ValueError("invalid scientific assessment fields")
    instruction_id = value["instruction_id"]
    if type(instruction_id) is not str or INSTRUCTION_ID.fullmatch(instruction_id) is None:
        raise ValueError("invalid scientific assessment instruction")
    expected_result = f"coordination/executions/{instruction_id}/RESULT.yaml"
    if value["result_ref"] != expected_result or SHA256.fullmatch(str(value["result_sha256"])) is None:
        raise ValueError("scientific assessment must bind the exact RESULT.yaml")
    refs = value["evidence_refs"]
    if type(refs) is not list or not refs or len(refs) != len(set(refs)) or len(refs) > 64:
        raise ValueError("invalid scientific assessment evidence refs")
    refs = [_safe_evidence(instruction_id, item) for item in refs]
    if expected_result not in refs:
        raise ValueError("scientific assessment evidence must include RESULT.yaml")
    _string(value["premise_check"], "premise check")
    facts = value["confirmed_facts"]
    if type(facts) is not list or not facts or len(facts) > 32:
        raise ValueError("confirmed facts are required")
    for item in facts:
        if type(item) is not dict or set(item) != FACT_KEYS:
            raise ValueError("invalid confirmed fact")
        _string(item["claim"], "confirmed fact")
        cited = [_safe_evidence(instruction_id, ref) for ref in item["evidence_refs"]]
        if not cited or any(ref not in refs for ref in cited):
            raise ValueError("confirmed fact lacks declared evidence")
    inferences = value["reasonable_inferences"]
    if type(inferences) is not list or not inferences or len(inferences) > 32:
        raise ValueError("reasonable inferences are required")
    for item in inferences:
        if type(item) is not dict or set(item) != INFERENCE_KEYS:
            raise ValueError("invalid reasonable inference")
        _string(item["claim"], "reasonable inference")
        cited = [_safe_evidence(instruction_id, ref) for ref in item["basis_refs"]]
        if not cited or any(ref not in refs for ref in cited):
            raise ValueError("reasonable inference lacks declared basis")
    _strings(value["personal_judgments"], "personal judgments")
    _strings(value["currently_unverifiable"], "currently unverifiable", empty=True)
    disagreement = value["disagreement"]
    if type(disagreement) is not dict or set(disagreement) != DISAGREEMENT_KEYS:
        raise ValueError("invalid disagreement analysis")
    _string(disagreement["position"], "disagreement position")
    _strings(disagreement["reasons"], "disagreement reasons")
    _strings(disagreement["counterexamples_or_risks"], "counterexamples or risks")
    venue = value["venue_assessment"]
    venue_fields = set(venue) if type(venue) is dict else set()
    if type(venue) is not dict or (
        venue_fields != VENUE_INPUT_KEYS and venue_fields != VENUE_KEYS
    ):
        raise ValueError("invalid venue assessment")
    if venue["ranking_system"] != "CAS_JOURNAL_PARTITION" or venue["ranking_edition"] != "2025_FINAL":
        raise ValueError("venue assessment must use the final CAS 2025 edition")
    selected = journal_benchmarks.validate_selection(
        root,
        venue.get("benchmark_zone"),
        venue.get("benchmark_zone_label"),
        venue.get("reference_journal"),
    )
    normalized_venue = {
        **{key: venue[key] for key in VENUE_INPUT_KEYS},
        "reference_journal": selected["full_name"],
        "reference_journal_short_name": selected["short_name"],
        "partition_basis": selected["official_partition"]["basis"],
        "partition_category": selected["official_partition"]["category"],
        "partition_source_url": selected["partition_source_url"],
        "scope_source_url": selected["scope_source_url"],
        "verified_at": selected["verified_at"],
        "project_level": selected["project_level"],
    }
    if venue_fields == VENUE_KEYS and venue != normalized_venue:
        raise ValueError("stored venue assessment differs from the built-in journal library")
    if venue["level_vs_tgrs"] not in LEVELS or type(venue["goal_reached"]) is not bool:
        raise ValueError("invalid TGRS benchmark assessment")
    papers = value["comparable_papers"]
    if type(papers) is not list or not papers or len(papers) > 5:
        raise ValueError("one to five comparable papers are required")
    for paper in papers:
        if type(paper) is not dict or set(paper) != PAPER_KEYS:
            raise ValueError("invalid comparable paper")
        _string(paper["title"], "paper title", limit=512)
        if (
            type(paper["venue"]) is not str
            or not paper["venue"].strip()
            or len(paper["venue"].encode("utf-8")) > 160
        ):
            raise ValueError("invalid paper venue")
        if type(paper["year"]) is not int or not 1900 <= paper["year"] <= 2100:
            raise ValueError("invalid paper year")
        _url(paper["doi_or_url"], "paper DOI or source")
        _date(paper["verified_at"], "paper verification date")
        _string(paper["comparison"], "paper comparison")
    if not any(
        journal_benchmarks.matches_selected_journal(selected, paper["venue"])
        for paper in papers
    ):
        raise ValueError(
            "reference journal must match a concrete comparable paper venue"
        )
    _string(value["strongest_rejection_case"], "strongest rejection case")
    _string(value["gap_to_goal"], "gap to goal")
    action = value["next_action"]
    level = venue["level_vs_tgrs"]
    reached = venue["goal_reached"]
    if selected["benchmark_zone"] > 1 and (level != "BELOW_TGRS" or reached):
        raise ValueError("zone two through four are current-level references and must continue")
    if selected["benchmark_zone"] == 1 and (level == "BELOW_TGRS" or not reached):
        raise ValueError("zone-one level must be a goal-reached candidate")
    if level == "BELOW_TGRS" and (reached or action != "CONTINUE_WITH_NEXT_R"):
        raise ValueError("below-TGRS work must continue with the next r instruction")
    if reached and (level == "BELOW_TGRS" or action != "GOAL_REACHED_CANDIDATE"):
        raise ValueError("goal reached assessment is inconsistent")
    if not reached and action != "CONTINUE_WITH_NEXT_R":
        raise ValueError("unfinished research must continue with the next r instruction")
    _string(value["next_scientific_question"], "next scientific question")
    model = value["model_recommendation"]
    if type(model) is not dict or set(model) != MODEL_KEYS or model["action"] not in {
        "KEEP_CURRENT", "SUGGEST_HIGHER_MODEL"
    }:
        raise ValueError("invalid model recommendation")
    for field in MODEL_KEYS - {"action"}:
        _string(model[field], f"model {field}")
    summary = value["concise_summary"]
    if type(summary) is not dict or set(summary) != SUMMARY_KEYS:
        raise ValueError("invalid concise user summary")
    for field in SUMMARY_KEYS:
        _string(summary[field], f"concise summary {field}", limit=1024)
    result = dict(value)
    result["venue_assessment"] = normalized_venue
    return result


def _result_branch(root: Path, instruction_id: str) -> str:
    try:
        return research_execution.load_server_plan(root, instruction_id)["result_branch"]
    except ValueError:
        # Read-only compatibility for historical/minimal evidence fixtures.
        shown = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", f"refs/heads/exec/{instruction_id}"],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
            check=False, shell=False,
        )
        return f"exec/{instruction_id}" if shown.returncode == 0 and shown.stdout.strip() else "main"


def _fetch_evidence(root: Path, instruction_id: str, refs: list[str]) -> str:
    branch = _result_branch(root, instruction_id)
    remote_ref = f"refs/remotes/origin/{branch}"
    completed = subprocess.run(
        ["git", "fetch", "origin", f"refs/heads/{branch}:{remote_ref}"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", check=False, shell=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"cannot fetch completed SERVER result: {(completed.stderr or completed.stdout).strip()}")
    commit = subprocess.run(
        ["git", "rev-parse", remote_ref], cwd=root, check=True, capture_output=True,
        text=True, encoding="utf-8", shell=False,
    ).stdout.strip()
    total = 0
    for relative in refs:
        size = subprocess.run(
            ["git", "cat-file", "-s", f"{remote_ref}:{relative}"], cwd=root,
            capture_output=True, text=True, encoding="utf-8", check=False, shell=False,
        )
        try:
            count = int(size.stdout.strip())
        except ValueError:
            count = -1
        if size.returncode != 0 or count < 0:
            raise ValueError(f"assessment evidence is absent from {branch}: {relative}")
        if count > MAX_EVIDENCE_FILE_BYTES:
            raise ValueError(f"assessment evidence is too large: {relative}")
        total += count
        if total > MAX_EVIDENCE_TOTAL_BYTES:
            raise ValueError("scientific assessment evidence set is too large")
    return commit


def _evidence(root: Path, instruction_id: str, refs: list[str]) -> list[dict[str, Any]]:
    result = []
    branch = _result_branch(root, instruction_id)
    remote_ref = f"refs/remotes/origin/{branch}"
    for relative in refs:
        relative = _safe_evidence(instruction_id, relative)
        shown = subprocess.run(
            ["git", "show", f"{remote_ref}:{relative}"], cwd=root,
            capture_output=True, check=False, shell=False,
        )
        if shown.returncode != 0:
            raise ValueError(f"assessment evidence is missing: {relative}")
        payload = shown.stdout
        result.append({"path": relative, "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    return result


def _validate_result(root: Path, request: dict[str, Any], commit: str) -> None:
    branch = _result_branch(root, request["instruction_id"])
    remote_ref = f"refs/remotes/origin/{branch}"
    shown = subprocess.run(
        [
            "git", "show",
            f"{remote_ref}:{request['result_ref']}",
        ],
        cwd=root, capture_output=True, check=False, shell=False,
    )
    if shown.returncode != 0:
        raise ValueError("scientific assessment RESULT is absent from the result branch")
    payload = shown.stdout
    if hashlib.sha256(payload).hexdigest() != request["result_sha256"]:
        raise ValueError("scientific assessment RESULT digest mismatch")
    result = yaml.safe_load(payload)
    files = result.get("result_files") if type(result) is dict else None
    if (
        type(result) is not dict
        or result.get("instruction_id") != request["instruction_id"]
        or result.get("status") != "SUCCEEDED"
        or result.get("bc_scientific_assessment_required") is not True
        or type(result.get("acceptance_checkpoint_index")) is not int
        or result["acceptance_checkpoint_index"] <= 0
        or type(files) is not list
        or not files
    ):
        raise ValueError("scientific assessment requires a verified successful result")
    for item in files:
        if (
            type(item) is not dict
            or set(item) != {"path", "size_bytes", "sha256"}
            or type(item["path"]) is not str
            or _relative(item["path"], "result file") != item["path"]
            or type(item["size_bytes"]) is not int
            or item["size_bytes"] <= 0
            or type(item["sha256"]) is not str
            or SHA256.fullmatch(item["sha256"]) is None
        ):
            raise ValueError("scientific assessment result file binding is invalid")
        blob = subprocess.run(
            [
                "git", "show",
                f"{remote_ref}:{item['path']}",
            ],
            cwd=root, capture_output=True, check=False, shell=False,
        )
        if (
            blob.returncode != 0
            or len(blob.stdout) != item["size_bytes"]
            or hashlib.sha256(blob.stdout).hexdigest() != item["sha256"]
        ):
            raise ValueError("scientific assessment result blob does not match RESULT.yaml")
    branch_commit = subprocess.run(
        ["git", "rev-parse", remote_ref],
        cwd=root, check=True, capture_output=True, text=True, encoding="utf-8", shell=False,
    ).stdout.strip()
    if branch_commit != commit:
        raise ValueError("SERVER result branch changed during assessment")


def record(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    root = _root(root)
    actor = _actor(root)
    _require_https_origin(root)
    request = _validate_request(root, request)
    instruction_id = request["instruction_id"]
    commit = _fetch_evidence(root, instruction_id, request["evidence_refs"])
    _validate_result(root, request, commit)
    evidence = _evidence(root, instruction_id, request["evidence_refs"])
    directory = root / "coordination/instructions" / instruction_id / "scientific-assessments"
    directory.mkdir(exist_ok=True)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("invalid scientific assessment directory")
    existing = [
        int(match.group(2)) for path in directory.iterdir()
        if (match := RECEIPT_FILE.fullmatch(path.name)) is not None and match.group(1) == actor
    ]
    assessment_id = f"{actor}-{max(existing, default=0) + 1:03d}"
    document = {
        "schema_version": 1,
        "assessment_id": assessment_id,
        "reviewed_by": actor,
        "result_commit": commit,
        **request,
        "evidence": evidence,
        "reviewed_at": _utc_now(),
    }
    path = directory / f"{assessment_id}.yaml"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(document, handle, allow_unicode=True, sort_keys=False)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    relative = path.relative_to(root).as_posix()
    return {
        "status": request["next_action"],
        "instruction_id": instruction_id,
        "assessment_path": relative,
        "assessment_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "user_summary": {
            **request["concise_summary"],
            "benchmark_zone": request["venue_assessment"]["benchmark_zone"],
            "benchmark_zone_label": request["venue_assessment"]["benchmark_zone_label"],
            "reference_journal": request["venue_assessment"]["reference_journal"],
        },
    }


def load(root: Path, relative: str, expected_sha256: str | None = None) -> dict[str, Any]:
    root = _root(root)
    relative = _relative(relative, "scientific assessment receipt")
    pure = PurePosixPath(relative)
    if (
        len(pure.parts) != 5
        or pure.parts[:2] != ("coordination", "instructions")
        or INSTRUCTION_ID.fullmatch(pure.parts[2]) is None
        or pure.parts[3] != "scientific-assessments"
        or RECEIPT_FILE.fullmatch(pure.parts[4]) is None
    ):
        raise ValueError("invalid scientific assessment receipt path")
    path = root.joinpath(*pure.parts)
    if path.is_symlink() or not path.is_file():
        raise ValueError("scientific assessment receipt is missing")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("scientific assessment receipt changed")
    document = yaml.safe_load(payload)
    if type(document) is not dict or set(document) != RECEIPT_KEYS or document.get("schema_version") != 1:
        raise ValueError("invalid scientific assessment receipt")
    if document["instruction_id"] != pure.parts[2] or f"{document['assessment_id']}.yaml" != pure.parts[4]:
        raise ValueError("scientific assessment identity changed")
    _validate_request(root, {key: document[key] for key in REQUEST_KEYS})
    if document["reviewed_by"] not in {"B", "C", "DOCTORAL"} or not document["assessment_id"].startswith(document["reviewed_by"] + "-"):
        raise ValueError("invalid scientific assessment reviewer")
    if (
        type(document["result_commit"]) is not str
        or GIT_OID.fullmatch(document["result_commit"]) is None
        or type(document["reviewed_at"]) is not str
        or not document["reviewed_at"].endswith("Z")
        or type(document["evidence"]) is not list
        or [item.get("path") for item in document["evidence"] if type(item) is dict]
        != document["evidence_refs"]
    ):
        raise ValueError("scientific assessment receipt closure changed")
    for item in document["evidence"]:
        if (
            type(item) is not dict
            or set(item) != {"path", "size_bytes", "sha256"}
            or type(item["size_bytes"]) is not int
            or item["size_bytes"] < 0
            or item["size_bytes"] > MAX_EVIDENCE_FILE_BYTES
            or type(item["sha256"]) is not str
            or SHA256.fullmatch(item["sha256"]) is None
        ):
            raise ValueError("invalid scientific assessment evidence binding")
    if sum(item["size_bytes"] for item in document["evidence"]) > MAX_EVIDENCE_TOTAL_BYTES:
        raise ValueError("scientific assessment evidence binding is too large")
    return document
