"""tools/wbf_ensemble.py: fusion arithmetic, agreement rescaling, class separation, CLI."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import wbf_ensemble as wbf  # noqa: E402


class TestFuse(unittest.TestCase):
    def test_two_models_agree_weighted_average(self):
        out = wbf.fuse_boxes([(0, 0.8, [0, 0, 10, 10]), (1, 0.4, [2, 0, 10, 10])], [1, 1])
        self.assertEqual(len(out), 1)
        s, b = out[0]
        self.assertAlmostEqual(b[0], (0.8 * 0 + 0.4 * 2) / 1.2)   # score-weighted x1
        self.assertAlmostEqual(b[2], 10.0)
        self.assertAlmostEqual(s, 0.6)                             # mean score, both models present

    def test_single_model_box_is_down_weighted(self):
        (s, _), = wbf.fuse_boxes([(0, 0.8, [0, 0, 10, 10])], [1, 1])
        self.assertAlmostEqual(s, 0.4)

    def test_two_boxes_of_one_model_do_not_fake_agreement(self):
        (s, _), = wbf.fuse_boxes([(0, 0.8, [0, 0, 10, 10]), (0, 0.8, [0, 0, 10, 10])], [1, 1])
        self.assertAlmostEqual(s, 0.4)

    def test_far_boxes_stay_separate(self):
        out = wbf.fuse_boxes([(0, 0.9, [0, 0, 10, 10]), (1, 0.9, [50, 50, 10, 10])], [1, 1])
        self.assertEqual(len(out), 2)

    def test_model_weights(self):
        (s, b), = wbf.fuse_boxes([(0, 0.5, [0, 0, 10, 10]), (1, 0.5, [4, 0, 10, 10])], [3, 1], iou_thr=0.3)
        self.assertAlmostEqual(b[0], 1.0)                          # (3*0 + 1*4) / 4
        self.assertAlmostEqual(s, 0.5)                             # weighted mean, both models present

    def test_skip_threshold(self):
        self.assertEqual(wbf.fuse_boxes([(0, 0.0005, [0, 0, 10, 10])], [1, 1]), [])

    def test_classes_and_images_are_not_mixed(self):
        a = [{"image_id": "x", "category_id": 1, "bbox": [0, 0, 10, 10], "score": 0.9}]
        b = [{"image_id": "x", "category_id": 2, "bbox": [0, 0, 10, 10], "score": 0.9},
             {"image_id": "y", "category_id": 1, "bbox": [0, 0, 10, 10], "score": 0.9}]
        out, imgs = wbf.fuse_files([a, b], [1, 1])
        self.assertEqual(len(out), 3)
        self.assertEqual(imgs, {"x", "y"})


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_cli_and_no_overwrite(self):
        for n in "ab":
            (self.tmp / f"{n}.json").write_text(json.dumps(
                [{"image_id": "x", "category_id": 1, "bbox": [0, 0, 10, 10], "score": 0.9}]), encoding="utf-8")
        out = self.tmp / "o" / "predictions.json"
        cmd = [sys.executable, "-I", str(ROOT / "tools" / "wbf_ensemble.py"), "--pred", str(self.tmp / "a.json"),
               "--pred", f"{self.tmp / 'b.json'}:2", "--out", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        res = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(len(res), 1)
        self.assertAlmostEqual(res[0]["score"], 0.9, places=4)
        self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_needs_two_inputs(self):
        r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "wbf_ensemble.py"), "--pred", "a.json",
                            "--out", str(self.tmp / "o.json")], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
