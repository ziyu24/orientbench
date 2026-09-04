import math
import unittest

from orientbench.r011.audit import rp1_from_wh


class RP1CanonicalizationTest(unittest.TestCase):
    def test_width_height_swap_compensates_ninety_degrees(self):
        self.assertAlmostEqual(
            rp1_from_wh(0.0, 4.0, 1.0),
            rp1_from_wh(math.pi / 2, 1.0, 4.0),
        )
