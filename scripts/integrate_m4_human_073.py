#!/usr/bin/env python3
"""Independently verify and integrate the 072 human annotations for 073."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
REP = ROOT / "reports"
DOC = ROOT / "docs"


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty output: {path}")
    fields = fields or list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    os.replace(temporary, path)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def state(row: dict) -> str:
    if row["long_side_angle_deg_le90"].strip(): return "LABELED"
    if row["ambiguous"] == "1": return "AMBIGUOUS"
    if row["skip"] == "1": return "SKIP"
    return "PENDING"


def summarize(label: str, rows: list[dict], seed: int) -> dict:
    values = np.asarray([row["disagreement"] for row in rows], dtype=float)
    clusters = defaultdict(list)
    for row in rows:
        clusters[row["image_id"]].append(row["disagreement"])
    rng = np.random.default_rng(seed)
    means, p5s, p10s = [], [], []
    keys = list(clusters)
    for _ in range(10000):
        chosen = rng.choice(keys, size=len(keys), replace=True)
        sample = np.asarray([value for key in chosen for value in clusters[key]])
        means.append(float(sample.mean()))
        p5s.append(float((sample > 5).mean()))
        p10s.append(float((sample > 10).mean()))
    mean_ci = np.percentile(means, [2.5, 97.5])
    p5_ci = np.percentile(p5s, [2.5, 97.5])
    p10_ci = np.percentile(p10s, [2.5, 97.5])
    return {
        "subset": label, "n": len(values), "mean_deg": round(float(values.mean()), 4),
        "mean_cluster_ci95_low": round(float(mean_ci[0]), 4),
        "mean_cluster_ci95_high": round(float(mean_ci[1]), 4),
        "median_deg": round(float(np.median(values)), 4),
        "p90_deg": round(float(np.percentile(values, 90)), 4),
        "p95_deg": round(float(np.percentile(values, 95)), 4),
        "P_gt5": round(float((values > 5).mean()), 6),
        "P_gt5_cluster_ci95_low": round(float(p5_ci[0]), 6),
        "P_gt5_cluster_ci95_high": round(float(p5_ci[1]), 6),
        "P_gt10": round(float((values > 10).mean()), 6),
        "P_gt10_cluster_ci95_low": round(float(p10_ci[0]), 6),
        "P_gt10_cluster_ci95_high": round(float(p10_ci[1]), 6),
        "interpretation": "human circular disagreement; not dataset GT error",
    }


def replace_section(path: Path, marker: str, content: str) -> None:
    text = path.read_text()
    start = f"<!-- {marker}_START -->"
    end = f"<!-- {marker}_END -->"
    block = f"\n\n{start}\n{content.strip()}\n{end}\n"
    if start in text and end in text:
        text = text[:text.index(start)] + block + text[text.index(end) + len(end):]
    else:
        text = text.rstrip() + block
    path.write_text(text)


def augment_csv(path: Path, updater) -> None:
    rows = read_csv(path)
    for row in rows:
        updater(row)
    write_csv(path, rows)


def main() -> None:
    raw = {
        "A": PKG / "internal/m600_A_combined.csv",
        "B": PKG / "internal/m600_B_combined.csv",
    }
    before_hash = {slot: sha256(path) for slot, path in raw.items()}
    returns = {slot: read_csv(path) for slot, path in raw.items()}
    mapping_rows = read_csv(PKG / "internal/instance_id_mapping.csv")
    mapping = {(row["annotator_slot"], row["task_id"]): row["canonical_anon_id"]
               for row in mapping_rows}
    meta_rows = read_csv(PKG / "internal/m600_sampling_manifest.csv")
    metadata = {row["anon_id"]: row for row in meta_rows}
    if len(metadata) != 600 or Counter(row["dataset"] for row in meta_rows) != Counter(
            {"DIOR-R": 200, "FAIR1M-v1.0": 200, "SODA-A": 200}):
        raise RuntimeError("primary target set is not 600 with 200 per dataset")

    canonical = {}
    identities = {}
    for slot in "AB":
        if len(returns[slot]) != 600 or len({row["task_id"] for row in returns[slot]}) != 600:
            raise RuntimeError(f"slot {slot} does not contain 600 unique rows")
        ids = {row["annotator_id"] for row in returns[slot] if row["annotator_id"]}
        if len(ids) != 1:
            raise RuntimeError(f"slot {slot} identity is not stable")
        identities[slot] = next(iter(ids))
        canonical[slot] = {mapping[(slot, row["task_id"])]: row for row in returns[slot]}
    if identities["A"] == identities["B"] or set(canonical["A"]) != set(canonical["B"]) or set(canonical["A"]) != set(metadata):
        raise RuntimeError("A/B independence or canonical set equality failed")
    if set(canonical["A"]) != set(metadata):
        raise RuntimeError("canonical target differs from m600 manifest")

    usable = []
    pair_states = Counter()
    for anon_id in metadata:
        a, b = canonical["A"][anon_id], canonical["B"][anon_id]
        sa, sb = state(a), state(b)
        if sa == "PENDING" or sb == "PENDING":
            raise RuntimeError(f"pending primary annotation: {anon_id}")
        pair_states[f"{sa}|{sb}"] += 1
        if sa == sb == "LABELED":
            angle_a = float(a["long_side_angle_deg_le90"])
            angle_b = float(b["long_side_angle_deg_le90"])
            if not (0 <= angle_a < 180 and 0 <= angle_b < 180):
                raise RuntimeError("angle outside [0,180)")
            usable.append({
                **metadata[anon_id],
                "disagreement": abs((angle_a - angle_b + 90) % 180 - 90),
            })
    if len(usable) != 450:
        raise RuntimeError(f"expected 450 numeric pairs, got {len(usable)}")

    summaries = [summarize("overall", usable, 71210)]
    by_dataset = []
    for index, dataset in enumerate(("DIOR-R", "FAIR1M-v1.0", "SODA-A"), 1):
        row = summarize(dataset, [item for item in usable if item["dataset"] == dataset], 71210 + index)
        summaries.append(row); by_dataset.append(row)
    ar21_rows = [item for item in usable if float(item["matched_gt_aspect_ratio"]) >= 2.1]
    ar_summary = summarize("ar>=2.1", ar21_rows, 71214)
    summaries.append(ar_summary)
    expected = {
        "overall": (450, 2.3112, 1.6359, 4.4220, 5.9359, 0.08, 0.008889),
        "ar>=2.1": (308, 2.2823, 1.6130, None, None, 0.068182, 0.006494),
    }
    for row in summaries:
        if row["subset"] not in expected: continue
        exp = expected[row["subset"]]
        observed = (row["n"], row["mean_deg"], row["median_deg"], row["p90_deg"],
                    row["p95_deg"], row["P_gt5"], row["P_gt10"])
        for got, want in zip(observed, exp):
            if want is not None and not np.isclose(float(got), float(want), atol=5e-5):
                raise RuntimeError(f"072 mismatch {row['subset']}: {observed} vs {exp}")

    rechecks = read_csv(REP / "m4_m600_one_sided_recheck.csv")
    if len(rechecks) != 29 or Counter(row["recheck_state"] for row in rechecks) != Counter(
            {"LABELED": 27, "AMBIGUOUS": 2}):
        raise RuntimeError("blind recheck counts differ from 072")
    resolved = np.asarray([float(row["resolved_disagreement_deg"]) for row in rechecks
                           if row["resolved_disagreement_deg"]], dtype=float)
    if len(resolved) != 27:
        raise RuntimeError("expected 27 numeric recheck pairs")
    recheck_summary = {
        "endpoint": "secondary_blind_recheck", "targets": 29, "numeric_pairs": 27,
        "remaining_ambiguous": 2, "mean_deg": round(float(resolved.mean()), 4),
        "median_deg": round(float(np.median(resolved)), 4),
        "p90_deg": round(float(np.percentile(resolved, 90)), 4),
        "p95_deg": round(float(np.percentile(resolved, 95)), 4),
        "primary_overwritten": False,
        "interpretation": "secondary endpoint only; selected from one-sided nonnumeric primary outcomes",
    }
    if not np.isclose(recheck_summary["mean_deg"], 2.2126, atol=5e-5):
        raise RuntimeError("recheck mean mismatch")

    summary_fields = list(summaries[0])
    write_csv(REP / "m4_human_annotation_primary_summary_073.csv", summaries, summary_fields)
    write_csv(REP / "m4_human_annotation_by_dataset_073.csv", by_dataset, summary_fields)
    write_csv(REP / "m4_human_annotation_by_ar_073.csv", [ar_summary], summary_fields)
    write_csv(REP / "m4_human_annotation_recheck_secondary_073.csv", rechecks)
    write_csv(REP / "m4_human_annotation_disagreement.csv",
              read_csv(REP / "m4_m600_disagreement.csv"))
    write_csv(REP / "m4_human_annotation_pairs.csv", read_csv(REP / "m4_m600_pairs.csv"))
    write_json(REP / "m4_human_annotation_merge_audit.json", {
        "status": "COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION",
        "primary_targets": 600,
        "decision_complete_counts": {"DIOR-R": 200, "FAIR1M-v1.0": 200, "SODA-A": 200},
        "usable_numeric_pairs": 450,
        "usable_counts": dict(Counter(row["dataset"] for row in usable)),
        "same_canonical_target_set": True, "identities_distinct": True,
        "pending": 0, "test_annotations_included": False,
        "pair_state_counts": dict(pair_states),
    })
    write_json(REP / "m4_human_annotation_analysis_audit.json", {
        "status": "COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION",
        "circular_period_deg": 180, "bootstrap_cluster_unit": "source image",
        "bootstrap_replicates": 10000, "primary_recheck_separated": True,
        "ambiguous_skip_treated_as_zero": False,
        "summary": summaries, "recheck_summary": recheck_summary,
    })

    human_by_dataset = {row["subset"]: row for row in by_dataset}
    def fixed_update(row: dict) -> None:
        threshold = int(float(row["angle_threshold_deg"]))
        anchor = human_by_dataset.get(row["dataset"])
        row["human_anchor_scope"] = "600 primary targets; 200 per dataset" if anchor else "not sampled"
        row["human_disagreement_probability"] = (
            anchor["P_gt5"] if anchor and threshold == 5 else
            anchor["P_gt10"] if anchor and threshold == 10 else ""
        )
        if threshold == 5 and anchor:
            row["noise_sensitive"] = "True"
            row["interp"] = "fine-risk; human-noise-sensitive"
            row["note"] = "human disagreement above 5deg is nonzero; SODA-A requires extra caution"
        elif threshold == 10 and anchor:
            row["interp"] = "severe-risk sensitivity with clearer human-noise margin"
            row["note"] = "human disagreement above 10deg is rare; do not subtract a noise correction"
        elif threshold == 15:
            row["interp"] = "fixed-angle sensitivity"
        row["proxy_role"] = "corner-jitter proxy sensitivity only; strictly separate from human disagreement"
    augment_csv(REP / "m4_fixed_angle_sensitivity.csv", fixed_update)

    def geometry_update(row: dict) -> None:
        anchor = human_by_dataset.get(row["dataset"])
        row["human_anchor_role"] = (
            "human disagreement contextualizes label noise; it is not subtracted from model error"
            if anchor else "no human sample for this dataset"
        )
        row["human_P_gt5"] = anchor["P_gt5"] if anchor else ""
        row["human_P_gt10"] = anchor["P_gt10"] if anchor else ""
    augment_csv(REP / "m4_geometry_normalized_risk.csv", geometry_update)

    def m3_update(row: dict) -> None:
        row["human_noise_interpretation"] = (
            "geometry-normalized event remains primary; 1.5-2deg mean budgets are label-noise-aware; "
            "human disagreement is not a correction term"
        )
    augment_csv(REP / "m3_image_level_ltt.csv", m3_update)

    human_doc = """
## 真人双标噪声锚点

三数据集各 200 个独立互盲目标构成 600 个 primary 目标，其中 450 对双方均给出数值角度。180° 周期圆周分歧的均值为 2.3112°（按源图像聚类自助法 95% 区间 1.9970°–2.7854°），中位数为 1.6359°，p90/p95 为 4.4220°/5.9359°；P(>5°)=8.00%，P(>10°)=0.89%。ar≥2.1 子集含 308 对，均值 2.2823°，P(>5°)=6.82%，P(>10°)=0.65%。因此 5° 是有实际意义但对标签噪声敏感的 fine-risk，10° 具有更清楚的 severe-risk 人工噪声余量；SODA-A 的人工分歧尾部较高，固定角度结论需更克制。人工分歧不等于数据集真实 GT error，也不作为从模型误差中扣除的校正项。corner-jitter 只保留为独立 proxy sensitivity，不能替代真人锚点。
"""
    replace_section(DOC / "m4_risk_event_definition.md", "HUMAN_073", human_doc)
    replace_section(DOC / "m3_image_level_risk_control.md", "HUMAN_073", """
## 人工噪声与风险预算解释

真人双标均值分歧为 2.3112°，其 95% 区间为 1.9970°–2.7854°。因此 1.5°–2° 的均值风险预算接近人工分歧地板，只能解释为 label-noise-aware mean risk，不能写成强语义精度保证。5° 事件仍有 8.00% 的人工分歧越界，属于 noise-sensitive fine-risk；10° 事件的人工越界率为 0.89%，具有更清楚的 severe-risk 解释。正式保证仍以完整图像为可交换单位、以 geometry-normalized severe event 为主风险；人工分歧不进入阈值选择，也不从模型风险中扣除。
""")
    (DOC / "m4_human_angle_annotation_audit.md").write_text("""# 人工长轴角独立双标审计

## 最终协议与状态

- 两名真实标注者在互盲条件下独立完成同一组 600 个 canonical targets；DIOR-R、FAIR1M-v1.0、SODA-A 各 200 个，标注者身份不同，原始文件已持久化。
- primary 端点保留原始 600 个决策：450 对同时给出数值角度。总体 180° 周期差异均值 2.3112°（按图像聚类 bootstrap 95% CI 1.9970°--2.7854°），中位数 1.6359°，p90 4.4220°，p95 5.9359°；P(>5°)=8.00%，P(>10°)=0.89%。
- ar>=2.1 子集有 308 对：均值 2.2823°，中位数 1.6130°，P(>5°)=6.82%，P(>10°)=0.65%。
- SODA-A 的人工差异尾部更高，因此该数据集上的 5° 结果必须作 noise-sensitive 解读。
- 29 个单方无数值目标的匿名盲重检严格作为 secondary endpoint：27 对获得数值，2 对仍 ambiguous；重检没有覆盖或替换 primary 原始标注。
- 该样本支持总体噪声锚点、宽粒度数据集比较、5°/10° 风险解释和 ar>=2.1 主边界；不支持 rare-class 精确噪声率、精细 size-bin 因果比较或极端尾部强结论。
- 人工 disagreement 不是数据集真实 GT error，不能作为从模型误差中扣除的修正项。corner-jitter 仅为独立的 proxy sensitivity，不称为真实标注方差。

状态：人工锚点协议完成，统计可从原始 A/B 输出独立复算。
""", encoding="utf-8")

    repro_doc = DOC / "third_party_reproduction_log.md"
    replace_section(repro_doc, "COMMAND_073", """
## Command 073 final reproduction

The default entry point `bash scripts/reproduce_all_main_tables.sh` rebuilds all CPU statistical tables, reconstructs the 600-target human endpoint from persistent A/B raw exports, keeps the 29-target blind recheck secondary, validates frozen machine artifacts, and runs the final freeze verifier. The authoritative log is `logs/reproduce_all_main_tables_073.log`; status and gate outputs are `reports/073_final_reproduction_status.csv` and `reports/073_submission_freeze_gate.csv`. No main table depends on `/dev/shm`.

This final state supersedes the historical 069/070 `HUMAN_BLOCKED` entries above: the real independent annotation endpoint is now complete and the final state is `FROZEN_FOR_COLLABORATOR_REVIEW`.
""")

    if before_hash != {slot: sha256(path) for slot, path in raw.items()}:
        raise RuntimeError("raw human annotation files changed during integration")
    manifest_inputs = [
        raw["A"], raw["B"], PKG / "internal/m600_sampling_manifest.csv",
        PKG / "internal/instance_id_mapping.csv",
        REP / "m4_m600_one_sided_recheck.csv",
        PKG / "annotator_A/outputs_m600_plus_recheck/annotations_A_m600_plus_recheck.csv",
        PKG / "annotator_B/outputs_m600_plus_recheck/annotations_B_m600_plus_recheck.csv",
        ROOT / "scripts/merge_m4_human_annotations.py",
        ROOT / "scripts/analyze_m4_human_disagreement.py",
        ROOT / "scripts/integrate_m4_human_073.py",
    ]
    outputs = [
        REP / "m4_human_annotation_disagreement.csv",
        REP / "m4_human_annotation_primary_summary_073.csv",
        REP / "m4_human_annotation_recheck_secondary_073.csv",
        REP / "m4_human_annotation_by_dataset_073.csv",
        REP / "m4_human_annotation_by_ar_073.csv",
        REP / "m4_human_annotation_merge_audit.json",
        REP / "m4_human_annotation_analysis_audit.json",
    ]
    manifest = []
    for role, paths in (("input", manifest_inputs), ("output", outputs)):
        for path in paths:
            manifest.append({
                "role": role, "path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                "bytes": path.stat().st_size, "can_recompute": True,
                "contains_primary_human_labels": str(path in raw.values()),
                "note": "persistent; no /dev/shm dependency",
            })
    write_csv(REP / "m4_human_annotation_artifact_manifest_073.csv", manifest)
    print("HUMAN_073_COMPLETE targets=600 usable=450 rechecks=29")


if __name__ == "__main__":
    main()
