import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import coco_eval as ce  # noqa: E402


def toy():
    meta = {"a": {"out_w": "1000", "out_h": "500"}, "b": {"out_w": "1000", "out_h": "500"}}
    gt = {"a": [(0, (0.1, 0.1, 0.3, 0.5), 0.08)], "b": [(1, (0.5, 0.6, 0.9, 0.8), 0.08)]}
    return meta, gt


class TestCocoEval(unittest.TestCase):
    def test_perfect_predictions_score_one(self):
        meta, gt = toy()
        pr = {"a": [(0, 0.9, (0.1, 0.1, 0.3, 0.5))], "b": [(1, 0.8, (0.5, 0.6, 0.9, 0.8))]}
        s = ce.coco_stats(*ce.to_coco(meta, gt, pr))
        self.assertAlmostEqual(s["AP"], 1.0, places=3)
        self.assertAlmostEqual(s["AP50"], 1.0, places=3)

    def test_wrong_class_and_pixel_boxes(self):
        meta, gt = toy()
        pr = {"a": [(1, 0.9, (0.1, 0.1, 0.3, 0.5))]}  # right box, wrong class
        gtj, dets = ce.to_coco(meta, gt, pr)
        for got, want in zip(gtj["annotations"][0]["bbox"], [100.0, 50.0, 200.0, 200.0]):
            self.assertAlmostEqual(got, want, places=6)
        self.assertEqual(dets[0]["category_id"], 2)
        self.assertAlmostEqual(ce.coco_stats(gtj, dets, [1])["AP50"], 0.0, places=3)

    def test_half_recall(self):
        meta, gt = toy()
        pr = {"a": [(0, 0.9, (0.1, 0.1, 0.3, 0.5))]}  # pothole found, bump missed
        gtj, dets = ce.to_coco(meta, gt, pr)
        self.assertAlmostEqual(ce.coco_stats(gtj, dets, [1])["AP50"], 1.0, places=3)
        self.assertAlmostEqual(ce.coco_stats(gtj, dets, [2])["AP50"], 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
