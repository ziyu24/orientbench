"""Threshold-freeze / evaluation readiness checklist (CHECK ONLY, never freeze).

Each item resolves to one of: ready | blocked | pending | not_applicable.
Never promotes pending -> ready. Reads thresholds.yaml, baseline inventory,
angle audit, prediction discovery, and split summary.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:  # pragma: no cover
    _HAS_YAML = False

STATUSES = {"ready", "blocked", "pending", "not_applicable"}


def _load_yaml(path: str) -> Optional[dict]:
    if not os.path.isfile(path):
        return None
    if _HAS_YAML:
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    return None


def _load_json(path: str) -> Optional[Any]:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_csv_rows(path: str) -> List[dict]:
    import csv
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_readiness(outputs_dir: str, configs_dir: str) -> Dict[str, Any]:
    rep = os.path.join(outputs_dir, "reports")
    thr = _load_yaml(os.path.join(configs_dir, "thresholds.yaml")) or {}
    items: List[Dict[str, str]] = []

    def add(key, status, detail):
        assert status in STATUSES, status
        items.append({"item": key, "status": status, "detail": detail})

    # threshold blocks
    def block_status(name):
        b = thr.get(name, {}) if isinstance(thr, dict) else {}
        st = (b or {}).get("status")
        return "ready" if st == "frozen" else "pending"
    add("B_C1_thresholds", block_status("B_C1"), f"thresholds.yaml B_C1.status={ (thr.get('B_C1') or {}).get('status') }")
    add("A_A4_thresholds", block_status("A_A4"), f"A_A4.status={ (thr.get('A_A4') or {}).get('status') }")
    add("D2_thresholds", block_status("D2"), f"D2.status={ (thr.get('D2') or {}).get('status') }")

    freeze_time = thr.get("freeze_time") if isinstance(thr, dict) else None
    add("freeze_time_set", "pending" if not freeze_time else "ready", f"freeze_time={freeze_time}")
    rr = thr.get("responsible_role") if isinstance(thr, dict) else None
    rr_filled = bool(rr) and all(v for v in rr.values()) if isinstance(rr, dict) else False
    add("responsible_role_filled", "ready" if rr_filled else "pending", f"responsible_role={rr}")
    add("change_log_present", "ready" if (isinstance(thr, dict) and thr.get("change_log")) else "pending",
        "thresholds.yaml change_log")

    # hosts
    inv = _load_json(os.path.join(outputs_dir, "baseline_inventory.json"))
    rhino = bool(inv and any("rhino" in (r.get("model_id") or "").lower() for r in inv["records"]))
    add("rhino_host", "ready" if rhino else "blocked",
        "RHINO-style rotated DETR present" if rhino else "RHINO missing in pth_data/readme.md")
    add("a4_hybrid_host", "blocked", "A4 hybrid-encoder oriented DETR frozen snapshot pending")

    # datasets
    ds = _load_json(os.path.join(outputs_dir, "dataset_inventory.json"))
    miss = [r["dataset_name"] for r in ds["records"] if not r["exists"]] if ds else []
    add("soda_a_icdar_mlt_datasets", "blocked" if miss else "ready",
        f"missing: {miss}" if miss else "all present")

    # real predictions (formal external + smoke)
    disc = _read_csv_rows(os.path.join(rep, "prediction_discovery.csv"))
    ready_schema = [r for r in disc if r.get("schema_status") == "matches_prediction_schema"
                    and r.get("origin") == "external"]
    smoke = _load_json(os.path.join(rep, "real_prediction_smoke_summary.json"))
    n_smoke = smoke.get("n_ok", 0) if smoke else 0
    angle_resolved = bool(smoke and "RESOLVED" in str(smoke.get("angle_convention", "")))
    if ready_schema:
        add("real_prediction_available", "ready",
            f"formal external predictions: {len(ready_schema)}")
    elif n_smoke:
        add("real_prediction_available", "pending",
            f"real_prediction_smoke_available={n_smoke} baselines (NON-formal real predictions; "
            f"DOTA angle convention {'RESOLVED' if angle_resolved else 'unresolved'}); formal pending")
    else:
        add("real_prediction_available", "pending", "no_real_prediction_found")
    # calibration input from real D_cal metrics
    has_candidate = os.path.isfile(os.path.join(configs_dir, "thresholds.calibration_candidate.yaml"))
    add("calibration_input_available", "ready" if (n_smoke and has_candidate) else "pending",
        f"real D_cal calibration candidate present={has_candidate}; baselines={n_smoke}")

    # angle evidence audit — resolved where evidence exists; HRSC + detector-sign uncertain
    ev = _load_json(os.path.join(rep, "angle_version_evidence_audit.json"))
    if ev:
        add("angle_version_certain", "pending",
            f"evidence audit: resolved_with_evidence={ev.get('n_resolved')} "
            f"uncertain={ev.get('n_uncertain')}; HRSC={ev.get('hrsc_status')}; "
            "detector-sign equivalence still needs real prediction")
    else:
        aa = _read_csv_rows(os.path.join(rep, "angle_version_audit.csv"))
        add("angle_version_certain", "pending",
            f"audited {len(aa)} baselines; HRSC mbox le90 equivalence uncertain")

    # cal/audit split disjoint
    sp = _load_json(os.path.join(outputs_dir, "splits", "splits_summary.json"))
    if sp is None:
        add("dcal_daudit_disjoint", "pending", "splits not built yet (run 15_build_audit_splits)")
    else:
        add("dcal_daudit_disjoint", "ready" if sp.get("all_mutually_exclusive") else "blocked",
            f"all_mutually_exclusive={sp.get('all_mutually_exclusive')}")

    # 010 execution-package readiness (existence of guarded machinery)
    runner_ok = os.path.isfile(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "runners", "inference_runner.py"))
    add("guarded_inference_runner_available", "ready" if runner_ok else "pending",
        "orientbench/runners/inference_runner.py present (refuses execution by default)")
    policy_ok = os.path.isfile(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "io", "output_policy.py"))
    add("output_policy_valid", "ready" if policy_ok else "pending",
        "outputs/predictions/{dataset}/{baseline_id}/ policy enforced")
    add("baseline_shortlist_exists",
        "ready" if os.path.isfile(os.path.join(rep, "baseline_shortlist.csv")) else "pending",
        "baseline_shortlist.csv")
    add("calibration_plan_exists",
        "ready" if os.path.isfile(os.path.join(rep, "calibration_plan.csv")) else "pending",
        "calibration_plan.csv")
    # approval-gated items (collaborator-controlled)
    appr = _load_yaml(os.path.join(configs_dir, "approvals.yaml")) or {}
    dec = appr.get("decisions", {}) if isinstance(appr, dict) else {}
    add("formal_inference_approval", "ready" if dec.get("D5_allow_real_inference") == "allow" else "blocked",
        f"approvals.D5={dec.get('D5_allow_real_inference')}")
    add("training_approval", "ready" if dec.get("D6_allow_training") == "allow" else "blocked",
        f"approvals.D6={dec.get('D6_allow_training')}")

    n_blocked = sum(1 for i in items if i["status"] == "blocked")
    n_pending = sum(1 for i in items if i["status"] == "pending")
    overall = "blocked" if n_blocked else ("pending" if n_pending else "ready")
    blockers = [i["item"] for i in items if i["status"] in ("blocked", "pending")]
    return {
        "overall_readiness": overall, "n_items": len(items),
        "n_ready": sum(1 for i in items if i["status"] == "ready"),
        "n_pending": n_pending, "n_blocked": n_blocked,
        "blockers": blockers, "items": items,
        "formal_gate_allowed": overall == "ready",
    }


def build_host_decision_packet(timestamp: str) -> str:
    """RHINO / A4 host decision packet for collaborator ruling (markdown)."""
    L = ["# Host Decision Packet (RHINO / A4)", "", f"> 生成时间: {timestamp}",
         "> 供合作者裁示；不替代 RHINO；不把 ARS-DETR 当 RHINO；不启动训练/推理。", ""]
    L += [
        "## 1. RHINO-style rotated DETR — MISSING",
        "- 现状: `pth_data/readme.md` 73 baselines 中无 RHINO-style rotated DETR（C1/B host, R6）。",
        "- ARS-DETR (#14–19,44,72) 只能作为 DETR-like baseline，**不可替代 RHINO**（R6 冻结对象不同）。",
        "- C1/B 若要启动，需合作者裁示其一: **下载** RHINO 权重 / **训练** RHINO / **补充**到 pth_data / **批准**明确替代方案。",
        "- 裁示前: B-MVE-0/1 不启动。",
        "",
        "## 2. A4 hybrid-encoder oriented DETR host — PENDING",
        "- 现状: A4 source-attribution host (frozen hybrid-encoder oriented DETR) frozen snapshot 未提供 (R3/R6)。",
        "- A-gate-1 必须在该 frozen host 上跑，**不得用 RHINO 或 convenience snapshot 替代** (R3)。",
        "- 需合作者提供 frozen snapshot 路径或裁示获取方式。",
        "",
        "## 3. 训练前对齐方案（host 选定后仍需）",
        "- config / log / schedule / lr / batch / SyncBN 必须对齐官方或 valid baseline；",
        "- 4×A30 默认，爆显存回退并留痕；",
        "- 只保存最高 mAP + 最近 epoch；每 epoch 评估；",
        "- 首 epoch 明显偏低必须停并汇报；",
        "- 自建 baseline 放 `orientbench/pth_data`，以 `baseline_` 前缀，维护 readme。",
        "",
        "## 4. 需要合作者裁示的事项",
        "1. RHINO host 处置（下载/训练/补充/批准替代）。",
        "2. A4 frozen host 提供方式。",
        "3. 是否授权将某 coco/pseudo-label prediction 转换后用于 ingestion（非正式 gate）。",
        "4. 阈值冻结责任角色与数值（见 threshold_freeze_proposal）。",
    ]
    return "\n".join(L) + "\n"


def build_collaborator_form(timestamp: str) -> str:
    """Minimal collaborator decision form. All items default pending; never pre-checked."""
    L = ["# Collaborator Decision Form", "", f"> 生成时间: {timestamp}",
         "> 所有项默认 pending；cc 不替合作者勾选；裁示后回填。", ""]
    decisions = [
        ("D1", "接受 threshold draft (configs/thresholds.draft.yaml)？", "accept / revise / reject"),
        ("D2", "RHINO 处置", "download / train / supply_to_pth_data / approve_substitute / defer"),
        ("D3", "A4 hybrid-encoder frozen host 处置", "supply_path / train / defer"),
        ("D4", "SODA-A / ICDAR-MLT 是否排除出 coverage？", "exclude / supply_path / defer"),
        ("D5", "是否允许真实 detector 推理 (inference)？", "allow / deny"),
        ("D6", "是否允许后续训练 (training)？", "allow_after_preconditions / deny"),
        ("D7", "是否授权某 prediction 转换后用于 ingestion (非正式 gate)？", "allow / deny"),
        ("D8", "允许 guarded inference dry-run runner 合并 (不执行推理)？", "allow / deny"),
        ("D9", "在批准 D5 后允许执行真实 baseline inference？", "allow_after_D5 / deny"),
        ("D10", "在批准 D1 后允许冻结 thresholds.yaml？", "allow_after_D1 / deny"),
    ]
    L.append("| id | decision | options | choice | status |")
    L.append("|---|---|---|---|---|")
    for did, q, opts in decisions:
        L.append(f"| {did} | {q} | {opts} | ____ | **pending** |")
    L.append("")
    L.append("说明：D5/D6 在 readiness/training_readiness 满足硬前置且本表批准前，cc 不得启动推理或训练。")
    return "\n".join(L) + "\n"
