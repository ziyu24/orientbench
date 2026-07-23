#!/usr/bin/env python3
"""Final machine-side auditor and freeze gate for Command 070."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
REPORTS = ROOT / "reports"
STATUS = REPORTS / "m4_third_dataset_job_status"
TOOL = ROOT / "annotation_tools/m4_angle_annotation"
EXPECTED_THRESHOLD = "b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
HEADS = ("PSC", "CSL", "DCL")
SEEDS = (0, 1, 2)


def rows(path: Path) -> list[dict]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"missing nonempty CSV: {path}")
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, output: list[dict]) -> None:
    if not output:
        raise RuntimeError(f"refuse empty output: {path}")
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    os.replace(temp, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def append_once(path: Path, marker: str, body: str) -> None:
    text = path.read_text() if path.is_file() else ""
    if marker in text:
        before = text.split(marker, 1)[0].rstrip()
        end_marker = marker.replace("START", "END")
        after = text.split(end_marker, 1)[1].lstrip() if end_marker in text else ""
        text = before + ("\n\n" + after if after else "")
    path.write_text(text.rstrip() + "\n\n" + body.strip() + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    args = parser.parse_args()
    log_path = ROOT / args.log

    pilot = rows(REPORTS / "m4_third_dataset_pilot_results.csv")
    selection = rows(REPORTS / "m4_third_dataset_lr_selection.csv")
    seed_results = rows(REPORTS / "m4_third_dataset_seed_results.csv")
    variance = rows(REPORTS / "m4_third_dataset_seed_variance.csv")
    bootstrap = rows(REPORTS / "m4_third_dataset_bootstrap_intervals.csv")
    detailed = rows(REPORTS / "m4_optional_third_dataset_results.csv")
    manifest = rows(REPORTS / "m4_third_dataset_artifact_manifest.csv")
    validation = rows(REPORTS / "m4_human_annotation_package_validation.csv")

    pilot_statuses = [r["status"] for r in pilot]
    require(len(pilot) == 9 and all(s in {"complete", "FAILED_BY_PREREGISTERED_GATE"}
                                    for s in pilot_statuses), "pilot matrix incomplete")
    require(pilot_statuses.count("FAILED_BY_PREREGISTERED_GATE") <= 1,
            "unexpected number of preregistered pilot gate failures")
    require(len(selection) == 3 and {r["head"] for r in selection} == set(HEADS), "LR selection incomplete")
    require(len(seed_results) == 9, "final matrix incomplete")
    require({(r["head"], int(r["seed"])) for r in seed_results} ==
            {(h, s) for h in HEADS for s in SEEDS}, "final head/seed matrix mismatch")
    require(all(r["status"] == "COMPLETE" for r in seed_results), "non-complete final evaluation")
    require(len(variance) == 3 and len(bootstrap) == 18, "variance/bootstrap schema incomplete")
    require(any(r.get("scope") == "decision" and r.get("group") in
                {"REPLICATES_A", "PARTIAL_REPLICATION", "DOES_NOT_REPLICATE"}
                for r in detailed), "scientific decision absent")

    status_records = []
    for row in pilot + seed_results:
        record = json.loads((STATUS / f"{row['run_id']}.json").read_text())
        require(record["status"] in {"complete", "FAILED_BY_PREREGISTERED_GATE"},
                f"invalid terminal status: {row['run_id']}")
        require(record["gpu_count"] == 4 and record["cuda_visible_devices"] == "0,1,2,3",
                f"four-GPU invariant failed: {row['run_id']}")
        if record["status"] == "complete":
            require(all(a["status"] not in {"process_failure", "nan_or_inf", "empty_or_degenerate_prediction"}
                        for a in record["attempts"]), f"invalid attempt entered result: {row['run_id']}")
        else:
            require(row["run_id"] == "M4_070_pilot__DCL__FAIR1M__lr0.01" and
                    all(a["status"] == "empty_or_degenerate_prediction" for a in record["attempts"]),
                    "pilot failure was not the frozen DCL LR quality gate")
        status_records.append((row["run_id"], record))
    seed0_mtime = max((STATUS / f"M4_070_final__{h}__FAIR1M__seed0.json").stat().st_mtime for h in HEADS)
    later_mtime = min((STATUS / f"M4_070_final__{h}__FAIR1M__seed{s}.json").stat().st_mtime
                      for h in HEADS for s in (1, 2))
    require(seed0_mtime <= later_mtime, "seed1/2 launched before all seed0 gates")

    for item in manifest:
        path = ROOT / item["artifact"]
        require(path.is_file() and path.stat().st_size == int(item["bytes"]), f"artifact size mismatch: {path}")
        require(sha256(path) == item["sha256"], f"artifact hash mismatch: {path}")
        require(item["depends_on_dev_shm"].lower() == "false" and "/dev/shm" not in item["artifact"],
                f"formal artifact depends on /dev/shm: {path}")

    required_checks = {
        "annotator_A_package", "annotator_B_package", "different_anonymous_ids",
        "same_target_set", "different_random_order", "blind_schema",
        "dataset_sampling_and_source_validation", "browser_start_save_restore_export_csv_json",
        "merge_script_smoke", "disagreement_analysis_smoke", "smoke_data_isolated_from_formal_results",
    }
    require(required_checks <= {r["check"] for r in validation}, "annotation validation checks missing")
    require(all(r["status"] == "PASS" for r in validation), "annotation package validation failed")
    for slot in ("A", "B"):
        tasks = rows(TOOL / f"annotator_{slot}/tasks.csv")
        require(len(tasks) == 1500, f"annotator {slot} task count")
        require(all(not r["long_side_angle_deg_le90"] and not r["annotator_id"] for r in tasks),
                f"annotator {slot} package contains labels")
    require(not (TOOL / "annotator_A/annotatorA_raw.csv").exists() and
            not (TOOL / "annotator_B/annotatorB_raw.csv").exists(), "formal human output unexpectedly exists")
    human_audit = json.loads((REPORTS / "m4_human_annotation_merge_audit.json").read_text())
    require(human_audit.get("status") == "HUMAN_BLOCKED" and human_audit.get("human_usable") == 0,
            "human status must remain HUMAN_BLOCKED")

    require(sha256(ROOT / "configs/thresholds.yaml") == EXPECTED_THRESHOLD, "thresholds.yaml changed")
    frozen = rows(REPORTS / "069_final_reproduction_status.csv")
    require(all(r["status"] == "PASS" for r in frozen if r["scope"] == "frozen"), "069 frozen assets no longer pass")
    require("`selected_dataset`: FAIR1M-v1.0" in (ROOT / "docs/m4_optional_third_dataset_extension.md").read_text(),
            "FAIR1M selection not frozen")
    process_text = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True,
                                  text=True, check=True).stdout
    active = [line.strip() for line in process_text.splitlines()
              if ("scripts/run_m4_third_dataset_070.py" in line or
                  "scripts/m4_third_dataset_train_job_070.py" in line or
                  ("torch.distributed.run" in line and "m4_third_dataset_070" in line))
              and "verify_m4_command_070.py" not in line]
    require(not active, f"M4 training process still active: {active}")
    log_text = log_path.read_text() if log_path.is_file() else ""
    for step in ("m4_third_dataset_aggregate", "m4_annotation_package", "m4_human_merge_gate", "m4_human_analysis_gate"):
        require(f"STEP_OK {step}" in log_text, f"reproduction step absent: {step}")

    reproduction = [
        {"check": "9 pilots", "status": "PASS", "evidence": "3 heads x 3 frozen LR candidates; DCL lr=0.01 rejected by frozen quality gate after AMP+FP32"},
        {"check": "9 finals", "status": "PASS", "evidence": "3 heads x 3 seeds; all full-val evaluations COMPLETE"},
        {"check": "four-GPU scheduling", "status": "PASS", "evidence": "all 18 statuses gpu_count=4 devices=0,1,2,3"},
        {"check": "seed0 gate", "status": "PASS", "evidence": "all seed0 status mtimes precede seed1/2"},
        {"check": "persistent artifact chain", "status": "PASS", "evidence": f"{len(manifest)} hashes verified; no /dev/shm dependency"},
        {"check": "annotation package", "status": "PASS", "evidence": "A/B blind packages and browser/merge/analysis smoke passed"},
        {"check": "human results", "status": "HUMAN_BLOCKED", "evidence": "0 real mutually blind pairs; not synthesized"},
    ]
    write_csv(REPORTS / "070_machine_reproduction_status.csv", reproduction)

    old_gate = {r["condition"]: r for r in rows(REPORTS / "069_submission_freeze_gate.csv")}
    gate = [
        {"condition": "M1", "status": old_gate["M1 ar>=2.1 unified"]["status"], "evidence": "069 frozen result unchanged", "blocking": "False"},
        {"condition": "M2", "status": old_gate["M2 decided"]["status"], "evidence": old_gate["M2 decided"]["evidence"], "blocking": "False"},
        {"condition": "M3", "status": old_gate["M3 image-level guarantee"]["status"], "evidence": "069 frozen result unchanged", "blocking": "False"},
        {"condition": "geometry-normalized risk", "status": old_gate["geometry-normalized risk"]["status"], "evidence": "069 frozen result unchanged", "blocking": "False"},
        {"condition": "Phase 1", "status": old_gate["PSC Phase 1 terminal decision"]["status"], "evidence": old_gate["PSC Phase 1 terminal decision"]["evidence"], "blocking": "False"},
        {"condition": "M4 third dataset", "status": "PASS", "evidence": "9 pilots + 9 finals + full-val aggregation", "blocking": "False"},
        {"condition": "human annotation", "status": "HUMAN_BLOCKED", "evidence": "execution packages complete; real labels=0", "blocking": "True"},
        {"condition": "one-click reproduction", "status": "PASS", "evidence": "070 machine chain and hashes verified", "blocking": "False"},
        {"condition": "FINAL", "status": "NOT_FROZEN", "evidence": "human annotation is the remaining blocker", "blocking": "True"},
    ]
    write_csv(REPORTS / "070_submission_freeze_gate.csv", gate)

    decision = next(r["group"] for r in detailed if r.get("scope") == "decision")
    doc_marker = "<!-- CODEX_070_REPRO_START -->"
    doc_body = f"""{doc_marker}
## Command 070 machine reproduction

- Entry point: `bash scripts/reproduce_all_main_tables.sh --070-machine-only`
- M4 FAIR1M: 9/9 pilots and 9/9 final runs verified; decision `{decision}`.
- Recomputed from persistent final evaluations: seed results, variance, image-cluster bootstrap, strata decision, and artifact hashes.
- Annotation A/B packages: 1500 tasks each; blind-schema, browser save/restore/export, merge, and disagreement smoke checks pass.
- Real human annotations: 0; state `HUMAN_BLOCKED`. Test labels remain isolated under `/dev/shm` and are not formal results.
- Final gate: `NOT_FROZEN` solely because two real mutually blind annotation submissions are absent.
<!-- CODEX_070_REPRO_END -->"""
    append_once(ROOT / "docs/third_party_reproduction_log.md", doc_marker, doc_body)

    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    record_marker = "<!-- CODEX_070_FINAL_START -->"
    record = f"""{record_marker}
## [{now}] 命令 070 完成

- 指令来源：用户命令 070；只完成 M4 FAIR1M 第三数据集扩展和三数据集人工双标执行包。
- 执行动作：9 个等预算 pilot、9 个 4-GPU final runs、full-val 原生不确定性评测、三 seed 聚合、A/B 互盲包和机器复算。
- 决策：第三数据集 `{decision}`；人工真实结果 0，状态 `HUMAN_BLOCKED`；提交冻结门控 `NOT_FROZEN`。
- 关键产物：`reports/m4_optional_third_dataset_results.csv`、`reports/m4_third_dataset_seed_results.csv`、`reports/m4_third_dataset_artifact_manifest.csv`、`reports/m4_human_annotation_package_validation.csv`、`reports/070_submission_freeze_gate.csv`、`logs/reproduce_all_main_tables_070.log`。
- 合规：thresholds 与 D_cal/D_audit 未改；host/K2/PSC 未重跑；未追 public mAP；未伪造人工标注；无范围外工作。
- 停止条件：真人双标缺失是唯一冻结 blocker。下一正式命令编号：071。
<!-- CODEX_070_FINAL_END -->"""
    append_once(ROOT / "claude_code_and_supervisor.md", record_marker, record)
    print(f"M4_070_VERIFIED decision={decision} final=NOT_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
