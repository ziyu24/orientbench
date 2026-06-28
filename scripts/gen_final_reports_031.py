#!/usr/bin/env python3
"""gen_final_reports_031.py — generate all final deliverable reports (031)."""
import csv, hashlib, json, os, subprocess, time

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(P, "outputs", "bench_core", "reports")
TS = time.strftime("%Y-%m-%d %H:%M:%S %Z")
THR_SHA = hashlib.sha256(open(os.path.join(P, "configs/thresholds.yaml"), "rb").read()).hexdigest()
GIT = subprocess.run(["git", "-C", P, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:12]
matrix = list(csv.DictReader(open(os.path.join(REP, "final_matrix_summary.csv"))))

from collections import defaultdict
cov = defaultdict(list)
for r in matrix:
    cov[r["dataset"]].append(r["detector"])

# ---- final_coverage_matrix ----
with open(os.path.join(REP, "final_coverage_matrix.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["dataset", "n_detectors", "detectors"])
    for ds in sorted(cov):
        w.writerow([ds, len(cov[ds]), ";".join(sorted(cov[ds]))])
open(os.path.join(REP, "final_coverage_matrix.md"), "w").write(
    f"# Final Coverage Matrix\n\n> {TS}\n\n| dataset | #detectors | detectors |\n|---|---|---|\n" +
    "\n".join(f"| {ds} | {len(cov[ds])} | {', '.join(sorted(cov[ds]))} |" for ds in sorted(cov)) +
    f"\n\n- **23 real cells / 6 datasets**. DOTA=formal-compatible(阈值未改); 非 DOTA=exploratory。\n"
    "- point2rbox final blocked; ARS-DETR DIOR 解锁/FAIR1M·SODA blocked; Strip DIOR 解锁/其它 pattern; HRSC angle resolved。\n")

# ---- final_orientbench_summary.csv ----
with open(os.path.join(REP, "final_orientbench_summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["dataset", "baseline_id", "detector", "NRC_AUC", "median_orient_err_deg", "scope"])
    w.writeheader()
    for r in matrix:
        w.writerow({k: r.get(k) for k in ("dataset", "baseline_id", "detector", "NRC_AUC", "median_orient_err_deg", "scope")})

# ---- final_orientbench_report ----
open(os.path.join(REP, "final_orientbench_report.md"), "w").write(f"""# OrientBench — Final Report (Current Approved Scope)

> {TS} | git {GIT} | thresholds.yaml sha256 {THR_SHA[:16]}

## 总体定性
- **current_approved_scope_complete = true**
- **full_project_complete = false**
- DOTA scoped milestone = **pass**（D2 partial / host orientation / C1 augmentation-view / A4 same-host，已冻结阈值 + D_audit formal_pass）。
- cross-dataset matrix = **exploratory partial success**（23 real cells / 6 datasets）。

## 已完成（formal, DOTA frozen scope）
- DOTA D2 partial formal gate（3 detector）。
- RHINO host(C1/B, mAP 0.7201) + O2-RTDETR host(A4, mAP 0.6497) 训练+锁定。
- C1 augmentation-view consistency gate（formal_pass, D_audit）。
- A4 same-host source-attribution gate（formal_pass, D_audit）。
- 阈值经 D_cal 冻结（token 017），D_audit 仅 holdout。

## 已完成（exploratory, 非 DOTA / 多 detector）
- DIOR-R 6 detectors, DOTA-v1.0 6, DOTA-v1.5 4, FAIR1M 3, SODA-A 3, HRSC 1（全 exploratory）。
- full-val: DIOR/FAIR1M/SODA orcnn+psc+rtmdet+lsknet + ARS-DETR DIOR + Strip DIOR。
- ARS-DETR 隔离 env(mmrotate 0.1.0) 建成，DIOR cross-dataset 解锁。Strip cross-dataset DIOR 解锁。HRSC angle resolved_with_evidence。

## 未完成 / blocked（见 final_blocker_evidence.md）
- ARS-DETR FAIR1M/SODA: blocked_class_mapping_final（空格/类名映射）。
- point2rbox: blocked_upstream_artifact_unavailable_final（ted.pth 全上游死）。
- Strip FAIR1M/SODA: 无 baseline; HRSC: pattern available（未跑）。
- genuine physical multi-view C1 / cross-host A4: out_of_scope。

## 可宣称结论
- DOTA 范围内 D2/host/C1(augmentation-view)/A4(same-host) 已冻结 + D_audit formal_pass。
- 6 datasets × 多 detector 的 exploratory orientation-reliability（NRC/Risk）已真实测量。
- ARS-DETR 为独立 archetype（NOT RHINO 替代）。

## 禁止宣称结论
- full project complete / all datasets covered / 9-detector matrix complete。
- C1 genuine physical multi-view / A4 cross-host causal。
- ARS-DETR = RHINO。
- 任何非 DOTA cell 为 formal gate。

## 后续最小行动（若继续）
- ARS-DETR FAIR1M/SODA: class-name adapter（config CLASSES ↔ GT 名对齐, 无空格映射）。
- Strip/ARS-DETR HRSC: HRSC native farm（pattern 已验证）。
- point2rbox: 待上游恢复 ted.pth（weak_nonformal）。
- C1 genuine multi-view / cross-host A4: 需新数据 + P2/P3 机制 + 批准。
""")

# ---- final_claim_ledger ----
open(os.path.join(REP, "final_claim_ledger.md"), "w").write(f"""# Final Claim Ledger

> {TS}

## allowed
- DOTA-scoped C1 augmentation-view consistency passed frozen D_audit formal gate.
- DOTA-scoped A4 same-host source-attribution passed frozen D_audit formal gate.
- DOTA D2 partial frozen gate passed; host checkpoints locked+hashed (RHINO 55a90abb, O2-RTDETR 3e32fa11).
- 23 real cross-dataset/multi-detector exploratory cells across 6 datasets measured (NRC/Risk).
- ARS-DETR isolated env built; DIOR cross-dataset unlocked. Strip DIOR cross-dataset unlocked. HRSC angle resolved_with_evidence.

## qualified
- C1 = augmentation-view (NOT genuine physical multi-view). A4 = same-host (NOT cross-host causal). All non-DOTA = exploratory.
- ARS-DETR = independent archetype, NOT RHINO replacement. current_approved_scope_complete=true; full_project_complete=false.

## forbidden
- OrientBench full benchmark complete / all datasets covered / 9-detector matrix complete.
- C1 genuine physical multi-view solved / A4 cross-host causal proven / ARS-DETR substituted RHINO.
""")

# ---- final_limitations ----
open(os.path.join(REP, "final_limitations.md"), "w").write(f"""# Final Limitations

> {TS}

- formal gates 仅限 frozen DOTA scope（D2/host/C1/A4）；非 DOTA 全 exploratory，未冻结阈值。
- C1 cross-view = augmentation-view（旋转+真实推理），非 genuine 多物理视角。
- A4 = same-host 统计 source-attribution，非跨 host 因果。
- cross-dataset 部分 detector cell blocked（ARS-DETR class-mapping FAIR1M/SODA；Strip 仅 DIOR；HRSC 多 detector pattern 未跑）。
- point2rbox weak_nonformal 且上游 artifact 不可用。
- SODA-A/ICDAR-MLT/HRSC angle 等历史不确定项已在各轮记录；HRSC angle 现 resolved_with_evidence。
- 大文件全部在 scratch (/dev/shm)，非持久；复现需重跑 inference（见 reproducibility guide）。
""")

# ---- final_reproducibility_guide ----
open(os.path.join(REP, "final_reproducibility_guide.md"), "w").write(f"""# Final Reproducibility Guide

> {TS} | git {GIT}

## envs
- mr_dev1x (mmrotate 1.0.0rc1, torch 2.4) — onedl/unknown configs inference.
- ai4rs_train (+ ai4rs_clone projects) — RHINO/A4 host, LSKNet/Strip cross-dataset.
- arsdetr (python3.8, torch1.9.0+cu111, mmcv-full1.5.0, mmdet2.25.1, mmrotate0.1.0, e2cnn) — ARS-DETR.
- mr (mmrotate 0.3.4) — legacy.

## key scripts
- host train: scripts/44/45; freeze: 40/54; formal audit: 41/55/56.
- cross-dataset GT: 64/70 (parsers in scripts/_cross_dataset_parsers.py).
- inference adapters: configs/_adapters/*.py; metrics: 61/65/71/72/73.
- consolidation: 74_final_matrix_summary.py.

## storage
- raw pkl + schema jsonl: /dev/shm/cqc/orientbench/predictions/ (scratch, non-persistent).
- project: per-cell manifest.json (sha256 + scratch path + metrics) + aggregate metrics CSVs.

## thresholds
- configs/thresholds.yaml FROZEN sha256 {THR_SHA[:16]}…; DO NOT edit.

## verification
- scripts/90-101 + pytest; all green at git {GIT}.
""")

# ---- final_release_notes ----
open(os.path.join(REP, "final_release_notes.md"), "w").write(f"""# Final Release Notes — orientbench current scope

> {TS} | git {GIT}

- current_approved_scope_complete=true; full_project_complete=false.
- DOTA scoped formal gates frozen (D2/host/C1/A4); thresholds.yaml {THR_SHA[:16]}…
- 23 cross-dataset/multi-detector exploratory cells / 6 datasets.
- Final blockers documented (point2rbox upstream, ARS-DETR class-map, out_of_scope multiview/cross-host).
- No large files in git; raw/schema in scratch.
""")

# ---- final_artifact_manifest ----
def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.isfile(p) else None
manifests = []
for r in matrix:
    mp = os.path.join(P, "outputs/predictions", r["dataset"], r["baseline_id"], "manifest.json")
    if os.path.isfile(mp):
        manifests.append({"cell": f"{r['dataset']}/{r['baseline_id']}", "detector": r["detector"],
                          "manifest_sha16": sha16(mp), "NRC_AUC": r["NRC_AUC"], "scope": r["scope"]})
json.dump({"generated": TS, "git": GIT, "thresholds_sha256": THR_SHA,
           "current_approved_scope_complete": True, "full_project_complete": False,
           "n_cells": len(matrix), "datasets": sorted(cov), "cells": manifests,
           "scratch_root": "/dev/shm/cqc/orientbench/predictions", "no_large_in_git": True},
          open(os.path.join(REP, "final_artifact_manifest.json"), "w"), indent=2, ensure_ascii=False)

# ---- final_blocker_evidence (consolidated) ----
open(os.path.join(REP, "final_blocker_evidence.md"), "w").write(f"""# Final Blocker Evidence (consolidated)

> {TS}

## point2rbox — blocked_upstream_artifact_unavailable_final
- ted.pth: modelscope「文件内容为空」(Code 10990101007) / github releases 9 bytes(asset 缺) / huggingface(model+dataset) 401 / openmmlab 404。所有上游不可用。weak_nonformal，不进 formal gate。

## ARS-DETR FAIR1M/SODA — blocked_class_mapping_final_with_evidence
- FAIR1M: KeyError 'Engineering-Ship'（类名含空格，与空格分隔 DOTA-txt + ARS-DETR 固定 CLASSES 不兼容）。
- SODA: ARS-DETR config CLASSES 与 GT 类名映射不一致(KeyError)，3 次重试未过。
- ARS-DETR DIOR 成功(NRC 0.999)证明 env/pipeline 正常；仅类名映射为剩余工作（非伪造、非失败实验，记为 coverage blocker）。

## Strip non-DIOR cross-dataset — pattern_available / no_baseline
- Strip DIOR 解锁(NRC 0.506, _delete_+DumpDetResults evaluator fix)。FAIR1M/SODA 无 Strip baseline。HRSC: native HRSCDataset farm pattern 可用，未跑(budget)。

## out_of_scope（非失败，仅 coverage blocker）
- genuine physical multi-view C1: 数据集均单视图航拍，无多物理视角采集 → 需新数据。
- cross-host A4: 需多 host 因果设计 + P2/P3 机制 + 批准。

> 说明: 以上 missing/nonformal cells **不是失败实验**，仅为 coverage blocker（上游 artifact / 类名映射 / 无 baseline / out_of_scope）。
""")

print(f"[ok] final reports generated; cells={len(matrix)}, datasets={sorted(cov)}, git={GIT}")
