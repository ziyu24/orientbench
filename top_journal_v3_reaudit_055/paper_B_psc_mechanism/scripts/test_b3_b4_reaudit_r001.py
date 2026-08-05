#!/usr/bin/env python3
"""Focused deterministic tests for the r001 weighted-cluster NRC implementation."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("reaudit_b3_b4_r001.py")
SPEC = importlib.util.spec_from_file_location("reaudit_b3_b4_r001", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WeightedClusterNrcTests(unittest.TestCase):
    def test_all_registered_equivalence_cases(self):
        rows = MODULE.equivalence_tests()
        self.assertGreaterEqual(len(rows), 9)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))

    def test_resample_plan_is_deterministic(self):
        clusters = np.array(["a", "a", "b", "c", "c", "c"], dtype=object)
        first = MODULE.resample_plan(clusters, 12345)
        second = MODULE.resample_plan(clusters, 12345)
        np.testing.assert_array_equal(first[1], second[1])
        np.testing.assert_array_equal(first[2], second[2])
        self.assertEqual(first[3], second[3])

    def test_stable_ties_equal_explicit_expansion(self):
        score = np.array([.5, .5, .5, .2, .2])
        risk = np.array([5., 1., 3., 8., 2.])
        weights = np.array([3, 1, 2, 0, 4])
        expected = MODULE.explicit_expansion_nrc(score, risk, weights)
        observed = MODULE.weighted_nrc(score, risk, weights)
        self.assertAlmostEqual(expected, observed, places=12)

    def test_heterogeneous_clusters_reject_legacy_mean_estimand(self):
        rows = MODULE.equivalence_tests()
        row = next(item for item in rows if item["test_id"] == "heterogeneous_cluster_old_estimand_rejected")
        self.assertEqual(row["status"], "PASS")
        self.assertGreater(float(row["observed"]), 0.01)


if __name__ == "__main__":
    unittest.main(verbosity=2)
