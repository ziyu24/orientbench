#!/usr/bin/env python3
"""Verify the pinned Git source and execute an AST-derived isolated adapter."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


COMMIT = "c4467aec134e99691359da209f811d91283fc1e3"
REMOTE = "https://github.com/IML-DKFZ/fd-shifts.git"
EXPECTED_PATHS = {
    "rc_stats.py": "fd_shifts/analysis/rc_stats.py",
    "rc_stats_utils.py": "fd_shifts/analysis/rc_stats_utils.py",
}
VECTORS = {
    "tie": ([0.9, 0.8, 0.8, 0.1], [0.0, 1.0, 0.0, 1.0]),
    "binary": ([0.95, 0.6, 0.4, 0.2], [0.0, 1.0, 1.0, 0.0]),
    "continuous": ([0.91, 0.73, 0.41, 0.19], [0.1, 0.4, 0.8, 0.2]),
    "boundary": ([1.0, 0.0], [0.0, 1.0]),
}


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="microseconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(checkout: Path, hooks: Path, template: Path, *args: str, check: bool = True):
    command = [
        "git", "-C", str(checkout),
        "-c", f"core.hooksPath={hooks}",
        "-c", f"init.templateDir={template}",
        "-c", "submodule.recurse=false",
        "-c", "protocol.file.allow=never",
        *args,
    ]
    env = os.environ.copy()
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_LFS_SKIP_SMUDGE": "1",
    })
    result = subprocess.run(command, env=env, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(
            f"local git command failed: {command!r}: {result.stderr.decode(errors='replace')}"
        )
    return command, result


def source_segment(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    if segment is None:
        raise RuntimeError(f"cannot recover source span for {type(node).__name__}")
    return segment


def choose_nodes(path: str, source: str):
    tree = ast.parse(source, filename=path)
    selected = []
    for node in tree.body:
        keep = False
        if path.endswith("rc_stats_utils.py"):
            keep = (
                isinstance(node, (ast.Import, ast.ImportFrom))
                or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "generalized_risk_stats"
            )
        else:
            if isinstance(node, ast.Import):
                keep = any(alias.name in {"logging", "numpy", "numpy.typing"} for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                keep = node.module in {"functools", "typing"}
            elif isinstance(node, ast.ClassDef):
                keep = node.name in {"RiskCoverageStatsMixin", "RiskCoverageStats"}
        if keep:
            raw = source_segment(source, node)
            selected.append({
                "node_type": type(node).__name__,
                "name": getattr(node, "name", None),
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
                "col_offset": node.col_offset,
                "end_col_offset": node.end_col_offset,
                "raw_source": raw,
                "raw_source_bytes": len(raw.encode("utf-8")),
                "raw_source_sha256": sha256(raw.encode("utf-8")),
            })
    return tree, selected


def receipt_curve(score, residual):
    score = np.asarray(score, dtype=np.float64)
    residual = np.asarray(residual, dtype=np.float64)
    order = np.argsort(-score, kind="stable")
    sorted_score = score[order]
    sorted_residual = residual[order]
    starts = np.r_[0, np.flatnonzero(sorted_score[1:] != sorted_score[:-1]) + 1]
    counts = np.diff(np.r_[starts, len(score)])
    sums = np.add.reduceat(sorted_residual, starts)
    coverage = np.r_[0.0, np.cumsum(counts) / len(score)]
    risk = np.r_[0.0, np.cumsum(sums) / len(score)]
    return coverage, risk, float(np.trapz(risk, coverage))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--full-import-exit", type=int, required=True)
    parser.add_argument("--full-import-stdout", required=True)
    parser.add_argument("--full-import-stderr", required=True)
    args = parser.parse_args()
    def deny_network(event, _arguments):
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo"}:
            raise RuntimeError(f"network disabled during pinned reference adapter: {event}")
    sys.addaudithook(deny_network)
    checkout = args.checkout.resolve()
    reference_root = args.reference_root.resolve()
    hooks = reference_root / "empty-hooks"
    template = reference_root / "empty-template"
    started = now()

    commands = []
    command, remote_result = git(checkout, hooks, template, "remote", "get-url", "origin")
    commands.append(command)
    origin = remote_result.stdout.decode().strip()
    command, type_result = git(checkout, hooks, template, "cat-file", "-t", COMMIT)
    commands.append(command)
    object_type = type_result.stdout.decode().strip()
    command, head_result = git(checkout, hooks, template, "rev-parse", "HEAD")
    commands.append(command)
    head = head_result.stdout.decode().strip()
    command, symbolic = git(checkout, hooks, template, "symbolic-ref", "-q", "HEAD", check=False)
    commands.append(command)
    command, status_result = git(checkout, hooks, template, "status", "--porcelain=v1")
    commands.append(command)
    command, remotes_result = git(checkout, hooks, template, "remote")
    commands.append(command)
    command, submodule_result = git(checkout, hooks, template, "submodule", "status")
    commands.append(command)
    command, tree_result = git(checkout, hooks, template, "ls-tree", "-r", "--full-tree", COMMIT)
    commands.append(command)

    if origin != REMOTE or object_type != "commit" or head != COMMIT:
        raise RuntimeError("remote/commit/HEAD identity mismatch")
    if symbolic.returncode == 0 or status_result.stdout or remotes_result.stdout.decode().split() != ["origin"]:
        raise RuntimeError("checkout is not detached, clean, and single-remote")
    if submodule_result.stdout.strip():
        raise RuntimeError("submodule materialization detected")

    hits = {}
    for line in tree_result.stdout.decode().splitlines():
        left, rel = line.split("\t", 1)
        mode, obj_type, oid = left.split()
        basename = Path(rel).name
        if basename in EXPECTED_PATHS:
            hits.setdefault(basename, []).append((rel, mode, obj_type, oid))
    if set(hits) != set(EXPECTED_PATHS) or any(len(v) != 1 for v in hits.values()):
        raise RuntimeError(f"ambiguous required basename hits: {hits!r}")

    sources = {}
    source_identities = []
    for basename, expected_path in EXPECTED_PATHS.items():
        rel, mode, obj_type, oid = hits[basename][0]
        if rel != expected_path or obj_type != "blob":
            raise RuntimeError(f"unexpected source identity for {basename}: {hits[basename]!r}")
        command, blob_result = git(checkout, hooks, template, "cat-file", "blob", oid)
        commands.append(command)
        blob = blob_result.stdout
        checkout_bytes = (checkout / rel).read_bytes()
        if blob != checkout_bytes:
            raise RuntimeError(f"checkout/blob byte mismatch for {rel}")
        sources[rel] = blob.decode("utf-8")
        source_identities.append({
            "basename": basename,
            "path": rel,
            "mode": mode,
            "type": obj_type,
            "blob_oid": oid,
            "bytes": len(blob),
            "sha256": sha256(blob),
            "checkout_bytes_equal_blob": True,
        })

    adapter_parts = []
    adapter_nodes = []
    parsed = {}
    for rel in (EXPECTED_PATHS["rc_stats_utils.py"], EXPECTED_PATHS["rc_stats.py"]):
        tree, nodes = choose_nodes(rel, sources[rel])
        parsed[rel] = tree
        for node in nodes:
            adapter_parts.append(node["raw_source"])
            adapter_nodes.append({"source_path": rel, **{k: v for k, v in node.items() if k != "raw_source"}})

    scale_nodes = []
    for node in ast.walk(parsed[EXPECTED_PATHS["rc_stats.py"]]):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "AUC_DISPLAY_SCALE":
            raw = source_segment(sources[EXPECTED_PATHS["rc_stats.py"]], node)
            value = ast.literal_eval(node.value)
            scale_nodes.append({
                "node_type": type(node).__name__,
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
                "raw_source": raw,
                "raw_source_bytes": len(raw.encode()),
                "raw_source_sha256": sha256(raw.encode()),
                "value": value,
            })
    if len(scale_nodes) != 1 or scale_nodes[0]["value"] != 1000:
        raise RuntimeError(f"AUC_DISPLAY_SCALE is not uniquely pinned to 1000: {scale_nodes!r}")

    adapter_text = "\n\n".join(adapter_parts) + "\n"
    adapter_path = reference_root / "reference_adapter.py"
    adapter_path.write_text(adapter_text, encoding="utf-8")
    namespace = {}
    exec(compile(adapter_text, str(adapter_path), "exec"), namespace)
    risk_coverage_stats = namespace["RiskCoverageStats"]
    scale = int(namespace["RiskCoverageStatsMixin"].AUC_DISPLAY_SCALE)
    if scale != 1000:
        raise RuntimeError(f"runtime AUC_DISPLAY_SCALE mismatch: {scale}")

    vector_results = []
    for name, (score, residual) in VECTORS.items():
        score_np = np.asarray(score, dtype=np.float64)
        residual_np = np.asarray(residual, dtype=np.float64)
        stats = risk_coverage_stats(confids=score_np, residuals=residual_np)
        reference_curve = stats.curve_stats_generalized_risk
        reference_coverages = np.asarray(reference_curve["coverages"], dtype=np.float64)
        reference_risks = np.asarray(reference_curve["risks"], dtype=np.float64)
        display = float(stats.augrc)
        unscaled = display / scale
        receipt_coverages, receipt_risks, receipt_augrc = receipt_curve(score_np, residual_np)
        curve_ok = (
            np.allclose(reference_coverages[::-1], receipt_coverages, atol=1e-12, rtol=0)
            and np.allclose(reference_risks[::-1], receipt_risks, atol=1e-12, rtol=0)
        )
        augrc_ok = bool(np.isclose(unscaled, receipt_augrc, atol=1e-12, rtol=0))
        vector_results.append({
            "case": name,
            "score": score,
            "residual": residual,
            "call": "RiskCoverageStats(confids=score,residuals=residual).curve_stats_generalized_risk / .augrc",
            "reference_coverages_descending": reference_coverages.tolist(),
            "reference_risks_descending": reference_risks.tolist(),
            "reference_augrc_display": display,
            "reference_auc_display_scale": scale,
            "reference_augrc_unscaled": unscaled,
            "receipt_coverages_ascending": receipt_coverages.tolist(),
            "receipt_risks_ascending": receipt_risks.tolist(),
            "receipt_augrc_unscaled": receipt_augrc,
            "curve_atol_1e_12_pass": bool(curve_ok),
            "augrc_atol_1e_12_pass": augrc_ok,
        })
    if not all(row["curve_atol_1e_12_pass"] and row["augrc_atol_1e_12_pass"] for row in vector_results):
        raise RuntimeError("pinned reference dynamic behavior mismatch")

    result = {
        "status": "PASS",
        "started_at": started,
        "ended_at": now(),
        "verified_reference_path": str(checkout),
        "network_attempts_used": 1,
        "network_attempts_max": 3,
        "origin_url": origin,
        "commit_object_type": object_type,
        "head": head,
        "detached_head": True,
        "worktree_clean": True,
        "single_remote_origin": True,
        "submodule_materialization": False,
        "lfs_materialization": False,
        "local_identity_commands": commands,
        "source_identities": source_identities,
        "full_import": {
            "attempted": True,
            "exit_code": args.full_import_exit,
            "stdout_path": args.full_import_stdout,
            "stderr_path": args.full_import_stderr,
            "selected_execution_path": "FULL_IMPORT" if args.full_import_exit == 0 else "AST_ADAPTER",
        },
        "adapter": {
            "path": str(adapter_path.relative_to(args.runtime.resolve())),
            "bytes": len(adapter_text.encode()),
            "sha256": sha256(adapter_text.encode()),
            "assembly": "verbatim AST source segments joined by newline separators",
            "nodes": adapter_nodes,
        },
        "auc_display_scale_provenance": scale_nodes[0],
        "reference_auc_display_scale": scale,
        "vectors": vector_results,
        "atol": 1e-12,
        "rtol": 0,
    }
    output = args.runtime / "track_m_reference_check.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "execution_path": result["full_import"]["selected_execution_path"], "vectors": len(vector_results)}))


if __name__ == "__main__":
    main()
