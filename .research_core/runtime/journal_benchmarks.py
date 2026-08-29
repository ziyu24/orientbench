"""Strict access to the single built-in CAS 2025 journal benchmark library."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from .context import _read_project_file


LIBRARY_PATH = "research/venue-benchmarks/CAS-2025-FINAL.yaml"
ZONE_LABELS = {1: "一区", 2: "二区", 3: "三区", 4: "四区"}
STORED_ZONE_LABELS = {str(zone): label for zone, label in ZONE_LABELS.items()}
TOP_LEVEL_FIELDS = {
    "schema_version", "ranking_system", "edition", "frozen_after_edition",
    "official_platform", "official_discontinuation_notice", "checked_at",
    "allowed_rating_labels", "benchmark_policy",
    "rating_requires_built_in_zone_journal_match", "benchmarks", "warning",
}
POLICY_FIELDS = {
    "partition_basis", "partition_category", "terminal_floor_zone",
    "minimum_journal", "preferred_journal",
    "below_zone_one_requires_continued_experiment",
    "above_zone_one_conference_alternatives",
}
BENCHMARK_FIELDS = {
    "benchmark_zone", "benchmark_zone_label", "full_name", "short_name",
    "issn", "official_partition", "relevant_minor_partitions",
    "partition_source_url", "scope_source_url", "verified_at",
    "remote_sensing_object_detection_rationale", "project_level",
}
PARTITION_FIELDS = {"basis", "category", "zone"}
PROJECT_LEVELS = {"PREFERRED", "MINIMUM", "CURRENT_LEVEL_ONLY"}


class _StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if type(key) is not str:
            raise ValueError("journal library YAML mapping keys must be strings")
        if key in mapping:
            raise ValueError(f"duplicate YAML key in journal library: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _fail(message: str) -> None:
    raise ValueError(f"invalid built-in journal benchmark library: {message}")


def _text(value: object, label: str, *, limit: int = 2048) -> str:
    if type(value) is not str or not value.strip():
        _fail(f"{label} must be non-empty text")
    value = value.strip()
    if len(value.encode("utf-8")) > limit:
        _fail(f"{label} is oversized")
    return value


def _url(value: object, label: str) -> str:
    value = _text(value, label)
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        _fail(f"{label} must be an HTTPS URL")
    return value


def _date(value: object, label: str) -> str:
    value = _text(value, label, limit=10)
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError:
        _fail(f"{label} must be an ISO date")
    return value


def _load_yaml(root: Path) -> dict:
    try:
        value = yaml.load(
            _read_project_file(Path(root), LIBRARY_PATH), Loader=_StrictSafeLoader
        )
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ValueError("built-in journal benchmark library is unreadable") from error
    if type(value) is not dict:
        _fail("top level must be a mapping")
    return value


def load_library(root: Path) -> dict:
    value = _load_yaml(root)
    if set(value) != TOP_LEVEL_FIELDS:
        _fail("unexpected top-level fields")
    if (
        value["schema_version"] != 2
        or value["ranking_system"]
        != "CHINESE_ACADEMY_OF_SCIENCES_JOURNAL_PARTITION"
        or value["edition"] != "2025_FINAL"
        or value["frozen_after_edition"] is not True
        or value["rating_requires_built_in_zone_journal_match"] is not True
    ):
        _fail("ranking identity or policy is inconsistent")
    _url(value["official_platform"], "official platform")
    _url(value["official_discontinuation_notice"], "official discontinuation notice")
    _date(value["checked_at"], "library check date")
    if value["allowed_rating_labels"] != STORED_ZONE_LABELS:
        _fail("allowed rating labels must be zones one through four")
    policy = value["benchmark_policy"]
    if type(policy) is not dict or set(policy) != POLICY_FIELDS:
        _fail("unexpected benchmark policy fields")
    if (
        policy["partition_basis"] != "MAJOR_CATEGORY"
        or policy["partition_category"] != "EARTH_SCIENCES"
        or policy["terminal_floor_zone"] != 1
        or policy["below_zone_one_requires_continued_experiment"] is not True
    ):
        _fail("benchmark policy must use the Earth Sciences major category")
    minimum = _text(policy["minimum_journal"], "minimum journal", limit=80)
    preferred = _text(policy["preferred_journal"], "preferred journal", limit=80)
    conferences = policy["above_zone_one_conference_alternatives"]
    if conferences != ["CVPR", "ICCV"]:
        _fail("above-zone-one conference alternatives must be CVPR and ICCV")
    benchmarks = value["benchmarks"]
    if type(benchmarks) is not list or len(benchmarks) != 5:
        _fail("exactly five journal benchmarks are required")
    names: set[str] = set()
    shorts: set[str] = set()
    issns: set[str] = set()
    zone_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    levels: dict[str, str] = {}
    for item in benchmarks:
        if type(item) is not dict or set(item) != BENCHMARK_FIELDS:
            _fail("unexpected benchmark fields")
        zone = item["benchmark_zone"]
        if type(zone) is not int or zone not in ZONE_LABELS:
            _fail("benchmark zone must be 1, 2, 3, or 4")
        if item["benchmark_zone_label"] != ZONE_LABELS[zone]:
            _fail("benchmark zone label mismatch")
        full_name = _text(item["full_name"], "journal full name", limit=160)
        short_name = _text(item["short_name"], "journal short name", limit=80)
        issn = _text(item["issn"], "ISSN", limit=9)
        if len(issn) != 9 or issn[4] != "-":
            _fail("ISSN must use NNNN-NNNN form")
        folded_name = full_name.casefold()
        folded_short = short_name.casefold()
        if folded_name in names or folded_short in shorts or issn.casefold() in issns:
            _fail("journal names, short names, and ISSNs must be unique")
        names.add(folded_name)
        shorts.add(folded_short)
        issns.add(issn.casefold())
        partition = item["official_partition"]
        if type(partition) is not dict or set(partition) != PARTITION_FIELDS:
            _fail("unexpected official partition fields")
        if partition != {
            "basis": "MAJOR_CATEGORY", "category": "EARTH_SCIENCES", "zone": zone
        }:
            _fail("official major-category partition must match benchmark zone")
        minors = item["relevant_minor_partitions"]
        if (
            type(minors) is not dict
            or not minors
            or any(type(key) is not str or type(minor_zone) is not int
                   or minor_zone not in ZONE_LABELS for key, minor_zone in minors.items())
        ):
            _fail("relevant minor partitions are invalid")
        _url(item["partition_source_url"], "partition source")
        _url(item["scope_source_url"], "scope source")
        _date(item["verified_at"], "benchmark verification date")
        _text(
            item["remote_sensing_object_detection_rationale"],
            "remote-sensing object-detection rationale",
        )
        level = item["project_level"]
        if level not in PROJECT_LEVELS:
            _fail("invalid project level")
        levels[short_name] = level
        zone_counts[zone] += 1
    if zone_counts != {1: 2, 2: 1, 3: 1, 4: 1}:
        _fail("zone distribution must be 2/1/1/1")
    if levels.get(minimum) != "MINIMUM" or levels.get(preferred) != "PREFERRED":
        _fail("minimum and preferred journals must identify their project levels")
    _text(value["warning"], "warning")
    return deepcopy(value)


def validate_selection(
    root: Path, benchmark_zone: object, benchmark_zone_label: object,
    reference_journal: object,
) -> dict:
    if type(benchmark_zone) is not int or benchmark_zone not in ZONE_LABELS:
        raise ValueError("benchmark zone must be one of 1, 2, 3, or 4")
    if benchmark_zone_label != ZONE_LABELS[benchmark_zone]:
        raise ValueError("benchmark zone label does not match the numeric zone")
    if type(reference_journal) is not str or not reference_journal.strip():
        raise ValueError("reference journal must name a built-in journal")
    library = load_library(root)
    candidate = reference_journal.strip().casefold()
    matches = [
        item for item in library["benchmarks"]
        if candidate in {item["full_name"].casefold(), item["short_name"].casefold()}
    ]
    allowed = [
        item for item in library["benchmarks"]
        if item["benchmark_zone"] == benchmark_zone
    ]
    allowed_text = ", ".join(
        f"{item['short_name']} ({item['full_name']})" for item in allowed
    )
    if not matches:
        raise ValueError(
            f"unknown reference journal; allowed journal(s) for "
            f"{ZONE_LABELS[benchmark_zone]}: {allowed_text}"
        )
    selected = matches[0]
    if selected["benchmark_zone"] != benchmark_zone:
        raise ValueError(
            f"{selected['short_name']} does not belong to {ZONE_LABELS[benchmark_zone]}; "
            f"allowed journal(s): {allowed_text}"
        )
    return deepcopy(selected)


def matches_selected_journal(selected: dict, value: object) -> bool:
    return type(value) is str and value.strip().casefold() in {
        selected["full_name"].casefold(),
        selected["short_name"].casefold(),
    }


def help_entries(root: Path) -> list[dict]:
    return [
        {
            "benchmark_zone": item["benchmark_zone"],
            "benchmark_zone_label": item["benchmark_zone_label"],
            "full_name": item["full_name"],
            "short_name": item["short_name"],
            "partition_basis": item["official_partition"]["basis"],
            "partition_category": item["official_partition"]["category"],
            "partition_source_url": item["partition_source_url"],
            "verified_at": item["verified_at"],
        }
        for item in load_library(root)["benchmarks"]
    ]
