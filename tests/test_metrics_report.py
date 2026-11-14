"""AP and operating-point checks of tools/metrics_report.py on toy cases with known answers."""
import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from helpers import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import metrics_report as mr  # noqa: E402


class TestAP(unittest.TestCase):
    def test_perfect_detector_ap_is_one(self):
        self.assertAlmostEqual(mr.ap101([0.9, 0.8, 0.7], [True, True, True], 3), 1.0)

    def test_no_predictions_is_zero_and_no_gt_is_none(self):
        self.assertEqual(mr.ap101([], [], 5), 0.0)
        self.assertIsNone(mr.ap101([0.5], [False], 0))

    def test_half_recall_only(self):
        # 1 TP out of 2 GT, precision 1 up to recall 0.5, nothing after -> 51 of 101 points at 1.0
        self.assertAlmostEqual(mr.ap101([0.9], [True], 2), 51 / 101)

    def test_fp_ranked_first(self):
        # FP (0.9) then TP (0.8): precision at recall 1 = 0.5 everywhere -> AP 0.5
        self.assertAlmostEqual(mr.ap101([0.9, 0.8], [False, True], 1), 0.5)

    def test_tp_then_fp_does_not_lower_ap(self):
        self.assertAlmostEqual(mr.ap101([0.9, 0.8], [True, False], 1), 1.0)

    def test_order_of_input_does_not_matter(self):
        a = mr.ap101([0.2, 0.9, 0.5, 0.7], [True, False, True, False], 3)
        b = mr.ap101([0.9, 0.7, 0.5, 0.2], [False, False, True, True], 3)
        self.assertAlmostEqual(a, b)


class TestMatch(unittest.TestCase):
    def test_greedy_by_score_and_one_gt_per_pred(self):
        g = np.array([[0.1, 0.1, 0.3, 0.3]])
        preds = [(0.5, (0.1, 0.1, 0.3, 0.3)), (0.9, (0.11, 0.11, 0.31, 0.31))]
        tp, gi = mr.match(preds, g, 0.5)
        self.assertEqual(tp.tolist(), [False, True])  # the higher score takes the only GT
        self.assertEqual(gi.tolist(), [-1, 0])

    def test_iou_threshold(self):
        g = np.array([[0.0, 0.0, 0.2, 0.2]])
        tp, _ = mr.match([(0.9, (0.1, 0.0, 0.3, 0.2))], g, 0.5)  # IoU = 1/3
        self.assertFalse(tp[0])
        tp, _ = mr.match([(0.9, (0.1, 0.0, 0.3, 0.2))], g, 0.3)
        self.assertTrue(tp[0])


def make_toy_dataset(d, images, split="val"):
    """images: {stem: [(cls, xc, yc, w, h), ...]}, all 100x100 px."""
    (d / "labels" / split).mkdir(parents=True)
    with open(d / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["split", "out_image", "out_w", "out_h", "source"])
        w.writeheader()
        for stem, boxes in images.items():
            w.writerow({"split": split, "out_image": f"images/{split}/{stem}.jpg", "out_w": 100, "out_h": 100,
                        "source": "toy"})
            (d / "labels" / split / f"{stem}.txt").write_text(
                "".join(f"{c} {x} {y} {bw} {bh}\n" for c, x, y, bw, bh in boxes), encoding="utf-8")


def pred(stem, cls, score, xc, yc, w, h):  # normalised -> save_json pixel format (100x100)
    return {"image_id": stem, "category_id": cls + 1, "score": score,
            "bbox": [(xc - w / 2) * 100, (yc - h / 2) * 100, w * 100, h * 100]}


class TestEvaluate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        make_toy_dataset(self.tmp, {
            "a": [(0, 0.5, 0.8, 0.2, 0.2)],      # near pothole (bottom edge 0.9)
            "b": [(1, 0.5, 0.3, 0.4, 0.1)],      # far bump
            "c": [],                             # hazard-free
            "d": [(0, 0.2, 0.2, 0.1, 0.1), (1, 0.6, 0.85, 0.4, 0.1)],
        })
        P = [pred("a", 0, 0.9, 0.5, 0.8, 0.2, 0.2), pred("b", 1, 0.8, 0.5, 0.3, 0.4, 0.1),
             pred("c", 0, 0.6, 0.5, 0.5, 0.1, 0.1),            # FP on the empty frame
             pred("d", 0, 0.3, 0.2, 0.2, 0.1, 0.1), pred("d", 1, 0.7, 0.6, 0.85, 0.4, 0.1)]
        self.pj = self.tmp / "predictions.json"
        self.pj.write_text(json.dumps(P), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_pothole_numbers(self):
        meta, gt, pr = mr.load(self.tmp, "val", self.pj)
        e = mr.evaluate(sorted(meta), gt, pr, 0)
        # ranking: a 0.9 TP, c 0.6 FP, d 0.3 TP -> AP: P=1 up to R=.5, then 2/3 up to R=1
        self.assertAlmostEqual(e["AP50"], (51 * 1.0 + 50 * (2 / 3)) / 101, places=6)
        self.assertEqual(e["n_gt"], 2)
        # argmax F1: at 0.9 -> P1 R.5 F1 .667; at 0.3 -> P 2/3 R1 F1 .8  => thr 0.3
        self.assertAlmostEqual(e["op"]["thr"], 0.3)
        self.assertEqual((e["op"]["tp"], e["op"]["fp"], e["op"]["fn"]), (2, 1, 0))
        self.assertAlmostEqual(e["op"]["BoxAcc"], 2 / 3)
        # image level: a ok, b ok (no pothole, none predicted), c wrong (FP), d ok -> 3/4
        self.assertAlmostEqual(e["op"]["ImgAcc"], 0.75)
        self.assertEqual(e["op"]["n_neg"], 2)
        # near-range: only box a is near and large enough (d pothole is far and small)
        self.assertEqual(e["op"]["n_near"], 1)
        self.assertAlmostEqual(e["op"]["NearR"], 1.0)
        # deployed conf 0.35 drops the d pothole
        self.assertEqual((e["deploy"]["tp"], e["deploy"]["fp"], e["deploy"]["fn"]), (1, 1, 1))

    def test_bump_perfect(self):
        meta, gt, pr = mr.load(self.tmp, "val", self.pj)
        e = mr.evaluate(sorted(meta), gt, pr, 1)
        self.assertAlmostEqual(e["AP50"], 1.0)
        self.assertAlmostEqual(e["P_at_R50"], 1.0)
        self.assertEqual(e["op"]["n_near"], 1)  # d bump: y2 = 0.9, sqrt(0.04) = 0.2

    def test_fixed_threshold_is_used(self):
        meta, gt, pr = mr.load(self.tmp, "val", self.pj)
        e = mr.evaluate(sorted(meta), gt, pr, 0, thr=0.95)
        self.assertEqual(e["op"]["tp"], 0)
        self.assertEqual(e["op"]["thr"], 0.95)

    def test_prediction_for_unknown_image_exits(self):
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps([pred("zzz", 0, 0.9, 0.5, 0.5, 0.1, 0.1)]), encoding="utf-8")
        with self.assertRaises(SystemExit):
            mr.load(self.tmp, "val", bad)


class TestNearCare(TestEvaluate):
    """--care near: KITTI/COCO ignore-region semantics (definition in CLOUD_REPORT.md §0-S5 B1)."""

    def test_care_range(self):
        self.assertTrue(mr.in_care((0.4, 0.7, 0.6, 0.9)))      # y2 0.9, side 0.2
        self.assertFalse(mr.in_care((0.4, 0.3, 0.6, 0.55)))    # bottom edge above 0.60 H
        self.assertFalse(mr.in_care((0.5, 0.9, 0.52, 0.92)))   # sqrt(area) 0.02 < 0.05

    def test_pothole_near(self):
        meta, gt, pr = mr.load(self.tmp, "val", self.pj)
        e = mr.evaluate(sorted(meta), gt, pr, 0)
        n = mr.evaluate_near(sorted(meta), gt, pr, 0, {"op": e["op"]["thr"], "deploy": 0.35})
        # a: near GT, TP. d: far small pothole -> ignore GT, its prediction is ignored (not TP, not FP).
        # c: FP box with y2 = 0.55 -> outside the care range -> ignored.
        self.assertEqual((n["n_gt"], n["n_ignore_gt"]), (1, 1))
        self.assertAlmostEqual(n["AP50"], 1.0)
        self.assertEqual((n["op"]["tp"], n["op"]["fp"], n["op"]["fn"]), (1, 0, 0))
        self.assertAlmostEqual(n["op"]["thr"], e["op"]["thr"])   # same threshold as "all", never re-chosen
        self.assertAlmostEqual(n["op"]["ImgAcc"], 1.0)
        # the full numbers are unchanged next to it
        self.assertEqual((e["op"]["tp"], e["op"]["fp"]), (2, 1))

    def test_fp_inside_care_range_counts(self):
        st, _ = mr.match_care([(0.9, (0.1, 0.7, 0.3, 0.9))], np.zeros((0, 4)), np.zeros((0, 4)))
        self.assertEqual(st.tolist(), [0])

    def test_ignore_gt_absorbs_several_predictions(self):
        ign = np.array([[0.1, 0.1, 0.3, 0.3]])
        st, _ = mr.match_care([(0.9, (0.1, 0.1, 0.3, 0.3)), (0.8, (0.11, 0.1, 0.31, 0.3))], np.zeros((0, 4)), ign)
        self.assertEqual(st.tolist(), [-1, -1])

    def test_care_gt_matched_before_ignore_gt(self):
        care = np.array([[0.1, 0.7, 0.3, 0.9]])
        ign = np.array([[0.1, 0.7, 0.3, 0.9]])
        st, gi = mr.match_care([(0.9, (0.1, 0.7, 0.3, 0.9)), (0.5, (0.1, 0.7, 0.3, 0.9))], care, ign)
        self.assertEqual(st.tolist(), [1, -1])   # 2nd duplicate falls on the ignore GT, not an FP
        self.assertEqual(gi.tolist()[0], 0)

    def test_cli_writes_near_next_to_all(self):
        import subprocess
        out = self.tmp / "rep"
        r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "metrics_report.py"), "--data", str(self.tmp),
                            "--split", "val", "--pred", f"m={self.pj}", "--care", "near", "--out", str(out)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads((out / "report.json").read_text(encoding="utf-8"))
        c = rep["models"]["m"]["classes"]["pothole"]
        self.assertIn("AP50", c)
        self.assertIn("near", c)
        self.assertEqual(rep["care"], "near")
        self.assertIn("AP50 all | AP50 near", (out / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
