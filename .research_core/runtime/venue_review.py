from datetime import date
import hashlib
import math
import os
from pathlib import PurePosixPath
import re
import subprocess
from urllib.parse import urlsplit

import yaml

from .context import _read_project_file
from . import journal_benchmarks, lessons, research_execution
from . import paper_transaction_platform as platform
from . import paper_version

pv = paper_version

FIT = {"不具备投稿条件", "低适配", "条件适配", "高适配"}
DELTA = {"UP", "DOWN", "UNCHANGED", "INITIAL"}
CLAIM_STATUS = {"SUPPORTED", "WEAK", "MISSING", "CONTRADICTED"}
FIT_ORDER = {name: index for index, name in enumerate(("不具备投稿条件", "低适配", "条件适配", "高适配"))}

G, P, E, R = "paper_git_sha", "profile_refs", "evidence_refs", "review_version"
PROFILE_FIELDS = {"schema_version", "profile_id", "venue", "profile_version", "source_url", "read_date", "scope", "novelty_bar", "evidence_bar"}
ASSESSMENT_FIELDS = {"paper_version", G, E, P, "true_claim", "claim_evidence_matrix", "strongest_rejection_case", "fatal_flaws", "novelty_attack", "experimental_attack", "reproducibility_attack", "venue_matrix", "journal_level_assessment", "current_target", "stretch_target", "not_ready_reason", "confidence", "previous_review", "rating_delta", "delta_reasons"}
RECORD_FIELDS = ASSESSMENT_FIELDS | {"schema_version", R}
CLAIM_FIELDS = {"claim", E, "status"}
VENUE_FIELDS = {"profile_ref", "venue", "fit", "scope", "novelty", "evidence", "biggest_blocker", "upgrade_conditions", "downgrade_conditions"}
JOURNAL_LEVEL_INPUT_FIELDS = {
    "ranking_system", "ranking_edition", "benchmark_zone", "benchmark_zone_label",
    "reference_journal", "rationale",
}
JOURNAL_LEVEL_DERIVED_FIELDS = {
    "reference_journal_short_name", "partition_basis", "partition_category",
    "partition_source_url", "scope_source_url", "verified_at", "project_level",
}
JOURNAL_LEVEL_FIELDS = JOURNAL_LEVEL_INPUT_FIELDS | JOURNAL_LEVEL_DERIVED_FIELDS
DELTA_REASON_FIELDS = {"reason", E}
ORDINARY_REVIEW_FIELDS = {"schema_version", R, "paper_version", G, "summary"}

PROFILE_MAX_BYTES = 16384
REVIEW_MAX_BYTES = pv.VERSION_MAX_BYTES
EVIDENCE_MAX_BYTES = 1048576
MAX_REVIEW_ENTRIES = 1000
MAX_REFS = 64
ASSESSMENT_REQUEST = "build/paper-assessment.yaml"
_PROFILE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REVIEW = re.compile(r"v([0-9]{3})\Z")


def _fail(message):
    raise ValueError(message)
def _mapping(value, fields, label):
    if type(value) is not dict or set(value) != fields: _fail(f"invalid {label} fields")
    if any(type(key) is not str for key in value): _fail(f"invalid {label} keys")
    return value
def _normalize(value):
    if type(value) in {str, int, float, bool, type(None)}:
        return value
    if type(value) is list:
        return [_normalize(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: _normalize(item) for key, item in value.items()}
    _fail("unsafe assessment value")
def _string(value, label, limit=4096):
    if type(value) is not str or not value.strip(): _fail(f"invalid {label} string")
    if len(value.encode("utf-8")) > limit: _fail(f"oversize {label}")
    return value
def _date(value, label):
    value = _string(value, label, 10)
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError as error:
        raise ValueError(f"invalid {label}") from error
    return value
def _url(value, label):
    parsed = urlsplit(_string(value, label, 2048))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        _fail(f"invalid {label} URL")
    return value
def _reference_journal(value):
    value = _string(value, "reference_journal", 160).strip()
    if re.fullmatch(r"(?:中科院)?[一二三四1-4]区(?:参考)?期刊", value):
        _fail("invalid reference_journal: a concrete journal is required")
    if value.casefold() in {"journal", "reference journal", "a vague journal level"}:
        _fail("invalid reference_journal: a concrete journal is required")
    return value
def _strings(value, label, *, empty=False):
    if type(value) is not list or (not empty and not value) or len(value) > MAX_REFS:
        _fail(f"invalid {label} list")
    result = [_string(item, label) for item in value]
    if len({item.casefold() for item in result}) != len(result): _fail(f"duplicate {label}")
    return result
def _relative(value, label):
    value = _string(value, label, 512)
    path = PurePosixPath(value)
    if (path.is_absolute() or value != path.as_posix() or "\\" in value or ":" in value
            or not path.parts or any(part in {"", ".", ".."} for part in path.parts)):
        _fail(f"invalid {label} path")
    return value
def _snapshot(path):
    value = os.stat(path, follow_symlinks=False)
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns
def _read_text(root, relative, *, label, limit, context=True):
    relative = _relative(relative, label)
    path = root.joinpath(*PurePosixPath(relative).parts)
    lessons._require_no_follow_path(root, path, label=label, directory=False)
    before = _snapshot(path)
    try:
        if context: _read_project_file(root, relative)
        with platform._guard_directory(path.parent) as guard:
            payload = platform._read_guarded(guard, path.name, limit)
        text = payload.decode("utf-8")
    except UnicodeError as error:
        raise ValueError(f"{label} must be valid UTF-8") from error
    lessons._require_no_follow_path(root, path, label=label, directory=False)
    if _snapshot(path) != before:
        _fail(f"changed {label}")
    return text
def _yaml(text, label):
    try:
        value = yaml.load(text, Loader=lessons._StrictSafeLoader)
    except (RecursionError, yaml.YAMLError) as error:
        raise ValueError(f"invalid {label} YAML") from error
    if type(value) is not dict:
        _fail(f"invalid {label} mapping")
    return value
def load_assessment_request(root, relative_path):
    if type(relative_path) is not str or relative_path != ASSESSMENT_REQUEST:
        _fail("request must be build/paper-assessment.yaml")
    return _yaml(_read_text(_root(root), relative_path, label="assessment request",
                            limit=REVIEW_MAX_BYTES, context=False), "assessment request")


def _root(value):
    return pv._root(value)


def _validate_profile(value):
    profile = _mapping(value, PROFILE_FIELDS, "venue profile")
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1:
        _fail("invalid profile schema")
    profile_id = _string(profile["profile_id"], "profile_id", 64)
    if _PROFILE_ID.fullmatch(profile_id) is None: _fail("invalid profile_id")
    _string(profile["venue"], "venue", 120)
    _string(profile["profile_version"], "profile_version", 120)
    source = urlsplit(_string(profile["source_url"], "source_url", 2048))
    if source.scheme not in {"http", "https"} or not source.netloc: _fail("invalid profile URL")
    read_date = _string(profile["read_date"], "read_date", 10)
    try:
        if date.fromisoformat(read_date).isoformat() != read_date:
            raise ValueError
    except ValueError as error:
        raise ValueError("invalid profile date") from error
    for field in ("scope", "novelty_bar", "evidence_bar"):
        _string(profile[field], field)
    return profile


def load_profile(root, relative_path):
    root = _root(root)
    relative = _relative(relative_path, "venue profile reference")
    return _profile_payload(relative, _read_text(
        root, relative, label="venue profile", limit=PROFILE_MAX_BYTES
    ).encode("utf-8"))
def _profile_payload(relative: str, payload: bytes) -> dict:
    parts = PurePosixPath(relative).parts
    if (len(parts) != 4 or parts[:3] != ("paper", "review", "venue-profiles")
            or not parts[3].endswith(".yaml")):
        _fail("invalid profile path")
    profile = _validate_profile(_yaml(payload.decode("utf-8"), "venue profile"))
    if profile["profile_id"] != PurePosixPath(relative).stem:
        _fail("profile_id/stem mismatch")
    return profile


def _refs(value, label, *, empty=False):
    return [_relative(item, label) for item in _strings(value, label, empty=empty)]
def _validate_business(root, request):
    value = _mapping(request, ASSESSMENT_FIELDS, "venue assessment")
    if pv.VERSION.fullmatch(_string(value["paper_version"], "paper_version", 64)) is None:
        _fail("invalid paper_version")
    if _SHA.fullmatch(_string(value[G], G, 40)) is None: _fail("invalid paper_git_sha")
    evidence_refs = _refs(value[E], E)
    profile_refs = _refs(value[P], P)
    _string(value["true_claim"], "true_claim")
    claims = value["claim_evidence_matrix"]
    if type(claims) is not list or not claims or len(claims) > 64:
        _fail("invalid claim matrix")
    for item in claims:
        row = _mapping(item, CLAIM_FIELDS, "claim-evidence row")
        _string(row["claim"], "claim")
        refs = _refs(row[E], "claim refs", empty=True)
        if any(ref not in evidence_refs for ref in refs): _fail("undeclared claim ref")
        if row["status"] not in CLAIM_STATUS: _fail("invalid claim status")
    for field in (
        "strongest_rejection_case", "novelty_attack", "experimental_attack",
        "reproducibility_attack", "not_ready_reason",
    ):
        _string(value[field], field)
    _strings(value["fatal_flaws"], "fatal_flaws", empty=True)
    matrix = value["venue_matrix"]
    if type(matrix) is not list or not matrix or len(matrix) > 16:
        _fail("invalid venue matrix")
    seen_profiles: set[str] = set()
    for item in matrix:
        row = _mapping(item, VENUE_FIELDS, "venue matrix row")
        profile_ref = _relative(row["profile_ref"], "matrix profile_ref")
        if profile_ref not in profile_refs or profile_ref in seen_profiles:
            _fail("invalid matrix profile_ref")
        seen_profiles.add(profile_ref)
        _string(row["venue"], "matrix venue", 120)
        if row["fit"] not in FIT: _fail("invalid venue fit")
        for field in ("scope", "novelty", "evidence", "biggest_blocker"):
            _string(row[field], f"matrix {field}")
        _strings(row["upgrade_conditions"], "upgrade_conditions")
        _strings(row["downgrade_conditions"], "downgrade_conditions")
    if seen_profiles != set(profile_refs):
        _fail("incomplete venue matrix")
    journal = value["journal_level_assessment"]
    journal_fields = set(journal) if type(journal) is dict else set()
    if type(journal) is not dict or (
        journal_fields != JOURNAL_LEVEL_INPUT_FIELDS
        and journal_fields != JOURNAL_LEVEL_FIELDS
    ):
        _fail("invalid CAS journal level assessment fields")
    if (
        journal["ranking_system"] != "CAS_JOURNAL_PARTITION"
        or journal["ranking_edition"] != "2025_FINAL"
    ):
        _fail("invalid CAS journal level assessment")
    selected = journal_benchmarks.validate_selection(
        root,
        journal.get("benchmark_zone"),
        journal.get("benchmark_zone_label"),
        journal.get("reference_journal"),
    )
    normalized_journal = {
        **{key: journal[key] for key in JOURNAL_LEVEL_INPUT_FIELDS},
        "reference_journal": selected["full_name"],
        "reference_journal_short_name": selected["short_name"],
        "partition_basis": selected["official_partition"]["basis"],
        "partition_category": selected["official_partition"]["category"],
        "partition_source_url": selected["partition_source_url"],
        "scope_source_url": selected["scope_source_url"],
        "verified_at": selected["verified_at"],
        "project_level": selected["project_level"],
    }
    if journal_fields == JOURNAL_LEVEL_FIELDS and journal != normalized_journal:
        _fail("stored CAS journal level assessment differs from the built-in library")
    _string(journal["rationale"], "CAS journal level rationale")
    profile_ids = {PurePosixPath(ref).stem for ref in profile_refs}
    if any(_PROFILE_ID.fullmatch(profile_id) is None for profile_id in profile_ids):
        _fail("invalid referenced profile_id")
    for field in ("current_target", "stretch_target"):
        target = value[field]
        if target is not None:
            target = _string(target, f"assessment {field}", 64)
            if target not in profile_ids:
                _fail(f"invalid {field}")
    confidence = value["confidence"]
    if type(confidence) is not float or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        _fail("invalid confidence")
    previous = value["previous_review"]
    if previous is not None and (type(previous) is not str or _REVIEW.fullmatch(previous) is None):
        _fail("invalid previous_review")
    if value["rating_delta"] not in DELTA:
        _fail("invalid rating_delta")
    reasons = value["delta_reasons"]
    if type(reasons) is not list or len(reasons) > 32:
        _fail("invalid delta_reasons")
    for item in reasons:
        row = _mapping(item, DELTA_REASON_FIELDS, "delta reason")
        _string(row["reason"], "delta reason")
        refs = _refs(row[E], "delta refs")
        if any(ref not in evidence_refs for ref in refs): _fail("undeclared delta ref")
    result = dict(value)
    result["journal_level_assessment"] = normalized_journal
    return result


def _git(root, *args):
    try:
        return subprocess.run(["git", *args], cwd=root, check=True, text=True,
                              encoding="utf-8", capture_output=True).stdout.rstrip("\r\n")
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        raise ValueError("venue assessment git binding failed") from error
def _git_blob(root, commit, relative, limit):
    query = ["git", "ls-tree", "-z", commit, "--", f":(literal){relative}"]
    try:
        tree = subprocess.run(query, cwd=root, check=True, capture_output=True).stdout
        match = re.fullmatch(rb"(100644|100755) blob ([0-9a-f]{40})\t"
                             + re.escape(relative.encode()) + rb"\0", tree)
        if match is None:
            _fail("assessment reference is not one exact plain Git blob")
        oid = match.group(2).decode("ascii")
        size = _git(root, "cat-file", "-s", oid)
        if not size.isdigit() or int(size) > limit:
            _fail("oversize assessment Git blob")
        blob = subprocess.run(["git", "cat-file", "blob", oid], cwd=root, check=True,
                              capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        raise ValueError("assessment Git blob binding failed") from error
    if len(blob) != int(size):
        _fail("Git blob size mismatch")
    return match.group(1).decode("ascii"), blob


def _bound_ref(root, commit, relative, label, limit):
    relative = _relative(relative, label)
    path = root.joinpath(*PurePosixPath(relative).parts)
    before = _snapshot(path)
    payload = _read_text(root, relative, label=label, limit=limit).encode("utf-8")
    if _snapshot(path) != before:
        _fail(f"{label} identity changed")
    mode, blob = _git_blob(root, commit, relative, limit)
    if payload != blob:
        _fail(f"{label}/Git mismatch")
    return relative, label, limit, mode, before, hashlib.sha256(payload).hexdigest(), payload


def _bound_refs(root, value):
    commit = value[G]
    groups = ((P, "venue profile", PROFILE_MAX_BYTES),
              (E, "assessment evidence", EVIDENCE_MAX_BYTES))
    return [_bound_ref(root, commit, ref, label, limit)
            for field, label, limit in groups for ref in value[field]]


def _verify_refs(root, commit, tokens):
    for token in tokens:
        if _bound_ref(root, commit, token[0], token[1], token[2]) != token:
            _fail("assessment ref changed")


def _paper_binding(root):
    paper = root / "paper"
    return pv._read_small_plain_payload(root, paper / "VERSION",
                                        label="paper/VERSION", parents=(paper,))


def _review_binding(root):
    review = root / "paper/review"
    return pv._read_small_plain_payload(root, review / "VERSION",
        label="paper/review/VERSION", parents=(root / "paper", review))


def _verify_binding(root, head, paper_bytes, paper_leaf, allowed, review=None):
    if _git(root, "rev-parse", "HEAD") != head:
        _fail("assessment HEAD changed")
    status = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    changed = {entry[3:] for entry in status.split("\0") if entry}
    if changed - set(allowed):
        _fail("assessment worktree changed")
    _, current_bytes, current_leaf = _paper_binding(root)
    if current_bytes != paper_bytes or current_leaf != paper_leaf:
        _fail("paper/VERSION changed")
    if review is not None:
        _, current_bytes, current_leaf = _review_binding(root)
        if current_bytes != review[0] or current_leaf != review[1]:
            _fail("review VERSION changed")


def _load_record(root, review_version):
    if type(review_version) is not str or _REVIEW.fullmatch(review_version) is None:
        _fail("invalid review version")
    relative = f"paper/review/review-{review_version}.yaml"
    return _yaml(_read_text(root, relative, label="paper review record",
                            limit=REVIEW_MAX_BYTES), "paper review record")


def _assessment_record(root, document, version):
    record = _mapping(document, RECORD_FIELDS, "venue assessment record")
    if (type(record["schema_version"]) is not int
            or record["schema_version"] != 1 or record[R] != version):
        _fail("invalid assessment binding")
    _validate_business(root, {key: record[key] for key in ASSESSMENT_FIELDS})
    return record


def _assessments(root):
    review = root / "paper/review"
    pv._require_plain_directory(review, label="paper review directory")
    names = os.listdir(review)
    if len(names) > MAX_REVIEW_ENTRIES:
        _fail("too many review entries")
    result = []
    for name in sorted(names):
        match = re.fullmatch(r"review-(v[0-9]{3})\.yaml", name)
        if match is None:
            continue
        document = _load_record(root, match.group(1))
        if set(document) == ORDINARY_REVIEW_FIELDS:
            _mapping(document, ORDINARY_REVIEW_FIELDS, "ordinary paper review")
            if (type(document["schema_version"]) is not int or document["schema_version"] != 1
                    or document[R] != match.group(1)):
                _fail("invalid ordinary review binding")
            if pv.VERSION.fullmatch(_string(document["paper_version"],
                                            "ordinary version", 64)) is None:
                _fail("invalid ordinary paper version")
            if _SHA.fullmatch(_string(document[G],
                                     "ordinary Git SHA", 40)) is None:
                _fail("invalid ordinary Git SHA")
            _string(document["summary"], "ordinary summary", 240)
            continue
        result.append(_assessment_record(root, document, match.group(1)))
    for index, record in enumerate(result):
        if index == 0:
            _validate_initial(record)
        else:
            if int(record[R][1:]) <= int(result[index - 1][R][1:]):
                _fail("unordered assessments")
            _validate_transition(result[index - 1], record)
    return result


def _validate_initial(value):
    if (
        value["previous_review"] is not None
        or value["rating_delta"] != "INITIAL"
        or value["delta_reasons"]
    ):
        _fail("invalid initial assessment")


def _validate_transition(previous, current):
    if current["previous_review"] != previous[R]:
        _fail("stale previous_review")
    delta = current["rating_delta"]
    if delta == "INITIAL":
        _fail("unexpected INITIAL")
    if delta in {"UP", "DOWN"} and not current["delta_reasons"]:
        _fail("delta reasons required")
    old = {row["profile_ref"]: FIT_ORDER[row["fit"]] for row in previous["venue_matrix"]}
    new = {row["profile_ref"]: FIT_ORDER[row["fit"]] for row in current["venue_matrix"]}
    shared = set(old) & set(new)
    rises = any(new[ref] > old[ref] for ref in shared)
    falls = any(new[ref] < old[ref] for ref in shared)
    if delta == "UP" and (not rises or falls):
        _fail("invalid UP direction")
    if delta == "DOWN" and (not falls or rises):
        _fail("invalid DOWN direction")
    if delta == "UNCHANGED":
        if rises or falls or any(
            previous[field] != current[field]
            for field in ("current_target", "stretch_target")
        ):
            _fail("invalid UNCHANGED delta")
        if set(old) != set(new) and not current["delta_reasons"]:
            _fail("profile delta reasons required")


def load_assessment(root, review_version):
    root = _root(root)
    value = _assessment_record(root, _load_record(root, review_version), review_version)
    commit = value[G]
    try: kind = _git(root, "cat-file", "-t", commit)
    except ValueError as error:
        raise ValueError("assessment paper_git_sha is unavailable") from error
    if kind != "commit": _fail("assessment paper_git_sha must identify a commit")
    for ref in value[P]: _git_blob(root, commit, ref, PROFILE_MAX_BYTES)
    for ref in value[E]: _git_blob(root, commit, ref, EVIDENCE_MAX_BYTES)
    return value


def validate_assessment(root, request):
    root = _root(root)
    research_execution._actor_role(root)
    value = _validate_business(root, request)
    paper = pv.validate(root)
    if value["paper_version"] != paper["paper_version"]:
        _fail("paper_version mismatch")
    head = _git(root, "rev-parse", "HEAD")
    if value[G] != head:
        _fail("paper_git_sha mismatch")
    tokens = _bound_refs(root, value)
    by_ref = {token[0]: token for token in tokens}
    profiles = {
        ref: _profile_payload(ref, by_ref[ref][6]) for ref in value[P]
    }
    for row in value["venue_matrix"]:
        if row["venue"] != profiles[row["profile_ref"]]["venue"]:
            _fail("venue/profile mismatch")
    previous = _assessments(root)
    latest = previous[-1] if previous else None
    if latest is None:
        _validate_initial(value)
    else:
        _validate_transition(latest, value)
    return dict(value)


def record_assessment(root, request):
    root = _root(root)
    pv.transactions.recover(root)
    if _git(root, "status", "--porcelain"):
        _fail("dirty worktree")
    value = validate_assessment(root, request)
    paper = pv.validate(root)
    review_root = root / "paper/review"
    review_identity = pv._require_plain_directory(
        review_root, label="paper review directory"
    )
    version_path = review_root / "VERSION"
    old_version, old_bytes, old_leaf = pv._read_small_plain_payload(
        root, version_path, label="paper/review/VERSION", parents=(root / "paper", review_root))
    if old_version != paper[R]:
        _fail("review VERSION changed")
    if _git(root, "status", "--porcelain"):
        _fail("dirty worktree")
    if _git(root, "rev-parse", "HEAD") != value[G]:
        _fail("assessment HEAD changed")
    paper_text, paper_bytes, paper_leaf = _paper_binding(root)
    if paper_text != value["paper_version"]:
        _fail("paper/VERSION changed")
    ref_tokens = _bound_refs(root, value)
    current = old_version
    while True:
        path = review_root / f"review-{current}.yaml"
        if not os.path.lexists(path):
            break
        pv._require_plain_file(path, label="existing review")
        number = int(_REVIEW.fullmatch(current).group(1)) + 1
        if number > 999:
            _fail("review versions exhausted")
        current = f"v{number:03d}"
    document = _normalize({"schema_version": 1, "review_version": current, **value})
    payload = yaml.safe_dump(document, allow_unicode=True, sort_keys=False).encode("utf-8")
    if len(payload) > REVIEW_MAX_BYTES:
        _fail("oversize assessment")
    checked = _mapping(_yaml(payload.decode("utf-8"), "assessment output"),
                       RECORD_FIELDS, "assessment output")
    if (
        type(checked["schema_version"]) is not int
        or checked["schema_version"] != 1
        or checked[R] != current
    ):
        _fail("invalid output binding")
    _validate_business(root, {key: checked[key] for key in ASSESSMENT_FIELDS})
    if checked != document:
        _fail("output round-trip mismatch")
    document = checked
    record = pv._exclusive_yaml(
        path, document, root=root, expected_parent=review_identity
    )
    version_written = False
    written_leaf = None
    try:
        pv._verify_exclusive_record(record)
        _verify_binding(root, value[G], paper_bytes, paper_leaf,
                        {path.relative_to(root).as_posix()})
        _verify_refs(root, value[G], ref_tokens)
        written_leaf = pv._atomic_text(
            version_path, current + "\n", expected_parent=review_identity,
            expected_leaf=old_leaf, expected_bytes=old_bytes,
        )
        version_written = True
        pv._verify_exclusive_record(record)
        current_version, current_bytes, current_leaf = _review_binding(root)
        expected_version_bytes = (current + "\n").encode("utf-8")
        if (current_version != current or current_bytes != expected_version_bytes
                or current_leaf != written_leaf):
            _fail("review VERSION update failed")
        _verify_binding(root, value[G], paper_bytes, paper_leaf,
            {path.relative_to(root).as_posix(), version_path.relative_to(root).as_posix()},
            (expected_version_bytes, written_leaf))
        _verify_refs(root, value[G], ref_tokens)
        pv._verify_exclusive_record(record)
        final_version, final_bytes, final_leaf = _review_binding(root)
        if (final_version != current or final_bytes != expected_version_bytes
                or final_leaf != written_leaf):
            _fail("review VERSION closing check failed")
    except BaseException as error:
        compensation_error = None
        try:
            if version_written and written_leaf is not None:
                new_bytes = (current + "\n").encode("utf-8")
                try:
                    pv._atomic_text(
                        version_path, old_bytes.decode("utf-8"),
                        expected_parent=review_identity,
                        expected_leaf=written_leaf, expected_bytes=new_bytes,
                    )
                except ValueError:
                    raise RuntimeError("review VERSION competitor needs audit")
        except (OSError, UnicodeError, ValueError, RuntimeError) as caught:
            compensation_error = caught
        try:
            pv._close_exclusive_record(record, close_parent=False)
        except OSError as caught:
            if compensation_error is None:
                compensation_error = caught
        try:
            pv.transactions.quarantine(
                root, path, expected_identity=record["identity"],
                expected_payload=record["payload"],
                label="venue assessment record compensation",
                source_dir_fd=record["parent_fd"],
            )
        except (OSError, ValueError, RuntimeError) as caught:
            if compensation_error is None:
                compensation_error = caught
        if compensation_error is not None:
            raise RuntimeError("assessment compensation needs audit") from compensation_error
        raise error
    finally:
        pv._close_exclusive_record(record)
    return path
