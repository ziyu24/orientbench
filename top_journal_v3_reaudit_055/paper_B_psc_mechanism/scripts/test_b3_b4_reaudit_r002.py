#!/usr/bin/env python3
"""Focused regression tests for the r002 evidence-closure implementation."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("reaudit_b3_b4_r002.py")
SPEC = importlib.util.spec_from_file_location("reaudit_b3_b4_r002", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
OLD = MODULE.load_r001()


class R002Tests(unittest.TestCase):
    def test_formal_suite(self):
        rows = MODULE.run_tests(OLD)
        self.assertGreaterEqual(len(rows), 7)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))

    def test_bootstrap_respects_37_rows(self):
        clusters = np.array(["a", "a", "b", "c"])
        _, inverse = np.unique(clusters, return_inverse=True)
        multiplicities = np.tile(np.array([[1, 1, 1]], dtype=np.uint16), (37, 1))
        scores = {"candidate": np.array([.9,.8,.5,.2]), "phase_mod": np.array([.2,.3,.4,.5]),
                  "detection_score": np.array([.8,.7,.6,.5])}
        result = MODULE.bootstrap_nrc(scores, np.array([1.,2.,3.,5.]), inverse, multiplicities, OLD, workers=2)
        self.assertTrue(all(len(values) == 37 for values in result.values()))

    def test_nan_mask_is_shared(self):
        clusters = np.array(["a", "b", "c"])
        mask, reasons = MODULE.common_finite_mask(
            clusters, np.array([1., 2., np.nan]),
            {"candidate": np.array([.1, np.nan, .3]), "phase_mod": np.ones(3), "detection_score": np.ones(3)},
        )
        np.testing.assert_array_equal(mask, np.array([True, False, False]))
        self.assertEqual(reasons, {"risk_nonfinite": 1, "candidate_nonfinite": 1})

    def test_machine_verdict_does_not_invent_pass(self):
        self.assertEqual(MODULE.derive_verdict(True, True, False, 0, 24),
                         ("PASS_EVIDENCE_CLOSURE", "FAIL_CANDIDATE_GATE"))
        self.assertEqual(MODULE.derive_verdict(True, True, True, 0, 24)[0], "FAIL_EVIDENCE_DRIFT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
