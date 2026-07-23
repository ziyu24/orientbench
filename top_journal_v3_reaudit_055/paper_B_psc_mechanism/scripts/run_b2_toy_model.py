#!/usr/bin/env python3
"""Frozen minimal PSC-style toy model for mechanism sufficiency only."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BROOT = Path(__file__).resolve().parents[1]
PROTOCOL = BROOT / "reports/b1_protocol_frozen.json"
GRID_OUT = BROOT / "reports/b2_toy_model_grid.csv"
SUMMARY_OUT = BROOT / "reports/b2_toy_model_sufficiency.csv"
DOC_OUT = BROOT / "docs/b2_toy_model_analysis.md"
LOG_OUT = BROOT / "logs/b2_toy_model.log"


def circular_abs_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(a - b) % 180.0
    return np.minimum(d, 180.0 - d)


def nrc(score: np.ndarray, risk: np.ndarray) -> float:
    order = np.argsort(-score, kind="stable")
    curve = np.cumsum(risk[order]) / np.arange(1, len(risk) + 1)
    oracle = np.cumsum(np.sort(risk, kind="stable")) / np.arange(1, len(risk) + 1)
    random = float(np.mean(risk))
    denom = float(np.mean(np.full(len(risk), random) - oracle))
    return float(np.mean(curve - oracle) / denom) if denom > 1e-12 else float("nan")


def decode(primary_phase, secondary_phase, secondary_mod, threshold):
    # PSC dual-frequency candidate selection followed by its secondary-modulation gate.
    c0 = secondary_phase / 2.0
    c1 = ((c0 + np.pi + np.pi) % (2 * np.pi)) - np.pi
    use1 = np.cos(primary_phase - c0) < 0
    selected = np.where(use1, c1, c0)
    selected = np.where(secondary_mod < threshold, 0.0, selected)
    return selected / 2.0, use1


def atomic_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(value, encoding="utf-8")
    os.replace(tmp, path)


def run() -> None:
    frozen = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if frozen["hypotheses"] != ["H1", "H2", "H3", "H4"]:
        raise RuntimeError("B1 protocol is not frozen as expected")
    rows = []
    radial_levels = (0.55, 0.9, 1.35)
    noise_levels = (0.03, 0.12, 0.28)
    thresholds = (0.30, 0.47, 0.80)
    boundary_masses = (0.10, 0.40, 0.75)
    couplings = (-0.8, 0.0, 0.8)
    ambiguities = (0.05, 0.45, 0.85)
    n = 512
    for radial in radial_levels:
        for noise in noise_levels:
            for threshold in thresholds:
                for boundary_mass in boundary_masses:
                    for coupling in couplings:
                        for ambiguity in ambiguities:
                            key = f"{radial}|{noise}|{threshold}|{boundary_mass}|{coupling}|{ambiguity}"
                            rng = np.random.default_rng(int(hashlib.sha256(key.encode()).hexdigest()[:8], 16))
                            truth = rng.uniform(-np.pi / 2, np.pi / 2, n)
                            near = rng.random(n) < boundary_mass
                            boundary_sign = rng.choice((-1.0, 1.0), n)
                            truth = np.where(near, boundary_sign * (np.pi / 2 - rng.uniform(0, 0.12, n)), truth)
                            latent = rng.normal(0, 1, n)
                            amp = np.clip(radial * np.exp(0.35 * coupling * latent), 0.08, 3.0)
                            directional_noise = noise * np.exp(0.35 * latent)
                            p1 = 2 * truth + rng.normal(0, directional_noise, n)
                            conflict = ambiguity * rng.normal(0, 0.9, n)
                            p2 = 4 * truth + rng.normal(0, 1.2 * directional_noise, n) + conflict
                            secondary_mod = (amp * (1.0 - 0.35 * ambiguity * np.abs(latent))) ** 2
                            decoded, switched = decode(p1, p2, secondary_mod, threshold)
                            truth_deg = np.degrees(truth)
                            decoded_deg = np.degrees(decoded)
                            error = circular_abs_deg(decoded_deg, truth_deg)
                            severe = (error > 10.0).astype(float)
                            phase_mod = amp ** 2
                            negative = -phase_mod
                            disagreement = circular_abs_deg(np.degrees(p1 / 2), np.degrees(p2 / 4))
                            align0 = np.cos(p1 - p2 / 2)
                            align1 = np.cos(p1 - (((p2 / 2 + np.pi + np.pi) % (2 * np.pi)) - np.pi))
                            gap = np.abs(align0 - align1)
                            margin = gap * np.sqrt(np.maximum(secondary_mod, 0))
                            nr = nrc(phase_mod, error)
                            direction = "INFORMATIVE" if nr < 0.9 else ("REVERSE" if nr > 1.1 else "NEAR_RANDOM")
                            rows.append({
                                "radial_norm": radial, "noise_level": noise,
                                "modulation_threshold": threshold, "boundary_mass": boundary_mass,
                                "radial_risk_coupling": coupling, "unwrap_ambiguity": ambiguity,
                                "frequency_ratio": "1:2", "n": n,
                                "decoded_angle_mean_deg": round(float(np.mean(decoded_deg)), 8),
                                "angle_error_mean_deg": round(float(np.mean(error)), 8),
                                "phase_mod_mean": round(float(np.mean(phase_mod)), 8),
                                "negative_phase_mod_nrc_continuous": round(nrc(negative, error), 8),
                                "phase_mod_nrc_continuous": round(nr, 8),
                                "phase_mod_nrc_severe_event": round(nrc(phase_mod, severe), 8),
                                "direction_margin_nrc_continuous": round(nrc(margin, error), 8),
                                "multi_frequency_disagreement_nrc_continuous": round(nrc(-disagreement, error), 8),
                                "unwrap_energy_gap_nrc_continuous": round(nrc(gap, error), 8),
                                "candidate_switch_rate": round(float(np.mean(switched)), 8),
                                "severe_event_rate": round(float(np.mean(severe)), 8),
                                "phase_mod_direction": direction,
                            })
    atomic_csv(GRID_OUT, rows)
    counts = {d: sum(r["phase_mod_direction"] == d for r in rows)
              for d in ("INFORMATIVE", "NEAR_RANDOM", "REVERSE")}
    reverse = [r for r in rows if r["phase_mod_direction"] == "REVERSE"]
    nonextreme = [r for r in reverse if r["noise_level"] <= 0.12 and r["unwrap_ambiguity"] <= 0.45
                  and r["radial_norm"] in (0.9, 1.35)]
    decision = "SUPPORTS_MECHANISM_SUFFICIENCY" if all(counts.values()) and nonextreme else (
        "WEAK_EXTREME_ONLY" if reverse else "DOES_NOT_SUPPORT")
    summary = [{
        "decision": decision,
        "grid_rows": len(rows),
        "informative_rows": counts["INFORMATIVE"],
        "near_random_rows": counts["NEAR_RANDOM"],
        "reverse_rows": counts["REVERSE"],
        "reverse_nonextreme_rows": len(nonextreme),
        "toy_is_sufficiency_only": True,
        "real_network_mechanism_proved": False,
    }]
    atomic_csv(SUMMARY_OUT, summary)
    doc = f"""# B2 PSC-style toy-model sufficiency analysis

The frozen grid contains {len(rows)} parameter cells, each with {n} simulated targets. It explicitly represents radial norm, phase direction, dual frequency, wrapping/candidate selection, modulation threshold, noise, unwrap ambiguity, direction margin, decoded angle, and two endpoint-specific NRCs.

| phase-mod region | cells |
|---|---:|
| informative | {counts['INFORMATIVE']} |
| near-random | {counts['NEAR_RANDOM']} |
| reverse | {counts['REVERSE']} |
| reverse under non-extreme settings | {len(nonextreme)} |

Decision: **{decision}**.

The model demonstrates sufficiency, not identification: ordinary radial/noise/ambiguity settings can produce informative, near-random, and reversed `phase_mod` ordering. Directional disagreement and candidate-gap signals change with the constructed phase conflict, showing how magnitude and error semantics can decouple. No toy result is used as proof of the trained PSC network; B3 real-output interventions are mandatory.
"""
    atomic_text(DOC_OUT, doc)
    atomic_text(LOG_OUT, f"[{time.strftime('%F %T')}] rows={len(rows)} counts={counts} nonextreme={len(nonextreme)} decision={decision}\n")


if __name__ == "__main__":
    run()
