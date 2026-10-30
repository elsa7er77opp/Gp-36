"""Regression cases on the real raw data. Skipped when GP36_Dataset is not present.

Set GP36_REQUIRE_REAL_DATA=1 to turn the skip into a failure (use this on the project laptop, so a
missing dataset can never be reported as a clean run).
"""
import os
import unittest
from pathlib import Path

from helpers import ROOT

from gp36data.labels import compare_box_sets, parse_label_file
from gp36data.manifest import sha256_file

DS = ROOT.parent / "GP36_Dataset"
RF = DS / "roboflow"
if os.environ.get("GP36_REQUIRE_REAL_DATA") == "1" and not DS.exists():
    raise RuntimeError(f"GP36_REQUIRE_REAL_DATA=1 but {DS} does not exist")


@unittest.skipUnless(DS.exists(), "GP36_Dataset not available")
class TestRealData(unittest.TestCase):
    def test_pothole_058_has_three_valid_road_boxes(self):
        boxes, issues = parse_label_file(DS / "potholes" / "labels" / "pothole_058.txt")
        self.assertEqual(issues, [])
        self.assertEqual(len(boxes), 3)
        # the box blamed on the CAUTION sign lies in the bottom strip of the image (road surface)
        low = [b for b in boxes if b.xc < 0.35 and b.yc > 0.85]
        self.assertEqual(len(low), 1)

    def test_g0040808_pair_is_identical_image_with_conflicting_labels(self):
        a = "G0040808_JPG.rf.db88a6d7fee09c7b426a27b644691f9e"
        b = "G0040808_JPG.rf.e29f0b5101177b9051d4c54ff274a47b"
        self.assertEqual(sha256_file(RF / "train" / "images" / f"{a}.jpg"), sha256_file(RF / "test" / "images" / f"{b}.jpg"))
        la, _ = parse_label_file(RF / "train" / "labels" / f"{a}.txt")
        lb, _ = parse_label_file(RF / "test" / "labels" / f"{b}.txt")
        self.assertEqual(compare_box_sets(la, lb), "conflict")

    def test_every_roboflow_name_has_multiple_dots_and_pairs(self):
        from gp36data.io_utils import pair_images_labels
        for s in ("train", "valid", "test"):
            pairs, nl, ol = pair_images_labels(RF / s / "images", RF / s / "labels")
            self.assertEqual((len(nl), len(ol)), (0, 0))
            self.assertTrue(all(p[0].stem.count(".") >= 2 for p in pairs))


if __name__ == "__main__":
    unittest.main()
