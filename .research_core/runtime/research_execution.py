"""Bounded B/C consultation, r-prefixed instructions, and SERVER authority."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any

import yaml

from . import journal_benchmarks

DECISION_ID = re.compile(r"RD[0-9]{4}\Z")
INSTRUCTION_ID = re.compile(r"r(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
SCIENCE_CASE_KEYS = {
    "novelty_claim",
    "strongest_prior_difference",
    "top_venue_relevance",
    "decisive_question",
    "minimum_discriminating_experiment",
    "decision_change_condition",
    "premise_check",
    "epistemic_status",
    "cas_2025_venue_assessment",
    "comparable_papers",
    "strongest_rejection_case",
    "model_escalation_recommendation",
}
SCIENCE_STRING_KEYS = {
    "novelty_claim",
    "strongest_prior_difference",
    "top_venue_relevance",
    "decisive_question",
    "minimum_discriminating_experiment",
    "decision_change_condition",
    "strongest_rejection_case",
}
PREMISE_CHECK_KEYS = {"problem_found", "explanation"}
EPISTEMIC_STATUS_KEYS = {
    "confirmed_facts",
    "reasonable_inferences",
    "personal_judgments",
    "currently_unverifiable",
}
FACT_KEYS = {"statement", "evidence_ref", "verified_at"}
CAS_ASSESSMENT_INPUT_KEYS = {
    "system",
    "edition",
    "benchmark_zone",
    "benchmark_zone_label",
    "reference_journal",
    "minimum_benchmark",
    "preferred_benchmark",
    "conclusion",
}
CAS_ASSESSMENT_DERIVED_KEYS = {
    "reference_journal_short_name",
    "partition_basis",
    "partition_category",
    "partition_source_url",
    "scope_source_url",
    "verified_at",
    "project_level",
}
CAS_ASSESSMENT_KEYS = CAS_ASSESSMENT_INPUT_KEYS | CAS_ASSESSMENT_DERIVED_KEYS
COMPARABLE_PAPER_KEYS = {
    "title",
    "venue",
    "year",
    "doi_or_url",
    "verified_at",
    "comparison",
}
MODEL_ESCALATION_KEYS = {
    "recommend_higher_model",
    "reason",
    "expected_benefit",
    "token_cost",
}
CONFIGURATION_BASELINE_KEYS = {
    "schema_version",
    "baseline_id",
    "task",
    "official_gpu_count",
    "official_global_batch_size",
    "official_optimizer_learning_rate",
    "official_config_refs",
    "prior_project_config_refs",
    "verified_at",
    "notes",
}
SERVER_PLAN_KEYS = {
    "execution_summary",
    "objective",
    "argv",
    "acceptance_argv",
    "datasets",
    "resources",
    "configuration_alignment",
    "execution_scope",
    "expected_results",
    "acceptance_criteria",
    "required_permissions",
    "hard_boundaries",
    "execution_followup",
    "startup_dataset",
}
RESOURCE_KEYS = {
    "cpu_count",
    "gpu_count",
    "gpu_tier",
    "gpu_memory_mib",
    "disk_gib",
    "max_hours",
}
CONFIGURATION_ALIGNMENT_KEYS = {
    "mode",
    "baseline_ref",
    "baseline_sha256",
    "preferred_gpu_count",
    "planned_gpu_count",
    "official_config_refs",
    "prior_project_config_refs",
    "official_global_batch_size",
    "planned_global_batch_size",
    "per_gpu_batch_size",
    "gradient_accumulation_steps",
    "official_optimizer_learning_rate",
    "planned_optimizer_learning_rate",
    "deviation_reason",
    "resource_inventory_policy",
}
DATASET_KEYS = {"dataset_id", "version"}
DATASET_SHARD_KEYS = DATASET_KEYS | {"shards"}
STARTUP_DATASET_KEYS = {"dataset_id", "mode", "reason"}
EXECUTION_SCOPE_KEYS = {
    "repo_write_roots",
    "host_write_scopes",
    "secret_read_scopes",
    "network_scopes",
}
EXECUTION_FOLLOWUP_KEYS = {
    "mode",
    "prior_instruction_id",
    "reviewer_role",
    "evidence_refs",
    "review_receipt",
    "review_sha256",
    "correction_summary",
    "post_correction_verification_required",
    "prior_scientific_assessment",
    "prior_scientific_assessment_sha256",
}
LOGICAL_SCOPE = re.compile(r"[A-Z][A-Z0-9_]{2,63}\Z")
INHERITANCE_KEYS = {"inherited", "rejected", "evidence_reason"}
AUTHORITY_KEYS = {
    "schema_version",
    "level",
    "authorization_ref",
    "authorization_sha256",
    "changed_at",
}
FLEXIBLE_FIELDS = {
    "command",
    "launch_strategy",
    "parameters",
    "batch_size",
    "parallelism",
    "scheduling",
    "gpu_allocation",
    "cpu_allocation",
    "temporary_path",
    "ephemeral_storage",
    "symlink_layout",
    "retry",
    "failure_recovery",
    "checkpoint",
    "conda_environment",
    "virtual_environment",
    "dependency_environment",
    "dependency_installation",
    "dependency_versioning",
    "dependency_recovery",
    "engineering_code",
    "engineering_configuration",
    "equivalent_implementation",
    "data_staging",
    "logging",
}
HARD_BLOCKERS = {
    "USER_STOP",
    "HARD_PERMISSION",
    "HARD_RESOURCE",
    "HARD_DATA",
    "SECRET_BOUNDARY",
    "DESTRUCTIVE_BOUNDARY",
}
REQUIRED_PERMISSIONS = {
    "real_experiment",
    "external_write",
    "resource_expansion",
    "publish",
}
REQUIRED_HARD_BOUNDARIES = {
    "NO_SCIENTIFIC_ROUTE_CHANGE",
    "HONOR_USER_STOP",
    "NO_SECRET_ACCESS_OUTSIDE_PLAN",
    "NO_IRREVERSIBLE_DESTRUCTIVE_ACTION",
    "NO_UNAUTHORIZED_RESOURCE_EXPANSION",
    "NO_UNAUTHORIZED_EXTERNAL_WRITE",
}
CONSUMPTION_KEYS = {
    "schema_version",
    "instruction_id",
    "decision_id",
    "reviewer_role",
    "review_receipt",
    "review_sha256",
    "request_sha256",
    "server_plan",
    "server_plan_sha256",
    "created_at",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _governance():
    path = Path(__file__).with_name("peer_governance.py")
    specification = importlib.util.spec_from_file_location(
        f"research_execution_governance_{id(path)}", path
    )
    if specification is None or specification.loader is None:
        raise ValueError("peer governance runtime is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _safe_relative(value: str, label: str) -> str:
    if type(value) is not str or not value or "\\" in value or "\x00" in value:
        raise ValueError(f"invalid {label}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"invalid {label}")
    return path.as_posix()


def _load_yaml(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"plain YAML file required: {path.name}")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(document) is not dict:
        raise ValueError(f"YAML mapping required: {path.name}")
    return document


def _exclusive_yaml(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _atomic_yaml(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(
        prefix=f".{path.name}-", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _authority_path(root: Path) -> Path:
    return Path(root) / "coordination/research-execution/AUTHORITY.yaml"


def load_authority(root: Path) -> dict[str, Any]:
    document = _load_yaml(_authority_path(root))
    if (
        set(document) != AUTHORITY_KEYS
        or type(document.get("schema_version")) is not int
        or document["schema_version"] != 1
        or document.get("level") not in {"MASTER", "DOCTORAL"}
        or type(document.get("changed_at")) is not str
        or not document["changed_at"]
    ):
        raise ValueError("invalid SERVER authority state")
    if document["level"] == "MASTER":
        if (
            document["authorization_ref"] is not None
            and type(document["authorization_ref"]) is not str
        ) or (
            document["authorization_sha256"] is not None
            and (
                type(document["authorization_sha256"]) is not str
                or SHA256.fullmatch(document["authorization_sha256"]) is None
            )
        ):
            raise ValueError("invalid MASTER authority proof")
    elif (
        type(document["authorization_ref"]) is not str
        or type(document["authorization_sha256"]) is not str
        or SHA256.fullmatch(document["authorization_sha256"]) is None
    ):
        raise ValueError("DOCTORAL requires explicit user authorization")
    return document


def _require_server(root: Path) -> None:
    if _governance().current_worker(root)["role"] != "SERVER":
        raise ValueError("only SERVER changes or uses SERVER authority")


def set_authority(
    root: Path,
    *,
    level: str,
    authorization_ref: str,
    authorization_sha256: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    _require_server(root)
    if level not in {"MASTER", "DOCTORAL"}:
        raise ValueError("authority level must be MASTER or DOCTORAL")
    relative = _safe_relative(authorization_ref, "authority authorization ref")
    if not relative.startswith("coordination/controls/SERVER/"):
        raise ValueError("authority requires a SERVER user-control authorization")
    if type(authorization_sha256) is not str or SHA256.fullmatch(authorization_sha256) is None:
        raise ValueError("invalid authority authorization digest")
    proof = root.joinpath(*PurePosixPath(relative).parts)
    if proof.is_symlink() or not proof.is_file():
        raise ValueError("authority authorization proof is missing")
    payload = proof.read_bytes()
    if hashlib.sha256(payload).hexdigest() != authorization_sha256:
        raise ValueError("authority authorization proof changed")
    try:
        wording = payload.decode("utf-8")
    except UnicodeError as error:
        raise ValueError("authority authorization must be UTF-8") from error
    required_line = (
        "用户明确启用博士生权限"
        if level == "DOCTORAL"
        else "用户明确启用硕士生权限"
    )
    if required_line not in {line.strip() for line in wording.splitlines()}:
        raise ValueError("authority authorization wording does not match level")
    document = {
        "schema_version": 1,
        "level": level,
        "authorization_ref": relative,
        "authorization_sha256": authorization_sha256,
        "changed_at": _utc_now(),
    }
    _atomic_yaml(_authority_path(root), document)
    return document


def _actor_role(root: Path) -> str:
    from . import execution_issues

    execution_issues.require_no_unnotified(root)
    role = _governance().current_worker(root)["role"]
    if role == "PEER_B":
        return "B"
    if role == "PEER_C":
        return "C"
    if role == "SERVER" and load_authority(root)["level"] == "DOCTORAL":
        return "DOCTORAL"
    raise ValueError("SERVER MASTER has no research authority; enable DOCTORAL explicitly")


def _dated_text(value: object, label: str) -> str:
    if type(value) is not str or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ValueError(f"invalid {label}")
    return value


def _science_case(root: Path, value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != SCIENCE_CASE_KEYS:
        raise ValueError("invalid innovation/novelty case")
    if any(
        type(value[field]) is not str or len(value[field].strip()) < 12
        for field in SCIENCE_STRING_KEYS
    ):
        raise ValueError("invalid innovation/novelty case")
    premise = value["premise_check"]
    if (
        type(premise) is not dict
        or set(premise) != PREMISE_CHECK_KEYS
        or type(premise["problem_found"]) is not bool
        or type(premise["explanation"]) is not str
        or len(premise["explanation"].strip()) < 12
    ):
        raise ValueError("invalid premise check")
    epistemic = value["epistemic_status"]
    if type(epistemic) is not dict or set(epistemic) != EPISTEMIC_STATUS_KEYS:
        raise ValueError("invalid epistemic status")
    facts = epistemic["confirmed_facts"]
    if type(facts) is not list or not facts:
        raise ValueError("confirmed facts with evidence are required")
    for fact in facts:
        if (
            type(fact) is not dict
            or set(fact) != FACT_KEYS
            or type(fact["statement"]) is not str
            or len(fact["statement"].strip()) < 8
            or type(fact["evidence_ref"]) is not str
            or not fact["evidence_ref"].strip()
        ):
            raise ValueError("invalid confirmed fact evidence")
        _dated_text(fact["verified_at"], "fact verification date")
    for field in (
        "reasonable_inferences",
        "personal_judgments",
        "currently_unverifiable",
    ):
        _string_list(epistemic[field], field, allow_empty=True)
    venue = value["cas_2025_venue_assessment"]
    venue_fields = set(venue) if type(venue) is dict else set()
    if (
        type(venue) is not dict
        or (
            venue_fields != CAS_ASSESSMENT_INPUT_KEYS
            and venue_fields != CAS_ASSESSMENT_KEYS
        )
        or venue["system"] != "CHINESE_ACADEMY_OF_SCIENCES_JOURNAL_PARTITION"
        or venue["edition"] != "2025_FINAL"
        or venue["minimum_benchmark"] != "TGRS"
        or venue["preferred_benchmark"] != "ISPRS JPRS"
        or type(venue["conclusion"]) is not str
        or len(venue["conclusion"].strip()) < 12
    ):
        raise ValueError("invalid 2025 CAS venue assessment")
    selected = journal_benchmarks.validate_selection(
        root,
        venue.get("benchmark_zone"),
        venue.get("benchmark_zone_label"),
        venue.get("reference_journal"),
    )
    normalized_venue = {
        **{key: venue[key] for key in CAS_ASSESSMENT_INPUT_KEYS},
        "reference_journal": selected["full_name"],
        "reference_journal_short_name": selected["short_name"],
        "partition_basis": selected["official_partition"]["basis"],
        "partition_category": selected["official_partition"]["category"],
        "partition_source_url": selected["partition_source_url"],
        "scope_source_url": selected["scope_source_url"],
        "verified_at": selected["verified_at"],
        "project_level": selected["project_level"],
    }
    if venue_fields == CAS_ASSESSMENT_KEYS and venue != normalized_venue:
        raise ValueError("stored 2025 CAS venue assessment differs from the built-in library")
    papers = value["comparable_papers"]
    if type(papers) is not list or not papers or len(papers) > 5:
        raise ValueError("one to five comparable papers are required")
    for paper in papers:
        if (
            type(paper) is not dict
            or set(paper) != COMPARABLE_PAPER_KEYS
            or type(paper["title"]) is not str
            or len(paper["title"].strip()) < 6
            or type(paper["venue"]) is not str
            or not paper["venue"].strip()
            or type(paper["year"]) is not int
            or paper["year"] < 1900
            or paper["year"] > datetime.now(timezone.utc).year
            or type(paper["doi_or_url"]) is not str
            or not paper["doi_or_url"].startswith("https://")
            or type(paper["comparison"]) is not str
            or len(paper["comparison"].strip()) < 12
        ):
            raise ValueError("invalid comparable paper")
        _dated_text(paper["verified_at"], "paper verification date")
    if not any(
        journal_benchmarks.matches_selected_journal(selected, paper["venue"])
        for paper in papers
    ):
        raise ValueError(
            "CAS reference journal must match a concrete comparable paper venue"
        )
    model = value["model_escalation_recommendation"]
    if (
        type(model) is not dict
        or set(model) != MODEL_ESCALATION_KEYS
        or type(model["recommend_higher_model"]) is not bool
        or type(model["reason"]) is not str
        or len(model["reason"].strip()) < 8
        or type(model["expected_benefit"]) is not str
        or len(model["expected_benefit"].strip()) < 8
        or model["token_cost"] not in {"LOW", "MEDIUM", "HIGH"}
    ):
        raise ValueError("invalid model escalation recommendation")
    result = copy.deepcopy(value)
    result["cas_2025_venue_assessment"] = normalized_venue
    return result


def _string_list(value: object, label: str, *, allow_empty: bool = False) -> list[str]:
    if (
        type(value) is not list
        or (not allow_empty and not value)
        or any(type(item) is not str or not item.strip() for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError(f"invalid {label}")
    return list(value)


def _adapt_legacy_server_plan(value: dict[str, Any]) -> dict[str, Any]:
    """Adapt an already-issued pre-single-host plan in memory, never on disk."""

    legacy_keys = SERVER_PLAN_KEYS - {"execution_summary", "startup_dataset"}
    if set(value) != legacy_keys:
        raise ValueError("invalid legacy SERVER experiment plan")
    result = copy.deepcopy(value)
    objective = str(result.get("objective", "")).strip()
    result["execution_summary"] = objective[:50] or "执行既定本地实验"
    normalized_datasets = []
    for dataset in result.get("datasets", []):
        if type(dataset) is not dict:
            raise ValueError("invalid legacy SERVER dataset identity")
        normalized = {
            key: copy.deepcopy(dataset[key])
            for key in ("dataset_id", "version", "shards")
            if key in dataset
        }
        normalized_datasets.append(normalized)
    alignment = result.get("configuration_alignment", {})
    resources = result.get("resources", {})
    training = type(alignment) is dict and alignment.get("mode") == "TRAINING"
    if type(resources) is dict:
        legacy_count = resources.get("gpu_count")
        resources["gpu_tier"] = (
            "CPU_ONLY"
            if legacy_count == 0
            else "QUICK_VALIDATION"
            if legacy_count == 1
            else "NORMAL_TRAINING"
        )
    if training and type(alignment) is dict:
        alignment["preferred_gpu_count"] = 2
    if training and type(resources) is dict and resources.get("gpu_count") == 4:
        resources["gpu_count"] = 2
        alignment["planned_gpu_count"] = 2
        alignment["preferred_gpu_count"] = 2
        planned = alignment.get("planned_global_batch_size")
        per_gpu = alignment.get("per_gpu_batch_size")
        if type(planned) is int and type(per_gpu) is int and planned > 0 and per_gpu > 0:
            divisor = 2 * per_gpu
            if planned % divisor == 0:
                alignment["gradient_accumulation_steps"] = planned // divisor
    if training and normalized_datasets:
        if normalized_datasets[0]["dataset_id"].casefold() != "hrsc2016":
            normalized_datasets.insert(
                0, {"dataset_id": "HRSC2016", "version": "official"}
            )
        startup = {
            "dataset_id": "HRSC2016",
            "mode": "ENGINEERING_CHAIN",
            "reason": "Legacy plan first opens HRSC2016 to verify the local chain",
        }
    else:
        startup = {
            "dataset_id": None,
            "mode": "NOT_APPLICABLE",
            "reason": "This legacy instruction has no applicable dataset training stage",
        }
    result["datasets"] = normalized_datasets
    result["startup_dataset"] = startup
    return result


def _validate_server_plan(
    value: object, *, allow_legacy: bool = False
) -> dict[str, Any]:
    if allow_legacy and type(value) is dict and set(value) != SERVER_PLAN_KEYS:
        value = _adapt_legacy_server_plan(value)
    if type(value) is not dict or set(value) != SERVER_PLAN_KEYS:
        raise ValueError("invalid SERVER experiment plan")
    if (
        type(value["execution_summary"]) is not str
        or not value["execution_summary"].strip()
        or len(value["execution_summary"].strip()) > 50
        or "\n" in value["execution_summary"]
        or "\r" in value["execution_summary"]
        or
        type(value["objective"]) is not str
        or len(value["objective"].strip()) < 12
        or type(value["acceptance_criteria"]) is not str
        or len(value["acceptance_criteria"].strip()) < 12
    ):
        raise ValueError("invalid SERVER experiment objective")
    for field in ("argv", "acceptance_argv"):
        argv = value[field]
        if (
            type(argv) is not list
            or not argv
            or any(
                type(command) is not list
                or not command
                or any(type(argument) is not str or not argument for argument in command)
                for command in argv
            )
        ):
            raise ValueError(f"invalid SERVER experiment {field}")
        for command in argv:
            rendered = " ".join(command).casefold()
            if (
                "while true" in rendered
                or "tail -f" in rendered
                or "tail --follow" in rendered
                or "get-content -wait" in rendered
                or command[0].casefold() == "watch"
            ):
                raise ValueError(
                    "unbounded observer loops are forbidden; use goal status and bounded checks"
                )
    datasets = value["datasets"]
    if type(datasets) is not list:
        raise ValueError("invalid SERVER dataset manifest")
    identities: set[tuple[str, str]] = set()
    for dataset in datasets:
        if (
            type(dataset) is not dict
            or set(dataset) not in (DATASET_KEYS, DATASET_SHARD_KEYS)
            or type(dataset["dataset_id"]) is not str
            or not dataset["dataset_id"]
            or type(dataset["version"]) is not str
            or not dataset["version"]
            or (
                dataset["dataset_id"].casefold(),
                dataset["version"].casefold(),
            ) in identities
        ):
            raise ValueError("invalid SERVER dataset identity")
        shards = dataset.get("shards", [])
        if (
            type(shards) is not list
            or any(type(shard) is not str or not shard for shard in shards)
            or len(shards) != len(set(shards))
        ):
            raise ValueError("invalid SERVER dataset shards")
        for shard in shards:
            _safe_relative(shard, "dataset shard")
        identities.add(
            (dataset["dataset_id"].casefold(), dataset["version"].casefold())
        )
    resources = value["resources"]
    if type(resources) is not dict or set(resources) != RESOURCE_KEYS:
        raise ValueError("invalid SERVER resources")
    startup = value["startup_dataset"]
    if (
        type(startup) is not dict
        or set(startup) != STARTUP_DATASET_KEYS
        or startup["mode"] not in {"SCIENTIFIC", "ENGINEERING_CHAIN", "NOT_APPLICABLE"}
        or type(startup["reason"]) is not str
        or len(startup["reason"].strip()) < 12
    ):
        raise ValueError("invalid HRSC2016 startup policy")
    if startup["mode"] == "NOT_APPLICABLE":
        if startup["dataset_id"] is not None:
            raise ValueError("non-applicable HRSC2016 startup must not name a dataset")
    elif (
        startup["dataset_id"] != "HRSC2016"
        or not datasets
        or datasets[0]["dataset_id"].casefold() != "hrsc2016"
    ):
        raise ValueError("HRSC2016 must be the first applicable dataset")
    if any(
        type(resources[key]) is not int or resources[key] < 0
        for key in ("cpu_count", "gpu_count")
    ) or any(
        type(resources[key]) not in {int, float} or resources[key] < 0
        for key in ("gpu_memory_mib", "disk_gib", "max_hours")
    ):
        raise ValueError("invalid SERVER resources")
    expected_tier = {
        0: "CPU_ONLY",
        1: "QUICK_VALIDATION",
        2: "NORMAL_TRAINING",
        4: "EXPANDED_TRAINING",
    }.get(resources["gpu_count"])
    if resources["gpu_tier"] != expected_tier:
        raise ValueError("GPU tier does not match the requested local GPU count")
    alignment = value["configuration_alignment"]
    if type(alignment) is not dict or set(alignment) != CONFIGURATION_ALIGNMENT_KEYS:
        raise ValueError("invalid SERVER configuration alignment")
    if alignment["resource_inventory_policy"] != "DISCOVER_HOST_LOCAL_THEN_OFFICIAL_AND_PROJECT":
        raise ValueError("invalid SERVER resource inventory policy")
    if alignment["mode"] == "NON_TRAINING":
        if any(
            alignment[field] is not None
            for field in (
                "baseline_ref",
                "baseline_sha256",
                "official_global_batch_size",
                "planned_global_batch_size",
                "per_gpu_batch_size",
                "gradient_accumulation_steps",
                "official_optimizer_learning_rate",
                "planned_optimizer_learning_rate",
                "deviation_reason",
            )
        ) or alignment["preferred_gpu_count"] != 0 or alignment["planned_gpu_count"] != resources["gpu_count"]:
            raise ValueError("non-training plan carries training configuration")
        for field in ("official_config_refs", "prior_project_config_refs"):
            if alignment[field] != []:
                raise ValueError("non-training plan carries training configuration refs")
    elif alignment["mode"] == "TRAINING":
        if resources["gpu_count"] not in {1, 2, 4} or alignment["preferred_gpu_count"] != 2:
            raise ValueError("GPU training must use 1, 2, or approved 4 GPUs and prefer two")
        if alignment["planned_gpu_count"] != resources["gpu_count"]:
            raise ValueError("training GPU count does not match resources")
        baseline_ref = _safe_relative(alignment["baseline_ref"], "configuration baseline")
        if (
            not baseline_ref.startswith("research/configuration-baselines/")
            or not baseline_ref.endswith(".yaml")
            or type(alignment["baseline_sha256"]) is not str
            or SHA256.fullmatch(alignment["baseline_sha256"]) is None
        ):
            raise ValueError("training configuration baseline is invalid")
        for field, empty in (("official_config_refs", False), ("prior_project_config_refs", True)):
            refs = _string_list(alignment[field], field, allow_empty=empty)
            for ref in refs:
                if ref.startswith(("https://", "http://")):
                    continue
                _safe_relative(ref, field)
        integer_fields = (
            "official_global_batch_size",
            "planned_global_batch_size",
            "per_gpu_batch_size",
            "gradient_accumulation_steps",
        )
        if any(type(alignment[field]) is not int or alignment[field] <= 0 for field in integer_fields):
            raise ValueError("invalid training batch alignment")
        if alignment["planned_global_batch_size"] != (
            resources["gpu_count"]
            * alignment["per_gpu_batch_size"]
            * alignment["gradient_accumulation_steps"]
        ):
            raise ValueError("planned global batch does not match GPU/batch/accumulation")
        for field in ("official_optimizer_learning_rate", "planned_optimizer_learning_rate"):
            if type(alignment[field]) not in {int, float} or alignment[field] <= 0:
                raise ValueError("invalid optimizer learning-rate alignment")
        aligned = (
            alignment["planned_global_batch_size"] == alignment["official_global_batch_size"]
            and alignment["planned_optimizer_learning_rate"]
            == alignment["official_optimizer_learning_rate"]
        )
        if aligned:
            if alignment["deviation_reason"] is not None:
                raise ValueError("aligned training plan must not invent a deviation")
        elif type(alignment["deviation_reason"]) is not str or len(alignment["deviation_reason"].strip()) < 12:
            raise ValueError("training deviation from official totals requires a reason")
    else:
        raise ValueError("invalid training configuration mode")
    results = _string_list(value["expected_results"], "expected results")
    for result in results:
        _safe_relative(result, "expected result")
    permissions = _string_list(
        value["required_permissions"], "required permissions", allow_empty=True
    )
    if not set(permissions).issubset(REQUIRED_PERMISSIONS):
        raise ValueError("invalid SERVER required permissions")
    if resources["gpu_count"] == 4 and "resource_expansion" not in permissions:
        raise ValueError("four-GPU training requires resource_expansion permission")
    boundaries = _string_list(value["hard_boundaries"], "hard boundaries")
    if not REQUIRED_HARD_BOUNDARIES.issubset(boundaries):
        raise ValueError("SERVER plan is missing mandatory hard boundaries")
    scope = value["execution_scope"]
    if type(scope) is not dict or set(scope) != EXECUTION_SCOPE_KEYS:
        raise ValueError("invalid SERVER execution scope")
    repo_roots = _string_list(scope["repo_write_roots"], "repo write roots")
    repo_roots = [_safe_relative(item, "repo write root") for item in repo_roots]
    for field in ("host_write_scopes", "secret_read_scopes", "network_scopes"):
        names = _string_list(scope[field], field, allow_empty=True)
        if any(LOGICAL_SCOPE.fullmatch(item) is None for item in names):
            raise ValueError(f"invalid SERVER execution scope: {field}")
    if scope["secret_read_scopes"]:
        raise ValueError("v1.8 SERVER execution scope does not authorize secret reads")
    if (
        scope["host_write_scopes"] or scope["network_scopes"]
    ) and "external_write" not in permissions:
        raise ValueError("external execution scopes require external_write permission")
    for result in results:
        result_path = PurePosixPath(result)
        if not any(
            result_path == PurePosixPath(base)
            or PurePosixPath(base) in result_path.parents
            for base in repo_roots
        ):
            raise ValueError("expected result is outside declared repo write roots")
    followup = value["execution_followup"]
    if type(followup) is not dict or set(followup) != EXECUTION_FOLLOWUP_KEYS:
        raise ValueError("invalid SERVER execution followup")
    if followup["mode"] == "NEW_EXPERIMENT":
        if (
            followup["prior_instruction_id"] is not None
            or followup["reviewer_role"] is not None
            or followup["evidence_refs"] != []
            or followup["review_receipt"] is not None
            or followup["review_sha256"] is not None
            or followup["correction_summary"] is not None
            or followup["post_correction_verification_required"] is not False
        ):
            raise ValueError("new experiment cannot carry correction metadata")
        assessment_ref = followup["prior_scientific_assessment"]
        assessment_sha = followup["prior_scientific_assessment_sha256"]
        if (assessment_ref is None) != (assessment_sha is None):
            raise ValueError("new experiment assessment binding is incomplete")
        if assessment_ref is not None and (
            type(assessment_ref) is not str
            or type(assessment_sha) is not str
            or SHA256.fullmatch(assessment_sha) is None
        ):
            raise ValueError("new experiment assessment binding is invalid")
    elif followup["mode"] == "CORRECT_PREVIOUS_EXECUTION":
        if (
            type(followup["prior_instruction_id"]) is not str
            or INSTRUCTION_ID.fullmatch(followup["prior_instruction_id"]) is None
            or followup["reviewer_role"] not in {"B", "C"}
            or type(followup["evidence_refs"]) is not list
            or not followup["evidence_refs"]
            or any(type(item) is not str or not item.strip() for item in followup["evidence_refs"])
            or type(followup["review_receipt"]) is not str
            or not followup["review_receipt"]
            or type(followup["review_sha256"]) is not str
            or SHA256.fullmatch(followup["review_sha256"]) is None
            or type(followup["correction_summary"]) is not str
            or len(followup["correction_summary"].strip()) < 12
            or followup["post_correction_verification_required"] is not True
            or followup["prior_scientific_assessment"] is not None
            or followup["prior_scientific_assessment_sha256"] is not None
        ):
            raise ValueError("corrective experiment requires B/C review evidence and re-verification")
    else:
        raise ValueError("invalid SERVER execution followup mode")
    return copy.deepcopy(value)


def _instruction_root(root: Path) -> Path:
    path = Path(root) / "coordination/instructions"
    if path.is_symlink() or not path.is_dir():
        raise ValueError("instruction root must be a plain directory")
    return path


def _source_commit(root: Path) -> str:
    root = Path(root).resolve()
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        shell=False,
    )
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        raise ValueError("SERVER plan requires the exact Git repository root")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        shell=False,
    )
    source_commit = head.stdout.strip()
    if head.returncode != 0 or GIT_OID.fullmatch(source_commit) is None:
        raise ValueError("SERVER plan requires an exact source commit")
    return source_commit


def _next_instruction(
    root: Path, *, expected_id: str | None = None
) -> tuple[str, Path]:
    parent = _instruction_root(root)
    if expected_id is not None and (
        type(expected_id) is not str
        or INSTRUCTION_ID.fullmatch(expected_id) is None
    ):
        raise ValueError("invalid r-prefixed instruction id")
    for _ in range(32):
        values = [
            int(item.name[1:])
            for item in parent.iterdir()
            if item.is_dir() and INSTRUCTION_ID.fullmatch(item.name) is not None
        ]
        number = max(values, default=0) + 1
        instruction_id = f"r{number:03d}"
        if expected_id is not None and instruction_id != expected_id:
            raise ValueError(
                f"r-prefixed instruction must be the next monotonic id {instruction_id}"
            )
        path = parent / instruction_id
        try:
            path.mkdir()
        except FileExistsError:
            continue
        return instruction_id, path
    raise ValueError("cannot allocate a unique r-prefixed instruction")


def reserve_numeric_instruction(
    root: Path, *, expected_id: str | None = None, kind: str
) -> tuple[str, Path]:
    """Reserve the shared r-prefixed namespace for non-plan SERVER work."""

    if kind not in {"USER_DIRECTIVE"}:
        raise ValueError("invalid numeric instruction kind")
    instruction_id, directory = _next_instruction(root, expected_id=expected_id)
    reservation = {
        "schema_version": 1,
        "instruction_id": instruction_id,
        "kind": kind,
        "status": "RESERVED",
        "created_at": _utc_now(),
    }
    _exclusive_yaml(directory / "RESERVATION.yaml", reservation)
    return instruction_id, directory


def _validate_configuration_binding(root: Path, plan: dict[str, Any]) -> None:
    alignment = plan["configuration_alignment"]
    if alignment["mode"] != "TRAINING":
        return
    relative = _safe_relative(alignment["baseline_ref"], "configuration baseline")
    path = Path(root).joinpath(*PurePosixPath(relative).parts)
    if path.is_symlink() or not path.is_file():
        raise ValueError("training configuration baseline is missing")
    if hashlib.sha256(path.read_bytes()).hexdigest() != alignment["baseline_sha256"]:
        raise ValueError("training configuration baseline changed")
    baseline = _load_yaml(path)
    if (
        set(baseline) != CONFIGURATION_BASELINE_KEYS
        or baseline.get("schema_version") != 1
        or type(baseline.get("baseline_id")) is not str
        or not baseline["baseline_id"].strip()
        or type(baseline.get("task")) is not str
        or len(baseline["task"].strip()) < 8
        or type(baseline.get("official_gpu_count")) is not int
        or baseline["official_gpu_count"] <= 0
        or baseline.get("official_global_batch_size")
        != alignment["official_global_batch_size"]
        or baseline.get("official_optimizer_learning_rate")
        != alignment["official_optimizer_learning_rate"]
        or baseline.get("official_config_refs") != alignment["official_config_refs"]
        or baseline.get("prior_project_config_refs")
        != alignment["prior_project_config_refs"]
        or type(baseline.get("notes")) is not str
        or len(baseline["notes"].strip()) < 8
    ):
        raise ValueError("training configuration baseline does not match the plan")
    _dated_text(baseline.get("verified_at"), "configuration baseline verification date")
    for ref in [*alignment["official_config_refs"], *alignment["prior_project_config_refs"]]:
        if ref.startswith(("https://", "http://")):
            continue
        candidate = Path(root).joinpath(*PurePosixPath(_safe_relative(ref, "configuration ref")).parts)
        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError(f"training configuration reference is missing: {ref}")


def _latest_server_instruction(root: Path) -> str | None:
    values = []
    for item in _instruction_root(root).iterdir():
        if item.is_dir() and INSTRUCTION_ID.fullmatch(item.name) is not None:
            plan = item / "SERVER_PLAN.yaml"
            if plan.is_file() and not plan.is_symlink():
                values.append(item.name)
    return max(values, key=lambda value: int(value[1:])) if values else None


def _validate_scientific_assessment_followup(root: Path, plan: dict[str, Any]) -> None:
    followup = plan["execution_followup"]
    if followup["mode"] != "NEW_EXPERIMENT":
        return
    latest = _latest_server_instruction(root)
    reference = followup["prior_scientific_assessment"]
    digest = followup["prior_scientific_assessment_sha256"]
    if latest is None:
        if reference is not None or digest is not None:
            raise ValueError("first experiment cannot bind a prior scientific assessment")
        return
    if reference is None or digest is None:
        raise ValueError("next experiment requires B/C assessment of the latest COMPLETE result")
    from . import outcome_assessment

    assessment = outcome_assessment.load(root, reference, expected_sha256=digest)
    committed = subprocess.run(
        ["git", "show", f"HEAD:{reference}"],
        cwd=root,
        capture_output=True,
        check=False,
        shell=False,
    )
    assessment_path = Path(root).joinpath(*PurePosixPath(reference).parts)
    if committed.returncode != 0 or committed.stdout != assessment_path.read_bytes():
        raise ValueError("scientific assessment must be committed before the next experiment")
    if (
        assessment["instruction_id"] != latest
        or assessment["next_action"] != "CONTINUE_WITH_NEXT_R"
        or assessment["venue_assessment"]["goal_reached"] is not False
    ):
        raise ValueError("next experiment does not bind an unfinished latest scientific assessment")


def _issue_server_plan(
    root: Path,
    *,
    decision_id: str,
    actor_role: str,
    science_case: dict[str, str],
    server_plan: dict[str, Any],
) -> tuple[str, str, str]:
    plan = _validate_server_plan(server_plan)
    _validate_configuration_binding(root, plan)
    _validate_scientific_assessment_followup(root, plan)
    followup = plan["execution_followup"]
    if followup["mode"] == "CORRECT_PREVIOUS_EXECUTION":
        _validate_correction_binding(root, followup, actor_role)
        existing = _load_correction_consumption(root, followup, required=False)
        if existing is not None:
            return _resume_consumed_correction(
                root,
                existing,
                decision_id=decision_id,
                actor_role=actor_role,
                science_case=science_case,
                plan=plan,
            )
    instruction_id, directory = _next_instruction(root)
    document = {
        "schema_version": 1,
        "instruction_id": instruction_id,
        "decision_id": decision_id,
        "status": "READY",
        "issued_by_role": actor_role,
        "source_commit": _source_commit(root),
        "authority_snapshot": copy.deepcopy(load_authority(root)),
        "science_case": copy.deepcopy(science_case),
        **plan,
        "run_path": f"runs/{instruction_id}",
        "supervision_path": f"coordination/supervision/{instruction_id}/SUPERVISION.yaml",
        "result_path": f"coordination/executions/{instruction_id}/RESULT.yaml",
        # New plans publish the verified result commit to the authoritative main
        # branch.  A short-lived exec/rNNN branch is reserved for abnormal
        # evidence; historical plans that already name one remain readable.
        "result_branch": "main",
    }
    path = directory / "SERVER_PLAN.yaml"
    if followup["mode"] == "CORRECT_PREVIOUS_EXECUTION":
        consumption = _correction_consumption_document(
            decision_id=decision_id,
            actor_role=actor_role,
            followup=followup,
            science_case=science_case,
            plan=plan,
            document=document,
        )
        consumption_path = _correction_consumption_path(
            root, followup["review_receipt"]
        )
        try:
            _exclusive_yaml(consumption_path, consumption)
        except FileExistsError:
            existing = _load_correction_consumption(root, followup, required=True)
            return _resume_consumed_correction(
                root,
                existing,
                decision_id=decision_id,
                actor_role=actor_role,
                science_case=science_case,
                plan=plan,
            )
    try:
        _exclusive_yaml(path, document)
    except BaseException:
        # The reservation intentionally remains: numeric identities are never
        # reused after a partial issuance.
        raise
    relative = path.relative_to(root).as_posix()
    return instruction_id, relative, hashlib.sha256(path.read_bytes()).hexdigest()


def _correction_request_sha256(
    *, decision_id: str, actor_role: str, science_case: dict[str, str], plan: dict[str, Any]
) -> str:
    payload = yaml.safe_dump(
        {
            "decision_id": decision_id,
            "actor_role": actor_role,
            "science_case": science_case,
            "plan": plan,
        },
        allow_unicode=True,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _correction_consumption_path(root: Path, review_relative: str) -> Path:
    pure = PurePosixPath(review_relative)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or len(pure.parts) != 5
        or pure.parts[:2] != ("coordination", "instructions")
        or pure.parts[3] != "reviews"
        or re.fullmatch(r"[BC]-[0-9]{3,}\.yaml", pure.parts[4]) is None
    ):
        raise ValueError("invalid correction review receipt path")
    return root.joinpath(*pure.with_name(f"{pure.stem}-CONSUMPTION.yaml").parts)


def _correction_consumption_document(
    *,
    decision_id: str,
    actor_role: str,
    followup: dict[str, Any],
    science_case: dict[str, str],
    plan: dict[str, Any],
    document: dict[str, Any],
) -> dict[str, Any]:
    plan_payload = yaml.safe_dump(
        document, allow_unicode=True, sort_keys=False
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "instruction_id": document["instruction_id"],
        "decision_id": decision_id,
        "reviewer_role": actor_role,
        "review_receipt": followup["review_receipt"],
        "review_sha256": followup["review_sha256"],
        "request_sha256": _correction_request_sha256(
            decision_id=decision_id,
            actor_role=actor_role,
            science_case=science_case,
            plan=plan,
        ),
        "server_plan": document,
        "server_plan_sha256": hashlib.sha256(plan_payload).hexdigest(),
        "created_at": _utc_now(),
    }


def _load_correction_consumption(
    root: Path, followup: dict[str, Any], *, required: bool
) -> dict[str, Any] | None:
    path = _correction_consumption_path(root, followup["review_receipt"])
    if not path.exists():
        if required:
            raise ValueError("correction receipt consumption is missing")
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("correction receipt consumption is invalid")
    value = _load_yaml(path)
    document = value.get("server_plan") if type(value) is dict else None
    plan = (
        {key: document[key] for key in SERVER_PLAN_KEYS}
        if type(document) is dict and SERVER_PLAN_KEYS.issubset(document)
        else None
    )
    if (
        set(value) != CONSUMPTION_KEYS
        or value.get("schema_version") != 1
        or INSTRUCTION_ID.fullmatch(str(value.get("instruction_id"))) is None
        or DECISION_ID.fullmatch(str(value.get("decision_id"))) is None
        or value.get("reviewer_role") != followup["reviewer_role"]
        or value.get("review_receipt") != followup["review_receipt"]
        or value.get("review_sha256") != followup["review_sha256"]
        or SHA256.fullmatch(str(value.get("request_sha256"))) is None
        or type(document) is not dict
        or document.get("instruction_id") != value["instruction_id"]
        or document.get("decision_id") != value["decision_id"]
        or document.get("issued_by_role") != value["reviewer_role"]
        or document.get("execution_followup") != followup
        or type(document.get("science_case")) is not dict
        or type(plan) is not dict
        or value["request_sha256"]
        != _correction_request_sha256(
            decision_id=value["decision_id"],
            actor_role=value["reviewer_role"],
            science_case=document["science_case"],
            plan=plan,
        )
        or hashlib.sha256(
            yaml.safe_dump(document, allow_unicode=True, sort_keys=False).encode("utf-8")
        ).hexdigest()
        != value.get("server_plan_sha256")
    ):
        raise ValueError("correction receipt consumption changed")
    return value


def _resume_consumed_correction(
    root: Path,
    consumption: dict[str, Any],
    *,
    decision_id: str,
    actor_role: str,
    science_case: dict[str, str],
    plan: dict[str, Any],
) -> tuple[str, str, str]:
    expected = _correction_request_sha256(
        decision_id=decision_id,
        actor_role=actor_role,
        science_case=science_case,
        plan=plan,
    )
    if consumption["request_sha256"] != expected:
        raise ValueError("B/C correction review is already consumed by another plan")
    instruction_id = consumption["instruction_id"]
    directory = _instruction_root(root) / instruction_id
    directory.mkdir(exist_ok=True)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("consumed correction instruction directory is invalid")
    path = directory / "SERVER_PLAN.yaml"
    if not path.exists():
        try:
            _exclusive_yaml(path, consumption["server_plan"])
        except FileExistsError:
            pass
    if (
        path.is_symlink()
        or not path.is_file()
        or hashlib.sha256(path.read_bytes()).hexdigest()
        != consumption["server_plan_sha256"]
    ):
        raise ValueError("consumed correction SERVER plan changed")
    load_server_plan(root, instruction_id)
    return (
        instruction_id,
        path.relative_to(root).as_posix(),
        consumption["server_plan_sha256"],
    )


def _validate_correction_binding(
    root: Path,
    followup: dict[str, Any],
    actor_role: str,
    correction_instruction_id: str | None = None,
) -> None:
    if actor_role not in {"B", "C"} or followup["reviewer_role"] != actor_role:
        raise ValueError("the B/C reviewer must directly issue its correction plan")
    prior = _instruction_root(root) / followup["prior_instruction_id"] / "SERVER_PLAN.yaml"
    if prior.is_symlink() or not prior.is_file():
        raise ValueError("correction plan does not bind an existing prior instruction")
    from . import execution_reviews

    review = execution_reviews.load_review(
        root,
        followup["review_receipt"],
        expected_sha256=followup["review_sha256"],
    )
    if (
        review["instruction_id"] != followup["prior_instruction_id"]
        or review["reviewed_by"] != actor_role
        or review["verdict"] != "ISSUE_NEXT_R_CORRECTION"
        or [item["path"] for item in review["evidence"]]
        != followup["evidence_refs"]
        or review["summary"].strip() != followup["correction_summary"].strip()
    ):
        raise ValueError("correction plan does not match the B/C review receipt")
    if correction_instruction_id is not None:
        consumption = _load_correction_consumption(root, followup, required=True)
        if consumption["instruction_id"] != correction_instruction_id:
            raise ValueError("correction plan does not match its durable receipt consumption")


def load_server_plan(root: Path, instruction_id: str) -> dict[str, Any]:
    if type(instruction_id) is not str or INSTRUCTION_ID.fullmatch(instruction_id) is None:
        raise ValueError("invalid r-prefixed instruction id")
    path = _instruction_root(root) / instruction_id / "SERVER_PLAN.yaml"
    document = _load_yaml(path)
    common_issued_keys = {
        "schema_version",
        "instruction_id",
        "decision_id",
        "status",
        "issued_by_role",
        "source_commit",
        "authority_snapshot",
        "science_case",
        "run_path",
        "supervision_path",
        "result_path",
        "result_branch",
    }
    issued_keys = common_issued_keys | SERVER_PLAN_KEYS
    legacy_plan_keys = SERVER_PLAN_KEYS - {"execution_summary", "startup_dataset"}
    legacy_issued_keys = common_issued_keys | legacy_plan_keys
    if (
        set(document) not in (issued_keys, legacy_issued_keys)
        or document.get("schema_version") != 1
        or document.get("instruction_id") != instruction_id
        or document.get("status") != "READY"
        or document.get("issued_by_role") not in {"B", "C", "DOCTORAL"}
        or type(document.get("source_commit")) is not str
        or GIT_OID.fullmatch(document["source_commit"]) is None
        or document.get("run_path") != f"runs/{instruction_id}"
        or document.get("supervision_path")
        != f"coordination/supervision/{instruction_id}/SUPERVISION.yaml"
        or document.get("result_path")
        != f"coordination/executions/{instruction_id}/RESULT.yaml"
        or document.get("result_branch") not in {"main", f"exec/{instruction_id}"}
    ):
        raise ValueError("invalid SERVER instruction binding")
    _science_case(root, document["science_case"])
    selected_plan_keys = (
        SERVER_PLAN_KEYS if set(document) == issued_keys else legacy_plan_keys
    )
    plan = _validate_server_plan(
        {key: document[key] for key in selected_plan_keys},
        allow_legacy=True,
    )
    if plan["execution_followup"]["mode"] == "CORRECT_PREVIOUS_EXECUTION":
        _validate_correction_binding(
            root,
            plan["execution_followup"],
            document["issued_by_role"],
            correction_instruction_id=instruction_id,
        )
    return {**document, **plan}


def _decision_directory(root: Path, decision_id: str) -> Path:
    if type(decision_id) is not str or DECISION_ID.fullmatch(decision_id) is None:
        raise ValueError("invalid research decision id")
    return Path(root) / "coordination/research-execution/decisions" / decision_id


def _events(root: Path, decision_id: str) -> list[tuple[Path, dict[str, Any]]]:
    directory = _decision_directory(root, decision_id) / "events"
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("research decision is missing")
    paths = sorted(directory.glob("[0-9][0-9][0-9].yaml"))
    if not paths:
        raise ValueError("research decision has no events")
    result: list[tuple[Path, dict[str, Any]]] = []
    previous = None
    for index, path in enumerate(paths, 1):
        if path.name != f"{index:03d}.yaml":
            raise ValueError("research decision event sequence is invalid")
        document = _load_yaml(path)
        if (
            document.get("schema_version") != 1
            or document.get("decision_id") != decision_id
            or document.get("sequence") != index
            or document.get("previous_event_sha256") != previous
        ):
            raise ValueError("research decision event chain is invalid")
        previous = hashlib.sha256(path.read_bytes()).hexdigest()
        result.append((path, document))
    return result


def load_decision(root: Path, decision_id: str) -> dict[str, Any]:
    return copy.deepcopy(_events(root, decision_id)[-1][1])


def _append_event(
    root: Path, decision_id: str, fields: dict[str, Any]
) -> dict[str, Any]:
    history = _events(root, decision_id)
    previous_path = history[-1][0]
    document = {
        "schema_version": 1,
        "decision_id": decision_id,
        "sequence": len(history) + 1,
        "previous_event_sha256": hashlib.sha256(previous_path.read_bytes()).hexdigest(),
        "created_at": _utc_now(),
        **fields,
    }
    _exclusive_yaml(
        previous_path.parent / f"{document['sequence']:03d}.yaml", document
    )
    return document


def _server_event_fields(
    root: Path,
    *,
    decision_id: str,
    actor_role: str,
    science_case: dict[str, str],
    server_plan: dict[str, Any],
) -> dict[str, Any]:
    instruction_id, reference, digest = _issue_server_plan(
        root,
        decision_id=decision_id,
        actor_role=actor_role,
        science_case=science_case,
        server_plan=server_plan,
    )
    return {
        "state": "SERVER_PLAN",
        "actor_role": actor_role,
        "science_case": science_case,
        "instruction_id": instruction_id,
        "server_plan_ref": reference,
        "server_plan_sha256": digest,
    }


def begin_decision(
    root: Path,
    *,
    decision_id: str,
    discussion_required: bool,
    discussion_reason: str | None,
    science_case: dict[str, str],
    server_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    actor = _actor_role(root)
    science = _science_case(root, science_case)
    if (
        server_plan is not None
        and type(server_plan) is dict
        and type(server_plan.get("execution_followup")) is dict
        and server_plan["execution_followup"].get("mode") == "CORRECT_PREVIOUS_EXECUTION"
        and discussion_required
    ):
        raise ValueError("ordinary execution correction must go directly to the next r instruction")
    if type(discussion_required) is not bool:
        raise ValueError("discussion_required must be boolean")
    directory = _decision_directory(root, decision_id)
    directory.mkdir(parents=True, exist_ok=False)
    events = directory / "events"
    events.mkdir()
    try:
        if discussion_required:
            if actor == "DOCTORAL":
                raise ValueError("DOCTORAL resolves research directly without synthetic peer discussion")
            if (
                type(discussion_reason) is not str
                or len(discussion_reason.strip()) < 12
                or server_plan is not None
            ):
                raise ValueError("first discussion must contain only a discussion plan")
            fields = {
                "state": "DISCUSSION_1",
                "actor_role": actor,
                "owner_role": actor,
                "next_actor_role": "C" if actor == "B" else "B",
                "discussion_reason": discussion_reason,
                "science_case": science,
            }
        else:
            if discussion_reason is not None or server_plan is None:
                raise ValueError("direct decision requires a SERVER experiment plan")
            fields = {
                **_server_event_fields(
                    root,
                    decision_id=decision_id,
                    actor_role=actor,
                    science_case=science,
                    server_plan=server_plan,
                ),
                "owner_role": actor,
            }
        document = {
            "schema_version": 1,
            "decision_id": decision_id,
            "sequence": 1,
            "previous_event_sha256": None,
            "created_at": _utc_now(),
            **fields,
        }
        _exclusive_yaml(events / "001.yaml", document)
        return document
    except BaseException:
        try:
            events.rmdir()
            directory.rmdir()
        except OSError:
            pass
        raise


def _inheritance(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != INHERITANCE_KEYS:
        raise ValueError("invalid critique inheritance")
    inherited = _string_list(value["inherited"], "inherited findings")
    rejected = _string_list(value["rejected"], "rejected findings", allow_empty=True)
    if (
        type(value["evidence_reason"]) is not str
        or len(value["evidence_reason"].strip()) < 12
    ):
        raise ValueError("critique inheritance requires evidence reasoning")
    return {
        "inherited": inherited,
        "rejected": rejected,
        "evidence_reason": value["evidence_reason"],
    }


def critique_inherit(
    root: Path,
    *,
    decision_id: str,
    inheritance: dict[str, Any],
    can_execute: bool,
    reason: str,
    science_case: dict[str, str],
    server_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    current = load_decision(root, decision_id)
    actor = _actor_role(root)
    if current["state"] != "DISCUSSION_1":
        raise ValueError("research decision is not awaiting peer critique")
    if actor != current["next_actor_role"]:
        raise ValueError("the designated peer must provide critique inheritance")
    if type(can_execute) is not bool or type(reason) is not str or len(reason.strip()) < 8:
        raise ValueError("invalid critique execution decision")
    inherited = _inheritance(inheritance)
    science = _science_case(root, science_case)
    if not can_execute:
        raise ValueError(
            "one critique must issue a SERVER plan; use record_final_blocker for a hard blocker"
        )
    if can_execute:
        if server_plan is None:
            raise ValueError("executable critique must issue a SERVER plan")
        fields = {
            **_server_event_fields(
                root,
                decision_id=decision_id,
                actor_role=actor,
                science_case=science,
                server_plan=server_plan,
            ),
            "owner_role": current["owner_role"],
            "inheritance": inherited,
            "critique_reason": reason,
        }
    return _append_event(root, decision_id, fields)


def record_final_blocker(
    root: Path,
    *,
    decision_id: str,
    blocker: str,
    reason: str,
    recovery_condition: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    current = load_decision(root, decision_id)
    actor = _actor_role(root)
    if current["state"] != "DISCUSSION_1" or actor != current["next_actor_role"]:
        raise ValueError("hard blocker is only valid as the one peer critique outcome")
    if (
        blocker not in HARD_BLOCKERS
        or type(reason) is not str
        or len(reason.strip()) < 8
        or type(recovery_condition) is not str
        or len(recovery_condition.strip()) < 8
    ):
        raise ValueError("invalid final hard blocker")
    return _append_event(
        root,
        decision_id,
        {
            "state": "BLOCKED",
            "actor_role": actor,
            "owner_role": current["owner_role"],
            "blocker": blocker,
            "reason": reason,
            "recovery_condition": recovery_condition,
        },
    )


def record_adaptation(
    root: Path,
    *,
    instruction_id: str,
    changes: dict[str, str],
    reason: str,
    changed_paths: list[str] | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    _require_server(root)
    load_server_plan(root, instruction_id)
    if (
        type(changes) is not dict
        or not changes
        or not set(changes).issubset(FLEXIBLE_FIELDS)
        or any(type(value) is not str or not value.strip() for value in changes.values())
    ):
        raise ValueError("principle or scientific changes require a new B/C plan")
    if type(reason) is not str or len(reason.strip()) < 8:
        raise ValueError("adaptation reason is required")
    paths = [] if changed_paths is None else _string_list(
        changed_paths, "engineering changed paths", allow_empty=True
    )
    for relative in paths:
        safe = _safe_relative(relative, "engineering changed path")
        parts = PurePosixPath(safe).parts
        if parts[0] == ".git":
            raise ValueError("engineering changed path cannot enter Git metadata")
        if parts[0] == ".research_core" or safe in {"project.yaml", "AGENTS.md", "CLAUDE.md"}:
            raise ValueError("engineering adaptation cannot modify governance or guard runtime")
    parent = _instruction_root(root) / instruction_id / "deviations"
    parent.mkdir(exist_ok=True)
    existing = [
        int(path.stem)
        for path in parent.glob("[0-9][0-9][0-9].yaml")
        if path.stem.isdecimal()
    ]
    sequence = max(existing, default=0) + 1
    event = {
        "schema_version": 1,
        "instruction_id": instruction_id,
        "sequence": sequence,
        "authority_level": load_authority(root)["level"],
        "action": "CONTINUE_AND_LOG",
        "changes": copy.deepcopy(changes),
        "changed_paths": paths,
        "reason": reason,
        "created_at": _utc_now(),
    }
    _exclusive_yaml(parent / f"{sequence:03d}.yaml", event)
    return event
