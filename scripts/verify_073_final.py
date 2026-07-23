#!/usr/bin/env python3
"""Verify the final statistical chain and write the collaborator-review gate."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "reports"
LOG = ROOT / "logs/reproduce_all_main_tables_073.log"
PAPER = ROOT / "docs/paper_A_zh_post_human_073/orientation_reliability_paper_A_zh.md"

THRESHOLD_SHA = "b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
SPLITS = {
    "outputs/bench_core/splits/D_audit_dior_trainval.csv": "11c61be3a03c922b5e00e4cf9e866cf73e18eff44bd6b868b53f54612065669b",
    "outputs/bench_core/splits/D_audit_dota10_train.csv": "d4fb9a793a4c2f31ddd42cde0ba8c571114e78b2ab0d3af36002f201fafc1eb7",
    "outputs/bench_core/splits/D_audit_dota15_train.csv": "ac97d1f3f2a780f79019612fce6f7f93d13aa9f7a65c4f1c14aa96447e743856",
    "outputs/bench_core/splits/D_audit_fair1m_train.csv": "140ef6855909cdca2904656ad76baca31ff11d8c571e3978e005d945440c335e",
    "outputs/bench_core/splits/D_audit_hrsc_trainval.csv": "55734ae8aa3f49350186fd066a761a54fe1a99921897012c5e59ca1fdf9f6679",
    "outputs/bench_core/splits/D_cal_dior_trainval.csv": "f624a21451de394a35041af35c9a910c3a1bdc11fb5c942d15416e04e0e6f632",
    "outputs/bench_core/splits/D_cal_dota10_train.csv": "48a0319a1ea51fcbadf43e7e632d5a77f77d3db73442acfd639acb0c455daed4",
    "outputs/bench_core/splits/D_cal_dota15_train.csv": "aa59e4266872c2f3f48b6c027798255e21fae64b09519a895d3ba8deb85b9364",
    "outputs/bench_core/splits/D_cal_fair1m_train.csv": "84b32cb5e0bd9a7afdc772f824e1b64f9daaca54fccdbbb98750180bc04b16a0",
    "outputs/bench_core/splits/D_cal_hrsc_trainval.csv": "bbaf79002ad683893292101744e32e379d711f14ab7c187ae5bad42d2e37bdb0",
}
HOSTS = {
    "outputs/training/rhino/SNAPSHOT_LOCK.json": ("b38f2420e0125d64558e479aa8c414e6f66ba0b9595612b8066756d8413f65c7", "55a90abbace429276e593f8e4418fad002240ff1951912172367d997b474f9d9"),
    "outputs/training/a4_host/SNAPSHOT_LOCK.json": ("f6790f8bba0a17d8286ece9324f82b2e0e30b298f660e62ddbbe6740d9725c85", "3e32fa11114ced82c2fb5ecdb25031ff45c1d2815b034a315b1af11ef8487e32"),
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rows(name: str) -> list[dict[str, str]]:
    with (REP / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


checks: list[dict[str, str]] = []


def check(scope: str, name: str, ok: bool, evidence: str) -> None:
    checks.append({"scope": scope, "check": name, "status": "PASS" if ok else "FAIL", "blocking": str(not ok), "evidence": evidence})


def write_csv(path: Path, data: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


def main() -> None:
    # Protocol and statistical tables.
    main = rows("m1_all_main_results_ar21.csv")
    sensitivity = rows("m1_sensitivity_ar16_ar13.csv")
    check("protocol", "ar>=2.1 main protocol", bool(main) and all(float(r["ar_threshold"]) == 2.1 for r in main), f"rows={len(main)}")
    check("protocol", "lower-ar sensitivity only", bool(sensitivity) and {float(r["ar_threshold"]) for r in sensitivity} <= {1.3, 1.6}, f"thresholds={sorted({r['ar_threshold'] for r in sensitivity})}")

    m2d = rows("m2_g2doubleprime_decision.csv")
    m2 = rows("m2_g2doubleprime_ar21.csv")
    m2_ok = len(m2d) == 1 and m2d[0]["decision"] == "PASS" and int(m2d[0]["n_bins_nonlinear_sig"]) == 11 and all(float(r["ar_threshold"]) == 2.1 for r in m2)
    check("science", "fixed-size nonlinear comparison", m2_ok, "decision=PASS; 11/15 significant bins; target-domain GT-fit remains upper-bound")

    protocol = json.loads((REP / "m3_image_level_protocol_frozen.json").read_text())
    m3d = rows("m3_decision.csv")
    m3 = rows("m3_image_level_ltt.csv")
    m3_ok = (m3d[0]["decision"] == "PASS" and protocol["exchangeable_unit"] == "image"
             and "Hoeffding-Bentkus" in protocol["primary_loss"]["ucb_method"]
             and all(r["formal_guarantee_unit"] == "complete_evaluation_image" for r in m3))
    check("science", "image-level formal guarantee", m3_ok, f"rows={len(m3)}; bounded image loss; HB UCB")

    geom = rows("m4_geometry_normalized_risk.csv")
    fixed = rows("m4_fixed_angle_sensitivity.csv")
    geom_ok = bool(geom) and all(float(r["ar_threshold"]) == 2.1 and "delta_theta_0.75" in r["event_def"] for r in geom)
    fixed_ok = bool(fixed) and {int(float(r["angle_threshold_deg"])) for r in fixed} == {5, 10, 15}
    check("science", "geometry-normalized primary risk", geom_ok and fixed_ok, f"geometry_rows={len(geom)}; fixed_rows={len(fixed)}")

    # Human raw reconstruction and strict primary/recheck separation.
    audit = json.loads((REP / "m4_human_annotation_merge_audit.json").read_text())
    analysis = json.loads((REP / "m4_human_annotation_analysis_audit.json").read_text())
    human = rows("m4_human_annotation_primary_summary_073.csv")
    recheck = rows("m4_human_annotation_recheck_secondary_073.csv")
    overall = next(r for r in human if r["subset"] == "overall")
    human_ok = (audit["status"] == "COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION" and audit["primary_targets"] == 600
                and audit["usable_numeric_pairs"] == 450 and audit["identities_distinct"]
                and audit["decision_complete_counts"] == {"DIOR-R": 200, "FAIR1M-v1.0": 200, "SODA-A": 200}
                and analysis["primary_recheck_separated"] and not analysis["ambiguous_skip_treated_as_zero"]
                and int(overall["n"]) == 450 and abs(float(overall["mean_deg"]) - 2.3112) < 5e-5
                and len(recheck) == 29 and sum(r["resolved_to_numeric_pair"] == "True" for r in recheck) == 27)
    check("science", "real independent blinded human anchor", human_ok, "600 targets; 200/dataset; 450 numeric pairs; recheck secondary")

    # Split decision, third dataset, DOTA, and DIOR lineage.
    split = rows("psc_phase1_split_gate_decision.csv")
    split_ok = (len(split) == 1 and split[0]["decision"] == "PASS"
                and split[0]["start"] == "2026-07-12 20:14:39 -0700"
                and split[0]["deadline"] == "2026-08-23 20:14:39 -0700")
    check("science", "PSC split decision", split_ok, f"decision={split[0]['decision']}; deadline={split[0]['deadline']}")
    third = rows("m4_optional_third_dataset_results.csv")
    third_ok = any(r["scope"] == "decision" and r["group"] == "REPLICATES_A" for r in third)
    check("science", "FAIR1M independent replication", third_ok, "three heads x three final seeds; REPLICATES_A")

    dota = rows("k4b_dota_full_val_metrics.csv")
    dota_ok = len(dota) == 2 and all(r["can_recompute"] == "yes" and "full-val" in r["gt_source"] for r in dota)
    check("lineage", "DOTA clean full-validation", dota_ok, f"cells={len(dota)}; AP50={','.join(r['AP50'] for r in dota)}")
    lineage = rows("069_dior_partial_gt_lineage_audit.csv")
    repl = [r for r in lineage if r["record_type"] == "replacement_069"]
    dior_ok = len(repl) == 3 and all(r["status"] == "AUTHORITATIVE_FULLVAL" and r["integrity_pass"] == "True" and r["dev_shm_dependency"] == "False" for r in repl)
    check("lineage", "DIOR full-validation replacement", dior_ok, "three authoritative cells; old partial-GT rows superseded")

    # Immutable assets and hosts.
    actual_threshold = sha(ROOT / "configs/thresholds.yaml")
    check("integrity", "thresholds.yaml", actual_threshold == THRESHOLD_SHA, f"sha256={actual_threshold}")
    split_bad = [p for p, expected in SPLITS.items() if not (ROOT / p).is_file() or sha(ROOT / p) != expected]
    check("integrity", "D_cal and D_audit", not split_bad, "all 10 split hashes unchanged" if not split_bad else ";".join(split_bad))
    host_bad = []
    for rel, (lock_sha, ckpt_sha) in HOSTS.items():
        lock_path = ROOT / rel
        if sha(lock_path) != lock_sha:
            host_bad.append(rel + ":lock")
            continue
        lock = json.loads(lock_path.read_text())
        cp = ROOT / lock["best_checkpoint"]
        if lock["best_sha256"] != ckpt_sha or sha(cp) != ckpt_sha:
            host_bad.append(rel + ":checkpoint")
    check("integrity", "host checkpoints", not host_bad, "both host locks/checkpoints unchanged" if not host_bad else ";".join(host_bad))

    # Persistent provenance and one-click chain.
    manifests = list(csv.DictReader((REP / "m4_human_annotation_artifact_manifest_073.csv").open(encoding="utf-8")))
    persistent_ok = all("/dev/shm" not in r["path"] and r["can_recompute"] == "True" for r in manifests)
    check("integrity", "no /dev/shm main dependency", persistent_ok, f"human_manifest_rows={len(manifests)}; persistent paths only")
    log_text = LOG.read_text(encoding="utf-8", errors="replace")
    expected_steps = ["lineage_artifact_verification", "geometry_threshold_verification",
                      "ar21_main_results", "fixed_size_control", "image_level_risk_control",
                      "geometry_and_fixed_angle_events", "psc_split_decision", "fair1m_third_dataset",
                      "human_primary_and_recheck", "human_risk_integration"]
    repro_ok = all(f"STEP_OK {name}" in log_text for name in expected_steps) and "REPRO_073_FAILED" not in log_text
    check("reproduction", "full one-click machine chain", repro_ok, f"completed_steps={sum(f'STEP_OK {x}' in log_text for x in expected_steps)}/{len(expected_steps)}")

    # The sole post-split paper and its boundary language.
    papers = list((ROOT / "docs/paper_A_zh_post_human_073").glob("*.md"))
    paper_text = PAPER.read_text(encoding="utf-8") if PAPER.is_file() else ""
    banned_literal = ["Phase 1", "claim ledger", "frozen gate", "supervisor", "Codex", "Claude",
                      "submission ready", "待补", "/dev/shm", "DOTA#20"]
    banned_words = re.search(r"(?<![A-Za-z0-9_])(K1|K2|K3|K4|M1|M2|M3|M4|PASS|FAIL)(?![A-Za-z0-9_])", paper_text)
    paper_ok = (papers == [PAPER] and paper_text.count("## 参考文献") == 1
                and len(re.findall(r"^\d+\. ", paper_text, flags=re.M)) >= 20
                and not any(x in paper_text for x in banned_literal) and not banned_words
                and "![" not in paper_text and "图片占位" not in paper_text
                and all(x in paper_text for x in ["2.3112°", "1.9970°--2.7854°", "8.00%", "0.89%", "ar>=2.1", "Hoeffding--Bentkus"]))
    reference_count = len(re.findall(r"^\d+\. ", paper_text, flags=re.M))
    check("paper", "single Chinese paper with split boundary", paper_ok, f"markdown_files={len(papers)}; references={reference_count}")

    failed = [r for r in checks if r["status"] != "PASS"]
    write_csv(REP / "073_final_reproduction_status.csv", checks)

    gate_map = [
        ("ar>=2.1 protocol", ["ar>=2.1 main protocol", "lower-ar sensitivity only"]),
        ("M2 fixed-size control", ["fixed-size nonlinear comparison"]),
        ("image-level formal guarantee", ["image-level formal guarantee"]),
        ("geometry-normalized primary risk", ["geometry-normalized primary risk"]),
        ("human annotation anchor", ["real independent blinded human anchor"]),
        ("full reproduction", ["full one-click machine chain"]),
        ("PSC split decision", ["PSC split decision", "single Chinese paper with split boundary"]),
        ("DOTA clean full-val", ["DOTA clean full-validation"]),
        ("DIOR full-val lineage", ["DIOR full-validation replacement"]),
        ("frozen asset integrity", ["thresholds.yaml", "D_cal and D_audit", "host checkpoints", "no /dev/shm main dependency"]),
    ]
    gate = []
    by_name = {r["check"]: r for r in checks}
    for condition, dependencies in gate_map:
        ok = all(by_name[d]["status"] == "PASS" for d in dependencies)
        gate.append({"condition": condition, "status": "PASS" if ok else "FAIL", "blocking": str(not ok), "evidence": "; ".join(f"{d}={by_name[d]['status']}" for d in dependencies)})
    final = "FROZEN_FOR_COLLABORATOR_REVIEW" if all(r["status"] == "PASS" for r in gate) else "NOT_FROZEN"
    gate.append({"condition": "FINAL", "status": final, "blocking": str(final == "NOT_FROZEN"), "evidence": "all ten conditions passed" if final != "NOT_FROZEN" else "blocking checks: " + "; ".join(r["check"] for r in failed)})
    write_csv(REP / "073_submission_freeze_gate.csv", gate)
    print(f"VERIFY_073 {final} checks={len(checks)} failed={len(failed)}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
