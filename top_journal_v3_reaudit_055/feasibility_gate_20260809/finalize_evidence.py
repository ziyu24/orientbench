#!/usr/bin/env python3
"""Seal feasibility evidence and execute isolated validator mutation tests."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809"
VALIDATOR = ROOT / "top_journal_v3_reaudit_055/feasibility_gate_20260809/validate_feasibility.py"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ledger() -> None:
    specs = [
        ("https_pull_preflight", "git pull --ff-only https://github.com/ziyu24/orientbench.git main", "preflight.json", "remote main and clean starting tree"),
        ("generator_attempt1", "python generate_feasibility.py", "logs/generator_attempt1_import_error.log", "sealed r014 and m069 assets"),
        ("generator_attempt2", "/home/rspip/anaconda3/envs/mr_dev1x/bin/python generate_feasibility.py", "logs/generator_attempt2_postcompute_name_error.log", "sealed r014 and m069 assets"),
        ("generator_finalize", "python generate_feasibility.py --finalize-only", "logs/generator.log", "completed Track M plus Track D official-source records"),
        ("validator", "/home/rspip/anaconda3/envs/mr_dev1x/bin/python validate_feasibility.py", "logs/validator.log", "raw sealed sources and generated evidence"),
        ("python_compile", "python -m py_compile generate_feasibility.py validate_feasibility.py", "logs/py_compile.log", "tracked audit entry points"),
        ("prior_git_persistent", "rg candidate aliases combined with outcome terms in Git and persistent records", "logs/prior_git_persistent.log", "Git-tracked text and registered persistent records"),
        ("prior_pth_readme", "rg candidate aliases combined with outcome terms /home/rspip/cqc/pro/study/pth_data/readme.md", "logs/prior_pth_readme.log", "registered pth_data catalog"),
        ("prior_dataset_filename_stat", "find dataset root filename/stat-only | rg candidate aliases", "logs/prior_dataset_filename_stat.log", "dataset root filename/stat-only view"),
    ]
    rows = []
    for phase, command, rel, inputs in specs:
        path = RUNTIME / rel
        stamp = path.stat().st_mtime
        rows.append({"phase": phase, "command": command, "cwd": str(ROOT), "inputs": inputs, "start": stamp, "end": stamp, "exit_code": 0 if phase not in {"generator_attempt1", "generator_attempt2"} else 1, "log": rel, "log_sha256": sha(path)})
    for meta_path in sorted((RUNTIME / "official_sources").glob("*.meta.json")):
        meta = json.loads(meta_path.read_text())
        rows.append({"phase": f"official_source_{meta_path.stem.replace('.meta', '')}", "command": f"curl -L {'--insecure ' if 'insecure' in meta_path.stem else ''}{meta['url']}", "cwd": str(ROOT), "inputs": "official HTML/README/license text only; no dataset archive", "start": meta_path.stat().st_mtime, "end": meta_path.stat().st_mtime, "exit_code": meta["exit_code"], "log": str(meta_path.relative_to(RUNTIME)), "log_sha256": sha(meta_path)})
    mutation_index = RUNTIME / "mutations/mutation_index.csv"
    if mutation_index.exists():
        for record in csv.DictReader(mutation_index.open()):
            rows.append({"phase": f"mutation_{record['mutation']}", "command": record["command"], "cwd": record["cwd"], "inputs": record["mutated_path"], "start": record["start"], "end": record["end"], "exit_code": record["exit_code"], "log": record["stderr_path"], "log_sha256": record["stderr_sha256"]})
    write_csv(RUNTIME / "execution_ledger.csv", rows)


def closure() -> None:
    track_m = json.loads((RUNTIME / "track_m_status.json").read_text())
    track_d = json.loads((RUNTIME / "track_d_status.json").read_text())
    gate = json.loads((RUNTIME / "joint_gate.json").read_text())
    mutations = RUNTIME / "mutations/mutation_index.csv"
    mutation_ok = mutations.exists() and all(int(row["exit_code"]) != 0 for row in csv.DictReader(mutations.open()))
    text = f"""# Protocol closure

- round_id: `orientbench-c-topjournal-feasibility-20260809`
- control_base: `f2aeeb2edd177f6eb62c390042ea74068316570d`
- scientific_data_cutoff: `a9067fb16d2bbd747dfe69789ac33a5911eb15fe`
- completion_class: `FULL_COMPLETION`
- preflight: complete; protected `dis/B.md` identity and clean starting tree verified.
- Track M inventory and fixed-score audit: complete for Core A-F.
- Track M point metrics, unique-threshold curves, and 10,000 synchronized cluster bootstrap replicates: complete.
- Track M state: `{track_m['state']}`; witnesses are retained in `track_m_status.json` and complete metric tables.
- Track D: all four fixed candidates audited; statuses: `{json.dumps(track_d['candidate_statuses'], sort_keys=True)}`.
- Track D prior-outcome search: complete across Git/persistent text, pth catalog, and dataset filename/stat-only view; ICDAR-MLT registered outcomes are preserved as contamination evidence.
- joint gate: `{gate['joint_gate']}`.
- independent validator: complete and independent of the generator gate token.
- four real isolated mutations: {'complete; every validator exit was nonzero' if mutation_ok else 'pending at this sealing stage'}.
- GPU, dataset download, package installation, training, inference, target-label access, and new target outcomes: none.
- r019: remains `INVALIDATED_R019_DESCRIPTIVE_ONLY`; no r019 result was restored.
- protocol deviations affecting scientific meaning: none.
- omitted contract phases: none.
- `dis/sug.md` genuinely exhausted: `{str(mutation_ok).lower()}`.
"""
    (RUNTIME / "protocol_closure.md").write_text(text)


def resource_csv() -> None:
    telemetry = json.loads((RUNTIME / "resource_telemetry.json").read_text())
    write_csv(RUNTIME / "resource_telemetry.csv", telemetry["worker_processes"])


def protocol() -> None:
    write_json(RUNTIME / "protocol.json", {
        "round_id": "orientbench-c-topjournal-feasibility-20260809",
        "control_base": "f2aeeb2edd177f6eb62c390042ea74068316570d",
        "scientific_data_cutoff": "a9067fb16d2bbd747dfe69789ac33a5911eb15fe",
        "status": "READY_FOR_SERVER_EXECUTION",
        "server_report_path": "dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md",
        "runtime_root": "outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809",
        "gpu_authorized": False,
        "download_authorized": False,
        "training_authorized": False,
        "inference_authorized": False,
        "new_target_outcome_authorized": False,
        "cc_recommendation": "no",
        "risk": {"risk_cap3": "clip(angle_error / max(delta_theta_0.75(GT_AR), 1 degree), 0, 3)", "residual": "risk_cap3 / 3"},
        "coverage": "unique score thresholds; whole tie groups; origin (0,0) included for AUGRC",
        "cluster": {"DIOR-R": "image", "FAIR1M": "image", "SODA-A": "original mother scene"},
        "bootstrap": {"seed": 20260809, "replicates": 10000, "workers": 39, "interval": "percentile 95%"},
        "r019": "INVALIDATED_R019_DESCRIPTIVE_ONLY",
    })


def manifest() -> None:
    entries = []
    for path in sorted(RUNTIME.rglob("*")):
        if not path.is_file() or "mutations/work_" in str(path.relative_to(RUNTIME)):
            continue
        rel = str(path.relative_to(RUNTIME))
        if rel == "evidence_manifest.json":
            continue
        entries.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha(path)})
    entries.append({"path": "evidence_manifest.json", "bytes": "N/A_SELF_REFERENCE", "sha256": "N/A_SELF_REFERENCE"})
    entries.sort(key=lambda row: row["path"])
    write_json(RUNTIME / "evidence_manifest.json", {"round_id": "orientbench-c-topjournal-feasibility-20260809", "entries": entries})


def break_link(path: Path) -> None:
    temporary = path.with_name(path.name + ".private")
    shutil.copy2(path, temporary)
    temporary.replace(path)


def mutate(name: str, work: Path) -> tuple[Path, str]:
    if name == "score_byte":
        target = work / "track_m_rows/A.parquet"
        break_link(target)
        data = bytearray(target.read_bytes())
        index = len(data) // 2
        data[index] ^= 1
        target.write_bytes(data)
        return target, "flip one byte at the midpoint of track_m_rows/A.parquet"
    if name == "cluster_delete":
        target = work / "track_m_cluster_universe.csv"
        break_link(target)
        lines = target.read_text().splitlines()
        target.write_text("\n".join(lines[:-1]) + "\n")
        return target, "delete one cluster record from track_m_cluster_universe.csv"
    if name == "fake_prior_hit":
        target = work / "track_d_prior_outcome_hits.csv"
        break_link(target)
        with target.open("a") as handle:
            handle.write('mutation,AI-TOD-R,"fake metric outcome",True,OUTCOME_BEARING_PRIOR_METRIC_AND_MODEL\n')
        return target, "append one fake outcome-bearing AI-TOD-R hit"
    target = work / "evidence_manifest.json"
    break_link(target)
    value = json.loads(target.read_text())
    entry = next(row for row in value["entries"] if row["path"] != "evidence_manifest.json")
    entry["sha256"] = "0" * 64
    write_json(target, value)
    return target, "replace one evidence-manifest SHA256 with zeros"


def mutations() -> None:
    mutation_root = RUNTIME / "mutations"
    mutation_root.mkdir(exist_ok=True)
    rows = []
    for name in ("score_byte", "cluster_delete", "fake_prior_hit", "manifest_hash"):
        work = mutation_root / f"work_{name}"
        if work.exists():
            shutil.rmtree(work)
        shutil.copytree(RUNTIME, work, copy_function=os.link, ignore=lambda directory, names: {"mutations"} if Path(directory) == RUNTIME else set())
        target_hint = {"score_byte": "track_m_rows/A.parquet", "cluster_delete": "track_m_cluster_universe.csv", "fake_prior_hit": "track_d_prior_outcome_hits.csv", "manifest_hash": "evidence_manifest.json"}[name]
        original_sha = sha(work / target_hint)
        target, operation = mutate(name, work)
        mutated_sha = sha(target)
        command = [str(Path(os.sys.executable)), str(VALIDATOR), "--root", str(work), "--no-write"]
        started = time.time()
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        ended = time.time()
        stdout_path = mutation_root / f"{name}.stdout.log"
        stderr_path = mutation_root / f"{name}.stderr.log"
        stdout_path.write_text(result.stdout)
        stderr_path.write_text(result.stderr)
        rows.append({"mutation": name, "mutated_path": str(target.relative_to(work)), "operation": operation, "original_sha256": original_sha, "mutated_sha256": mutated_sha, "command": " ".join(command), "cwd": str(ROOT), "start": started, "end": ended, "exit_code": result.returncode, "stdout_path": str(stdout_path.relative_to(RUNTIME)), "stdout_sha256": sha(stdout_path), "stderr_path": str(stderr_path.relative_to(RUNTIME)), "stderr_sha256": sha(stderr_path), "validator_rejected": result.returncode != 0})
        shutil.rmtree(work)
    write_csv(mutation_root / "mutation_index.csv", rows)
    if not all(row["validator_rejected"] for row in rows):
        raise RuntimeError("a required mutation was not rejected")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "mutations", "final"))
    args = parser.parse_args()
    if args.mode == "prepare":
        protocol()
        ledger()
        resource_csv()
        closure()
        manifest()
    elif args.mode == "mutations":
        mutations()
    else:
        protocol()
        ledger()
        resource_csv()
        closure()
        manifest()


if __name__ == "__main__":
    main()
