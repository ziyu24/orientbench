"""Pure in-memory regression cases for the r025 correspondence error."""
import unittest

from orientbench.r025.run import pair_labels, parse_native


class TextInput:
    def __init__(self, text):
        self.text = text

    def read_text(self, **kwargs):
        return self.text


def label(x=0, kind="plane", difficult="0"):
    return f"{x} 0 {x+10} 0 {x+10} 10 {x} 10 {kind} {difficult}"


class PairingTests(unittest.TestCase):
    def pair(self, old, new):
        return pair_labels("fixture", TextInput(old), TextInput(new),
                           {"polygon_tolerance": 1e-6, "iou_threshold": .5})

    def test_one_sided_exact_key_reaches_iou(self):
        _, rows, edges, _ = self.pair(label(), label(1))
        self.assertEqual([r["status"] for r in rows], ["geometry_revised"])
        self.assertEqual(len(edges), 1)
        self.assertAlmostEqual(rows[0]["iou"], 9/11)

    def test_no_overlap_is_not_duplicate(self):
        _, rows, edges, _ = self.pair(label(), label(50))
        self.assertEqual({r["status"] for r in rows}, {"old_no_candidate", "new_no_candidate"})
        self.assertEqual(edges, [])

    def test_real_duplicate_stays_ambiguous(self):
        _, rows, edges, _ = self.pair(label()+"\n"+label(), label())
        self.assertEqual([r["status"] for r in rows], ["exact_duplicate_ambiguous"]*3)
        self.assertEqual(edges, [])

    def test_dense_iou_is_not_forced(self):
        _, rows, edges, _ = self.pair(label(), label(1)+"\n"+label(2))
        self.assertEqual(len(edges), 2)
        self.assertEqual({r["status"] for r in rows}, {"old_iou_ambiguous", "new_iou_ambiguous"})

    def test_cyclic_reversed_and_metadata(self):
        other = "10 10 10 0 0 0 0 10 ship 1"
        _, rows, _, _ = self.pair(label(), other)
        self.assertEqual(rows[0]["status"], "class_or_difficult_only")
        self.assertFalse(rows[0]["literal_quad_equal"])
        self.assertEqual(rows[0]["centroid_shift"], 0)

    def test_empty_images(self):
        objects, rows, edges, counts = self.pair("", "")
        self.assertEqual((objects, rows, edges), ([], [], []))
        self.assertEqual(counts["old_total"], 0)

    def test_missing_difficult_retained(self):
        objects = parse_native(TextInput(label().rsplit(" ", 1)[0]), "v1", "fixture", 1e-6)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0]["error"], "missing_difficult")

    def test_metadata_is_not_malformed_object(self):
        objects = parse_native(TextInput("acquisition date:2016-06-28\nimagesource:GoogleEarth\ngsd:None"), "v1", "fixture", 1e-6)
        self.assertEqual(objects, [])


if __name__ == "__main__":
    unittest.main()
