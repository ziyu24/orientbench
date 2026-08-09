#!/usr/bin/env python3
"""Production-path microtests frozen before r019 DOTA label access."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import torch
from mmrotate.structures.bbox import RotatedBoxes

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "p3_selector/deployable_proxy_r019/scripts"))
import eqs_rc_r019 as prod


def record(image, boxes, scores=None, labels=None):
    boxes = torch.tensor(boxes, dtype=torch.float32).reshape((-1, 5))
    n = len(boxes)
    return {"img_id": image, "ori_shape": (100, 120), "img_shape": (100, 120),
            "pred_instances": {"bboxes": boxes,
                               "scores": torch.tensor(scores if scores is not None else [0.8] * n),
                               "labels": torch.tensor(labels if labels is not None else [0] * n, dtype=torch.long)}}


def main():
    tests = []
    def check(name, actual, expected, tol=1e-9):
        if isinstance(expected, float):
            passed = abs(float(actual) - expected) <= tol
        else:
            passed = actual == expected
        tests.append({"name": name, "expected": expected, "actual": actual, "tolerance": tol, "pass": passed})

    # Inverse and double-flip use the actual mmrotate/r014 transformation path.
    original = torch.tensor([[20., 30., 14., 5., .31]])
    for direction in ("horizontal", "vertical"):
        flipped = RotatedBoxes(original.clone()); flipped.flip_((100, 120), direction)
        rec = record("x", flipped.tensor.tolist())
        restored = prod.inverse_view(rec, direction)
        check(f"{direction}_inverse_roundtrip", np.max(np.abs(prod.canonical_boxes(original).numpy() - restored.numpy())).item(), 0.0, 1e-5)

    c1 = prod.canonical_box([1, 2, 10, 4, 0.2])
    c2 = prod.canonical_box([1, 2, 4, 10, 0.2 + math.pi / 2])
    check("width_height_plus_90_canonical", float(np.max(np.abs(c1 - c2))), 0.0, 1e-12)
    check("zero_ninety_boundary", prod.R014.le90_deg(0, math.pi / 2), 90.0, 1e-12)
    check("axial_same", prod.axial_dispersion([.2, .2]), 0.0, 1e-12)
    check("axial_pi_equivalent", prod.axial_dispersion([.2, .2 + math.pi]), 0.0, 1e-12)
    check("axial_orthogonal", prod.axial_dispersion([0, math.pi / 2]), 1.0, 1e-12)
    check("axial_no_aux", prod.axial_dispersion([.2], no_auxiliary=True), 1.0, 0)

    ib = torch.tensor([[0., 0., 10., 4., 0.]])
    il = torch.tensor([0])
    m0, g0 = prod.association(ib, il, torch.empty((0, 5)), torch.empty((0,)), torch.empty((0,), dtype=torch.long))
    check("margin_zero_candidate", [m0, g0], [{}, {0: 0.0}], 0)
    m1, g1 = prod.association(ib, il, ib.clone(), torch.tensor([0.8]), il)
    check("margin_one_candidate", g1[0], 1.0, 0)
    shifted = torch.tensor([[0.8, 0., 10., 4., 0.]])
    ms, gs = prod.association(ib, il, shifted, torch.tensor([0.8]), il)
    check("margin_wrong_top1_iou_negative", gs[0] == float(ms[0][1]), False, 0)
    two = torch.tensor([[0., 0., 10., 4., 0.], [1., 0., 10., 4., 0.]])
    m2, g2 = prod.association(ib, il, two, torch.tensor([.8, .7]), torch.tensor([0, 0]))
    check("margin_two_candidate_range", 0.0 <= g2[0] <= 1.0, True, 0)
    dense = torch.cat([two, two], dim=0)
    md, _ = prod.association(torch.cat([ib, ib]), torch.tensor([0, 0]), dense, torch.tensor([.8, .8, .8, .8]), torch.tensor([0, 0, 0, 0]))
    check("dense_stable_unique", sorted(md), [0, 1], 0)
    check("stable_tie", m2[0][0], 0, 0)
    mc, _ = prod.association(ib, il, ib.clone(), torch.tensor([.8]), torch.tensor([1]))
    check("class_mismatch", mc, {}, 0)

    empty = record("x", [], [], [])
    base = record("x", [[0, 0, 10, 4, 0]])
    identity_inverse = lambda rec, direction: prod.canonical_boxes(prod.R014.tensors(rec)[0])
    sentinel = prod.build_feature_rows([base], [empty], [empty], lambda ar: 20., identity_inverse)[0]
    check("missing_sentinel", [sentinel[k] for k in ("axial_dispersion", "u_axis", "iou_loss", "center_dispersion", "long_side_dispersion", "short_side_dispersion", "score_dispersion", "association_margin")], [1., 3., 1., 3., 3., 3., 10., 0.], 0)
    swapped = record("x", [[0, 0, 4, 10, math.pi / 2]])
    s2 = prod.build_feature_rows([swapped], [empty], [empty], lambda ar: 20., identity_inverse)[0]
    check("all_13_width_height_equivalence", [sentinel[k] for k in prod.FEATURE_COLUMNS], [s2[k] for k in prod.FEATURE_COLUMNS], 0)

    fail_closed = []
    cases = [
        ("missing_image", [base], [empty], []),
        ("duplicate_image", [base, base], [empty, empty], [empty, empty]),
        ("wrong_unit", [record("a", [[0,0,10,4,0]])], [record("b", [], [], [])], [record("a", [], [], [])]),
    ]
    for name, a, b, c in cases:
        try:
            prod.build_feature_rows(a, b, c, lambda ar: 20., identity_inverse)
            failed = False
        except Exception:
            failed = True
        fail_closed.append({"name": name, "nonzero_equivalent": failed})
    try:
        prod.canonical_box([0, 0, float("nan"), 4, 0]); finite_closed = False
    except Exception:
        finite_closed = True
    fail_closed.append({"name": "non_finite", "nonzero_equivalent": finite_closed})
    try:
        prod.inverse_view(base, "diagonal"); unknown_closed = False
    except Exception:
        unknown_closed = True
    fail_closed.append({"name": "unknown_view", "nonzero_equivalent": unknown_closed})
    try:
        bad = record("x", [[0, 0, 10, 4, 0]])
        del bad["pred_instances"]["scores"]
        prod.build_feature_rows([bad], [empty], [empty], lambda ar: 20., identity_inverse)
        schema_closed = False
    except Exception:
        schema_closed = True
    fail_closed.append({"name": "schema_drift", "nonzero_equivalent": schema_closed})

    forbidden = ("gt", "ground_truth", "angle_error", "risk", "gt_ar", "split", "role")
    persisted = prod.KEY_COLUMNS + prod.FEATURE_COLUMNS
    schema_hits = {column: [token for token in forbidden if token in column.lower()] for column in persisted}
    schema_hits = {k: v for k, v in schema_hits.items() if v}
    tests.append({"name": "schema_forbidden_prefix_contains", "expected": {}, "actual": schema_hits, "tolerance": 0, "pass": not schema_hits})
    tests.append({"name": "fail_closed_suite", "expected": True, "actual": all(x["nonzero_equivalent"] for x in fail_closed), "tolerance": 0, "pass": all(x["nonzero_equivalent"] for x in fail_closed), "cases": fail_closed})
    payload = {"schema": "r019_production_microtests_v1", "seed": 20260809, "production_module": str(Path(prod.__file__).relative_to(ROOT)), "tests": tests, "all_pass": all(x["pass"] for x in tests)}
    output = ROOT / "p3_selector/deployable_proxy_r019/prelabel/production_microtests_r019.json"
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"all_pass": payload["all_pass"], "tests": len(tests)}))
    raise SystemExit(0 if payload["all_pass"] else 1)


if __name__ == "__main__": main()
