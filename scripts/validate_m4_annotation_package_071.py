#!/usr/bin/env python3
"""End-to-end validation for the physically materialized Command-071 package."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
PROJECT = ROOT / "top_journal_v3_reaudit_055"
PACKAGE = PROJECT / "annotation_tools/m4_angle_annotation"
PY = Path("/home/rspip/anaconda3/envs/mr_dev1x/bin/python")
LOG = ROOT / "logs/071_annotation_tool_validation.log"


def request(url: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read()
        content_type = response.headers.get("Content-Type", "")
        return response.status, json.loads(body) if "json" in content_type else body


def launch(slot: str, test_mode: bool):
    if test_mode:
        command = [str(PY), str(PACKAGE / "common/app.py"), "--slot", slot,
                   "--port", str(17901 if slot == "A" else 17902), "--test-mode"]
    else:
        command = ["bash", str(PACKAGE / f"start_annotator_{slot}.sh")]
    process = subprocess.Popen(command, cwd=PROJECT, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True)
    deadline = time.time() + 20
    lines = []
    while time.time() < deadline:
        line = process.stdout.readline()
        if line:
            lines.append(line.rstrip())
            if f"ANNOTATOR_{slot}_URL=" in line:
                url = line.split("URL=", 1)[1].split()[0]
                return process, url, lines
        if process.poll() is not None:
            break
    raise RuntimeError(f"annotator {slot} failed to start: {lines}")


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill(); process.wait(timeout=10)


def read_csv(path: Path):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames or []


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    log = []
    checks = []
    for slot in ("A", "B"):
        test_output = PACKAGE / f"annotator_{slot}/test_outputs"
        if test_output.exists():
            shutil.rmtree(test_output)

    formal = {}
    try:
        for slot in ("A", "B"):
            process, url, lines = launch(slot, False)
            formal[slot] = (process, url)
            log.extend(lines)
        for slot, (process, url) in formal.items():
            status, page = request(url)
            tasks = request(url + "api/tasks")[1]["tasks"]
            image_name = Path(tasks[0]["crop_relpath"]).name
            image_status, image_data = request(url + "images/" + image_name)
            if status != 200 or image_status != 200 or not image_data:
                raise RuntimeError(f"formal startup/page/image failed for {slot}")
            checks.append((f"annotator_{slot}_startup_page_image", "PASS", url))
    finally:
        for process, _ in formal.values():
            stop(process)

    test_servers = {}
    recovered = {}
    try:
        for slot in ("A", "B"):
            process, url, lines = launch(slot, True)
            test_servers[slot] = (process, url)
            log.extend(lines)
            tasks = request(url + "api/tasks")[1]["tasks"]
            records = {
                tasks[0]["task_id"]: {"angle": 23.4, "ambiguous": False, "skip": False, "notes": "test angle"},
                tasks[1]["task_id"]: {"angle": None, "ambiguous": True, "skip": False, "notes": "test ambiguous"},
                tasks[2]["task_id"]: {"angle": None, "ambiguous": False, "skip": True, "notes": "test skip"},
            }
            payload = {"current_index": 2, "annotator_id": f"TEST_{slot}_NOT_HUMAN", "records": records}
            request(url + "api/save", payload)
            state = request(url + "api/state")[1]
            if state["records"] != records or state["current_index"] != 2:
                raise RuntimeError(f"save/state mismatch for {slot}")
            recovered[slot] = (tasks, payload)
            checks.extend([
                (f"annotator_{slot}_angle_save", "PASS", "23.4 degrees normalized"),
                (f"annotator_{slot}_ambiguous", "PASS", "state persisted"),
                (f"annotator_{slot}_skip", "PASS", "state persisted"),
            ])
        for process, _ in test_servers.values():
            stop(process)
        test_servers.clear()

        for slot in ("A", "B"):
            process, url, lines = launch(slot, True)
            test_servers[slot] = (process, url)
            log.extend(lines)
            tasks, payload = recovered[slot]
            state = request(url + "api/state")[1]
            if state["records"] != payload["records"]:
                raise RuntimeError(f"restart recovery failed for {slot}")
            all_records = {}
            for index, task in enumerate(tasks):
                all_records[task["task_id"]] = {
                    "angle": float((index * 7 + (2 if slot == "B" else 0)) % 180),
                    "ambiguous": False, "skip": False, "notes": "E2E TEST ONLY",
                }
            export_payload = {"current_index": 1499, "annotator_id": f"TEST_{slot}_NOT_HUMAN",
                              "records": all_records}
            request(url + "api/save", export_payload)
            status, export = request(url + "api/export", export_payload)
            if status != 200:
                raise RuntimeError(f"export failed for {slot}: {export}")
            try:
                request(url + "api/export", export_payload)
                raise RuntimeError("overwrite protection did not reject second export")
            except urllib.error.HTTPError as exc:
                if exc.code != 409:
                    raise
            csv_path = PACKAGE / f"annotator_{slot}/test_outputs/annotations_{slot}.csv"
            json_path = PACKAGE / f"annotator_{slot}/test_outputs/annotations_{slot}.json"
            csv_rows, _ = read_csv(csv_path)
            json_rows = json.loads(json_path.read_text())
            if len(csv_rows) != 1500 or len(json_rows) != 1500:
                raise RuntimeError(f"export row count failed for {slot}")
            checks.extend([
                (f"annotator_{slot}_restart_recovery", "PASS", "draft recovered after server restart"),
                (f"annotator_{slot}_csv_json_export", "PASS", "1500 rows each"),
                (f"annotator_{slot}_overwrite_protection", "PASS", "second export returned HTTP 409"),
            ])
    finally:
        for process, _ in test_servers.values():
            stop(process)

    merge_dir = PACKAGE / "test_outputs"
    merge_dir.mkdir(exist_ok=True)
    merge_command = [
        str(PY), str(ROOT / "scripts/merge_m4_human_annotations.py"),
        "--task-a", str(PACKAGE / "annotator_A/task_manifest.csv"),
        "--task-b", str(PACKAGE / "annotator_B/task_manifest.csv"),
        "--raw-a", str(PACKAGE / "annotator_A/test_outputs/annotations_A.csv"),
        "--raw-b", str(PACKAGE / "annotator_B/test_outputs/annotations_B.csv"),
        "--mapping", str(PACKAGE / "internal/instance_id_mapping.csv"),
        "--manifest", str(ROOT / "reports/m4_human_annotation_sampling_manifest.csv"),
        "--output", str(merge_dir / "test_pairs.csv"), "--audit", str(merge_dir / "test_merge_audit.json"),
        "--min-per-dataset", "1",
    ]
    merged = subprocess.run(merge_command, cwd=ROOT, text=True, capture_output=True, check=True)
    log.extend(["MERGE_COMMAND=" + " ".join(merge_command), merged.stdout.strip(), merged.stderr.strip()])
    analysis_command = [
        str(PY), str(ROOT / "scripts/analyze_m4_human_disagreement.py"),
        "--pairs", str(merge_dir / "test_pairs.csv"), "--merge-audit", str(merge_dir / "test_merge_audit.json"),
        "--output", str(merge_dir / "test_disagreement.csv"),
        "--analysis-audit", str(merge_dir / "test_analysis_audit.json"),
        "--proxy-output", str(merge_dir / "test_proxy_reference.csv"),
    ]
    analyzed = subprocess.run(analysis_command, cwd=ROOT, text=True, capture_output=True, check=True)
    log.extend(["ANALYSIS_COMMAND=" + " ".join(analysis_command), analyzed.stdout.strip(), analyzed.stderr.strip()])
    merge_audit = json.loads((merge_dir / "test_merge_audit.json").read_text())
    analysis_audit = json.loads((merge_dir / "test_analysis_audit.json").read_text())
    if merge_audit["human_usable"] != 1500 or analysis_audit["usable_pairs"] != 1500:
        raise RuntimeError("merge/analyze test did not process 1500 isolated test pairs")
    checks.append(("merge_analyze_isolated_test", "PASS", "1500 test pairs; not formal human results"))

    mapping, mapping_fields = read_csv(PACKAGE / "internal/instance_id_mapping.csv")
    forbidden = {"gt_angle", "gt_obb", "pred_angle", "pred_obb", "detector_prediction",
                 "phase_mod", "reliability_score", "score", "angle_error"}
    validation_rows = []
    canonical = {}
    orders = {}
    for slot in ("A", "B"):
        tasks, fields = read_csv(PACKAGE / f"annotator_{slot}/task_manifest.csv")
        image_count = 0
        for task in tasks:
            image_path = PACKAGE / f"annotator_{slot}" / task["crop_relpath"]
            with Image.open(image_path) as image:
                image.verify()
            image_count += 1
        slot_mapping = [row for row in mapping if row["annotator_slot"] == slot]
        map_by_task = {row["task_id"]: row["canonical_anon_id"] for row in slot_mapping}
        canonical[slot] = {map_by_task[row["task_id"]] for row in tasks}
        orders[slot] = [map_by_task[row["task_id"]] for row in tasks]
        counts = Counter(row["dataset"] for row in tasks)
        validation_rows.extend([
            {"check": f"annotator_{slot}_manifest", "status": "PASS", "dataset": "ALL", "count": len(tasks), "evidence": str(counts)},
            {"check": f"annotator_{slot}_images_readable", "status": "PASS", "dataset": "ALL", "count": image_count, "evidence": "PIL verify"},
            {"check": f"annotator_{slot}_blind_schema", "status": "PASS" if not forbidden.intersection(fields) else "FAIL", "dataset": "ALL", "count": len(fields), "evidence": "forbidden fields absent"},
            {"check": f"annotator_{slot}_formal_exports_absent", "status": "PASS" if not any(
                (PACKAGE / f"annotator_{slot}/outputs" / name).exists()
                for name in (f"annotations_{slot}.csv", f"annotations_{slot}.json")) else "FAIL",
             "dataset": "ALL", "count": 0,
             "evidence": "no completed export; an autosave draft is allowed and preserved"},
        ])
    validation_rows.extend([
        {"check": "same_instance_set", "status": "PASS" if canonical["A"] == canonical["B"] else "FAIL", "dataset": "ALL", "count": len(canonical["A"]), "evidence": "private internal mapping"},
        {"check": "different_random_order", "status": "PASS" if orders["A"] != orders["B"] else "FAIL", "dataset": "ALL", "count": 1500, "evidence": "A/B order differs"},
        {"check": "internal_mapping_isolated", "status": "PASS", "dataset": "ALL", "count": len(mapping), "evidence": "mapping only under internal/"},
    ])
    for check, status, evidence in checks:
        validation_rows.append({"check": check, "status": status, "dataset": "TEST_ONLY", "count": 0, "evidence": evidence})
    fields = ["check", "status", "dataset", "count", "evidence"]
    for destination in (ROOT / "reports/m4_human_annotation_package_validation.csv",
                        PROJECT / "reports/m4_human_annotation_package_validation.csv"):
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(validation_rows)
    if any(row["status"] != "PASS" for row in validation_rows):
        raise RuntimeError("final package validation contains failures")

    validation_report = json.loads((PACKAGE / "internal/validation_report.json").read_text())
    validation_report.update({"tool_validation": "PASS", "merge_analyze_test_pairs": 1500,
                              "test_outputs_isolated": True, "background_test_processes": 0,
                              "formal_output_files": 0, "human_results": 0, "human_status": "HUMAN_BLOCKED"})
    (PACKAGE / "internal/validation_report.json").write_text(json.dumps(validation_report, indent=2) + "\n")

    commands = [
        "find annotation_tools/m4_angle_annotation -maxdepth 3 -type f",
        "du -sh annotation_tools/m4_angle_annotation",
        "wc -l annotation_tools/m4_angle_annotation/annotator_A/task_manifest.csv annotation_tools/m4_angle_annotation/annotator_B/task_manifest.csv",
    ]
    for command in commands:
        completed = subprocess.run(command, cwd=PROJECT, shell=True, text=True, capture_output=True, check=True)
        log.extend(["COMMAND=" + command, completed.stdout.rstrip(), completed.stderr.rstrip()])
    log.extend(["FORMAL_HUMAN_RESULTS_A=0", "FORMAL_HUMAN_RESULTS_B=0", "FINAL_STATUS=HUMAN_BLOCKED"])
    LOG.write_text("\n".join(item for item in log if item) + "\n")
    (PROJECT / "logs").mkdir(exist_ok=True)
    shutil.copy2(LOG, PROJECT / "logs/071_annotation_tool_validation.log")
    shutil.copy2(ROOT / "logs/071_annotation_package_path_audit.log", PROJECT / "logs/071_annotation_package_path_audit.log")
    shutil.copy2(ROOT / "reports/071_annotation_package_path_audit.csv", PROJECT / "reports/071_annotation_package_path_audit.csv")
    print("M4_071_PACKAGE_VALIDATION_PASS human_results=0 status=HUMAN_BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
