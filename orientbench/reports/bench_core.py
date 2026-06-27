"""Unified Bench-Core v0.1 report builder.

Aggregates the artifacts produced by the dry-run closed loop into a single
markdown report. Reads only files under outputs/bench_core; tolerates missing
inputs (records them as 'not produced').
"""
from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List, Optional

from orientbench.core.registry import A4_HOST, DETECTOR_TAXONOMY, taxonomy_availability
from orientbench.reports.prediction_matrix import MISSING_NOTES

R_RULES = [
    ("R1", "GT-identity 必跑 (C1 B-MVE-1 一等对照)", "active (B 未启动)"),
    ("R2", "B 死不迁 A (cross-view 目标不得入 A4)", "active"),
    ("R3", "A-gate-1 同宿主审计 (frozen hybrid-encoder oriented DETR)", "pending host"),
    ("R4", "Calibration / Audit split 分离", "pending (dry-run 未分 split)"),
    ("R5", "扰动族互斥 G_geom ∩ G_style = ∅", "active (probe 未运行)"),
    ("R6", "Host / Baseline 冻结 (A4 / C1=RHINO / D2=9-detector)", "RHINO missing; A4 pending"),
    ("R7", "D2 独立性与 Bench-Core 基元统一", "active (GV/NRC/score 单源)"),
    ("R8", "跑前冻结闸门阈值", "pending (thresholds.yaml 未冻结)"),
]


def _read_json(path: str) -> Optional[Any]:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_csv(path: str) -> List[Dict[str, str]]:
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_report(outputs_dir: str, timestamp: str, stage: str = "core1") -> str:
    rep = os.path.join(outputs_dir, "reports")
    L: List[str] = []
    a = L.append

    a(f"# Bench-Core v0.1 Report (dry-run)\n")
    a(f"> 生成时间: {timestamp}")
    a(f"> stage: {stage} — **DRY-RUN / SANITY**，thresholds.yaml 未冻结，无 gate 结论。")
    a(f"> 只读数据；未推理/训练/下载；未替代 RHINO；未启动 9-detector matrix / B-MVE。\n")

    # 1. baseline inventory
    inv = _read_json(os.path.join(outputs_dir, "baseline_inventory.json"))
    a("## 1. Baseline Inventory")
    if inv:
        a(f"- 总数 **{inv['n_total']}**，valid **{inv['n_valid']}**，invalid **{inv['n_invalid']}**，"
          f"inference_ready={sum(1 for r in inv['records'] if r.get('inference_ready'))}。")
        a(f"- pth 不在磁盘: {inv.get('n_pth_not_on_disk', 0)}；含 warning 记录: {inv.get('n_records_with_warnings', 0)}。")
        miss = inv.get("field_missing_counts", {})
        a(f"- 字段缺失: {miss if miss else '无'}。")
    else:
        a("- baseline_inventory.json 未找到（运行 01_inventory_baselines）。")
    a("")

    # 2. dataset split + missing
    ds = _read_json(os.path.join(outputs_dir, "dataset_inventory.json"))
    a("## 2. Dataset Split 与 Missing 清单")
    if ds:
        present = [r["dataset_name"] for r in ds["records"] if r["exists"]]
        missing = [r["dataset_name"] for r in ds["records"] if not r["exists"]]
        a(f"- known={ds['n_known']} present={ds['n_present']} missing={ds['n_missing']}")
        a(f"- present: {', '.join(present)}")
        a(f"- **missing: {', '.join(missing) if missing else '无'}**")
    else:
        a("- dataset_inventory.json 未找到（运行 00_env_check）。")
    a("")

    # 3. GT index coverage
    a("## 3. GT Index 覆盖")
    metas = []
    gt_dir = os.path.join(outputs_dir, "gt_index")
    if os.path.isdir(gt_dir):
        for f in sorted(os.listdir(gt_dir)):
            if f.endswith(".meta.json"):
                m = _read_json(os.path.join(gt_dir, f))
                if m:
                    metas.append(m)
    if metas:
        a("| dataset | split | files_ok | objects | valid_geom | invalid_geom | max_files |")
        a("|---|---|---|---|---|---|---|")
        for m in metas:
            s = m["stats"]
            a(f"| {m['dataset']} | {m['split']} | {s.get('n_files_ok')} | {s.get('n_objects')} | "
              f"{s.get('n_valid_geometry')} | {s.get('n_invalid_geometry')} | {m.get('max_files')} |")
    else:
        a("- 无 GT index meta（运行 02_prepare_gt_index）。")
    a("")

    # 4. GV-obliquity baseline
    a("## 4. GV-Obliquity 分布 (per dataset/split/class, controlled sample)")
    gv = _read_csv(os.path.join(rep, "gv_obliquity_baseline.csv"))
    if gv:
        agg: Dict[str, Dict[str, float]] = {}
        for r in gv:
            key = f"{r['dataset']}/{r['split']}"
            d = agg.setdefault(key, {"count": 0, "valid": 0, "ns": 0})
            d["count"] += int(r["count"] or 0)
            d["valid"] += int(r["valid_count"] or 0)
            d["ns"] += int(r["near_square_count"] or 0)
        a(f"- gv_obliquity_baseline.csv: {len(gv)} class 行。数据集/split 汇总：")
        a("| dataset/split | objects | valid | near_square |")
        a("|---|---|---|---|")
        for k, d in sorted(agg.items()):
            a(f"| {k} | {d['count']} | {d['valid']} | {d['ns']} |")
    else:
        a("- gv_obliquity_baseline.csv 未找到（运行 05_make_buckets）。")
    a("")

    # 5. source measurement dry-run
    a("## 5. Source Measurement (dry-run)")
    src = _read_json(os.path.join(outputs_dir, "cache", "sources_summary.json"))
    if src:
        a(f"- max_bg_files={src.get('max_bg_files')} jobs={src.get('jobs')}（background 受控抽样，已记录非静默截断）。")
        a("| file | objects | V_layout | bg_ok_obj | V_bg | meanE_layout | meanE_bg |")
        a("|---|---|---|---|---|---|---|")
        for it in src["files"]:
            s = it["stats"]
            a(f"| {os.path.basename(it['file'])} | {s['n_objects']} | {s['n_V_layout']} | "
              f"{s['n_bg_objects_ok']} | {s['n_V_bg']} | {s['mean_E_layout']:.3f} | {s['mean_E_bg']:.3f} |")
        a("- 公式: layout (V_layout/D_nbr/R_nbr/A_align/E_layout) 与 background "
          "(V_bg/A_bg/E_bg/bg_valid_ratio) 按项目执行文件 §6.4/§6.5；未给定常数 (gamma/annulus/bins) 为 dry-run。")
    else:
        a("- sources_summary.json 未找到（运行 04_compute_sources）。")
    a("")

    # 6. stress buckets
    a("## 6. Stress Bucket 数量 (dry-run percentiles, pending_threshold_freeze)")
    sb = _read_csv(os.path.join(rep, "stress_bucket_summary.csv"))
    if sb:
        bucket_cols = [c for c in sb[0].keys() if c not in
                       ("dataset", "split", "n_objects", "pending_threshold_freeze")]
        a("| dataset/split | n | " + " | ".join(bucket_cols) + " |")
        a("|" + "---|" * (2 + len(bucket_cols)))
        for r in sb:
            a(f"| {r['dataset']}/{r['split']} | {r['n_objects']} | " +
              " | ".join(r.get(b, "0") for b in bucket_cols) + " |")
        a("- domain_fragile / rotated_valid_mismatch 为 placeholder（需 domain / rotated-view probe）。")
    else:
        a("- stress_bucket_summary.csv 未找到（运行 05_make_buckets）。")
    a("")

    # 7. default selection score
    a("## 7. Default Selection Score 定义 (frozen def, dry-run demo)")
    ss = _read_csv(os.path.join(rep, "default_selection_score_report.csv"))
    defs = [r for r in ss if r.get("dataset") == "_HEAD_TYPE_DEF_"]
    if defs:
        a("| head type | frozen default score |")
        a("|---|---|")
        for r in defs:
            a(f"| {r['class_name']} | {r['score_definition']} |")
        a(f"- dry-run demo 行数（per dataset/class）: {len(ss) - len(defs)}；"
          "标注 not_detector_prediction / not_formal_calibration / not_official_result。")
    else:
        a("- default_selection_score_report.csv 未找到（运行 06_compute_selection_scores）。")
    a("")

    # 8. NRC-AUC / Risk
    a("## 8. NRC-AUC Sanity + Risk@70 / Risk@90 (SYNTHETIC)")
    nr = _read_csv(os.path.join(rep, "nrc_auc_summary.csv"))
    if nr:
        a("| dataset/split | n | matched | AURC | Risk@70 | Risk@90 | NRC-AUC | oracle | random | risk_mode |")
        a("|---|---|---|---|---|---|---|---|---|---|")
        for r in nr:
            a(f"| {r['dataset']}/{r['split']} | {r['n']} | {r.get('n_matched','')} | {r['AURC']} | "
              f"{r['Risk@70']} | {r['Risk@90']} | {r['NRC_AUC']} | {r['oracle_AURC']} | "
              f"{r['random_AURC']} | {r.get('risk_mode','')} |")
        a("- risk_mode=`synthetic_prediction_angle_error` 时：orientation_risk 由 GT↔synthetic-pred "
          "匹配后的角度误差(deg)得到，selection_score=pred score。**SYNTHETIC，不代表任何 detector 性能**。")
    else:
        a("- nrc_auc_summary.csv 未找到（运行 07_eval_risk_coverage）。")
    a("")

    # 8.1 prediction contract
    a("## 8.1 Prediction Contract 状态 (synthetic)")
    ps = _read_json(os.path.join(outputs_dir, "predictions", "predictions_summary.json"))
    if ps:
        a(f"- mode={ps.get('mode')} detector={ps.get('detector')} views={ps.get('views')}")
        if ps.get("real_ingestion"):
            ri = ps["real_ingestion"]
            a(f"- real ingestion: status=**{ri.get('status')}** format={ri.get('format')} "
              f"n_records={ri.get('n_records')}")
        files = ps.get("files", [])
        tot = sum(f.get("n_preds", 0) for f in files)
        a(f"- synthetic prediction files: {len(files)}，总 preds={tot}（is_synthetic / not_detector_output）。")
        a("- schema: " + ", ".join(ps.get("schema", [])))
    else:
        a("- predictions_summary.json 未找到（运行 03_collect_predictions）。")
    a("")

    # 8.2 angle_version audit
    a("## 8.2 angle_version Audit 摘要")
    aa = _read_csv(os.path.join(rep, "angle_version_audit.csv"))
    if aa:
        vc: Dict[str, int] = {}
        sc: Dict[str, int] = {}
        for r in aa:
            vc[r["angle_version"]] = vc.get(r["angle_version"], 0) + 1
            sc[r["source"]] = sc.get(r["source"], 0) + 1
        a(f"- baselines audited: {len(aa)}；angle_version 分布: {vc}；source 分布: {sc}")
        a("- dataset GT 角度: DOTA/DIOR/FAIR1M = le90_derived(minAreaRect)；HRSC = mbox_ang_rad "
          "(**uncertain**, le90 等价未核验)。详见 angle_version_audit.md。")
    else:
        a("- angle_version_audit.csv 未找到（运行 13_audit_angle_version）。")
    a("")

    # 8.3 real prediction discovery
    a("## 8.3 Real Prediction Discovery")
    pd = _read_csv(os.path.join(rep, "prediction_discovery.csv"))
    if pd:
        ext = [r for r in pd if r.get("origin") == "external"]
        coco = [r for r in ext if r.get("schema_status") == "coco_style_needs_conversion"]
        ready = [r for r in ext if r.get("schema_status") == "matches_prediction_schema"]
        a(f"- candidates: {len(pd)}；external prediction-ish: {len(ext)}；"
          f"coco-style needs_conversion: {len(coco)}；ready-schema: {len(ready)}。")
        a(f"- **no_real_prediction_found (ready-schema external): {len(ready) == 0}**（synthetic 不计）。详见 prediction_discovery.md。")
    else:
        a("- prediction_discovery.csv 未找到（运行 14_discover_predictions）。")
    a("")

    # 8.4 D_cal / D_audit split
    a("## 8.4 D_cal / D_audit Split (R4)")
    sp = _read_json(os.path.join(outputs_dir, "splits", "splits_summary.json"))
    if sp:
        a(f"- salt={sp.get('salt')} cal_fraction={sp.get('cal_fraction')} "
          f"all_mutually_exclusive=**{sp.get('all_mutually_exclusive')}**（deterministic md5 hash）。")
        a("| dataset | n_images | n_cal | n_audit | intersection | disjoint |")
        a("|---|---|---|---|---|---|")
        for d in sp.get("datasets", []):
            a(f"| {d['stem']} | {d['n_images']} | {d['n_cal']} | {d['n_audit']} | "
              f"{d['intersection_size']} | {d['mutually_exclusive']} |")
    else:
        a("- splits_summary.json 未找到（运行 15_build_audit_splits）。")
    a("")

    # 8.5 readiness check
    a("## 8.5 Readiness Check (threshold-freeze / eval)")
    rc = _read_json(os.path.join(rep, "readiness_check.json"))
    if rc:
        a(f"- **overall_readiness: {rc['overall_readiness']}** "
          f"(ready={rc['n_ready']} pending={rc['n_pending']} blocked={rc['n_blocked']})；"
          f"formal_gate_allowed=**{rc['formal_gate_allowed']}**。")
        a(f"- blockers: {rc['blockers']}")
    else:
        a("- readiness_check.json 未找到（运行 16_readiness_check）。")
    a("")

    # 8.6 training readiness
    a("## 8.6 Training Readiness")
    tr = _read_json(os.path.join(rep, "training_readiness.json"))
    if tr:
        a(f"- **training_allowed: {tr['training_allowed']}**（expected {tr['expected']}）。")
        a(f"- reasons: {tr['reasons']}")
        a(f"- blockers: {tr['blockers']}")
    else:
        a("- training_readiness.json 未找到（运行 17_training_readiness）。")
    a("")

    # 8.7 angle evidence audit
    a("## 8.7 angle_version Evidence Audit")
    ev = _read_json(os.path.join(rep, "angle_version_evidence_audit.json"))
    if ev:
        a(f"- **resolved_with_evidence: {ev['n_resolved']} / uncertain: {ev['n_uncertain']}**；"
          f"HRSC: **{ev['hrsc_status']}**。")
        a("- DOTA/DIOR/FAIR1M GT le90-range 由 poly→obb→poly round-trip IoU + θ∈[-π/2,π/2) 证据支撑；"
          "HRSC mbox/le90 检测器等价仍 uncertain（标注 HBB 偏松，交叉验证不一致）；prediction theta unit 待真实 prediction。")
    else:
        a("- angle_version_evidence_audit.json 未找到（运行 21_verify_angle_conventions）。")
    a("")

    # 8.8 prediction import matrix
    a("## 8.8 Prediction Import Matrix")
    im = _read_csv(os.path.join(rep, "prediction_import_matrix.csv"))
    if im:
        cnt: Dict[str, int] = {}
        for r in im:
            cnt[r["status"]] = cnt.get(r["status"], 0) + 1
        a(f"- rows: {len(im)}；status 计数: {cnt}。")
        a(f"- ready_schema (importable now): {cnt.get('ready_schema', 0)}（多数 needs_inference / blocked）。")
    else:
        a("- prediction_import_matrix.csv 未找到（运行 22_prediction_import_matrix）。")
    a("")

    # 8.9 inference command plan + review packets
    a("## 8.9 Inference Plan & Decision Packets")
    ip = _read_csv(os.path.join(rep, "inference_command_plan.csv"))
    if ip:
        exe = sum(1 for r in ip if str(r.get("executable_now")).lower() == "true")
        a(f"- inference_command_plan: {len(ip)} 行，executable_now=True 的有 **{exe}**（仅计划，不执行）。")
    else:
        a("- inference_command_plan.csv 未找到（运行 23_plan_inference_commands）。")
    tr_rev = os.path.join(rep, "threshold_freeze_review.md")
    cf = os.path.join(rep, "collaborator_decision_form.md")
    a(f"- threshold_freeze_review: {'present' if os.path.isfile(tr_rev) else 'missing'}（thresholds.yaml 未改）。")
    a(f"- collaborator_decision_form: {'present' if os.path.isfile(cf) else 'missing'}（全部 pending）。")
    a("")

    # 9. detector taxonomy / probe matrix template
    av = taxonomy_availability()
    a("## 9. Detector Taxonomy & Probe Matrix Template")
    a(f"- 9-detector archetypes: {av['n_archetypes']}，available {av['n_available']}，missing {av['n_missing']}。")
    a(f"- A4 host: {A4_HOST['name']} — {A4_HOST['status']}。")
    a(f"- probe_matrix_template.csv 为模板（PENDING_PREREGISTRATION / PENDING_MEASUREMENT），非实测。")
    a(f"- missing 标注: {'; '.join(MISSING_NOTES)}。")
    a("")

    # 10. R1-R8 status
    a("## 10. R1–R8 状态")
    a("| 规则 | 内容 | 状态 |")
    a("|---|---|---|")
    for rid, desc, status in R_RULES:
        a(f"| {rid} | {desc} | {status} |")
    a("")

    # 11. risks & limitations
    a("## 11. Known Limitations / 风险留痕")
    a("- **RHINO-style rotated DETR missing**：C1/B host 缺失，待裁示；未用 ARS-DETR 替代；不阻塞 D2；B-MVE-0/1 未启动。")
    a("- **SODA-A / ICDAR-MLT dataset missing（监督 006 裁示）**：当前非 Bench-Core 阻塞项，不下载/不改路径/不停工；保留为 missing dataset risk；如 full coverage 需声明覆盖，再由合作者提供路径或裁示排除。")
    a("- **synthetic prediction 声明**：当前 prediction 由 GT + 可控 score/angle 扰动生成，"
      "is_synthetic=true / not_detector_output=true；NRC/risk 非任何真实 detector 性能。")
    a("- **A4 hybrid-host frozen snapshot pending**：A-gate-1 未可执行。")
    a("- **thresholds.yaml 未冻结**：所有 bucket/score/risk 输出为 dry-run/sanity，无 gate 结论 (R8)。")
    a("- background source 为受控抽样；GV-obliquity 用受控样本（非全量）；NRC-AUC 用 synthetic risk。")
    a("- angle_version: DOTA/DIOR/FAIR1M le90 由 poly 推导，HRSC mbox le90 等价未核验（对 GV 无影响）。")
    a("")

    # 12. next + remaining blockers
    a("## 12. Remaining Blockers / 下一步")
    rc = _read_json(os.path.join(rep, "readiness_check.json"))
    tr = _read_json(os.path.join(rep, "training_readiness.json"))
    if rc:
        a(f"- eval readiness blockers: {rc.get('blockers')}")
    if tr:
        a(f"- training_allowed={tr.get('training_allowed')}; reasons={tr.get('reasons')}")
    a("Estimated next actions:")
    a("1. 阈值冻结：各责任角色提交 B/C1、A/A4、D2 阈值与统计检验，写 thresholds.yaml 并设 freeze_time。")
    a("2. RHINO host 裁示（下载/训练/补充/批准替代）；A4 frozen host 提供后跑 A-gate-1。")
    a("3. 接真实 detector predictions（03_collect_predictions）替换 dry-run score / synthetic risk。")
    a("4. GV-obliquity / source 全量化（CPU 并行）；补 SODA-A / ICDAR-MLT 路径裁示。")
    a("5. angle_version le90 符号一致性核验后再做 angle-error gate。")
    return "\n".join(L) + "\n"


def build_v02_prediction_contract_report(outputs_dir: str, timestamp: str) -> str:
    """Focused v0.2 report: prediction contract + angle audit + synthetic chain."""
    rep = os.path.join(outputs_dir, "reports")
    L: List[str] = []
    a = L.append
    a("# Bench-Core v0.2 — Prediction Contract & angle_version Audit (dry-run)\n")
    a(f"> 生成时间: {timestamp}")
    a("> SYNTHETIC prediction（is_synthetic / not_detector_output）；未跑 detector；无 gate 结论。\n")

    a("## 1. Prediction Schema")
    ps = _read_json(os.path.join(outputs_dir, "predictions", "predictions_summary.json"))
    if ps:
        a("- schema: " + ", ".join(ps.get("schema", [])))
        a(f"- mode={ps.get('mode')} detector={ps.get('detector')} views={ps.get('views')}")
        if ps.get("real_ingestion"):
            ri = ps["real_ingestion"]
            a(f"- real ingestion test: status=**{ri.get('status')}** format={ri.get('format')}")
        for f in ps.get("files", []):
            v = f.get("validation", {})
            a(f"  - {os.path.basename(f['pred_file'])}: n_preds={f['n_preds']} "
              f"valid={v.get('n_ok')}/{v.get('n_total')}")
    else:
        a("- predictions_summary.json 未找到。")
    a("")

    a("## 2. Format Auto-Detection (supported)")
    a("- json / jsonl / csv 已实现；pickle_placeholder / mmrotate_placeholder 为占位（未实现解析）。")
    a("- 文件缺失 -> `no_prediction_available`，不阻塞，回退 synthetic fixture。")
    a("")

    a("## 3. GT↔Prediction Matching Skeleton")
    nr = _read_csv(os.path.join(rep, "nrc_auc_summary.csv"))
    if nr:
        a("| dataset/split | n_preds | matched | iou_method | approximate_iou | risk_mode |")
        a("|---|---|---|---|---|---|")
        for r in nr:
            a(f"| {r['dataset']}/{r['split']} | {r.get('n_preds','')} | {r.get('n_matched','')} | "
              f"{r.get('iou_method','')} | {r.get('approximate_iou','')} | {r.get('risk_mode','')} |")
        a("- 同图同类、score 降序、贪心匹配；IoU 阈值=0.5 placeholder（pending_threshold_freeze）。")
        a("- shapely 可用时 iou_method=shapely_polygon；否则 approx_aabb 并标 approximate_iou。")
    else:
        a("- nrc_auc_summary.csv 未找到。")
    a("")

    a("## 4. angle_version Audit")
    aa = _read_csv(os.path.join(rep, "angle_version_audit.csv"))
    if aa:
        vc: Dict[str, int] = {}
        sc: Dict[str, int] = {}
        for r in aa:
            vc[r["angle_version"]] = vc.get(r["angle_version"], 0) + 1
            sc[r["source"]] = sc.get(r["source"], 0) + 1
        a(f"- baselines: {len(aa)}；angle_version: {vc}；source: {sc}")
        a("- HRSC mbox le90 等价 = **uncertain**；DOTA/DIOR/FAIR1M le90 = derived(minAreaRect)。")
        a("- 详见 angle_version_audit.md / .csv。不伪造确定性；无法确认 = unknown。")
    else:
        a("- angle_version_audit.csv 未找到。")
    a("")

    a("## 5. Synthetic Prediction Replacement Chain (03 -> 07 -> 11)")
    a("- 03_collect_predictions（synthetic）由 GT 生成 prediction → predictions/pred_*.jsonl。")
    a("- 07_eval_risk_coverage 匹配 pred↔GT，risk=角度误差(deg)，score=pred score → NRC（替换原 synthetic-risk demo）。")
    a("- 11_report_bench_core 汇总。全链路 dry-run，**不代表 detector 性能**。")
    a("")

    a("## 6. Missing Dataset 裁示 (006)")
    a("- SODA-A / ICDAR-MLT：非阻塞，不下载/不改路径；保留 missing dataset risk；full coverage 需声明时再裁示。")
    a("")

    a("## 7. 下一步 — 接真实 prediction")
    a("1. 真实 detector predictions 经 03 --pred-file 接入（json/jsonl/csv），validator 校验后替换 synthetic。")
    a("2. 接真实 prediction 若需启动 detector 推理 → 触发停手汇报条件（本轮不跑 detector）。")
    a("3. angle_version le90 符号一致性核验（尤其 HRSC）后再做 angle-error gate。")
    a("4. 阈值冻结(R8) → 正式 NRC/Risk gate。")
    return "\n".join(L) + "\n"
