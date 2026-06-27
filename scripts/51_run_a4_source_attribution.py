#!/usr/bin/env python3
"""51_run_a4_source_attribution.py — A4 source-attribution mechanism SMOKE (O2-RTDETR host)."""
from __future__ import annotations

import hashlib
import json
import os
import sys

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
from orientbench.io.reports import read_jsonl, write_csv  # noqa: E402
from orientbench.probes.source_attribution import source_attribution_smoke  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402

PRED = os.path.join(PROOT, "outputs/predictions/DOTA-v1.5/a4_host/schema/pred_a4_host_val.jsonl")
GT = os.path.join(PROOT, "outputs/predictions/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl")
CKPT = os.path.join(PROOT, "outputs/training/a4_host/best_dota_mAP_epoch_70.pth")
REPORT_DIR = os.path.join(PROOT, "outputs/bench_core/reports")
PROBE_DIR = os.path.join(PROOT, "outputs/probes/a4_source_attribution")


def main():
    os.makedirs(REPORT_DIR, exist_ok=True); os.makedirs(PROBE_DIR, exist_ok=True)
    preds = read_jsonl(PRED); gts = read_jsonl(GT)
    if not preds or not gts:
        print("[blocked] missing A4 host predictions or GT"); return
    a4_hash = hashlib.sha256(open(CKPT, "rb").read()).hexdigest()[:16] if os.path.isfile(CKPT) else "MISSING"
    imgs = sorted({g["image_id"] for g in gts})
    dcal = {i for i in imgs if assign_split(i) == "D_cal"}
    daudit = {i for i in imgs if assign_split(i) == "D_audit"}
    assert dcal & daudit == set()
    rows = []
    detail = {}
    for split, ids in [("D_cal", dcal), ("D_audit", daudit)]:
        r = source_attribution_smoke(preds, gts, ids, seed=0)
        detail[split] = r
        base = {"host": "O2-RTDETR", "route": "A4", "a4_snapshot_sha256": a4_hash, "split": split,
                "status": r.get("status"), "n_used": r.get("n_used"),
                "n_near_square_masked": r.get("n_near_square_masked"),
                "background_source": r.get("background_source")}
        for src, s in (r.get("sources") or {}).items():
            base[f"{src}_partial_corr"] = s["partial_corr_vs_orient_risk"]
            base[f"{src}_hsic_p"] = s["hsic_p_value"]
        rows.append(base)
        srcs = r.get("sources", {})
        print(f"[a4 {split}] n_used={r.get('n_used')} "
              + " ".join(f"{k}:pc={v['partial_corr_vs_orient_risk']},p={v['hsic_p_value']}"
                         for k, v in srcs.items()))
    write_csv(os.path.join(REPORT_DIR, "a4_source_attribution_smoke_summary.csv"), rows, list(rows[0].keys()))
    json.dump(detail, open(os.path.join(PROBE_DIR, "a4_attribution_detail.json"), "w"), indent=2, ensure_ascii=False)
    L = ["# A4 Source-Attribution — Mechanism SMOKE (O2-RTDETR host)", "",
         f"> A4 frozen snapshot sha256={a4_hash}…; **mechanism smoke**，非完整 A4 gate。background source 在 smoke 中 unavailable（需 raster image）。", "",
         "| split | n_used | masked | E_layout pc | E_layout HSIC p | score pc | score HSIC p | entropy pc | GV pc |",
         "|---|---|---|---|---|---|---|---|---|"]
    for split in ("D_cal", "D_audit"):
        r = detail[split]; s = r.get("sources", {})
        def g(k, f):
            return s.get(k, {}).get(f)
        L.append(f"| {split} | {r.get('n_used')} | {r.get('n_near_square_masked')} | "
                 f"{g('E_layout','partial_corr_vs_orient_risk')} | {g('E_layout','hsic_p_value')} | "
                 f"{g('score','partial_corr_vs_orient_risk')} | {g('score','hsic_p_value')} | "
                 f"{g('entropy','partial_corr_vs_orient_risk')} | {g('gv_needed','partial_corr_vs_orient_risk')} |")
    L += ["", "## 机制原语已实现并跑通",
          "- orientation evidence attribution、partial-corr(控 GV+class)、HSIC(置换 p, 受控抽样 max_samples=800/seed=0)、",
          "  source sanity(GV/layout/score/entropy vs orientation risk)、per-class、bootstrap CI、near-square mask、D_cal/D_audit。",
          "## 可进入 D_cal / 仍 blocked",
          "- 可进入 D_cal 探索: partial-corr / HSIC source-attribution 原语（机制级）。",
          "- **仍 blocked（不可进入 formal A4 gate）**: background source 未算（需 image annulus）；A4 vs GV/entropy/score 的最小 Δ、partial-corr/HSIC 上界 (R8) 未冻结；A-gate-1 source sanity 完整流程 + 批准未做。",
          "## 下一步",
          "- 补 background source（对 A4 frozen host 在 image 上算 annulus 梯度）；扩样本；预注册 A_A4 阈值后冻结并做 D_audit 正式 gate。"]
    open(os.path.join(REPORT_DIR, "a4_source_attribution_smoke_report.md"), "w").write("\n".join(L) + "\n")
    print("[ok] wrote a4_source_attribution_smoke_report.{md,csv}")


if __name__ == "__main__":
    main()
