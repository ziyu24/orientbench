import unittest
import numpy as np

from orientbench.r029.sampling import ap11, estimate, sample_plans


def image(rank, tp, fp, gt):
    return np.array(rank), np.array(tp), np.array(fp), gt


class SamplingTests(unittest.TestCase):
    def test_population_ap_is_not_image_average(self):
        a = image([0], [1], [0], 1)
        b = image([1], [0], [1], 0)
        self.assertEqual(estimate([a, b], [1, 1])[0], 1)
        self.assertEqual((estimate([a], [1])[0] + estimate([b], [1])[0]) / 2, .5)

    def test_constant_ht_weights_cancel(self):
        q = [image([0, 2], [0, 1], [1, 0], 2), image([1], [1], [0], 1)]
        self.assertAlmostEqual(estimate(q, [1, 1])[0], estimate(q, [7, 7])[0])

    def test_unbiased_totals_do_not_imply_unbiased_ap(self):
        a = image([0], [1], [0], 1)
        b = image([1], [0], [1], 0)
        draws = [estimate([q], [2]) for q in [a, b]]
        self.assertEqual(np.mean([x[1] for x in draws]), 1)
        self.assertEqual(np.mean([x[0] for x in draws]), .5)
        self.assertEqual(estimate([a, b], [1, 1])[0], 1)

    def test_weighting_changes_ap_and_unknown_gt_is_estimated(self):
        q = [image([0], [1], [0], 1), image([1], [0], [1], 2)]
        self.assertNotEqual(estimate(q, [1, 1])[0], estimate(q, [1, 3])[0])
        self.assertEqual(estimate(q, [1, 3])[1], 7)

    def test_sampling_no_duplicates_census_and_known_ht_totals(self):
        ids = list(map(str, range(12)))
        plans = list(sample_plans(ids, np.arange(12), [4, 8, 12], 2, 29029))
        self.assertEqual(len(plans), 18)
        for _, b, method, picked, weights in plans:
            self.assertEqual(len(set(picked)), b)
            if method != 'stratified_unweighted':
                self.assertAlmostEqual(sum(weights), 12)
            if b == 12:
                np.testing.assert_array_equal(picked, np.arange(12))
                np.testing.assert_array_equal(weights, np.ones(12))

    def test_empty_and_ignored_predictions(self):
        self.assertEqual(ap11([], [], 2), 0)
        self.assertEqual(ap11([0, 1], [0, 0], 1), 1)
        self.assertEqual(estimate([image([], [], [], 3)], [2]), (0, 6))

    def test_repeated_image_rejected(self):
        q = image([0], [1], [0], 1)
        with self.assertRaises(ValueError):
            estimate([q, q], [1, 1])


if __name__ == '__main__':
    unittest.main()
